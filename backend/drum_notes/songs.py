"""Songs of the แกะเพลง tab (drum-notes spec › Data, D3, D12, D18, D20).

A Song is `media/songs/{song_id}/song.json`, written with `write_atomic`, beside its `audio.m4a`
(none for a MIDI file). Every read and write of the folder takes `lock`. The API answers a Song as
a `SongView`: the Song and the bars its analysis found, worked out on read (spec › Score step 1). A `song_id` is the one
`spoil.links` gives imported media (ADR 0046): a YouTube id, `{site}-{id}` or `local-{sha1}`,
`[A-Za-z0-9_-]{1,64}`; every function checks it before it builds a path, so `..` never reaches
the disk. Start-up removes `.partial/` and any folder without a `song.json`: no json, no Song.
"""

import json
import logging
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import files, json_values
from backend.checks import now_iso
from backend.errors import ApiError, invalid_request
from backend.paths import ProjectPaths
from backend.spoil import links
from backend.video_gen import kit, lessons

log = logging.getLogger(__name__)

VERSION = 1
SONG_FILE = "song.json"
AUDIO_FILE = "audio.m4a"
# Letters are code points, `len` here and `[...text].length` on the page (story-kb D12).
TITLE_MAX = 60
MIN_SECONDS = 4
MAX_SECONDS = 600
RANGE_MIN_S = 4
RANGE_MAX_S = 90
DEFAULT_RANGE_END_S = 30
MAX_HITS = 20_000
TOO_LONG = f"เพลงยาวเกิน {MAX_SECONDS // 60} นาที"
TOO_SHORT = f"เพลงสั้นกว่า {MIN_SECONDS} วินาที"
IN_USE = "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง"
SONG_BUSY = "กำลังแกะเพลงนี้อยู่"
NOT_APPLICABLE = "เพลงจาก MIDI ไม่มีช่วงแกะ: การตีทั้งไฟล์คือผลอยู่แล้ว"
RANGE_RULE = f"ช่วงต้องยาว {RANGE_MIN_S}–{RANGE_MAX_S} วินาที และอยู่ในเพลง"

# The song an unfinished job works on, or None: `drum_notes.pick` adds its own as it is imported,
# which the routes do, so `delete` sees a Pick job before the app answers anything (D18; as `lessons.lesson_jobs`).
song_jobs: list[Callable[[], str | None]] = []

SourceKind = Literal["link", "file", "midi"]
Mode = Literal["drums", "melody"]
Level = Literal["ghost", "normal", "accent"]


class Source(BaseModel):
    """Where the Song came from: a link's `url`, or a file's `name` and `size` (D3, D4)."""

    kind: SourceKind
    url: str | None = None
    name: str | None = None
    size: int | None = None


class Range(BaseModel):
    """The stretch the Pick job works on, and in which mode (D5, D14); null for MIDI."""

    start_s: float
    end_s: float
    mode: Mode


class Hit(BaseModel):
    t: float  # seconds of the song
    piece: str  # an id of `video_gen.kit`
    level: Level


class Analysis(BaseModel):
    """What was found: beats and downbeats in seconds of the song, the hits, and when (D6, D10)."""

    mode: Mode
    start_s: float
    end_s: float
    beats: list[float]
    downbeats: list[float]
    hits: list[Hit]
    picked_at: str


class Song(BaseModel):
    """One `song.json`."""

    version: int
    id: str
    title: str
    subtitle: str
    source: Source
    duration_s: float
    range: Range | None
    analysis: Analysis | None
    lessons: list[str]
    created_at: str
    updated_at: str


class AnalysisSummary(BaseModel):
    """The list's view of an analysis: its mode and how many bars were found (D20)."""

    mode: Mode
    bars: int


class SongRow(BaseModel):
    """One row of `GET /api/songs`: no `hits`, the lessons as a count (spec › API)."""

    id: str
    title: str
    subtitle: str
    source_kind: SourceKind
    duration_s: float
    analysis: AnalysisSummary | None
    lessons: int
    updated_at: str


