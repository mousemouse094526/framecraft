"""A song's reel cover settings (drum-cover spec › Data, D2, D6, D18, D19): one `cover.json` in
the Song's folder beside `song.json`, written with `write_atomic` under `songs.lock` (ADR 0052).
No file yet: the defaults, worked out from the song and its analysis. A stored stretch that a new
pick no longer covers is pulled into the picked range when read, without a write, and marked
`adjusted`; the next `PUT` saves what the page then shows.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from backend import files
from backend.checks import now_iso
from backend.drum_notes import songs
from backend.drum_notes.songs import Analysis, Song
from backend.errors import ApiError
from backend.json_values import is_int, is_number
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

VERSION = 1
COVER_FILE = "cover.json"
BACKGROUND = "cover-background.jpg"
MIN_S, MAX_S = 2, 90  # a reel's stretch (D6)
# Letters are code points, as every text of the app (story-kb D12).
TITLE_MAX = 40
LINE_MAX = 60  # subtitle, caption
VOLUME_RANGE = (10, 100)
DEFAULT_VOLUME = 35
NO_ANALYSIS = "แกะโน้ตก่อน แล้วกลับมาทำ reel"
RANGE_RULE = f"ช่วงต้องยาว {MIN_S}–{MAX_S} วินาที และอยู่ในช่วงแกะ"
NO_AUDIO = "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ"
NO_PICTURE = "ยังไม่มีภาพพื้นหลัง"


class Backing(BaseModel):
    """The original song under the drums, off unless the user turns it on (D7, ADR 0050)."""

    on: bool
    volume: int


class CoverFields(BaseModel):
    """What `PUT` takes, checked (spec › Data)."""

    start_s: float
    end_s: float
    title: str
    subtitle: str
    caption: str
    background: Literal["color", "image"]
    backing: Backing


class Cover(CoverFields):
    """One `cover.json`."""

    version: int
    updated_at: str


class CoverView(CoverFields):
    """A cover as the API answers it: whether it is saved, whether its stretch was pulled into
    the picked range, whether the song has its own audio, and the hits in the stretch (D18)."""

    saved: bool
    adjusted: bool
    has_audio: bool
    hits: int
    length_s: float
    suggested_start_s: float
    updated_at: str | None


# --- the stretch ---


def suggested_start(analysis: Analysis) -> float:
    """The start of the first found bar with a hit; the first hit itself when it comes before
    every downbeat or after the last; no hit at all: the picked range's start (D6)."""
    if not analysis.hits:
        return analysis.start_s
    first = min(hit.t for hit in analysis.hits)
    bar_start = next((start for start, end in zip(analysis.downbeats, analysis.downbeats[1:]) if start <= first < end), first)
    return round(max(analysis.start_s, bar_start), 3)


def default_stretch(analysis: Analysis) -> tuple[float, float]:
    """From `suggested_start` to the picked range's end, at most 90 s; one shorter than 2 s
    starts 2 s before the end instead (D19)."""
    start = suggested_start(analysis)
    if analysis.end_s - start < MIN_S:
        start = max(analysis.start_s, analysis.end_s - MIN_S)
    return round(start, 3), round(min(analysis.end_s, start + MAX_S), 3)


def clamped(fields: CoverFields, analysis: Analysis) -> tuple[CoverFields, bool]:
    """The stretch pulled into the picked range; shorter than 2 s after that: the default (D6, D19)."""
    start, end = max(fields.start_s, analysis.start_s), min(fields.end_s, analysis.end_s)
    if end - start < MIN_S:
        start, end = default_stretch(analysis)
    adjusted = (start, end) != (fields.start_s, fields.end_s)
    return fields.model_copy(update={"start_s": start, "end_s": end}), adjusted


def hits_in(analysis: Analysis, fields: CoverFields) -> int:
    return sum(1 for hit in analysis.hits if fields.start_s <= hit.t < fields.end_s)


# --- the API ---


def get(project: ProjectPaths, song_id: str) -> CoverView:
    """`GET /cover`. Raises `ApiError` 404 `not_found`, or 409 `no_analysis`."""
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
        return view(project, song, _stored(project, song_id))


def replace(project: ProjectPaths, song_id: str, body: dict[str, Any]) -> CoverView:
    """`PUT /cover`: the whole cover, checked; a render that runs keeps the copy it took (D12).
    Raises `ApiError` 404, 409 `no_analysis`, or 400 `invalid_request` with the field."""
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
        analysis = require_analysis(song)
        fields = checked(body, song, analysis, songs.checked_dir(project, song_id))
        cover = Cover(version=VERSION, updated_at=now_iso(), **fields.model_dump())
        write(project, song_id, cover)
        log.info("saved the reel cover of song %s", song_id)
        return view(project, song, cover)


def used(project: ProjectPaths, song: Song, check_backing: bool = True) -> CoverFields:
    """What a render or a listen plays: the stored cover pulled into the range, or the defaults.
    Call with `songs.lock` held. Raises `ApiError` 409 `no_analysis`, or 400 for backing on a
    song with no audio (D7) unless `check_backing` is off (a picture's change keeps the rest as stored)."""
    analysis = require_analysis(song)
    stored = _stored(project, song.id)
    fields = clamped(_fields(stored), analysis)[0] if stored is not None else defaults(song, analysis)
    if check_backing and fields.backing.on and not has_audio(project, song.id):
        raise songs.invalid("backing.on", NO_AUDIO)
    return fields


