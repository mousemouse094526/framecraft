"""A lesson's timeline (video-gen seam 2 › `timeline.build`)."""

import pytest

from backend.video_gen import timeline

from .fakes import drum_chapter as chapter
from .fakes import drum_lesson as lesson
from .fakes import drum_note as note

RATE = 44_100


def hits_of(timing: timeline.Timeline, piece: str) -> list[timeline.Hit]:
    return [hit for hit in timing.hits if hit.piece == piece]


# --- timeline.build ---


def test_a_half_speed_first_chapter_counts_in_for_four_seconds_and_its_notes_follow():
    timing = timeline.build(lesson(note("snare", 2), note("tom_high", 4), bpm=120, chapters=[chapter(speed=50)]))

    assert [hit.at for hit in hits_of(timing, "hihat_closed")] == [0, RATE, 2 * RATE, 3 * RATE]
    assert {hit.layer for hit in hits_of(timing, "hihat_closed")} == {"soft"}
    assert timing.chapters[0].start == 4 * RATE
    # a 16th is 0.25 s at 60 BPM: step 2 at 4.5 s, step 4 at 5.0 s
    assert hits_of(timing, "snare")[0].at == round(4.5 * RATE)
    assert hits_of(timing, "tom_high")[0].at == 5 * RATE


def test_a_flam_is_a_soft_grace_note_with_the_other_hand_30_ms_before_the_main_one():
    timing = timeline.build(lesson(note("snare", 0, "R", "flam")))

    grace, main = hits_of(timing, "snare")
    assert main.at - grace.at == round(0.03 * RATE)
    assert (grace.hand, grace.layer) == ("L", "soft")
    assert (main.hand, main.layer) == ("R", "mid")


def test_accent_normal_and_ghost_play_the_hard_mid_and_soft_layers():
    timing = timeline.build(lesson(note("snare", 0, "R", "accent"), note("snare", 4, "R"), note("snare", 8, "R", "ghost")))

    assert [hit.layer for hit in hits_of(timing, "snare")] == ["hard", "mid", "soft"]


def test_round_robins_cycle_per_piece_and_layer_from_the_clip_s_start():
    notes = [note("snare", step, "L") for step in (0, 4, 8, 12)] + [note("ride", step, "R") for step in (0, 4, 8, 12)]
    timing = timeline.build(lesson(*notes, chapters=[chapter(repeats=2)]))

    assert [hit.round_robin for hit in hits_of(timing, "snare")] == [1, 2, 3, 4, 1, 2, 3, 4]
    # the ride has three round-robins per layer
    assert [hit.round_robin for hit in hits_of(timing, "ride")] == [1, 2, 3, 1, 2, 3, 1, 2]
    # the count-in's soft hi-hats don't touch the snare's count
    assert [hit.round_robin for hit in hits_of(timing, "hihat_closed")] == [1, 2, 3, 4]


def test_length_counts_the_count_in_every_chapter_and_a_1_5_s_tail():
    timing = timeline.build(lesson(bpm=100, bars=2, chapters=[chapter(repeats=2, speed=75), chapter(repeats=1)]))

    # count-in 4 × 0.8 s, then 2 × 2 bars × 3.2 s, then 2 bars × 2.4 s, then the tail
    assert timing.length_s == pytest.approx(3.2 + 12.8 + 4.8 + 1.5)
    assert timing.samples == round((3.2 + 12.8 + 4.8 + 1.5) * RATE)
    assert [(span.start, span.end) for span in timing.chapters] == [
        (round(3.2 * RATE), round(16.0 * RATE)),
        (round(16.0 * RATE), round(20.8 * RATE)),
    ]


def test_every_bar_has_four_beats_numbered_after_the_count_in():
    timing = timeline.build(lesson(bpm=120, bars=2))

    assert [beat.number for beat in timing.beats] == [1, 2, 3, 4] * 3
    assert timing.beats[4].at == round(2.0 * RATE)
