"""What every ffmpeg run shares: the binary from imageio-ffmpeg
(ADR 0005), a kill when the job is cancelled, and reading a file's length and
streams from `ffmpeg -i`, since there is no ffprobe (docs/library-notes/ffmpeg.md).

spoil_maker's `frames` (Shots) and `compose` (renders), and spoil's `trim` (cut ranges)
run ffmpeg through these; video_gen's render sends its frames through `run_piped`; drum_notes'
Pick job reads a stretch of a song as raw PCM through `run_capture`.
"""

import io
import logging
import re
import subprocess
import sys
import threading
from collections import deque
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import NamedTuple, Protocol

from backend.jobs import Cancelled

log = logging.getLogger(__name__)

KILL_POLL_SECONDS = 0.2
STDERR_LINES = 20  # the tail of ffmpeg's errors that goes to the log

DURATION = re.compile(r"Duration: (\d+):(\d\d):(\d\d(?:\.\d+)?)")


class FfmpegFailed(Exception):
    """ffmpeg exited with an error. The message names the exit code and the last line
    ffmpeg printed, for the log; `last_line` is that line alone, for a message the user
    sees (spoil spec › Trim `ffmpeg_failed`)."""

    def __init__(self, message: str, last_line: str):
        super().__init__(message)
        self.last_line = last_line


class Media(NamedTuple):
    duration_s: float
    has_audio: bool


def exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def seconds_of(found: re.Match) -> float:
    hours, minutes, seconds = found.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def input_info(path: Path, timeout: float | None = None) -> str:
    """What `ffmpeg -i` prints about the file: its container, length and streams. With no
    output it exits 1 by design, so the exit code says nothing; callers read the text.
    Past `timeout` seconds ffmpeg is killed and `subprocess.TimeoutExpired` raised."""
    command = [exe(), "-hide_banner", "-nostdin", "-i", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout)
    return result.stderr


def probe(path: Path, timeout: float | None = None) -> Media:
    """The file's length and whether it has sound; only a missing `Duration:` is a failure,
    and ffmpeg still reading it after `timeout` seconds."""
    try:
        stderr = input_info(path, timeout)
    except subprocess.TimeoutExpired:
        raise FfmpegFailed(f"no length for {path.name}: still reading after {timeout} s", "timed out") from None
    found = DURATION.search(stderr)
    if found is None:
        lines = stderr.strip().splitlines()
        last_line = lines[-1] if lines else "no output"
        raise FfmpegFailed(f"no length for {path.name}: {last_line}", last_line)
    return Media(duration_s=seconds_of(found), has_audio=re.search(r"Stream #\S+.*: Audio:", stderr) is not None)


def h264_args(platform: str = sys.platform) -> list[str]:
    """The h264 encoder: videotoolbox on a Mac, libx264 elsewhere (spoil D36)."""
    return ["-c:v", "h264_videotoolbox"] if platform == "darwin" else ["-c:v", "libx264", "-preset", "veryfast"]


def kill_on_cancel(process: subprocess.Popen, cancel: threading.Event, finished: threading.Event) -> None:
    """Run in a thread beside ffmpeg: kills it once `cancel` is set, until `finished` is."""
    while not finished.is_set():
        if cancel.wait(KILL_POLL_SECONDS):
            process.kill()
            return


def _failed(returncode: int, stderr: deque[str]) -> FfmpegFailed:
    """ffmpeg's failure: the last 20 lines of stderr to the log, the last one in the error."""
    log.error("ffmpeg exited with %s:\n%s", returncode, "\n".join(stderr))
    last_line = stderr[-1] if stderr else "no output"
    return FfmpegFailed(f"ffmpeg exited with {returncode}: {last_line}", last_line)


def _watch_stderr(process: subprocess.Popen) -> tuple[deque[str], threading.Thread]:
    """A thread that keeps the last 20 lines ffmpeg prints, started; `join` it once ffmpeg exited."""
    stderr: deque[str] = deque(maxlen=STDERR_LINES)
    text = isinstance(process.stderr, io.TextIOBase)
    reader = threading.Thread(
        target=lambda: stderr.extend((line if text else line.decode(errors="replace")).rstrip() for line in process.stderr), daemon=True
    )
    reader.start()
    return stderr, reader


