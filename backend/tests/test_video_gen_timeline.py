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


def test_the_clip_starts_on_the_first_bar_with_no_count_in():
    timing = timeline.build(lesson(note("snare", 0), note("tom_high", 4), bpm=120))

    # reels-only D15: no soft hi-hat ticks, the snare on step 0 is the first sound at 0 s
    assert timing.hits[0] == timeline.Hit(0, "snare", "R", "mid", 1, "normal")
    assert hits_of(timing, "hihat_closed") == []
    assert timing.chapters[0].start == 0
    # a beat is 0.5 s at 120 BPM: the beats of the one bar, then the tail
    assert [(beat.at, beat.number) for beat in timing.beats] == [(round(t * RATE), n) for t, n in [(0, 1), (0.5, 2), (1.0, 3), (1.5, 4)]]
    assert timing.length_s == pytest.approx(2.0 + 1.5)


def test_a_half_speed_first_chapter_plays_its_notes_from_0_s():
    timing = timeline.build(lesson(note("snare", 2), note("tom_high", 4), bpm=120, chapters=[chapter(speed=50)]))

    # a 16th is 0.25 s at 60 BPM: step 2 at 0.5 s, step 4 at 1.0 s
    assert hits_of(timing, "snare")[0].at == round(0.5 * RATE)
    assert hits_of(timing, "tom_high")[0].at == RATE


def test_a_flam_is_a_soft_grace_note_with_the_other_hand_30_ms_before_the_main_one():
    timing = timeline.build(lesson(note("snare", 4, "R", "flam")))

    grace, main = hits_of(timing, "snare")
    assert main.at - grace.at == round(0.03 * RATE)
    assert (grace.hand, grace.layer, grace.note) == ("L", "soft", "grace")
    assert (main.hand, main.layer) == ("R", "mid")


def test_a_flam_on_the_clip_s_first_step_plays_its_main_note_only_and_the_next_round_s_in_full():
    timing = timeline.build(lesson(note("snare", 0, "R", "flam"), chapters=[chapter(repeats=2)]))

    # reels-only D16: the first grace note would fall at -0.03 s
    assert min(hit.at for hit in timing.hits) == 0
    assert [(hit.at, hit.note) for hit in hits_of(timing, "snare")] == [(0, "flam"), (round((2.0 - 0.03) * RATE), "grace"), (2 * RATE, "flam")]


def test_accent_normal_and_ghost_play_the_hard_mid_and_soft_layers():
    timing = timeline.build(lesson(note("snare", 0, "R", "accent"), note("snare", 4, "R"), note("snare", 8, "R", "ghost")))

    assert [hit.layer for hit in hits_of(timing, "snare")] == ["hard", "mid", "soft"]


def test_round_robins_cycle_per_piece_and_layer_from_the_clip_s_start():
    notes = [note("snare", step, "L") for step in (0, 4, 8, 12)] + [note("ride", step, "R") for step in (0, 4, 8, 12)]
    timing = timeline.build(lesson(*notes, chapters=[chapter(repeats=2)]))

    assert [hit.round_robin for hit in hits_of(timing, "snare")] == [1, 2, 3, 4, 1, 2, 3, 4]
    # the ride has three round-robins per layer
    assert [hit.round_robin for hit in hits_of(timing, "ride")] == [1, 2, 3, 1, 2, 3, 1, 2]


def test_length_counts_every_chapter_and_a_1_5_s_tail():
    timing = timeline.build(lesson(bpm=100, bars=2, chapters=[chapter(repeats=2, speed=75), chapter(repeats=1)]))

    # 2 × 2 bars × 3.2 s, then 2 bars × 2.4 s, then the tail: no count-in (reels-only D15)
    assert timing.length_s == pytest.approx(12.8 + 4.8 + 1.5)
    assert timing.samples == round((12.8 + 4.8 + 1.5) * RATE)
    assert [(span.start, span.end) for span in timing.chapters] == [
        (0, round(12.8 * RATE)),
        (round(12.8 * RATE), round(17.6 * RATE)),
    ]


def test_every_bar_has_four_beats_numbered_from_the_clip_s_start():
    timing = timeline.build(lesson(bpm=120, bars=2))

    assert [beat.number for beat in timing.beats] == [1, 2, 3, 4] * 2
    assert timing.beats[0].at == 0
    assert timing.beats[4].at == round(2.0 * RATE)
