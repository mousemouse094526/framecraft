"""Temp clips on disk: `{id}.mp4`, a thumbnail `{id}.{ext}`, and `{id}.json`
written last, so a clip without json is unfinished (spoil D14, D15)."""

import logging
import mimetypes
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, ValidationError

from backend import files
from backend.paths import ProjectPaths
from backend.errors import ApiError
from backend.spoil import links
from backend.spoil_maker import draft_file, shots

log = logging.getLogger(__name__)


class Range(BaseModel):
    """A span of a clip's time in seconds: `[start_s, end_s)`."""

    start_s: float
    end_s: float


class TempClip(BaseModel):
    id: str
    title: str
    # None for a local file (D52), and for a site that names no channel or uploader.
    channel: str | None
    # yt-dlp's `extractor_key`, or "local"; a json from before other sites is YouTube's (D52).
    site: str = links.YOUTUBE_KEY
    source_url: str | None
    duration_s: int | None
    width: int | None
    height: int | None
    orientation: Literal["portrait", "landscape"]
    file_bytes: int
    thumbnail: str | None
    downloaded_at: str
    yt_dlp_version: str | None
    # The ranges cut out, each in the time of the file before that cut; none before any (D36, D41).
    trimmed: list[Range] = []
    trimmed_at: str | None = None


class ListedClip(TempClip):
    """A row of `GET /clips`: the stored clip plus whether it has a Transcript (D23),
    Shots (spoil-maker D16), and a Spoil draft made from it (spoil-maker D49)."""

    transcribed: bool
    described: bool
    in_draft: bool


files_lock = threading.Lock()
"""Guards a Temp clip's files while they go or change under a job: a clip delete and a
Trim job's new mp4 take it, and so do a Transcribe job's start and a Transcript line
edit, so none slips between the others' checks and writes (D29, D42). Lock order: a job
slot's lock, then this one, then `gpu.slot.draft_lock`, then the GPU slot's own."""

TRANSCRIPT_SUFFIX = ".transcript.json"
TRIMMING_SUFFIX = ".trimming.json"  # the new json of a clip whose mp4 is being replaced (D41)


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "ไม่พบคลิปนี้")


def json_path(project: ProjectPaths, clip_id: str) -> Path:
    return project.clip_json(clip_id)


def has_clip(project: ProjectPaths, clip_id: str) -> bool:
    return json_path(project, clip_id).is_file()


def find_thumbnail(project: ProjectPaths, clip_id: str) -> str | None:
    """The thumbnail's file name; yt-dlp keeps whatever extension YouTube sent."""
    for path in project.media_temp_dir.glob(f"{clip_id}.*"):
        if path.suffix not in (".mp4", ".json", ".tmp"):
            return path.name
    return None


def list_clips(project: ProjectPaths) -> list[ListedClip]:
    """Every clip with both json and mp4, newest first; a json that can't be read is skipped.

    `{id}.transcript.json` and `{id}.trimming.json` are not clips, and `transcribed` only
    asks whether the Transcript exists (D29, D41).
    """
    found: list[tuple[datetime, ListedClip]] = []
    in_draft = draft_file.draft_clip_id(project)
    for path in project.media_temp_dir.glob("*.json"):
        if path.name.endswith((TRANSCRIPT_SUFFIX, TRIMMING_SUFFIX)):
            continue
        try:
            clip = TempClip.model_validate_json(path.read_bytes())
            downloaded = _instant(clip.downloaded_at)
        except (OSError, ValidationError, ValueError):
            log.warning("skipping unreadable %s", path)
            continue
        if clip.id == path.stem and video_path(project, clip.id).is_file():
            found.append((downloaded, _listed(project, clip, in_draft)))
    found.sort(key=lambda pair: pair[0], reverse=True)
    return [clip for _, clip in found]


def listed_clip(project: ProjectPaths, clip_id: str) -> ListedClip:
    """One row of `list_clips`. Raises `ApiError` 404 unless the clip has both json and mp4 (D46)."""
    video_file(project, clip_id)
    return _listed(project, read_clip(project, clip_id), draft_file.draft_clip_id(project))


def _listed(project: ProjectPaths, clip: TempClip, in_draft: str | None) -> ListedClip:
    transcribed = transcript_path(project, clip.id).is_file()
    described = shots.is_described(project, clip.id)
    return ListedClip(**clip.model_dump(), transcribed=transcribed, described=described, in_draft=clip.id == in_draft)


def read_clip(project: ProjectPaths, clip_id: str) -> TempClip:
    """A listed clip's `{id}.json`. Raises `ApiError` 404 when it isn't there."""
    check_known(project, clip_id)
    try:
        return TempClip.model_validate_json(json_path(project, clip_id).read_bytes())
    except (OSError, ValidationError):
        raise _not_found() from None


def video_file(project: ProjectPaths, clip_id: str) -> Path:
    """The clip's mp4. Raises `ApiError` 404 when it isn't a listed clip."""
    check_known(project, clip_id)
    mp4 = video_path(project, clip_id)
    if not mp4.is_file():
        raise _not_found()
    return mp4


