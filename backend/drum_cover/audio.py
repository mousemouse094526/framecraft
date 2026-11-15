"""The sound of a reel cover (drum-cover spec › เสียง, D7, D17; ADR 0050): one function, `reel_wav`,
that ฟัง and the Render job both play, so the two never sound different. The drums are
`video_gen.mixer`'s, timed by the `Timeline` (ADR 0041). With backing on, the song's own audio of the
stretch is decoded by ffmpeg to raw floats, laid under the drums at its volume, and the sum brought
to the mixer's −1 dBFS peak: nothing clips, and the render's ffmpeg command stays video-gen's.

numpy and soundfile are imported inside the functions, so the backend starts fast.
"""

import io
import threading
from collections.abc import Callable
from pathlib import Path

from backend import ffmpeg, gate_rows
from backend.drum_cover import cover
from backend.drum_cover import timeline as reel_timeline
from backend.drum_cover.cover import CoverFields
from backend.drum_notes import songs
from backend.errors import ApiError, require_rows
from backend.ffmpeg import FfmpegFailed
from backend.paths import ProjectPaths
from backend.video_gen import mixer, timeline
from backend.video_gen.timeline import Timeline

MIX_FAILED = "ผสมเสียงเพลงต้นฉบับไม่สำเร็จ"
CaptureRunner = Callable[[list[str], threading.Event], bytes]


def reel_wav(project: ProjectPaths, audio: Path, fields: CoverFields, timing: Timeline, cancel: threading.Event,
             run_capture: CaptureRunner = ffmpeg.run_capture) -> bytes:  # fmt: skip
    """A 16-bit 44.1 kHz stereo wav exactly `timing.samples` long. Backing off: the mixer's wav as
    it is (the same bytes every time, D15). Backing on: `audio` (the song's `audio.m4a`) of the
    stretch under the drums. Raises `Cancelled` or `FfmpegFailed` from ffmpeg."""
    drums = mixer.mix(project, timing)
    if not fields.backing.on:
        return drums
    import numpy as np
    import soundfile

    mixed, _ = soundfile.read(io.BytesIO(drums), dtype="float32")
    song = np.frombuffer(run_capture(_decode_command(audio, fields), cancel), dtype="<f4").reshape(-1, mixer.CHANNELS)
    length = min(len(song), len(mixed))
    mixed[:length] += song[:length] * (fields.backing.volume / 100)
    peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
    if peak > 0:
        mixed *= 10 ** (mixer.PEAK_DBFS / 20) / peak
    pcm = np.clip(np.rint(mixed * 32767), -32768, 32767).astype(np.int16)
    buffer = io.BytesIO()
    soundfile.write(buffer, pcm, timeline.RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def _decode_command(audio: Path, fields: CoverFields) -> list[str]:
    """The stretch as raw 32-bit floats at the mixer's rate and channels, to stdout: `-ss` before
    `-i` seeks, `-t` after it limits the length (docs/library-notes/ffmpeg.md)."""
    return [
        ffmpeg.exe(), "-hide_banner", "-v", "error",
        "-ss", f"{fields.start_s:.3f}", "-t", f"{fields.end_s - fields.start_s:.3f}", "-i", str(audio),
        "-vn", "-ac", str(mixer.CHANNELS), "-ar", str(timeline.RATE), "-f", "f32le", "-",
    ]  # fmt: skip


def listen(project: ProjectPaths, song_id: str) -> bytes:
    """ฟัง: the reel's whole sound from the saved cover (or its defaults), mixed as a render mixes
    it (D17). Raises `ApiError` 404, 409 `no_analysis`, 400 for backing on a song with no audio,
    then 503 `not_ready` without the samples (and ffmpeg with backing on)."""
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
        fields = cover.used(project, song)
    require_rows(gate_rows.drum_kit_row(project) | (gate_rows.FFMPEG if fields.backing.on else {}))
    timing = reel_timeline.build(cover.require_analysis(song), fields)
    audio = songs.checked_dir(project, song_id) / songs.AUDIO_FILE
    try:
        return reel_wav(project, audio, fields, timing, threading.Event())
    except FfmpegFailed as error:  # a broken `audio.m4a`, or one deleted with its song meanwhile
        raise ApiError(500, "ffmpeg_failed", f"{MIX_FAILED}: {error.last_line}") from None
