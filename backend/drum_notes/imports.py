"""Song import: a song comes in from a link, an audio file or a MIDI file (drum-notes spec › Song
import, D3, D4, D10, D18, D20; ADR 0028, ADR 0045, ADR 0046).

A link is a job in its own slot (thread, ADR 0010) on `backend.audio_imports`: the info, the id it
gives (a song already listed ends the job `done` with that id and loads nothing), the best audio
into `media/songs/.partial/`, then aac in m4a and `song.json` last. A file is one request: its raw
body to `.partial/`, then the same conversion, or `midi.read` for a `.mid`, which needs no audio.
One of the two at a time (`busy`); a Pick job runs beside them in its own slot.
"""

import logging
import os
import shutil
import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Literal

import anyio
from pydantic import BaseModel
from starlette.requests import ClientDisconnect

from backend import audio_imports, checks, disk, gate_rows, paths, uploads
from backend.audio_imports import ImportSlot, Limits, State
from backend.drum_notes import midi, songs
from backend.drum_notes.songs import TOO_LONG, TOO_SHORT, KnownSong, Song, Source
from backend.errors import ApiError, JobFailed, invalid_request, require_rows
from backend.jobs import Cancelled
from backend.paths import ProjectPaths
from backend.spoil import links
from backend.spoil.adapter import DownloadCancelled, error_code

log = logging.getLogger(__name__)

ErrorCode = Literal[
    "unsupported",
    "playlist",
    "live",
    "login_required",
    "unavailable",
    "download_error",
    "too_long",
    "too_short",
    "disk_full",
    "unsupported_file",
    "internal",
]

UPLOAD_MAX_BYTES = 200 * 1024**2
MIDI_MAX_BYTES = 5 * 1024**2
MIDI_SUFFIXES = (".mid", ".midi")
BYTES_PER_SECOND = 16 * 1024  # the spec's rough figure for a song's m4a on disk, for the free-space check (D20)
UPLOAD_SUFFIX = ".upload"

BUSY = "กำลังเอาเพลงอื่นเข้าอยู่"
LIMITS = Limits(max_seconds=songs.MAX_SECONDS, too_long=TOO_LONG, min_seconds=songs.MIN_SECONDS, too_short=TOO_SHORT)
PICK_FILE = 'โหลดเพลงเองแล้วกด "เลือกไฟล์ในเครื่อง"'
ERROR_MESSAGES: dict[ErrorCode, str] = {
    "unsupported": f"เว็บนี้โหลดอัตโนมัติไม่ได้ {PICK_FILE}",
    "playlist": audio_imports.PLAYLIST,
    "live": "ลิงก์นี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้",
    "login_required": f"เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ {PICK_FILE}",
    "unavailable": "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้",
    "download_error": "โหลดเพลงจากลิงก์นี้ไม่สำเร็จ",
    "too_long": TOO_LONG,
    "too_short": TOO_SHORT,
    "unsupported_file": audio_imports.UNREADABLE,
}
# A file's refusal keeps the job's code; its status is the spec's (spec › API).
FILE_STATUSES = {"unsupported_file": 415, "too_long": 422, "too_short": 422}

# Where a link's audio lands: the tab's `.partial/`, no thumbnail, no mp4 merge.
LINK_OPTIONS = audio_imports.link_options(lambda project: project.songs_partial_dir)


class SongImportError(BaseModel):
    code: ErrorCode
    message: str


class SongImport(BaseModel):
    """A link's Song import; a file's is one request and never shows here."""

    url: str
    state: State
    title: str | None = None
    percent: int | None = None
    error: SongImportError | None = None
    cancel_requested: bool = False
    song_id: str | None = None  # the song, once the info names it (D20): new when `done`, or one already in
    started_at: str