def _ended(process: subprocess.Popen, cancel: threading.Event, stderr: deque[str]) -> None:
    """How a run ended, once ffmpeg exited: `Cancelled` when `cancel` is set, `FfmpegFailed` on a bad exit code."""
    if cancel.is_set():
        raise Cancelled()
    if process.returncode != 0:
        raise _failed(process.returncode, stderr)


class Runner(Protocol):
    """What runs an ffmpeg command: `run`, or a test's stand-in that pauses it."""

    def __call__(
        self, command: list[str], cwd: Path, cancel: threading.Event, on_progress: Callable[[float], None] | None = None
    ) -> None: ...


def run(command: list[str], cwd: Path, cancel: threading.Event, on_progress: Callable[[float], None] | None = None) -> None:
    """Runs ffmpeg in `cwd`. `on_progress` gets the output's seconds so far from
    `-progress pipe:1`. Raises `Cancelled` once `cancel` is set (ffmpeg is killed), or
    `FfmpegFailed` with the last line it printed (`last_line`); the last 20 go to the log."""
    if cancel.is_set():
        raise Cancelled()
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace"
    )
    finished = threading.Event()
    threading.Thread(target=kill_on_cancel, args=(process, cancel, finished), daemon=True).start()
    stderr, reader = _watch_stderr(process)
    try:
        for line in process.stdout:
            key, _, value = line.strip().partition("=")
            if key == "out_time_us" and on_progress and value.isdigit():
                on_progress(int(value) / 1_000_000)
        process.wait()
        reader.join()
    finally:
        finished.set()
    _ended(process, cancel, stderr)


class PipedRunner(Protocol):
    """What runs an ffmpeg command fed through stdin: `run_piped`, or a test's stand-in."""

    def __call__(
        self, command: list[str], cwd: Path, cancel: threading.Event, frames: Iterable[bytes], on_frame: Callable[[int], None]
    ) -> None: ...


def run_piped(
    command: list[str], cwd: Path, cancel: threading.Event, frames: Iterable[bytes], on_frame: Callable[[int], None]
) -> None:
    """Runs ffmpeg in `cwd`, writing each of `frames` to its stdin and calling `on_frame` with
    how many went (video-gen D22). `cancel` is checked before every frame: once set, ffmpeg is
    killed and `Cancelled` raised. A write that breaks while `cancel` is set is `Cancelled` too.
    Any other broken write means ffmpeg stopped by itself: the frames stop and its exit code
    decides — not 0 is `FfmpegFailed` with the last line of stderr, which one thread reads meanwhile."""
    if cancel.is_set():
        raise Cancelled()
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    stderr, reader = _watch_stderr(process)
    try:
        for sent, frame in enumerate(frames, start=1):
            if cancel.is_set():
                break
            process.stdin.write(frame)
            on_frame(sent)
        if not cancel.is_set():
            process.stdin.close()
    except OSError:  # BrokenPipeError, or a plain OSError on Windows: ffmpeg is gone
        pass
    except BaseException:  # a frame that couldn't be drawn: ffmpeg must not wait for more
        process.kill()
        raise
    finally:
        if cancel.is_set():
            process.kill()
        process.wait()
        reader.join()
    _ended(process, cancel, stderr)


class CaptureRunner(Protocol):
    """What runs an ffmpeg command whose output is its stdout: `run_capture`, or a test's stand-in."""

    def __call__(self, command: list[str], cancel: threading.Event) -> bytes: ...


def run_capture(command: list[str], cancel: threading.Event) -> bytes:
    """Runs ffmpeg and returns everything it wrote to stdout (raw PCM, `-f f32le -`; drum-notes
    D20). Raises `Cancelled` once `cancel` is set (ffmpeg is killed), or `FfmpegFailed` with the
    last line it printed (`last_line`); the last 20 go to the log."""
    if cancel.is_set():
        raise Cancelled()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finished = threading.Event()
    threading.Thread(target=kill_on_cancel, args=(process, cancel, finished), daemon=True).start()
    stderr, reader = _watch_stderr(process)
    try:
        output = process.stdout.read()
        process.wait()
        reader.join()
    finally:
        finished.set()
    _ended(process, cancel, stderr)
    return output
