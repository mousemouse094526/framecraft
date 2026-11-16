"""The kalimba's synthesised sound (kalimba-cover seam 2; spec › เสียงคาลิมบา, D5, D12): a note at its
pitch, a timeline mixed to the same bytes every time at −1 dBFS, and silence as long as the clip."""

import io

import numpy as np
import pytest
import soundfile

from backend.kalimba_cover import sound
from backend.kalimba_cover.timeline import KalimbaNote, KalimbaTimeline

RATE = 44_100


def timing(*notes: KalimbaNote, length_s: float = 3.0) -> KalimbaTimeline:
    return KalimbaTimeline(notes=notes, beats=(), length_s=length_s, transpose=0, dropped=0, bent=0)


def pcm(wav: bytes) -> np.ndarray:
    data, rate = soundfile.read(io.BytesIO(wav), dtype="int16")
    assert rate == RATE and data.shape[1] == 2 and np.array_equal(data[:, 0], data[:, 1])
    return data[:, 0]


def test_c4_s_main_frequency_is_261_6_hz():
    tone = sound.note(60, "normal")

    spectrum = np.abs(np.fft.rfft(tone))
    assert tone.dtype == np.float32
    assert np.fft.rfftfreq(len(tone), 1 / RATE)[np.argmax(spectrum)] == pytest.approx(261.6, abs=1)


def test_a_note_starts_from_silence_rings_at_most_4_s_and_an_accent_is_louder_than_a_ghost():
    assert sound.note(60, "normal")[0] == 0
    assert len(sound.note(60, "normal")) == 4 * RATE  # C4's 5 τ is 7 s
    assert len(sound.note(88, "normal")) < 4 * RATE
    assert np.abs(sound.note(72, "accent")).max() > np.abs(sound.note(72, "ghost")).max()


def test_a_timeline_mixes_to_the_same_bytes_every_time_its_peak_at_minus_1_dbfs():
    notes = timing(KalimbaNote(RATE // 2, 8, 60, "normal"), KalimbaNote(RATE, 10, 67, "accent"), KalimbaNote(RATE, 15, 84, "ghost"))

    first, second = sound.mix(notes), sound.mix(notes)

    assert first == second
    samples = pcm(first)
    assert len(samples) == notes.samples
    assert np.abs(samples[: RATE // 2]).max() == 0  # nothing before the first note
    assert np.abs(samples.astype(np.int32)).max() == round(32767 * 10 ** (-1 / 20))


def test_a_tine_played_again_cuts_the_ring_before_it():
    again = pcm(sound.mix(timing(KalimbaNote(0, 8, 60, "normal"), KalimbaNote(RATE, 8, 60, "normal"))))
    once = pcm(sound.mix(timing(KalimbaNote(RATE, 8, 60, "normal"))))

    # From 10 ms after the second strike only it rings, at the level the pair's peak allows.
    after = RATE + 441
    ratio = np.abs(again[after:]).max() / np.abs(once[after:]).max()
    assert np.allclose(again[after:] / ratio, once[after:], atol=2)


def test_no_notes_is_silence_as_long_as_the_clip():
    samples = pcm(sound.mix(timing(length_s=2.5)))

    assert len(samples) == round(2.5 * RATE) and not samples.any()
