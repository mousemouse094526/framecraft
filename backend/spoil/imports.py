"""File import: an mp4 on this machine, sent by the page as a raw body, becomes a Temp clip
in one request (spec › File import, D49–D52, D55, ADR 0027, ADR 0028).

Not a job: nothing lives in memory but the "receiving a file" flag, which the Download
job's lock guards so that one of the two runs at a time. The body is written and ffmpeg
runs in threads, so the event loop keeps answering polls meanwhile. A restart half-way
leaves only `.partial/` and `local-…` files without a json, which start-up removes.
"""

import logging
import os
import threading
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import anyio
from pydantic import BaseModel
from starlette.requests import ClientDisconnect

from backend import checks, ffmpeg, gate_rows, paths
from backend.errors import ApiError, JobFailed, invalid_request, require_rows
from backend.paths import ProjectPaths
from backend.spoil import clips, downloads, links, mp4check
from backend.spoil.mp4check import NotPlayable

log = logging.getLogger(__name__)

STALL_SECONDS = 60  # no new byte this long → `stalled` (D55)
WRITE_BYTES = 2**20  # the body goes to its thread about a MiB at a time, not per chunk
THUMBNAIL_AT = 0.1  # of the length (D52)
SUFFIX = ".mp4"

ONLY_MP4 = "รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน"
DUPLICATE = "ไฟล์นี้เอาเข้าไว้แล้ว"
SIZE_MISMATCH = "ได้ไฟล์ไม่ครบหรือเกินขนาดที่บอก ลองอีกครั้ง"
# Names the app's limit; a test that shortens `stall_seconds` still gets these words.
STALLED = f"ไม่ได้รับข้อมูลไฟล์นาน {STALL_SECONDS} วินาที ลองอีกครั้ง"
CONVERT = "แปลงเป็น mp4 (H.264, AAC) ไม่เกิน 1080p ด้วยโปรแกรมอื่นแล้วลองอีกครั้ง"


def _duplicate(clip_id: str) -> ApiError:
    """The file is in the list already: the page points at its row (D51)."""
    return ApiError(409, "duplicate", DUPLICATE, clip_id=clip_id)


class ImportCheck(BaseModel):
    """`POST /imports/check`'s answer: the id the import will make."""

    clip_id: str