def defaults(song: Song, analysis: Analysis) -> CoverFields:
    """A cover never saved: the clip's title and channel as the song keeps them (drum-notes D4),
    which the page asks the user to make the song's and artist's (D18)."""
    start, end = default_stretch(analysis)
    return CoverFields(
        start_s=start,
        end_s=end,
        title=song.title[:TITLE_MAX],
        subtitle=song.subtitle[:LINE_MAX],
        caption="",
        background="color",
        backing=Backing(on=False, volume=DEFAULT_VOLUME),
    )


def require_analysis(song: Song) -> Analysis:
    if song.analysis is None:
        raise ApiError(409, "no_analysis", NO_ANALYSIS)
    return song.analysis


def has_audio(project: ProjectPaths, song_id: str) -> bool:
    return (songs.checked_dir(project, song_id) / songs.AUDIO_FILE).is_file()


def cover_file(project: ProjectPaths, song_id: str) -> Path:
    return songs.checked_dir(project, song_id) / COVER_FILE


def write(project: ProjectPaths, song_id: str, cover: Cover) -> None:
    """The whole `cover.json`, atomically. Call with `songs.lock` held."""
    files.write_atomic(cover_file(project, song_id), json.dumps(cover.model_dump(), ensure_ascii=False, indent=2))


# --- checking a body ---


def checked(body: dict[str, Any], song: Song, analysis: Analysis, folder: Path) -> CoverFields:
    """The rules of spec › Data, field by field."""
    start_s, end_s = body.get("start_s"), body.get("end_s")
    for key, value in (("start_s", start_s), ("end_s", end_s)):
        if not is_number(value) or not math.isfinite(value):
            raise songs.invalid(key, RANGE_RULE)
    start_s, end_s = round(float(start_s), 3), round(float(end_s), 3)
    if start_s < analysis.start_s:
        raise songs.invalid("start_s", RANGE_RULE)
    if end_s > analysis.end_s or not MIN_S <= end_s - start_s <= MAX_S:
        raise songs.invalid("end_s", RANGE_RULE)
    background = body.get("background")
    if background not in ("color", "image"):
        raise songs.invalid("background", "พื้นหลังไม่ถูกต้อง")
    if background == "image" and not (folder / BACKGROUND).is_file():
        raise songs.invalid("background", NO_PICTURE)
    backing = body.get("backing")
    if not isinstance(backing, dict) or not isinstance(backing.get("on"), bool):
        raise songs.invalid("backing.on", "ตัวเลือกเสียงไม่ถูกต้อง")
    volume = backing.get("volume")
    if not is_int(volume) or not VOLUME_RANGE[0] <= volume <= VOLUME_RANGE[1]:
        raise songs.invalid("backing.volume", f"ความดังเพลงต้องเป็นจำนวนเต็ม {VOLUME_RANGE[0]}–{VOLUME_RANGE[1]}")
    if backing["on"] and not (folder / songs.AUDIO_FILE).is_file():
        raise songs.invalid("backing.on", NO_AUDIO)
    return CoverFields(
        start_s=start_s,
        end_s=end_s,
        title=_text(body, "title", 1, TITLE_MAX, "หัวเรื่อง"),
        subtitle=_text(body, "subtitle", 0, LINE_MAX, "บรรทัดรอง"),
        caption=_text(body, "caption", 0, LINE_MAX, "คำบรรยาย"),
        background=background,
        backing=Backing(on=backing["on"], volume=volume),
    )


def _text(body: dict, key: str, low: int, high: int, name: str) -> str:
    """A one-line text: every run of spaces and line breaks made one space (story-kb D16)."""
    value = body.get(key)
    if not isinstance(value, str):
        raise songs.invalid(key, f"{name}ไม่ถูกต้อง")
    text = " ".join(value.split())
    if len(text) < low:
        raise songs.invalid(key, f"ใส่{name}")
    if len(text) > high:
        raise songs.invalid(key, f"{name}ยาวเกิน {high} ตัวอักษร")
    return text


# --- files; call with `songs.lock` held ---


def _stored(project: ProjectPaths, song_id: str) -> Cover | None:
    """The song's `cover.json`; None with none, and a log line for one that can't be read."""
    path = cover_file(project, song_id)
    try:
        return Cover.model_validate_json(path.read_bytes())
    except FileNotFoundError:
        return None
    except (OSError, ValidationError) as error:
        log.warning("cover of song %s can't be read: %s", song_id, type(error).__name__)
        return None


def _fields(stored: Cover) -> CoverFields:
    return CoverFields.model_validate(stored.model_dump(include=set(CoverFields.model_fields)))


def view(project: ProjectPaths, song: Song, stored: Cover | None) -> CoverView:
    analysis = require_analysis(song)
    if stored is None:
        fields, adjusted = defaults(song, analysis), False
    else:
        fields, adjusted = clamped(_fields(stored), analysis)
    if fields.background == "image" and not (songs.checked_dir(project, song.id) / BACKGROUND).is_file():
        fields = fields.model_copy(update={"background": "color"})  # its picture went: the page shows, and saves, the app's colours
    return CoverView(
        **fields.model_dump(),
        saved=stored is not None,
        adjusted=adjusted,
        has_audio=has_audio(project, song.id),
        hits=hits_in(analysis, fields),
        length_s=round(fields.end_s - fields.start_s, 3),
        suggested_start_s=suggested_start(analysis),
        updated_at=stored.updated_at if stored is not None else None,
    )
