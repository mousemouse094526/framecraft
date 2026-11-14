"""Audio brought in from a link or a file and converted to one m4a (ADR 0048): what the app's sound
library (`backend.sounds`) and the แกะเพลง tab's songs share (toon D39, drum-notes D4, D20).

A link's audio comes through spoil's yt-dlp adapter (`bestaudio`, ADR 0029): its info first, so a
length the site tells refuses it before anything loads, then the file into the caller's `.partial/`
with a percent. A file comes as a raw body the caller already wrote to `.partial/` (ADR 0028). Either
way `take_in` reads the file's length with ffmpeg, refuses what is too short, too long or has no
sound, converts it to aac in m4a through a `.partial` beside the target, and hands the finished file
to the caller's `place`, which moves it in and writes the entry.

Each caller keeps its own job slot, state and entries: this module takes the folder, the limits and
the callback from it, and imports nothing of the features.
"""

import logging
import math
import os
import threading
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar

import anyio
from pydantic import BaseModel

from backend import ffmpeg, spoil, uploads
from backend.errors import ApiError, JobFailed
from backend.ffmpeg import FfmpegFailed
from backend.jobs import Cancelled, JobSlot
from backend.paths import ProjectPaths
from backend.spoil.adapter import DownloadCancelled, DownloadOptions

log = logging.getLogger(__name__)

State = Literal["checking", "downloading", "converting", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"checking", "downloading", "converting"})

# aac 192k 48 kHz stereo: the format every render's mix is in too (toon D39).
M4A_RATE = 48_000
M4A_BITRATE = "192k"
NAME_MAX = 60  # a title cut from a clip's or a file's name
GONE_POLL_SECONDS = 0.25  # how often a file's conversion asks whether the page is still there

UNREADABLE = "ไฟล์นี้ไม่มีเสียงที่อ่านได้"
PLAYLIST = "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว"

Placed = TypeVar("Placed")
Job = TypeVar("Job", bound=BaseModel)


@dataclass(frozen=True)
class Limits:
    """How long a caller's audio may be, and the words of its refusals: `too_short` is only
    refused when `min_seconds` is above 0."""

    max_seconds: int
    too_long: str
    min_seconds: float = 0
    too_short: str = ""


class ImportSlot(JobSlot[Job]):
    """A feature's import slot: the latest link job, and whether a file is being received, one of
    the two at a time (`busy`, the subclass's words). `convert` runs ffmpeg; a test passes one that
    pauses (rules › testing). `stall_seconds` is how long a file's body may pause."""

    unfinished = UNFINISHED
    busy: str

    def __init__(self, convert: ffmpeg.Runner = ffmpeg.run, stall_seconds: float = uploads.STALL_SECONDS):
        super().__init__()
        self._convert = convert
        self._stall_seconds = stall_seconds
        self._receiving_file = False

    @contextmanager
    def receiving(self) -> Iterator[None]:
        """Holds the slot while a file's body comes in and is converted; the flag goes down
        however the block ends. Raises `ApiError` 409 `busy` when the slot is taken."""
        with self._lock:
            self._require_free()
            self._receiving_file = True
        try:
            yield
        finally:
            with self._lock:
                self._receiving_file = False

    def _require_free(self) -> None:
        """Raises `ApiError` 409 `busy` while a link job runs or a file is being received. Call with the lock held."""
        if self._taken() or self._receiving_file:
            raise ApiError(409, "busy", self.busy)

    def stop_on_shutdown(self) -> None:
        self._cancel.set()


def link_options(partial_dir: Callable[[ProjectPaths], Path]) -> DownloadOptions:
    """What a link's audio asks yt-dlp for: the best audio alone into the caller's `.partial/`,
    no thumbnail, no mp4 merge (toon spec › Modules touched)."""
    return DownloadOptions(format="bestaudio", folder=partial_dir, thumbnail=False, merge_mp4=False)


# --- a link ---


def fetch_info(url: str, options: DownloadOptions, limits: Limits, cancel: threading.Event) -> dict:
    """The link's info, refused when it is a playlist (`playlist`) or the site says it is longer
    than `limits` allow (`too_long`; a length the site doesn't tell is checked from the file).
    Raises `JobFailed`, or `DownloadCancelled` once `cancel` is set."""
    info = spoil.adapter.fetch_info(url, options)
    if info.get("_type") == "playlist":
        raise JobFailed("playlist", PLAYLIST)
    if (info.get("duration") or 0) > limits.max_seconds:
        raise JobFailed("too_long", limits.too_long)
    if cancel.is_set():
        raise DownloadCancelled()
    return info


def estimate_bytes(info: dict) -> int:
    """The download's size from its info; 0 when the site doesn't tell."""
    return sum(f.get("filesize") or f.get("filesize_approx") or 0 for f in info.get("requested_formats") or [info])


