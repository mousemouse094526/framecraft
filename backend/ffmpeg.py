"""What every ffmpeg run shares: the binary from imageio-ffmpeg
(ADR 0005), a kill when the job is cancelled, and reading a file's length and
streams from `ffmpeg -i`, since there is no ffprobe (docs/library-notes/ffmpeg.md).

spoil_maker's `frames` (Shots) and `compose` (renders), and spoil's `trim` (cut ranges)
run ffmpeg through these.
"""

import logging
import re
import subprocess
import threading
from collections import deque
from collections.abc import Callable
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


def input_info(path: Path) -> str:
    """What `ffmpeg -i` prints about the file: its container, length and streams. With no
    output it exits 1 by design, so the exit code says nothing; callers read the text."""
    result = subprocess.run([exe(), "-hide_banner", "-nostdin", "-i", str(path)], capture_output=True, text=True, errors="replace")
    return result.stderr


def probe(path: Path) -> Media:
    """The file's length and whether it has sound; only a missing `Duration:` is a failure."""
    stderr = input_info(path)
    found = DURATION.search(stderr)
    if found is None:
        lines = stderr.strip().splitlines()
        last_line = lines[-1] if lines else "no output"
        raise FfmpegFailed(f"no length for {path.name}: {last_line}", last_line)
    return Media(duration_s=seconds_of(found), has_audio=re.search(r"Stream #\S+.*: Audio:", stderr) is not None)


def kill_on_cancel(process: subprocess.Popen, cancel: threading.Event, finished: threading.Event) -> None:
    """Run in a thread beside ffmpeg: kills it once `cancel` is set, until `finished` is."""
    while not finished.is_set():
        if cancel.wait(KILL_POLL_SECONDS):
            process.kill()
            return


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
    stderr: deque[str] = deque(maxlen=STDERR_LINES)
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace"
    )
    finished = threading.Event()
    threading.Thread(target=kill_on_cancel, args=(process, cancel, finished), daemon=True).start()
    reader = threading.Thread(target=lambda: stderr.extend(line.rstrip() for line in process.stderr), daemon=True)
    reader.start()
    try:
        for line in process.stdout:
            key, _, value = line.strip().partition("=")
            if key == "out_time_us" and on_progress and value.isdigit():
                on_progress(int(value) / 1_000_000)
        process.wait()
        reader.join()
    finally:
        finished.set()
    if cancel.is_set():
        raise Cancelled()
    if process.returncode != 0:
        log.error("ffmpeg exited with %s:\n%s", process.returncode, "\n".join(stderr))
        last_line = stderr[-1] if stderr else "no output"
        raise FfmpegFailed(f"ffmpeg exited with {process.returncode}: {last_line}", last_line)