class FoundBar(BaseModel):
    """One bar between two downbeats of `analysis`, as `GET /songs/{id}` lists them: its number
    from 1, its seconds, how many beats and hits it holds, and whether four beats make it 4/4
    (spec › Score step 1, D20); worked out when the Song is read, never stored."""

    n: int
    start_s: float
    end_s: float
    beats: int
    hits: int
    four_four: bool


class SongView(Song):
    """A Song as the API answers it: the Song and the bars its analysis found (empty with none)."""

    bars: list[FoundBar]


class KnownSong(BaseModel):
    """The answer when what was asked in is a Song already: its id (D3, D20)."""

    song_id: str


lock = threading.Lock()


# --- checking values ---


def checked_analysis(analysis: Analysis) -> Analysis:
    """The rules of spec › Data: beats and downbeats ascending seconds, the downbeats among the
    beats and at least two, hits of known pieces and at most 20,000. Raises `invalid` with the field."""
    if analysis.beats != sorted(analysis.beats):
        raise invalid("analysis.beats", "จังหวะต้องเรียงตามเวลา")
    if analysis.downbeats != sorted(analysis.downbeats) or len(analysis.downbeats) < 2:
        raise invalid("analysis.downbeats", "ต้องพบต้นห้องอย่างน้อย 2 ตัว")
    if not set(analysis.downbeats) <= set(analysis.beats):
        raise invalid("analysis.downbeats", "ต้นห้องต้องเป็นจังหวะด้วย")
    if len(analysis.hits) > MAX_HITS:
        raise invalid("analysis.hits", f"การตีเกิน {MAX_HITS:,} ตัว")
    for index, hit in enumerate(analysis.hits):
        if hit.piece not in kit.BY_ID:
            raise invalid(f"analysis.hits[{index}]", "ไม่รู้จักชิ้นกลองนี้")
    return analysis


def default_range(duration_s: float) -> Range:
    """A new audio Song's stretch: from the start to 30 s, or to the end of a shorter song (D5)."""
    return Range(start_s=0.0, end_s=min(float(DEFAULT_RANGE_END_S), duration_s), mode="drums")


def checked_range(body: dict, duration_s: float) -> Range:
    """The rules of spec › Data: `start_s` ≥ 0, `end_s` ≤ `duration_s`, 4 ≤ `end_s − start_s` ≤ 90, a
    known `mode` (D5, D18). Raises `invalid_request` with the field that fails."""
    start_s, end_s, mode = body.get("start_s"), body.get("end_s"), body.get("mode")
    if not json_values.is_number(start_s) or not json_values.is_number(end_s) or mode not in ("drums", "melody"):
        raise invalid_request()
    if start_s < 0:
        raise invalid("start_s", RANGE_RULE)
    if end_s > duration_s:
        raise invalid("end_s", RANGE_RULE)
    if not RANGE_MIN_S <= end_s - start_s <= RANGE_MAX_S:
        raise invalid("end_s", RANGE_RULE)
    return Range(start_s=round(float(start_s), 3), end_s=round(float(end_s), 3), mode=mode)


def invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "invalid_request", message, field=field)


def not_found() -> ApiError:
    return ApiError(404, "not_found", "ไม่พบเพลงนี้")


# --- the API ---


def list_rows(project: ProjectPaths) -> list[SongRow]:
    """Every readable Song, latest change first; a `song.json` that can't be read is logged and
    left out, and can still be deleted (D20)."""
    rows = []
    with lock:
        folders = sorted(project.songs_dir.iterdir()) if project.songs_dir.is_dir() else []
        for folder in folders:
            if not links.CLIP_ID.fullmatch(folder.name):
                continue
            song = _read_folder(folder)
            if song is not None:
                rows.append(_row(project, song))
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows


def get(project: ProjectPaths, song_id: str) -> SongView:
    """`GET`: the whole Song with its bars, its `lessons` without the ones deleted since. Raises `ApiError` 404."""
    with lock:
        return view(_with_live_lessons(project, _read_known(project, song_id)))