def download(
    project: ProjectPaths,
    info: dict,
    media_id: str,
    options: DownloadOptions,
    on_percent: Callable[[int], None],
    cancel: threading.Event,
) -> Path:
    """The audio of `info` into `options.folder`, named after `media_id`; `on_percent` gets the
    whole-number percent so far, never going down. Raises `DownloadCancelled` once `cancel` is set."""
    estimate = estimate_bytes(info)
    options.folder(project).mkdir(parents=True, exist_ok=True)
    highest = 0

    def on_progress(event: dict) -> None:
        nonlocal highest
        if cancel.is_set():
            raise DownloadCancelled()
        total = event.get("total_bytes") or event.get("total_bytes_estimate") or estimate
        if event.get("status") == "downloading" and total:
            highest = max(highest, min(100, math.floor((event.get("downloaded_bytes") or 0) / total * 100)))
            on_percent(highest)

    return spoil.adapter.download(info, project, media_id, on_progress, options)


# --- both ---


def take_in(
    source: Path,
    target: Path,
    limits: Limits,
    convert: ffmpeg.Runner,
    cancel: threading.Event,
    place: Callable[[float], Placed],
    still_wanted: Callable[[], bool] | None = None,
    partial: Path | None = None,
) -> Placed:
    """In a thread: the file's length and sound (`unsupported_file`, `too_short`, `too_long`), then
    aac in m4a at `target` through `partial` (`partial_of(target)` unless the caller keeps its half-done
    files elsewhere), cut at `limits.max_seconds`, then `place(seconds)`, which moves the partial to
    `target` and writes the entry, unless `still_wanted` says no by then.
    Raises `JobFailed`, or `Cancelled`; the partial is gone whenever this raises."""
    try:
        media = ffmpeg.probe(source)
    except FfmpegFailed:
        raise JobFailed("unsupported_file", UNREADABLE) from None
    if not media.has_audio:
        raise JobFailed("unsupported_file", UNREADABLE)
    if media.duration_s > limits.max_seconds:
        raise JobFailed("too_long", limits.too_long)
    if media.duration_s < limits.min_seconds:
        raise JobFailed("too_short", limits.too_short)
    partial = partial or partial_of(target)
    for folder in {target.parent, partial.parent}:
        folder.mkdir(parents=True, exist_ok=True)
    try:
        try:
            convert(convert_command(source, partial, limits.max_seconds), partial.parent, cancel)
            seconds = ffmpeg.probe(partial).duration_s
        except FfmpegFailed as failed:
            log.warning("could not convert %s: %s", source.name, failed.last_line)
            raise JobFailed("unsupported_file", UNREADABLE) from None
        if still_wanted and not still_wanted():
            raise Cancelled()
        return place(seconds)
    finally:
        partial.unlink(missing_ok=True)  # a no-op once `place` moved it


def partial_of(target: Path) -> Path:
    """`{target}.partial` beside the target: where `take_in` converts unless told another `partial`,
    and where the caller's `place` moves from."""
    return target.with_name(target.name + ".partial")


def convert_command(source: Path, out: Path, max_seconds: int) -> list[str]:
    """The first audio stream as aac 192k 48 kHz stereo in m4a, no picture, no longer than
    `max_seconds` (D39; drum-notes D20)."""
    return [
        ffmpeg.exe(), "-nostdin", "-hide_banner", "-v", "error", "-y", "-i", str(source),
        "-map", "0:a:0", "-vn", "-t", str(max_seconds),
        "-c:a", "aac", "-b:a", M4A_BITRATE, "-ar", str(M4A_RATE), "-ac", "2",
        "-f", "mp4", str(out),
    ]  # fmt: skip


async def run_unless_gone(
    page_gone: Callable[[], Awaitable[bool]], cancel: threading.Event, work: Callable[[], Placed]
) -> Placed:
    """`work()` in a thread, with `cancel` set once `page_gone()` says the page went away.
    `work`'s exception is raised as it is: from inside the task group it would come out
    wrapped in an ExceptionGroup, which a caller's `except` lines don't catch."""

    async def watch() -> None:
        while not await page_gone():
            await anyio.sleep(GONE_POLL_SECONDS)
        cancel.set()

    failure: Exception | None = None
    async with anyio.create_task_group() as group:
        group.start_soon(watch)
        try:
            done = await anyio.to_thread.run_sync(work)
        except Exception as error:
            failure = error
        group.cancel_scope.cancel()
    if failure is not None:
        raise failure
    return done


def still_wanted(page_gone: Callable[[], Awaitable[bool]], cancel: threading.Event) -> Callable[[], bool]:
    """For `take_in`, from a thread: asked once more right before the file comes in, whether the
    page is still there and nothing cancelled."""
    return lambda: not cancel.is_set() and not anyio.from_thread.run(page_gone)


def remove_leftovers(folder: Path, media_id: str) -> None:
    """Every `{media_id}.*` a job left in `folder`, once it ended any way but `done`."""
    if folder.is_dir():
        for leftover in folder.glob(f"{media_id}.*"):
            leftover.unlink(missing_ok=True)


def file_title(name: str | None) -> str:
    """A file's title: its name without the extension, cut to 60; empty for no name."""
    return first_name(os.path.splitext((name or "").strip())[0])


def first_name(text: object, fallback: str = "") -> str:
    """A title cut to 60 letters from a clip's title or a file's name; `fallback` when there is none."""
    return (text.strip()[:NAME_MAX].strip() if isinstance(text, str) else "") or fallback