class SongImports(ImportSlot[SongImport]):
    """The tab's import slot: the latest link import, and whether a file is being received, one
    of the two at a time (D18); a Pick job runs beside it in its own slot."""

    busy = BUSY

    # --- a file ---

    def check(self, body: dict) -> uploads.UploadCheck | KnownSong:
        """Every check of the file but its body's, before the page sends it (ADR 0028); a file
        already in as a Song answers its id instead (D20)."""
        project = paths.project()
        name, size = _file_checks(project, body.get("name"), body.get("size"))
        song_id = links.local_id(name, size)
        if songs.exists(project, song_id):
            return KnownSong(song_id=song_id)
        with self._lock:
            self._require_free()
        return uploads.UploadCheck(size=size)

    async def receive(
        self, name: str | None, size: str | None, body: AsyncIterator[bytes], page_gone: Callable[[], Awaitable[bool]]
    ) -> Song:
        """Checks again, writes `body` to `.partial/`, then the Song: a `.mid` read by `midi`, anything
        else converted to `audio.m4a`. `page_gone` says whether the page went away: ffmpeg stops then
        and no song comes in. Raises `ApiError`, or `ClientDisconnect` once its file is gone."""
        project = paths.project()
        name, expected = await anyio.to_thread.run_sync(_file_checks, project, name, uploads.whole_number(size))
        song_id = links.local_id(name, expected)
        if songs.exists(project, song_id):
            return songs.get(project, song_id)
        source = Source(kind="midi" if _is_midi(name) else "file", name=name, size=expected)
        with self.receiving():
            partial = project.songs_partial_dir / f"{song_id}{UPLOAD_SUFFIX}"
            try:
                await uploads.receive(body, partial, expected, self._stall_seconds)
                if source.kind == "midi":
                    return await anyio.to_thread.run_sync(_midi_song, project, song_id, partial, source)
                cancel = threading.Event()
                return await audio_imports.run_unless_gone(
                    page_gone,
                    cancel,
                    lambda: self._take_in(
                        project, song_id, partial, audio_imports.file_title(name), "", source, cancel, audio_imports.still_wanted(page_gone, cancel)
                    ),
                )
            except (Cancelled, ClientDisconnect):  # `Cancelled`: the page left during ffmpeg
                log.info("the song import %s stopped: the page went away", song_id)
                raise ClientDisconnect() from None
            except JobFailed as refused:
                raise ApiError(FILE_STATUSES.get(refused.code, 400), refused.code, refused.message) from None
            finally:
                with anyio.CancelScope(shield=True):
                    await anyio.to_thread.run_sync(_remove_unfinished, project, song_id, partial)

    # --- a link ---

    def start(self, body: dict) -> tuple[int, dict]:
        """The gate, the link (spoil's rules, ADR 0029), `busy`; then the answer as its status and
        body: `202` with the job once its thread runs, or `200` with the song's id for a YouTube
        link whose song is listed already (spec › Song import, D3)."""
        require_rows(gate_rows.SONGS_LINK)
        url = body.get("url")
        link = links.parse(url) if isinstance(url, str) else None
        if link is None:
            raise ApiError(400, "invalid_request", "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของเพลง")
        project = paths.project()
        with self._lock:
            self._require_free()
            if link.youtube_id and songs.exists(project, link.youtube_id):
                return 200, KnownSong(song_id=link.youtube_id).model_dump()
            self._job = SongImport(url=link.url, state="checking", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, link.url), daemon=True).start()
        return 202, job.model_dump()

    def cancel(self) -> SongImport:
        with self._lock:
            if not self._taken():
                raise ApiError(409, "not_running", "ไม่มีการเอาเพลงเข้าที่ยังไม่จบ")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def _run(self, project: ProjectPaths, url: str) -> None:
        known: str | None = None  # the song's id, once the info gave it: what the ending cleans by
        ending: dict = {"state": "failed"}

        def found(song_id: str) -> None:
            nonlocal known
            known = song_id
            self.update(song_id=song_id)

        try:
            ending = {"state": "done", "song_id": self._download(project, url, found), "percent": 100}
        except (DownloadCancelled, Cancelled):
            ending = {"state": "cancelled"}
        except JobFailed as failure:
            ending["error"] = SongImportError(code=failure.code, message=failure.message)
        except Exception as error:
            code = error_code(error)
            if code not in ERROR_MESSAGES:
                code = "download_error"
            log.exception("song download of %s failed", url)
            ending["error"] = SongImportError(code=code, message=ERROR_MESSAGES[code])
        finally:
            if known is not None:
                audio_imports.remove_leftovers(project.songs_partial_dir, known)
                if ending["state"] != "done":
                    _remove_unfinished(project, known, None)
            self.update(**ending)

    def _download(self, project: ProjectPaths, url: str, found: Callable[[str], None]) -> str:
        """The info and the id it gives (`found` learns it, so the ending can clean by it), a song
        already in (D20), the free space, the load with %, the conversion; returns the song's id."""
        info = audio_imports.fetch_info(url, LINK_OPTIONS, LIMITS, self._cancel)
        if info.get("live_status") in ("is_live", "is_upcoming"):
            raise JobFailed("live", ERROR_MESSAGES["live"])
        song_id = links.clip_id(info["extractor_key"], str(info["id"]))
        found(song_id)
        if songs.exists(project, song_id):
            log.info("the link %s is song %s already", url, song_id)
            return song_id
        estimate = audio_imports.estimate_bytes(info) + int(info.get("duration") or 0) * BYTES_PER_SECOND
        try:
            disk.require_free(project.root, estimate)
        except ApiError as full:
            raise JobFailed("disk_full", full.message) from None
        title = audio_imports.first_name(info.get("title"), fallback=song_id)
        subtitle = audio_imports.first_name(info.get("channel") or info.get("uploader"))
        self.update(state="downloading", title=title, percent=0)
        loaded = audio_imports.download(project, info, song_id, LINK_OPTIONS, lambda percent: self.update(percent=percent), self._cancel)
        self.update(state="converting", percent=None)
        source = Source(kind="link", url=info.get("webpage_url") or url)
        return self._take_in(project, song_id, loaded, title, subtitle, source, self._cancel).id

    # --- both ---

    def _take_in(
        self,
        project: ProjectPaths,
        song_id: str,
        loaded: Path,
        title: str,
        subtitle: str,
        source: Source,
        cancel: threading.Event,
        still_wanted: Callable[[], bool] | None = None,
    ) -> Song:
        """In a thread: `audio_imports.take_in` into the song's folder, `song.json` written last under
        the songs' lock. Raises `JobFailed`, or `Cancelled`."""
        target = project.song_dir(song_id) / songs.AUDIO_FILE

        def place(seconds: float) -> Song:
            song = songs.new_song(song_id, title, subtitle, source, seconds, songs.default_range(seconds), None)
            with songs.lock:
                if songs.exists(project, song_id):  # the same song came in meanwhile: that one stays
                    return songs.get(project, song_id)
                os.replace(audio_imports.partial_of(target), target)
                return songs.write_new(project, song)

        return audio_imports.take_in(loaded, target, LIMITS, self._convert, cancel, place, still_wanted)