class Imports:
    """Takes local files in. `check_mp4` reads the received file with ffmpeg and
    `stall_seconds` is how long a body may pause; a test passes its own (rules › testing)."""

    def __init__(
        self,
        check_mp4: Callable[[Path], mp4check.Mp4Info] = mp4check.check,
        stall_seconds: float = STALL_SECONDS,
    ):
        self._check_mp4 = check_mp4
        self._stall_seconds = stall_seconds

    def check(self, body: dict[str, Any]) -> ImportCheck:
        """Step 0: every check of step 1 but the body's, before the page sends it — a
        refusal while the body is still going reaches the page as a network error only.
        Raises `ApiError`."""
        name, size = body.get("name"), body.get("size")
        # JSON `true` is an `int` to Python; it is no size.
        valid_size = size if isinstance(size, int) and not isinstance(size, bool) else None
        project, clip_id = self._first_checks(name if isinstance(name, str) else None, valid_size)
        downloads.downloads.refuse_if_busy()
        _require_disk(project, valid_size)
        return ImportCheck(clip_id=clip_id)

    async def receive(self, name: str | None, size: str | None, body: AsyncIterator[bytes]) -> clips.TempClip:
        """Steps 1–7: checks again (things change between the two requests), then writes
        `body` to `.partial/`, checks it and moves it in. Raises `ApiError`, or
        `ClientDisconnect` once its files are gone."""
        expected = _whole_number(size)
        project, clip_id = await anyio.to_thread.run_sync(self._first_checks, name, expected)
        with downloads.downloads.receiving_file():
            try:
                # Again under the flag: the same file sent twice at once may have just come in.
                if clips.has_clip(project, clip_id):
                    raise _duplicate(clip_id)
                await anyio.to_thread.run_sync(_require_disk, project, expected)
                partial = project.partial_dir / f"{clip_id}.import{SUFFIX}"
                await self._write_body(body, partial, expected)
                return await anyio.to_thread.run_sync(self._move_in, project, clip_id, name, partial)
            except ClientDisconnect:
                log.info("the import of %s stopped: the page went away", clip_id)
                raise
            finally:
                # A no-op once the json is written: only files of an unfinished clip go.
                # Shielded: a request cancelled at shutdown must still clean up.
                with anyio.CancelScope(shield=True):
                    await anyio.to_thread.run_sync(clips.remove_unfinished, project, clip_id)

    def _first_checks(self, name: str | None, size: int | None) -> tuple[ProjectPaths, str]:
        """Step 1 up to `busy`, in spec order; returns the project and the clip's id."""
        require_rows(gate_rows.FFMPEG)
        if not name:
            raise invalid_request()
        if not name.lower().endswith(SUFFIX):
            raise ApiError(400, "not_mp4", ONLY_MP4)
        if not _title(name) or size is None or size <= 0:
            raise invalid_request()
        project = paths.project()
        clip_id = links.local_id(name, size)
        if clips.has_clip(project, clip_id):
            raise _duplicate(clip_id)
        return project, clip_id

    async def _write_body(self, body: AsyncIterator[bytes], partial: Path, expected: int) -> None:
        """Steps 2–3: the body to `partial`, never more than `expected` bytes and never
        waiting `stall_seconds` for the next one."""
        await anyio.to_thread.run_sync(lambda: partial.parent.mkdir(parents=True, exist_ok=True))
        out = await anyio.to_thread.run_sync(partial.open, "wb")
        received, waiting, waiting_bytes = 0, [], 0
        try:
            chunks = aiter(body)
            while True:
                try:
                    with anyio.fail_after(self._stall_seconds):
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

    def _move_in(self, project: ProjectPaths, clip_id: str, name: str, partial: Path) -> clips.TempClip:
        """Steps 4–6, in a thread: check the file, take a thumbnail, move it in, json last."""
        try:
            shown = self._check_mp4(partial)
        except NotPlayable as refused:
            log.info("refused %s: %s", name, refused.reason)
            raise ApiError(400, "unsupported_file", f"{refused.reason}. {CONVERT}") from None
        thumbnail = _thumbnail(project, clip_id, partial, shown.duration_s)
        mp4 = clips.video_path(project, clip_id)
        os.replace(partial, mp4)  # the same volume: media/temp/.partial/ is inside media/temp/
        clip = clips.TempClip(
            id=clip_id,
            title=_title(name),
            channel=None,
            site=links.LOCAL_SITE,
            source_url=None,
            duration_s=round(shown.duration_s),
            width=shown.width,
            height=shown.height,
            orientation=shown.orientation,
            file_bytes=mp4.stat().st_size,
            thumbnail=thumbnail,
            downloaded_at=checks.now_iso(),
            yt_dlp_version=None,
        )
        clips.write_clip(project, clip)
        log.info("imported %s as %s (%d bytes)", name, clip_id, clip.file_bytes)
        return clip


def _title(name: str) -> str:
    """The file's name without `.mp4`, as the page shows it (D52)."""
    return name[: -len(SUFFIX)].strip()


def _whole_number(text: str | None) -> int | None:
    """A query's `size`: digits only, so `1.5`, `-5` and `1e3` are no size."""
    return int(text) if text and text.isascii() and text.isdigit() else None


def _require_disk(project: ProjectPaths, size: int) -> None:
    try:
        downloads.require_disk(project, size)
    except JobFailed as full:
        raise ApiError(409, full.code, full.message) from None


def _thumbnail(project: ProjectPaths, clip_id: str, mp4: Path, duration_s: float) -> str | None:
    """One frame at 10% of the length as `{id}.jpg`; None when ffmpeg makes none (D52)."""
    jpg = project.media_temp_dir / f"{clip_id}.jpg"
    command = [
        ffmpeg.exe(), "-nostdin", "-v", "error", "-y", "-ss", f"{duration_s * THUMBNAIL_AT:.3f}",
        "-i", str(mp4), "-frames:v", "1", "-update", "1", str(jpg),
    ]  # fmt: skip
    try:
        ffmpeg.run(command, project.media_temp_dir, threading.Event())
    except ffmpeg.FfmpegFailed as failed:
        log.warning("no thumbnail for %s: %s", clip_id, failed.last_line)
    if jpg.is_file() and jpg.stat().st_size:
        return jpg.name
    jpg.unlink(missing_ok=True)
    return None


imports = Imports()
