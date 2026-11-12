"""A raw file body written to disk as it comes (ADR 0028): shared by spoil's File import
and the การ์ตูนเล่า tab's uploads. The chunks go to a thread about a MiB at a time, so the
event loop keeps answering polls meanwhile."""

from collections.abc import AsyncIterator
from pathlib import Path

import anyio
from pydantic import BaseModel

from backend.errors import ApiError, invalid_request
from backend.json_values import is_int

STALL_SECONDS = 60  # no new byte this long → `stalled` (spoil D55)
WRITE_BYTES = 2**20

SIZE_MISMATCH = "ได้ไฟล์ไม่ครบหรือเกินขนาดที่บอก ลองอีกครั้ง"
# Names the app's limit; a test that shortens `stall_seconds` still gets these words.
STALLED = f"ไม่ได้รับข้อมูลไฟล์นาน {STALL_SECONDS} วินาที ลองอีกครั้ง"


class UploadCheck(BaseModel):
    """The size an upload's body must have, once its checks pass."""

    size: int


def require_size(size: object, max_bytes: int, too_large: str) -> int:
    """The size a page says it will send: a whole number of bytes from 1 to `max_bytes`.
    Raises `invalid_request`, or 400 `file_too_large` with `too_large`."""
    if not is_int(size) or size <= 0:
        raise invalid_request()
    if size > max_bytes:
        raise ApiError(400, "file_too_large", too_large)
    return size


def whole_number(text: str | None) -> int | None:
    """A query's `size`: digits only, so `1.5`, `-5` and `1e3` are no size."""
    return int(text) if text and text.isascii() and text.isdigit() else None


async def receive(
    body: AsyncIterator[bytes], partial: Path, expected: int, stall_seconds: float = STALL_SECONDS
) -> None:
    """`body` to `partial`, never more than `expected` bytes and never waiting
    `stall_seconds` for the next one. Raises `ApiError` 400 `size_mismatch` or 408 `stalled`;
    the caller removes `partial`."""
    await anyio.to_thread.run_sync(lambda: partial.parent.mkdir(parents=True, exist_ok=True))
    out = await anyio.to_thread.run_sync(partial.open, "wb")
    received, waiting, waiting_bytes = 0, [], 0
    try:
        chunks = aiter(body)
        while True:
            try:
                with anyio.fail_after(stall_seconds):
                    chunk = await anext(chunks, None)
            except TimeoutError:
                raise ApiError(408, "stalled", STALLED) from None
            if chunk is None:
                break
            received += len(chunk)
            if received > expected:
                raise ApiError(400, "size_mismatch", SIZE_MISMATCH)
            waiting.append(chunk)
            waiting_bytes += len(chunk)
            if waiting_bytes >= WRITE_BYTES:
                await anyio.to_thread.run_sync(out.write, b"".join(waiting))
                waiting, waiting_bytes = [], 0
        await anyio.to_thread.run_sync(out.write, b"".join(waiting))
    finally:
        # Closed before anything moves or removes it: Windows can't while it's open.
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(out.close)
    if received != expected:
        raise ApiError(400, "size_mismatch", SIZE_MISMATCH)