class Thumbnail(NamedTuple):
    path: Path
    media_type: str | None  # None: let the response guess


def thumbnail(project: ProjectPaths, clip_id: str) -> Thumbnail:
    """The clip's thumbnail and its media type: from the extension, or from the first
    bytes when a site's extension names none (TikTok's `{id}.image`, D56). Raises
    `ApiError` 404 when there is none."""
    check_known(project, clip_id)
    name = find_thumbnail(project, clip_id)
    if name is None:
        raise _not_found()
    path = project.media_temp_dir / name
    return Thumbnail(path, mimetypes.guess_type(name)[0] or _image_type(path))


# The first bytes of the image types sites send.
IMAGE_SIGNATURES = ((b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG\r\n\x1a\n", "image/png"))


def _image_type(path: Path) -> str | None:
    """The image's media type from its first bytes, or None for a type not known here."""
    with path.open("rb") as image:
        head = image.read(12)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return next((media for signature, media in IMAGE_SIGNATURES if head.startswith(signature)), None)


def delete_clip(project: ProjectPaths, clip_id: str) -> None:
    """mp4, thumbnail and Transcript first, json last, so a clip half deleted is
    cleaned at the next start (D15, D23).

    An mp4 Windows still holds open → `ApiError` 409 `in_use`, json untouched.
    The API calls it through `transcribe.transcriptions.delete_clip`, which holds
    `files_lock` and refuses a clip being transcribed.
    """
    check_known(project, clip_id)
    try:
        video_path(project, clip_id).unlink(missing_ok=True)
    except PermissionError:
        raise ApiError(409, "in_use", "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง") from None
    thumbnail = find_thumbnail(project, clip_id)
    if thumbnail:
        _remove(project.media_temp_dir / thumbnail)
    delete_derived(project, clip_id)
    json_path(project, clip_id).unlink(missing_ok=True)


def delete_derived(project: ProjectPaths, clip_id: str) -> None:
    """What was made from the clip's mp4: its Transcript, Shots and EP cuts, whichever
    feature made them (ADR 0018, ADR 0021). A delete and a Trim job share it (D37);
    the Spoil draft goes apart, after the slot's lock (spoil-maker D49)."""
    _remove(transcript_path(project, clip_id))
    shutil.rmtree(project.clip_shots_dir(clip_id), ignore_errors=True)
    project.episodes_file(clip_id).unlink(missing_ok=True)


def _remove(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        log.exception("could not remove %s; it goes at the next start", path.name)


def check_known(project: ProjectPaths, clip_id: str) -> None:
    """Only a `CLIP_ID` with its json gets near the disk (no path traversal, D51)."""
    if not links.CLIP_ID.fullmatch(clip_id) or not has_clip(project, clip_id):
        raise _not_found()


def video_path(project: ProjectPaths, clip_id: str) -> Path:
    """Where the clip's mp4 is, whether or not it is there; `video_file` checks."""
    return project.media_temp_dir / f"{clip_id}.mp4"


def transcript_path(project: ProjectPaths, clip_id: str) -> Path:
    return project.media_temp_dir / f"{clip_id}{TRANSCRIPT_SUFFIX}"


def _instant(downloaded_at: str) -> datetime:
    """Compared as instants, not text: offsets may differ between clips.

    Raises ValueError for a time without an offset, which can't be compared.
    """
    instant = datetime.fromisoformat(downloaded_at)
    if instant.tzinfo is None:
        raise ValueError(f"no UTC offset: {downloaded_at}")
    return instant


def write_clip(project: ProjectPaths, clip: TempClip) -> None:
    """Writes `{id}.json` so it appears complete or not at all."""
    files.write_atomic(json_path(project, clip.id), clip.model_dump_json(indent=2))


def remove_unfinished(project: ProjectPaths, clip_id: str) -> None:
    """Deletes one job's files in .partial/ and its `{id}.*` that has no json.

    Best effort: a file Windows still holds open is logged and left for the
    clean-up at the next start.
    """
    leftovers = list(project.partial_dir.glob(f"{clip_id}.*"))
    if not has_clip(project, clip_id):
        leftovers += project.media_temp_dir.glob(f"{clip_id}.*")
    for path in leftovers:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            log.exception("could not remove %s", path)


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart, so nothing they left is worth keeping."""
    shutil.rmtree(project.partial_dir, ignore_errors=True)
    project.partial_dir.mkdir(parents=True, exist_ok=True)
    for path in project.media_temp_dir.iterdir():
        clip_id = path.name.split(".")[0]
        # A `.tmp` is a json write that never finished (D29); other than that, only
        # `{id}.*` with a name the app makes is ours, and anything else (.DS_Store, a
        # user's notes.txt) stays (D55).
        unfinished = path.suffix == ".tmp" or (links.is_app_made(clip_id) and not has_clip(project, clip_id))
        if path.is_file() and unfinished:
            path.unlink(missing_ok=True)
