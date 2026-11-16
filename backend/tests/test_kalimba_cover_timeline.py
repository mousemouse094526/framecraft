"""A kalimba reel's timeline from a hand-made analysis (kalimba-cover seam 2; spec › Timeline ของคาลิมบา,
D6): the arranged notes at their samples on their tines, and the beats numbered by `drum_cover`'s own rule."""

import pytest

from backend.drum_cover import timeline as reel
from backend.drum_cover.cover import Backing, CoverFields
from backend.drum_notes.songs import Analysis, Note
from backend.kalimba_cover import timeline as kalimba
from backend.kalimba_cover.timeline import KalimbaNote


def analysis(notes: list[tuple[float, int]] = (), downbeats=(9.0, 11.0, 13.0)) -> Analysis:
    """Beats every 0.5 s from 8.0, the first bar starting a beat and a half in."""
    return Analysis(
        mode="melody", start_s=8.0, end_s=16.0, beats=[8.0 + n / 2 for n in range(17)], downbeats=list(downbeats), hits=[],
        notes=[Note(t=t, pitch=pitch, level="normal") for t, pitch in notes], picked_at="2026-11-16T00:00:00Z",
    )  # fmt: skip


def cover(start_s: float = 10.0, end_s: float = 14.0) -> CoverFields:
    return CoverFields(
        start_s=start_s, end_s=end_s, title="Yellow", subtitle="", caption="", background="color",
        backing=Backing(on=False, volume=35), instrument="kalimba",
    )  # fmt: skip


def test_a_note_a_second_into_the_stretch_starts_at_sample_44100_on_its_tine():
    timing = kalimba.build(analysis([(11.0, 60), (12.0, 88), (9.5, 64), (14.0, 67)]), cover())

    assert timing.notes == (KalimbaNote(44_100, 8, 60, "normal"), KalimbaNote(88_200, 16, 88, "normal"))
    assert timing.length_s == pytest.approx(4.0 + 1.5)
    assert timing.samples == round(5.5 * 44_100)


def test_a_chord_on_one_sample_plays_its_top_and_the_arrangement_s_counts_come_along():
    # Down 2 puts all three in C major. 61 and 74, 1/88_200 s apart, round to one sample and are one
    # chord, of which 72 is the top; 59 → 57 folds up to A4.
    timing = kalimba.build(analysis([(10.5, 59), (11.0, 61), (11.0 + 1 / 88_200, 74)]), cover())

    assert timing.notes == (KalimbaNote(22_050, 5, 69, "normal"), KalimbaNote(44_100, 4, 72, "normal"))
    assert (timing.transpose, timing.dropped, timing.bent) == (-2, 1, 0)


def test_the_beats_are_numbered_as_the_drum_reel_numbers_them():
    song = analysis([(11.0, 60)])

    timing = kalimba.build(song, cover())

    assert timing.beats == reel.build(song, cover()).beats
    assert [beat.number for beat in timing.beats][:4] == [3, 4, 1, 2]


def test_a_song_picked_before_its_notes_were_kept_has_none_to_play():
    song = analysis().model_copy(update={"notes": None})

    assert kalimba.build(song, cover()).notes == ()
