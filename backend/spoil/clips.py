"""Temp clips on disk: `{id}.mp4`, a thumbnail `{id}.{ext}`, and `{id}.json`
written last, so a clip without json is unfinished (spoil D14, D15)."""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend.paths import ProjectPaths
from backend.spoil.errors import SpoilError
from backend.spoil.links import VIDEO_ID

log = logging.getLogger(__name__)


class TempClip(BaseModel):
    id: str
    title: str
    channel: str | None
    source_url: str
    duration_s: int | None
    width: int | None
    height: int | None
    orientation: Literal["portrait", "landscape"]
    file_bytes: int
    thumbnail: str | None
    downloaded_at: str
    yt_dlp_version: str


def _not_found() -> SpoilError:
    return SpoilError(404, "not_found", "ไม่พบคลิปนี้")


def json_path(project: ProjectPaths, video_id: str) -> Path:
    return project.media_temp_dir / f"{video_id}.json"


def has_clip(project: ProjectPaths, video_id: str) -> bool:
    return json_path(project, video_id).is_file()


def find_thumbnail(project: ProjectPaths, video_id: str) -> str | None:
    """The thumbnail's file name; yt-dlp keeps whatever extension YouTube sent."""
    for path in project.media_temp_dir.glob(f"{video_id}.*"):
        if path.suffix not in (".mp4", ".json", ".tmp"):
            return path.name
    return None


def list_clips(project: ProjectPaths) -> list[TempClip]:
    """Every clip with both json and mp4, newest first; a json that can't be read is skipped."""
    found: list[tuple[datetime, TempClip]] = []
    for path in project.media_temp_dir.glob("*.json"):
        try:
            clip = TempClip.model_validate_json(path.read_bytes())
            downloaded = _instant(clip.downloaded_at)
        except (OSError, ValidationError, ValueError):
            log.warning("skipping unreadable %s", path)
            continue
        if clip.id == path.stem and _mp4_path(project, clip.id).is_file():
            found.append((downloaded, clip))
    found.sort(key=lambda pair: pair[0], reverse=True)
    return [clip for _, clip in found]


def video_file(project: ProjectPaths, video_id: str) -> Path:
    """The clip's mp4. Raises `SpoilError` 404 when it isn't a listed clip."""
    _check_known(project, video_id)
    mp4 = _mp4_path(project, video_id)
    if not mp4.is_file():
        raise _not_found()
    return mp4


def thumbnail_file(project: ProjectPaths, video_id: str) -> Path:
    """The clip's thumbnail. Raises `SpoilError` 404 when there is none."""
    _check_known(project, video_id)
    name = find_thumbnail(project, video_id)
    if name is None:
        raise _not_found()
    return project.media_temp_dir / name


def delete_clip(project: ProjectPaths, video_id: str) -> None:
    """mp4 and thumbnail first, json last, so a clip half deleted is cleaned at the next start (D15).

    An mp4 Windows still holds open → `SpoilError` 409 `in_use`, json untouched.
    """
    _check_known(project, video_id)
    try:
        _mp4_path(project, video_id).unlink(missing_ok=True)
    except PermissionError:
        raise SpoilError(409, "in_use", "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง") from None
    thumbnail = find_thumbnail(project, video_id)
    if thumbnail:
        try:
            (project.media_temp_dir / thumbnail).unlink(missing_ok=True)
        except OSError:
            log.exception("could not remove %s; it goes at the next start", thumbnail)
    json_path(project, video_id).unlink(missing_ok=True)


def _check_known(project: ProjectPaths, video_id: str) -> None:
    """Only an 11-character id with its json gets near the disk (no path traversal)."""
    if not VIDEO_ID.fullmatch(video_id) or not has_clip(project, video_id):
        raise _not_found()


def _mp4_path(project: ProjectPaths, video_id: str) -> Path:
    return project.media_temp_dir / f"{video_id}.mp4"


def _instant(downloaded_at: str) -> datetime:
    """Compared as instants, not text: offsets may differ between clips.

    Raises ValueError for a time without an offset, which can't be compared.
    """
    instant = datetime.fromisoformat(downloaded_at)
    if instant.tzinfo is None:
        raise ValueError(f"no UTC offset: {downloaded_at}")
    return instant


def write_clip(project: ProjectPaths, clip: TempClip) -> None:
    """Writes `{id}.json` through a temporary file, so it appears complete or not at all."""
    target = json_path(project, clip.id)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(clip.model_dump_json(indent=2), encoding="utf-8")
    os.replace(temporary, target)


def remove_unfinished(project: ProjectPaths, video_id: str) -> None:
    """Deletes one job's files in .partial/ and its `{id}.*` that has no json.

    Best effort: a file Windows still holds open is logged and left for the
    clean-up at the next start.
    """
    leftovers = list(project.partial_dir.glob(f"{video_id}.*"))
    if not has_clip(project, video_id):
        leftovers += project.media_temp_dir.glob(f"{video_id}.*")
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
        video_id = path.name.split(".")[0]
        # Only `{id}.*` files are ours; anything else (.DS_Store) stays.
        if path.is_file() and VIDEO_ID.fullmatch(video_id) and not has_clip(project, video_id):
            path.unlink(missing_ok=True)
