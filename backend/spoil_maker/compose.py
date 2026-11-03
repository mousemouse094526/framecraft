"""ffmpeg for a render (spoil-maker spec › Render job step 3, D9, D22, D31, D40, D45):
each half-sentence Shot becomes a 1080×1920 30 fps piece with the original sound
turned down, then the pieces are joined, the voice mixed in, the ASS text drawn and
the whole encoded for phones.

Every command runs with `cwd` at the render's work folder and names files there
bare, so no path goes through ffmpeg's filter escaping (docs/library-notes/ffmpeg.md).
"""

import logging
import subprocess
import threading
from collections import deque
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from backend.jobs import Cancelled
from backend.spoil_maker.ffmpeg import FfmpegFailed, Media, exe, kill_on_cancel

log = logging.getLogger(__name__)

FPS = 30
WIDTH, HEIGHT = 1080, 1920
AUDIO_RATE = 48_000
# Seeking this close to a clip's end may find no frame; a Shot past it shows the last
# frame held (spec › Render job step 3.2).
END_MARGIN_SECONDS = 0.5
STDERR_LINES = 20  # the tail of ffmpeg's errors that goes to the log (spec › Render job)

# The picture of each layout (D22): `{tail}` makes every piece the same format and
# holds its last frame when the source runs out.
LAYOUT_GRAPHS = {
    "A": (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30[blur];"
        "[fg]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350[top];"
        "[blur][top]overlay=0:285,{tail}[v]"
    ),
    "B": "[0:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:656+(608-ih)/2:black,{tail}[v]",
    "C": "[0:v]scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:420+(608-ih)/2:black,{tail}[v]",
}


class Piece(BaseModel):
    """Half a sentence on the timeline: one Shot played from its start (D31)."""

    clip_id: str
    start: float
    seconds: float


def piece_command(piece: Piece, mp4: Path, media: Media, layout: str, volume: int, out: str) -> list[str]:
    """The piece framed for `layout`, with the original sound at `volume` percent (0:
    silence, D40). Lossless-enough x264 and PCM, so the join and the final encode lose
    nothing that shows."""
    start = min(piece.start, max(0.0, media.duration_s - END_MARGIN_SECONDS))
    seconds = piece.seconds
    tail = f"fps={FPS},format=yuv420p,setsar=1,tpad=stop_mode=clone:stop_duration={seconds:.3f}"
    graph = LAYOUT_GRAPHS[layout].format(tail=tail)
    inputs = ["-ss", f"{start:.3f}", "-i", str(mp4)]
    if volume > 0 and media.has_audio:
        graph += f";[0:a]volume={volume / 100:.2f},aresample={AUDIO_RATE},aformat=channel_layouts=stereo,apad[a]"
        audio = "[a]"
    else:
        inputs += ["-f", "lavfi", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo"]
        audio = "1:a"
    return [
        exe(), "-nostdin", "-hide_banner", "-y", *inputs,
        "-filter_complex", graph, "-map", "[v]", "-map", audio, "-t", f"{seconds:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-ar", str(AUDIO_RATE), "-ac", "2", out,
    ]  # fmt: skip


def final_command(pieces_list: str, narration: str, captions: str, fonts_dir: str, seconds: float, out: str) -> list[str]:
    """Joins the pieces, mixes the voice over their sound (`normalize=0`, so neither is
    turned down) and draws the text (spec › Render job step 3.4)."""
    graph = (
        f"[0:v]ass=filename={captions}:fontsdir={fonts_dir}[v];"
        f"[1:a]aresample={AUDIO_RATE},aformat=channel_layouts=stereo[voice];"
        f"[0:a][voice]amix=inputs=2:duration=first:normalize=0[a]"
    )
    return [
        exe(), "-nostdin", "-hide_banner", "-y", "-progress", "pipe:1", "-nostats",
        "-f", "concat", "-safe", "0", "-i", pieces_list, "-i", narration,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{seconds:.3f}",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE),
        "-movflags", "+faststart", "-f", "mp4", out,
    ]  # fmt: skip


def run(command: list[str], cwd: Path, cancel: threading.Event, on_progress: Callable[[float], None] | None = None) -> None:
    """Runs ffmpeg in `cwd`. `on_progress` gets the output's seconds so far from
    `-progress pipe:1`. Raises `Cancelled` once `cancel` is set (ffmpeg is killed), or
    `FfmpegFailed` with the last line it printed; the last 20 go to the log."""
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
        raise FfmpegFailed(f"ffmpeg exited with {process.returncode}: {stderr[-1] if stderr else 'no output'}")
