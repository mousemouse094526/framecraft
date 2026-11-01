"""ffmpeg for Shots: where the picture cuts, and one frame per Shot (spoil-maker D17, D45).

Both run in the backend thread of the Describe job; ffmpeg is the one from
imageio-ffmpeg (ADR 0005). Steps are in docs/features/spoil-maker/spec.md › Describe job.
"""

import re
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

SCENE_THRESHOLD = 0.3  # D17
THUMBNAIL_WIDTH = 320  # the Shot picker loads dozens at once (D45)
# ffmpeg's JPEG quality is a 2–31 scale (lower is better), not 0–100: 5 is about 80 (D56).
THUMBNAIL_QSCALE = 5
LLM_FRAME_WIDTH = 448  # what Qwen describes (spec › Describe job step 5, D57)
LLM_FRAME_QSCALE = 2
KILL_POLL_SECONDS = 0.2

_DURATION = re.compile(r"Duration: (\d+):(\d\d):(\d\d(?:\.\d+)?)")
_PTS_TIME = re.compile(r"\bn:\s*\d+\s+pts:\s*\S+\s+pts_time:\s*(\d+(?:\.\d+)?)")


class FfmpegFailed(Exception):
    """ffmpeg exited with an error; the message is the last line it printed."""


def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def find_cuts(
    mp4: Path,
    on_progress: Callable[[float], None],
    cancel: threading.Event,
) -> tuple[list[float], float]:
    """The times the picture cuts (scene score above 0.3) and the clip's length, both
    in seconds. `on_progress` gets how far into the clip ffmpeg has read, once a second
    of video. Kills ffmpeg when `cancel` is set and returns early; the caller checks
    `cancel`. Raises `FfmpegFailed` otherwise.

    One branch selects the cuts; the other passes a frame per second only to say how
    far ffmpeg is, since `select` drops every frame between cuts. Each ends in a
    named `showinfo` that prints `pts_time` for every frame it sees
    ([ffmpeg filters](https://ffmpeg.org/ffmpeg-filters.html#select_002c-aselect)).
    """
    graph = (
        f"[0:v]split=2[scan][clock];"
        f"[scan]select='gt(scene,{SCENE_THRESHOLD})',showinfo@cut[cuts];"
        f"[clock]fps=1,showinfo@tick[ticks]"
    )
    command = [
        _ffmpeg(), "-nostdin", "-hide_banner", "-i", str(mp4), "-an", "-sn", "-filter_complex", graph,
        "-map", "[cuts]", "-f", "null", "-", "-map", "[ticks]", "-f", "null", "-",
    ]  # fmt: skip
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors="replace"
    )
    finished = threading.Event()
    threading.Thread(target=_kill_on_cancel, args=(process, cancel, finished), daemon=True).start()
    cuts: list[float] = []
    duration: float | None = None
    last_line = ""
    try:
        for line in process.stderr:
            last_line = line.strip() or last_line
            if duration is None and (found := _DURATION.search(line)):
                hours, minutes, seconds = found.groups()
                duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            elif found := _PTS_TIME.search(line):
                if line.startswith("[showinfo@cut "):
                    cuts.append(float(found.group(1)))
                elif line.startswith("[showinfo@tick "):
                    on_progress(float(found.group(1)))
        process.wait()
    finally:
        finished.set()
    if cancel.is_set():
        return cuts, duration or 0.0
    if process.returncode != 0 or duration is None:
        raise FfmpegFailed(f"ffmpeg exited with {process.returncode}: {last_line}")
    return cuts, duration


def _kill_on_cancel(process: subprocess.Popen, cancel: threading.Event, finished: threading.Event) -> None:
    while not finished.is_set():
        if cancel.wait(KILL_POLL_SECONDS):
            process.kill()
            return


def extract_frame(mp4: Path, at_s: float, thumbnail: Path, llm_frame: Path) -> None:
    """The frame at `at_s`, decoded once: a 448-wide JPEG for the LLM and a 320-wide
    thumbnail. Raises `FfmpegFailed` when ffmpeg finds no frame there."""
    graph = (
        f"[0:v]split=2[big][small];[big]scale={LLM_FRAME_WIDTH}:-2[llm];[small]scale={THUMBNAIL_WIDTH}:-2[thumb]"
    )
    command = [
        _ffmpeg(), "-nostdin", "-v", "error", "-y", "-ss", f"{at_s:.3f}", "-i", str(mp4),
        "-filter_complex", graph,
        "-map", "[llm]", "-frames:v", "1", "-q:v", str(LLM_FRAME_QSCALE), "-update", "1", str(llm_frame),
        "-map", "[thumb]", "-frames:v", "1", "-q:v", str(THUMBNAIL_QSCALE), "-update", "1", str(thumbnail),
    ]  # fmt: skip
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode != 0 or not (llm_frame.is_file() and thumbnail.is_file()):
        lines = result.stderr.strip().splitlines()
        raise FfmpegFailed(f"ffmpeg exited with {result.returncode}: {lines[-1] if lines else 'no frame'}")