def view(song: Song) -> SongView:
    """The Song as the API answers it, its bars worked out from the analysis (none: no bars)."""
    return SongView(**song.model_dump(), bars=bars_of(song.analysis) if song.analysis else [])


def bars_of(analysis: Analysis) -> list[FoundBar]:
    """Score step 1: the bars between consecutive downbeats, each with its beats (the downbeat among
    them) and hits counted; four beats make a 4/4 bar, any other count can't be picked for a lesson (D20)."""
    bars = []
    for index, (start, end) in enumerate(zip(analysis.downbeats, analysis.downbeats[1:])):
        beats = sum(1 for t in analysis.beats if start <= t < end)
        hits = sum(1 for hit in analysis.hits if start <= hit.t < end)
        bars.append(FoundBar(n=index + 1, start_s=start, end_s=end, beats=beats, hits=hits, four_four=beats == 4))
    return bars


def set_range(project: ProjectPaths, song_id: str, body: dict) -> SongView:
    """`PUT /range`: the stretch the next Pick job works on and its mode (D5). Raises `ApiError` 404,
    409 `not_applicable` for a MIDI song (D18), or 400 `invalid_request` with the field."""
    with lock:
        song = _read_known(project, song_id)
        if song.source.kind == "midi":
            raise ApiError(409, "not_applicable", NOT_APPLICABLE)
        song = song.model_copy(update={"range": checked_range(body, song.duration_s), "updated_at": now_iso()})
        _write(project, song)
        return view(_with_live_lessons(project, song))


def set_analysis(project: ProjectPaths, song_id: str, analysis: Analysis) -> None:
    """A Pick job's result in place of the old one, whole (D6). Raises `ApiError` 404 when the song went."""
    with lock:
        song = _read_known(project, song_id)
        _write(project, song.model_copy(update={"analysis": checked_analysis(analysis), "updated_at": now_iso()}))


def add_lesson(project: ProjectPaths, song_id: str, lesson_id: str) -> None:
    """A lesson made from the song, remembered in its `lessons` (D12, ADR 0044). Raises `ApiError` 404 when the song went."""
    with lock:
        song = _read_known(project, song_id)
        _write(project, song.model_copy(update={"lessons": [*song.lessons, lesson_id], "updated_at": now_iso()}))


def read_under_lock(project: ProjectPaths, song_id: str) -> Song:
    """The stored Song, for a caller that holds `lock`. Raises `ApiError` 404 `not_found`."""
    return _read_known(project, song_id)


def require_idle(song_id: str) -> None:
    """Raises `ApiError` 409 `song_busy` while a Pick job works on the song (D18). Call with `lock` held."""
    if any(job() == song_id for job in song_jobs):
        raise ApiError(409, "song_busy", SONG_BUSY)


def exists(project: ProjectPaths, song_id: str) -> bool:
    """Whether a Song of this id is listed (its `song.json` written). Call with `lock` held or not."""
    return links.CLIP_ID.fullmatch(song_id) is not None and (project.song_dir(song_id) / SONG_FILE).is_file()


def write_new(project: ProjectPaths, song: Song) -> Song:
    """A Song that isn't there yet, json last; one that is stays as it is and is returned (D20).
    Call with `lock` held: the caller moves the audio in under the same lock."""
    existing = _read_folder(checked_dir(project, song.id))
    if existing is not None:
        return existing
    _write(project, song)
    log.info("new song %s (%s, %.1f s)", song.id, song.source.kind, song.duration_s)
    return song


