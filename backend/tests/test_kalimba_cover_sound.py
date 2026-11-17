"""The kalimba's sound (kalimba-cover seam 2; spec › เสียงคาลิมบา, D5, D12, D18): the VCSL pluck
nearest a tine moved to its exact pitch, the buzz and the other tines filtered out, a timeline mixed
to the same bytes every time at −1 dBFS, and silence as long as the clip. The samples are
`fakes.fake_pluck`s at each file's measured pitch."""

import io

import numpy as np
import pytest
import soundfile

from backend import kalimba_kit
from backend.kalimba_cover import arrange, sound
from backend.kalimba_cover.timeline import KalimbaNote, KalimbaTimeline
from backend.paths import ProjectPaths

RATE = 44_100


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def timing(*notes: KalimbaNote, length_s: float = 3.0) -> KalimbaTimeline:
    return KalimbaTimeline(notes=notes, beats=(), length_s=length_s, changes=arrange.Changes(transpose=0, dropped=0, bent=0))


def pcm(wav: bytes) -> np.ndarray:
    data, rate = soundfile.read(io.BytesIO(wav), dtype="int16")
    assert rate == RATE and data.shape[1] == 2 and np.array_equal(data[:, 0], data[:, 1])
    return data[:, 0]


def main_hz(tone: np.ndarray) -> float:
    spectrum = np.abs(np.fft.rfft(tone, 2**20))
    return float(np.fft.rfftfreq(2**20, 1 / RATE)[np.argmax(spectrum)])


def level_at(tone: np.ndarray, hz: float) -> float:
    """The spectrum's height at `hz` against its highest."""
    spectrum = np.abs(np.fft.rfft(tone, 2**20))
    return float(spectrum[round(hz * 2**20 / RATE)] / spectrum.max())


@pytest.mark.parametrize(("pitch", "hz"), [(60, 261.63), (62, 293.66), (81, 880.0), (88, 1318.51)])
def test_each_tine_rings_at_its_own_pitch_from_the_nearest_sample(project, pitch, hz):
    tone = sound.note(project, pitch, "normal")

    assert tone.dtype == np.float32
    assert main_hz(tone) == pytest.approx(hz, abs=1.5)  # Hz: the FFT's bin and the fake pluck's decay


def test_the_nearest_sample_is_by_its_measured_pitch_and_a_tie_moves_the_higher_down(monkeypatch):
    assert kalimba_kit.nearest(60).path == "MBira3_pluck_Main_C#3_k16_50_100_rr2.wav"  # rings at 60.55: its name's C#3 + 12
    assert kalimba_kit.nearest(81).path == "MBira3_pluck_Main_A#4_k2_50_100_rr2.wav"  # 82.48 is nearer than G4's 79.33
    assert len({kalimba_kit.nearest(pitch).path for pitch in arrange.TINE_PITCHES}) == len(kalimba_kit.SAMPLES)  # each one used
    below, above = kalimba_kit.Sample("below.wav", 63.0, ""), kalimba_kit.Sample("above.wav", 65.0, "")
    monkeypatch.setattr(kalimba_kit, "SAMPLES", (below, above))
    assert kalimba_kit.nearest(64) == above


def test_the_pluck_starts_at_once_rings_at_most_4_s_and_an_accent_is_louder_than_a_ghost(project):
    tone = sound.note(project, 60, "normal")

    assert int(np.argmax(np.abs(tone) > 0.05 * np.abs(tone).max())) < RATE // 500  # the sample's silence is cut: within 2 ms
    assert len(tone) <= 4 * RATE
    assert np.abs(tone).max() == pytest.approx(sound.GAIN["normal"])
    assert np.abs(sound.note(project, 72, "accent")).max() > np.abs(sound.note(project, 72, "ghost")).max()


def test_the_other_tines_ringing_below_and_the_buzz_above_are_filtered_out(project):
    rate = 48_000
    t = np.arange(rate) / rate
    c4 = 440 * 2 ** ((60.55 - 69) / 12)
    # The tine, the tine an octave down ringing along, and the rattle's 12 kHz, as loud as the tine.
    recorded = np.exp(-t / 0.3) * (np.sin(2 * np.pi * c4 * t) + np.sin(np.pi * c4 * t) + np.sin(2 * np.pi * 12_000 * t))
    sample = kalimba_kit.nearest(60)
    soundfile.write(kalimba_kit.sample_path(project, sample), (recorded / 3).astype(np.float32), rate)

    tone = sound.note(project, 60, "normal")

    assert main_hz(tone) == pytest.approx(261.63, abs=1)
    assert level_at(tone, 261.63 / 2) < 0.01 and level_at(tone, 12_000 * 261.63 / c4) < 0.01


def test_a_timeline_mixes_to_the_same_bytes_every_time_its_peak_at_minus_1_dbfs(project):
    notes = timing(KalimbaNote(RATE // 2, 8, 60, "normal"), KalimbaNote(RATE, 10, 67, "accent"), KalimbaNote(RATE, 15, 84, "ghost"))

    first, second = sound.mix(project, notes), sound.mix(project, notes)

    assert first == second
    samples = pcm(first)
    assert len(samples) == notes.samples
    assert np.abs(samples[: RATE // 2]).max() == 0  # nothing before the first note
    assert np.abs(samples.astype(np.int32)).max() == round(32767 * 10 ** (-1 / 20))


def test_a_tine_played_again_cuts_the_ring_before_it(project):
    again = pcm(sound.mix(project, timing(KalimbaNote(0, 8, 60, "normal"), KalimbaNote(RATE, 8, 60, "normal"))))
    once = pcm(sound.mix(project, timing(KalimbaNote(RATE, 8, 60, "normal"))))

    # From 10 ms after the second strike only it rings, at the level the pair's peak allows.
    after = RATE + 441
    ratio = np.abs(again[after:]).max() / np.abs(once[after:]).max()
    assert np.allclose(again[after:] / ratio, once[after:], atol=2)


def test_no_notes_is_silence_as_long_as_the_clip(project):
    samples = pcm(sound.mix(project, timing(length_s=2.5)))

    assert len(samples) == round(2.5 * RATE) and not samples.any()

