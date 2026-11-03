"""What every ffmpeg run of the สปอย tab shares: the binary from imageio-ffmpeg
(ADR 0005), a kill when the job is cancelled, and reading a file's length and
streams from `ffmpeg -i`, since there is no ffprobe (docs/library-notes/ffmpeg.md).

`frames` (Shots) and `compose` (renders) run ffmpeg through these.
"""

import re
import subprocess
import threading
from pathlib import Path
from typing import NamedTuple

KILL_POLL_SECONDS = 0.2

DURATION = re.compile(r"Duration: (\d+):(\d\d):(\d\d(?:\.\d+)?)")


class FfmpegFailed(Exception):
    """ffmpeg exited with an error; the message is the last line it printed."""


class Media(NamedTuple):
    duration_s: float
    has_audio: bool


def exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def seconds_of(found: re.Match) -> float:
    hours, minutes, seconds = found.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def probe(path: Path) -> Media:
    """The file's length and whether it has sound. `ffmpeg -i` with no output exits 1
    by design, so only a missing `Duration:` is a failure."""
    result = subprocess.run([exe(), "-hide_banner", "-nostdin", "-i", str(path)], capture_output=True, text=True, errors="replace")
    found = DURATION.search(result.stderr)
    if found is None:
        lines = result.stderr.strip().splitlines()
        raise FfmpegFailed(f"no length for {path.name}: {lines[-1] if lines else 'no output'}")
    return Media(duration_s=seconds_of(found), has_audio=re.search(r"Stream #\S+.*: Audio:", result.stderr) is not None)


def kill_on_cancel(process: subprocess.Popen, cancel: threading.Event, finished: threading.Event) -> None:
    """Run in a thread beside ffmpeg: kills it once `cancel` is set, until `finished` is."""
    while not finished.is_set():
        if cancel.wait(KILL_POLL_SECONDS):
            process.kill()
            return
