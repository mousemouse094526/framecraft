"""The drum sound of a lesson, mixed from the samples at their own 44.1 kHz (video-gen spec ›
Timeline and audio, D8, D19, D21): ฟังจังหวะ plays it, the Render job encodes it.

Every hit's start comes from `timeline`; nothing here works out a time (ADR 0038). numpy and
soundfile are imported inside `mix`, so the backend starts fast.
"""

import io
from typing import TYPE_CHECKING

from backend import drum_kit, gate_rows
from backend.errors import require_rows
from backend.paths import ProjectPaths
from backend.video_gen import lessons, timeline
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    import numpy as np

PEAK_DBFS = -1.0
CHOKE_FADE_S = 0.010  # an open hi-hat fades this long once the hi-hat closes (D19)
CHOKED_BY = ("hihat_closed", "hihat_pedal")
CHANNELS = 2  # the samples are mono; the wav is stereo as spec › Timeline and audio asks, both channels alike


def listen(project: ProjectPaths, lesson_id: str) -> bytes:
    """ฟังจังหวะ: the whole clip's sound, mixed the way a render mixes it (D8). Raises `ApiError`
    503 `not_ready` without the samples, then 404 `not_found`, then 422 `too_long` over 90 s
    (D16): the order a render checks in (spec › Render job)."""
    require_rows(gate_rows.drum_kit_row(project))
    lesson = lessons.stored(project, lesson_id)
    lessons.require_short(lesson)
    return mix(project, timeline.build(lesson))


def mix(project: ProjectPaths, timing: Timeline) -> bytes:
    """A 16-bit 44.1 kHz stereo wav exactly `timing.samples` long, its peak at −1 dBFS. The
    same timeline always mixes the same bytes (D13): each file is read once per call and the
    float sum is rounded to 16 bits by numpy, not by libsndfile."""
    import numpy as np
    import soundfile

    files = {(s.piece, s.layer, s.round_robin): drum_kit.sample_path(project, s) for s in drum_kit.SAMPLES}
    sounds: dict[tuple, np.ndarray] = {}
    out = np.zeros(timing.samples, dtype=np.float32)
    for index, hit in enumerate(timing.hits):
        key = (hit.piece, hit.layer, hit.round_robin)
        if key not in sounds:
            sounds[key] = _mono(soundfile.read(files[key], dtype="float32")[0])
        sound = sounds[key][: timing.samples - hit.at]
        if hit.piece == "hihat_open":
            sound = _choked(sound, hit.at, timing.hits[index + 1 :])
        out[hit.at : hit.at + len(sound)] += sound

    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    if peak > 0:
        out *= 10 ** (PEAK_DBFS / 20) / peak
    pcm = np.clip(np.rint(out * 32767), -32768, 32767).astype(np.int16)
    buffer = io.BytesIO()
    soundfile.write(buffer, np.column_stack([pcm] * CHANNELS), timeline.RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


def _mono(sound: "np.ndarray") -> "np.ndarray":
    """A sample's channels averaged: the kit plays in the middle."""
    return sound if sound.ndim == 1 else sound.mean(axis=1, dtype="float32")


def _choked(sound: "np.ndarray", at: int, later: tuple[timeline.Hit, ...]) -> "np.ndarray":
    """An open hi-hat cut by the next closed hi-hat or pedal: it fades out over 10 ms from
    that hit and stops (spec › Timeline and audio step 6)."""
    import numpy as np

    closing = next((hit for hit in later if hit.piece in CHOKED_BY), None)
    if closing is None or closing.at - at >= len(sound):
        return sound
    cut = closing.at - at
    fade = min(round(CHOKE_FADE_S * timeline.RATE), len(sound) - cut)
    choked = sound[: cut + fade].copy()
    choked[cut:] *= np.linspace(1, 0, fade, endpoint=False, dtype=np.float32)
    return choked
