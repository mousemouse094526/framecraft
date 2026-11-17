"""The kalimba's sound (kalimba-cover spec › เสียงคาลิมบา, D5, D18): each note the VCSL pluck
nearest its pitch (`backend.kalimba_kit`), moved to the tine's exact pitch, with the mbira's buzz
and the other tines ringing along filtered down, mixed at the `KalimbaTimeline`'s samples to a
16-bit 44.1 kHz stereo wav at −1 dBFS the way `video_gen.mixer` mixes the drums. The same timeline
and samples always mix the same bytes. `note` is the one place the sound comes from, so the
timeline and the picture don't know it is a sample.

Every start comes from the timeline; nothing here works out a time (ADR 0041). numpy and soundfile
are imported inside the functions, so the backend starts fast.
"""

from typing import TYPE_CHECKING

from backend import kalimba_kit
from backend.drum_notes.songs import Level
from backend.kalimba_cover.timeline import KalimbaNote, KalimbaTimeline
from backend.paths import ProjectPaths
from backend.video_gen import mixer, timeline

if TYPE_CHECKING:
    import numpy as np

RATE = timeline.RATE
ONSET_OF_PEAK = 0.05  # a pluck starts at its first sample this loud against its peak
PRE_ONSET_S = 0.001  # kept before it, so the strike's first edge isn't cut
LONGEST_S = 4.0
FADE_OUT_S = 0.05
# Below the tine (the mbira's other tines ringing along, measured up to as loud as the plucked
# tine an octave down) and above its first overtones (the buzz): filtered out by a cosine over
# the band, kept in full between. Set from measuring the 14 files, not by ear (D18).
BELOW_FROM, BELOW_TO = 0.7, 0.9  # × the tine's frequency: none at the first, all from the second
BUZZ_FROM, BUZZ_TO = 4_000, 9_000  # Hz: all up to the first, none from the second
GAIN = {"ghost": 0.45, "normal": 0.7, "accent": 1.0}
CHOKE_FADE_S = mixer.CHOKE_FADE_S  # a tine struck again stops its ring this fast


def note(project: ProjectPaths, pitch: int, level: Level) -> "np.ndarray":
    """One tine struck: float32 mono at `RATE`, at most 4 s, its peak at `GAIN[level]` (spec ›
    เสียงคาลิมบา steps 1–4)."""
    import numpy as np
    import soundfile

    sample = kalimba_kit.nearest(pitch)
    recorded, rate = soundfile.read(kalimba_kit.sample_path(project, sample), dtype="float32", always_2d=True)
    mono = recorded.mean(axis=1)
    onset = int(np.argmax(np.abs(mono) >= ONSET_OF_PEAK * np.abs(mono).max()))
    pluck = mono[max(0, onset - round(PRE_ONSET_S * rate)) :]
    # Read `step` source samples per output sample: the move to the tine's pitch and to RATE at once.
    step = 2 ** ((pitch - sample.pitch) / 12) * rate / RATE
    pluck = pluck[: round(LONGEST_S * RATE * step)]
    tone = _retuned(pluck, step, 440 * 2 ** ((pitch - 69) / 12))
    fade = min(round(FADE_OUT_S * RATE), len(tone))
    tone[len(tone) - fade :] *= np.linspace(1, 0, fade, endpoint=False, dtype=np.float32)
    peak = float(np.abs(tone).max()) or 1.0  # a silent file stays silent
    return (tone * (GAIN[level] / peak)).astype(np.float32)


def _retuned(pluck: "np.ndarray", step: float, hz: float) -> "np.ndarray":
    """`pluck` resampled by its spectrum to `len / step` samples at RATE, filtered on the way:
    below the tine and the buzz above its overtones (D18). Zero-padded first, so the filter's
    ring doesn't wrap the tail onto the strike."""
    import numpy as np

    padded = np.concatenate([pluck, np.zeros(len(pluck), dtype=np.float32)])
    spectrum = np.fft.rfft(padded)
    out_hz = np.fft.rfftfreq(len(padded), 1 / (step * RATE))  # each source bin's frequency once retuned
    spectrum *= _ramp(out_hz, BELOW_FROM * hz, BELOW_TO * hz) * (1 - _ramp(out_hz, BUZZ_FROM, BUZZ_TO))
    length = round(len(padded) / step)
    # The bins up to RATE's Nyquist: cut when retuning down the rate (no alias), zero-padded by `irfft` when up.
    bins = spectrum[: length // 2 + 1]
    tone = np.fft.irfft(bins, length) * (length / len(padded))
    return tone[: round(len(pluck) / step)].astype(np.float32)


def _ramp(hz: "np.ndarray", start: float, end: float) -> "np.ndarray":
    """0 up to `start`, 1 from `end`, a raised cosine between."""
    import numpy as np

    x = np.clip((hz - start) / (end - start), 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * x)


def mix(project: ProjectPaths, timing: KalimbaTimeline) -> bytes:
    """A 16-bit 44.1 kHz stereo wav exactly `timing.samples` long, its peak at −1 dBFS; no notes:
    silence that long (steps 5–7). Each pitch and level is made once per call. The caller gates
    the samples' row (`gate_rows.kalimba`, `kalimba_kit_row`), as `video_gen.mixer.mix`'s do."""
    import numpy as np

    made: dict[tuple[int, Level], np.ndarray] = {}
    out = np.zeros(timing.samples, dtype=np.float32)
    for index, struck in enumerate(timing.notes):
        sound = (struck.pitch, struck.level)
        if sound not in made:
            made[sound] = note(project, *sound)
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
