"""A background picture sent from the page (video-gen D6, D36, drum-cover D8, D21; ADR 0028): the
size checked before the body, then the PNG or JPEG received to a `.tmp` the caller names, turned
the way its EXIF says, cropped to 1080×1920 and written as a jpg beside it, which the caller's
`place` puts where it belongs under its own lock. A drum lesson's and a reel cover's share it;
the idle and disk checks are each caller's, so this imports nothing of the features.
"""

import logging
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import anyio

from backend import uploads
from backend.errors import ApiError

log = logging.getLogger(__name__)

MAX_BYTES = 20 * 1024**2
TOO_LARGE_STATUS = 413  # these routes' specs say 413; spoil's and toon's uploads answer 400
TOO_LARGE = f"ไฟล์ภาพใหญ่เกิน {MAX_BYTES // 1024**2} MB"
UNSUPPORTED = "รับเฉพาะไฟล์ภาพ PNG หรือ JPG"
WIDTH, HEIGHT = 1080, 1920  # the clip's frame (`video_gen.frames`)
JPEG_QUALITY = 92  # blurred under 55 % black in every render: more would only cost disk


def checked_size(size: object) -> int:
    """The size a `check` or `PUT` gives: a whole number of at most 20 MB. Raises `ApiError` 400 or 413."""
    return uploads.require_size(size, MAX_BYTES, TOO_LARGE, too_large_status=TOO_LARGE_STATUS)


async def receive[Placed](body: AsyncIterator[bytes], partial: Path, expected: int, place: Callable[[Path], Placed]) -> Placed:
    """The body to `partial`, the picture cropped beside it, then `place(jpg)` in a thread; both
    files go whatever happens (one a crash leaves, start-up's `files.remove_unfinished` removes).
    Raises `ApiError` 415 `unsupported_image` for anything but a PNG or JPEG."""
    try:
        await uploads.receive(body, partial, expected)
        return await anyio.to_thread.run_sync(_take, partial, place)
    finally:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(lambda: partial.unlink(missing_ok=True))


def _take[Placed](partial: Path, place: Callable[[Path], Placed]) -> Placed:
    """In a thread: read the file with Pillow, crop it, write the jpg beside the upload, then
    `place` it: beside the upload, on the caller's disk, its swap is a rename."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(partial, formats=["PNG", "JPEG"]) as opened:
            opened.load()
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ApiError(415, "unsupported_image", UNSUPPORTED) from None
    image = ImageOps.fit(image, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    picture = partial.with_name(f"{partial.stem}.jpg.tmp")
    try:
        image.save(picture, "JPEG", quality=JPEG_QUALITY)
        return place(picture)
    finally:
        picture.unlink(missing_ok=True)