def delete(project: ProjectPaths, song_id: str) -> None:
    """`audio.m4a` first (a player may hold it open: `409` `in_use`), `song.json` last, then the
    folder; the lessons made from the song stay (D12, D18). Raises `ApiError` 404, or 409."""
    with lock:
        folder = checked_dir(project, song_id)
        if not (folder / SONG_FILE).is_file():
            raise not_found()
        require_idle(song_id)
        try:
            (folder / AUDIO_FILE).unlink(missing_ok=True)
        except PermissionError:
            raise ApiError(409, "in_use", IN_USE) from None
        (folder / SONG_FILE).unlink()
        shutil.rmtree(folder, ignore_errors=True)
    log.info("deleted song %s", song_id)


def audio_file(project: ProjectPaths, song_id: str) -> Path:
    """The Song's `audio.m4a`. Raises `ApiError` 404 for no song or no audio (a MIDI song)."""
    with lock:
        _read_known(project, song_id)
        path = checked_dir(project, song_id) / AUDIO_FILE
        if not path.is_file():
            raise ApiError(404, "not_found", "เพลงนี้ไม่มีไฟล์เสียง")
    return path


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart: `.partial/` is emptied, a folder with no `song.json` (an
    import that never finished) goes, and a `.tmp` of a json write that never finished (D20)."""
    shutil.rmtree(project.songs_partial_dir, ignore_errors=True)
    if project.songs_dir.is_dir():
        for folder in project.songs_dir.iterdir():
            if folder.is_dir() and not (folder / SONG_FILE).is_file():
                shutil.rmtree(folder, ignore_errors=True)
    files.remove_unfinished(project.songs_dir)


# --- files; call with `lock` held ---


def checked_dir(project: ProjectPaths, song_id: str) -> Path:
    """`project.song_dir(song_id)`, once the id is checked: `ApiError` 404 for one off the pattern (ADR 0046)."""
    if not links.CLIP_ID.fullmatch(song_id):
        raise not_found()
    return project.song_dir(song_id)


def new_song(song_id: str, title: str, subtitle: str, source: Source, duration_s: float, range_: Range | None, analysis: Analysis | None) -> Song:
    now = now_iso()
    return Song(
        version=VERSION,
        id=song_id,
        title=title,
        subtitle=subtitle,
        source=source,
        duration_s=round(duration_s, 1),
        range=range_,
        analysis=analysis,
        lessons=[],
        created_at=now,
        updated_at=now,
    )


def _write(project: ProjectPaths, song: Song) -> None:
    checked_dir(project, song.id).mkdir(parents=True, exist_ok=True)
    text = json.dumps(song.model_dump(), ensure_ascii=False, indent=2)
    files.write_atomic(checked_dir(project, song.id) / SONG_FILE, text)


def _read_known(project: ProjectPaths, song_id: str) -> Song:
    song = _read_folder(checked_dir(project, song_id))
    if song is None:
        raise not_found()
    return song


def _read_folder(folder: Path) -> Song | None:
    """The folder's Song; None with no file, and a log line for one that can't be read."""
    path = folder / SONG_FILE
    try:
        return Song.model_validate_json(path.read_bytes())
    except FileNotFoundError:
        return None
    except (OSError, ValidationError) as error:
        log.warning("song %s can't be read: %s", folder.name, type(error).__name__)
        return None


def _with_live_lessons(project: ProjectPaths, song: Song) -> Song:
    """The Song with only the lessons still on disk (D12): a lesson deleted in the สอนกลอง tab goes
    from the list on the next read, without a write."""
    live = [lesson_id for lesson_id in song.lessons if (project.lessons_dir / lesson_id / lessons.LESSON_FILE).is_file()]
    return song if live == song.lessons else song.model_copy(update={"lessons": live})


def _row(project: ProjectPaths, song: Song) -> SongRow:
    summary = None
    if song.analysis is not None:
        summary = AnalysisSummary(mode=song.analysis.mode, bars=max(0, len(song.analysis.downbeats) - 1))
    return SongRow(
        id=song.id,
        title=song.title,
        subtitle=song.subtitle,
        source_kind=song.source.kind,
        duration_s=song.duration_s,
        analysis=summary,
        lessons=len(_with_live_lessons(project, song).lessons),
        updated_at=song.updated_at,
    )
