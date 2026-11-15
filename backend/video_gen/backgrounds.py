"""A lesson's background picture (video-gen D6, spec › API): the page checks the size, then
sends the PNG or JPEG as the raw body (ADR 0028); `backend.pictures` turns it the way its EXIF
says and crops it to 1080×1920, and it is kept as the lesson's `background.jpg`. A render blurs
and darkens it."""

import logging
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import anyio

from backend import disk, pictures, uploads
from backend.paths import ProjectPaths
from backend.video_gen import lessons
from backend.video_gen.lessons import LessonView

log = logging.getLogger(__name__)

MAX_BYTES = pictures.MAX_BYTES


def check_upload(project: ProjectPaths, lesson_id: str, body: dict) -> uploads.UploadCheck:
    """The upload's checks before the page sends the body (ADR 0028)."""
    return uploads.UploadCheck(size=_upload_checks(project, lesson_id, body.get("size")))


async def receive_upload(project: ProjectPaths, lesson_id: str, size: str | None, body: AsyncIterator[bytes]) -> LessonView:
    """The checks again, then the body to a `.tmp` under `.partial/` that goes whatever happens
    (one a crash leaves, start-up's `files.remove_unfinished` removes)."""
    expected = uploads.whole_number(size)
    await anyio.to_thread.run_sync(_upload_checks, project, lesson_id, expected)
    view = await pictures.receive(body, partial_file(project, lesson_id), expected, lambda picture: lessons.set_background(project, lesson_id, picture))
    log.info("took a background picture for lesson %s", lesson_id)
    return view


def partial_file(project: ProjectPaths, lesson_id: str) -> Path:
    """Where one request's upload lands, under `.partial/`: a fresh name each call."""
    return project.drums_partial_dir / f"{lesson_id}.{secrets.token_hex(4)}.tmp"


def remove(project: ProjectPaths, lesson_id: str) -> LessonView:
    """`DELETE …/background`: back to the app's colours; no picture is no error."""
    view = lessons.set_background(project, lesson_id, None)
    log.info("removed the background of lesson %s", lesson_id)
    return view


# --- helpers ---


def _upload_checks(project: ProjectPaths, lesson_id: str, size: object) -> int:
    size = pictures.checked_size(size)
    lessons.require_known_idle(project, lesson_id)
    disk.require_free(project.root, size)
    return size
