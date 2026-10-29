"""Temp clips on disk: `{id}.mp4`, a thumbnail `{id}.{ext}`, and `{id}.json`
written last, so a clip without json is unfinished (spoil D14, D15)."""

import logging
import os
import shutil
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend.paths import ProjectPaths
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
