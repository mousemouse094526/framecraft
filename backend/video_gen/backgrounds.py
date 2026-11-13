"""A lesson's background picture (video-gen D6, spec › API): the page checks the size, then
sends the PNG or JPEG as the raw body (ADR 0028); it is turned the way its EXIF says, cropped
to 1080×1920 and kept as the lesson's `background.jpg`. A render blurs and darkens it."""

import logging
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import anyio

from backend import disk, uploads
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.video_gen import frames, lessons
from backend.video_gen.lessons import LessonView

log = logging.getLogger(__name__)

MAX_BYTES = 20 * 1024**2
TOO_LARGE_STATUS = 413  # this route's spec says 413; spoil's and toon's uploads answer 400
TOO_LARGE = f"ไฟล์ภาพใหญ่เกิน {MAX_BYTES // 1024**2} MB"
UNSUPPORTED = "รับเฉพาะไฟล์ภาพ PNG หรือ JPG"
JPEG_QUALITY = 92  # blurred under 55 % black in every render: more would only cost disk


def check_upload(project: ProjectPaths, lesson_id: str, body: dict) -> uploads.UploadCheck:
    """The upload's checks before the page sends the body (ADR 0028)."""
    return uploads.UploadCheck(size=_upload_checks(project, lesson_id, body.get("size")))


async def receive_upload(project: ProjectPaths, lesson_id: str, size: str | None, body: AsyncIterator[bytes]) -> LessonView:
    """The checks again, then the body to a `.tmp` under `.partial/` that goes whatever happens
    (one a crash leaves, start-up's `files.remove_unfinished` removes)."""
    expected = uploads.whole_number(size)
    await anyio.to_thread.run_sync(_upload_checks, project, lesson_id, expected)
    partial = project.drums_partial_dir / f"{lesson_id}.{secrets.token_hex(4)}.tmp"  # one per request
    try:
        await uploads.receive(body, partial, expected)
        return await anyio.to_thread.run_sync(_take_upload, project, lesson_id, partial)
    finally:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(lambda: partial.unlink(missing_ok=True))


def remove(project: ProjectPaths, lesson_id: str) -> LessonView:
    """`DELETE …/background`: back to the app's colours; no picture is no error."""
    view = lessons.set_background(project, lesson_id, None)
    log.info("removed the background of lesson %s", lesson_id)
    return view


# --- helpers ---


def _upload_checks(project: ProjectPaths, lesson_id: str, size: object) -> int:
    size = uploads.require_size(size, MAX_BYTES, TOO_LARGE, too_large_status=TOO_LARGE_STATUS)
    lessons.require_known_idle(project, lesson_id)
    disk.require_free(project.root, size)
    return size


def _take_upload(project: ProjectPaths, lesson_id: str, partial: Path) -> LessonView:
    """In a thread: read the file with Pillow, crop it, write the jpg beside the lesson, then
    swap it in. Raises `ApiError` 415 `unsupported_image` for anything but a PNG or JPEG."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(partial, formats=["PNG", "JPEG"]) as opened:
            opened.load()
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ApiError(415, "unsupported_image", UNSUPPORTED) from None
    image = ImageOps.fit(image, (frames.WIDTH, frames.HEIGHT), Image.Resampling.LANCZOS)
    # Beside the upload, on the lesson's disk: the swap is a rename, and a lesson deleted
    # meanwhile is a 404 from `set_background`, not a write into a folder that went.
    picture = partial.with_name(f"{partial.stem}.jpg.tmp")
    try:
        image.save(picture, "JPEG", quality=JPEG_QUALITY)
        view = lessons.set_background(project, lesson_id, picture)
    finally:
        picture.unlink(missing_ok=True)
    log.info("took a background picture for lesson %s", lesson_id)
    return view