# --- helpers ---


def _midi_song(project: ProjectPaths, song_id: str, partial: Path, source: Source) -> Song:
    """A `.mid` as a Song with its analysis and no audio (D10)."""
    track = midi.read(partial.read_bytes())
    title = audio_imports.first_name(track.title, fallback=audio_imports.file_title(source.name))
    song = songs.new_song(song_id, title, "", source, track.duration_s, None, songs.checked_analysis(track.analysis))
    with songs.lock:
        return songs.write_new(project, song)


def _file_checks(project: ProjectPaths, name: object, size: object) -> tuple[str, int]:
    """The gate, the name, the size (a `.mid` has its own limit, `413`), the disk; returns both."""
    require_rows(gate_rows.SONGS_FILE)
    if not isinstance(name, str) or not audio_imports.file_title(name):
        raise invalid_request()
    limit = MIDI_MAX_BYTES if _is_midi(name) else UPLOAD_MAX_BYTES
    size = uploads.require_size(size, limit, f"ไฟล์ใหญ่เกิน {limit // 1024**2} MB", too_large_status=413)
    disk.require_free(project.root, size)
    return name, size


def _is_midi(name: str) -> bool:
    return name.lower().endswith(MIDI_SUFFIXES)


def _remove_unfinished(project: ProjectPaths, song_id: str, partial: Path | None) -> None:
    """An upload's file, and the song's folder when no `song.json` made it a Song (D20)."""
    if partial is not None:
        partial.unlink(missing_ok=True)
    if not songs.exists(project, song_id):
        shutil.rmtree(project.song_dir(song_id), ignore_errors=True)


song_imports = SongImports()
