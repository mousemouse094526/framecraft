"""The kalimba's sound, synthesised (kalimba-cover spec › เสียงคาลิมบา, D5): each note three decaying
sines of a metal tine and a short strike of seeded noise, mixed at the `KalimbaTimeline`'s samples
to a 16-bit 44.1 kHz stereo wav at −1 dBFS the way `video_gen.mixer` mixes the drums. The same
timeline always mixes the same bytes; nothing to download, no Status check row. `note` is the one
place the sound comes from, so a recorded sample can replace it without touching the timeline or
the picture.

Every start comes from the timeline; nothing here works out a time (ADR 0041). numpy and soundfile
are imported inside the functions, so the backend starts fast.
"""

from typing import TYPE_CHECKING

from backend.drum_notes.songs import Level
from backend.kalimba_cover.timeline import KalimbaNote, KalimbaTimeline
from backend.video_gen import mixer, timeline

if TYPE_CHECKING:
    import numpy as np

RATE = timeline.RATE
# The tine's partials: (ratio to f0, amplitude, decay τ in s); the first decays by pitch instead.
PARTIALS = ((1.0, 1.0, None), (5.4, 0.12, 0.18), (13.0, 0.04, 0.05))
MIDDLE_C_HZ = 261.63
TOP_HZ = 20_000  # a partial above this is left out
STRIKE_S, STRIKE_AMPLITUDE, STRIKE_DECAY_S = 0.006, 0.06, 0.0015
STRIKE_SEED = 0
ATTACK_S = 0.002
LONGEST_S = 4.0
GAIN = {"ghost": 0.45, "normal": 0.7, "accent": 1.0}
CHOKE_FADE_S = mixer.CHOKE_FADE_S  # a tine struck again stops its ring this fast


def note(pitch: int, level: Level) -> "np.ndarray":
    """One tine struck: float32 mono at `RATE`, `min(5 τ0, 4 s)` long (spec › เสียงคาลิมบา steps 1–3)."""
    import numpy as np

    f0 = 440 * 2 ** ((pitch - 69) / 12)
    tau0 = 1.4 * (MIDDLE_C_HZ / f0) ** 0.5
    length = round(min(5 * tau0, LONGEST_S) * RATE)
    t = np.arange(length, dtype=np.float32) / RATE
    tone = np.zeros(length, dtype=np.float32)
    for ratio, amplitude, tau in PARTIALS:
        if f0 * ratio > TOP_HZ:
            continue
        tone += amplitude * np.exp(-t / (tau or tau0)) * np.sin(2 * np.pi * f0 * ratio * t)
    strike = round(STRIKE_S * RATE)
    noise = np.random.default_rng(STRIKE_SEED).uniform(-1, 1, strike).astype(np.float32)
    tone[:strike] += STRIKE_AMPLITUDE * noise * np.exp(-t[:strike] / STRIKE_DECAY_S)
    attack = round(ATTACK_S * RATE)
    tone[:attack] *= np.linspace(0, 1, attack, endpoint=False, dtype=np.float32)
    return (tone * GAIN[level]).astype(np.float32)


def mix(timing: KalimbaTimeline) -> bytes:
    """A 16-bit 44.1 kHz stereo wav exactly `timing.samples` long, its peak at −1 dBFS; no notes:
    silence that long (steps 4–6). Each pitch and level is made once per call."""
    import numpy as np

    made: dict[tuple[int, Level], np.ndarray] = {}
    out = np.zeros(timing.samples, dtype=np.float32)
    for index, struck in enumerate(timing.notes):
        sound = (struck.pitch, struck.level)
        if sound not in made:
            made[sound] = note(*sound)
        ring = _choked(made[sound][: timing.samples - struck.at], struck, timing.notes[index + 1 :])
        out[struck.at : struck.at + len(ring)] += ring
    return mixer.to_wav(out)


def _choked(ring: "np.ndarray", struck: KalimbaNote, later: tuple[KalimbaNote, ...]) -> "np.ndarray":
    """A tine's ring cut when the same tine is struck again: it fades over 10 ms from there and stops."""
    import numpy as np

    again = next((other for other in later if other.tine == struck.tine), None)
    if again is None or again.at - struck.at >= len(ring):
        return ring
    cut = again.at - struck.at
    fade = min(round(CHOKE_FADE_S * RATE), len(ring) - cut)
    choked = ring[: cut + fade].copy()
    choked[cut:] *= np.linspace(1, 0, fade, endpoint=False, dtype=np.float32)
    return choked
