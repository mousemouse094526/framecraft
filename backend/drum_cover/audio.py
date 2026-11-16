"""The sound of a reel cover (drum-cover spec › เสียง, D7, D17, D24; ADR 0050): one function,
`reel_wav`, that ฟัง and the Render job both play, so the two never sound different. It takes the
chosen instrument's wav, already mixed from its own timeline (ADR 0041; kalimba-cover D8): the
drums are `video_gen.mixer`'s, the kalimba `kalimba_cover.sound`'s, at the cover's volume of that
instrument. With backing on, the song's own audio of the stretch is decoded by ffmpeg to raw
floats and laid under it at its volume. A sum over the mixer's −1 dBFS peak is brought down to it, never pushed up: nothing
clips, a lower volume stays lower, and the render's ffmpeg command stays video-gen's.

numpy and soundfile are imported inside the functions, so the backend starts fast.
"""

import io
import threading
from collections.abc import Callable
from pathlib import Path

from backend import ffmpeg
from backend.drum_cover import cover
from backend.drum_cover.cover import CoverFields
from backend.video_gen import mixer, timeline

CaptureRunner = Callable[[list[str], threading.Event], bytes]
INT16_MAX = 32767  # full scale of a 16-bit sample, both ways


def reel_wav(audio: Path, fields: CoverFields, instrument_wav: bytes | None, samples: int, cancel: threading.Event,
             run_capture: CaptureRunner = ffmpeg.run_capture) -> bytes:  # fmt: skip
    """A 16-bit 44.1 kHz stereo wav exactly `samples` long from `instrument_wav`, the chosen
    instrument's wav that long (None while its sound is off). At full volume with backing off:
    `instrument_wav` as it is (the same bytes every time, D15). Backing on: `audio` (the song's
    `audio.m4a`) of the stretch under it. Raises `Cancelled` or `FfmpegFailed` from ffmpeg."""
    sound, backing = fields.instrument_sound(), fields.backing
    if instrument_wav is not None and not backing.on and sound.volume == cover.FULL_VOLUME:
        return instrument_wav
    import numpy as np
    import soundfile

    mixed = np.zeros((samples, mixer.CHANNELS), dtype=np.float32)
    if instrument_wav is not None:
        # Read as the mixer's 16-bit values over 32767, so a volume of 100 rounds back to them exactly.
        instrument_pcm, _ = soundfile.read(io.BytesIO(instrument_wav), dtype="int16")
        mixed += instrument_pcm.astype(np.float32) * (sound.volume / 100 / INT16_MAX)
    if backing.on:
        song = np.frombuffer(run_capture(_decode_command(audio, fields), cancel), dtype="<f4").reshape(-1, mixer.CHANNELS)
        length = min(len(song), len(mixed))
        mixed[:length] += song[:length] * (backing.volume / 100)
    peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
    ceiling = 10 ** (mixer.PEAK_DBFS / 20)
    if peak > ceiling:
        mixed *= ceiling / peak
    pcm = np.clip(np.rint(mixed * INT16_MAX), -32768, INT16_MAX).astype(np.int16)
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
