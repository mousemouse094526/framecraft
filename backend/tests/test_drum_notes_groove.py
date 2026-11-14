"""A lesson's Groove from the bars picked (drum-notes seam 2, D11, D13, D14, D20): the default BPM,
quantize, the base groove of melody mode, the trim to two hands and the sticking — on hand-made hits,
and on a lesson's own timeline round-tripped."""

import numpy as np

from backend.drum_notes import groove, score, songs
from backend.video_gen import lessons, timeline

from .fakes import drum_chapter, drum_lesson, drum_note


def bar(n: int, start_s: float, end_s: float, four_four: bool = True) -> songs.FoundBar:
    return songs.FoundBar(n=n, start_s=start_s, end_s=end_s, beats=4 if four_four else 3, hits=0, four_four=four_four)


def hit(t: float, piece: str = "kick", level: str = "normal") -> songs.Hit:
    return songs.Hit(t=t, piece=piece, level=level)


def placed(groove) -> list[tuple[str, int]]:
    return sorted((note.piece, note.step) for note in groove.notes)


def test_a_hit_rounds_to_its_nearest_step_one_just_before_the_bar_lands_on_step_0_and_one_at_the_next_bar_is_dropped_silently():
    # A 2.0 s bar from 10.0: a step is 0.125 s. 10.49 → 3.92 → step 4; 9.95 is 50 ms early, under half a step; 11.94 → 15.5 → 16, past the bar.
    preview = groove.preview([hit(9.95), hit(10.49, "snare"), hit(11.94, "crash")], [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert placed(preview.groove) == [("kick", 0), ("snare", 4)]
    assert preview.dropped == []
    assert preview.groove.bars == 1


def test_the_same_piece_twice_in_a_step_keeps_the_loudest_and_a_second_bar_s_steps_start_at_16():
    preview = groove.preview([hit(10.0, "snare", "ghost"), hit(10.02, "snare", "accent"), hit(12.25)], [bar(1, 10.0, 12.0), bar(2, 12.0, 14.0)], bpm=None, mode="drums")

    assert [(note.piece, note.step, note.hit) for note in preview.groove.notes] == [("snare", 0, "accent"), ("kick", 18, "normal")]
    assert preview.groove.bars == 2


def test_the_default_bpm_is_240_over_the_median_bar_length_within_40_to_240():
    assert groove.preview([], [bar(1, 10.0, 12.0)], bpm=None, mode="drums").bpm == 120
    assert groove.preview([], [bar(1, 0.0, 2.0), bar(2, 2.0, 4.0), bar(3, 4.0, 7.0)], bpm=None, mode="drums").bpm == 120
    assert groove.preview([], [bar(1, 0.0, 0.5)], bpm=None, mode="drums").bpm == 240
    assert groove.preview([], [bar(1, 0.0, 10.0)], bpm=None, mode="drums").bpm == 40
    assert groove.preview([], [bar(1, 0.0, 2.0)], bpm=95, mode="drums").bpm == 95


def test_a_third_hand_note_in_a_step_is_dropped_by_the_keep_order_and_an_open_hihat_beside_a_closed_one_goes():
    hits = [hit(10.0, "hihat_closed"), hit(10.0, "snare"), hit(10.0, "crash"), hit(10.0, "hihat_open"), hit(10.5, "hihat_open"), hit(10.5, "hihat_closed"), hit(10.5, "kick")]

    preview = groove.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert placed(preview.groove) == [("crash", 0), ("hihat_closed", 4), ("kick", 4), ("snare", 0)]
    # On a step the open hi-hat beside a closed one is listed first, then what the keep order cut (D25).
    assert [(d.piece, d.step) for d in preview.dropped] == [("hihat_open", 0), ("hihat_closed", 0), ("hihat_open", 4)]


def test_eight_sixteenth_hihats_alternate_hands_from_the_right():
    preview = groove.preview([hit(10.0 + n * 0.125, "hihat_closed") for n in range(8)], [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert [note.hand for note in preview.groove.notes] == ["R", "L", "R", "L", "R", "L", "R", "L"]


def test_a_rock_groove_keeps_the_hihat_in_the_right_hand_and_the_snare_in_the_left():
    hits = [hit(10.0 + n * 0.25, "hihat_closed") for n in range(8)] + [hit(10.5, "snare"), hit(11.5, "snare"), hit(10.0), hit(11.0)]

    preview = groove.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    hands = {(note.piece, note.step): note.hand for note in preview.groove.notes}
    assert all(hands[("hihat_closed", step)] == "R" for step in range(0, 16, 2))
    assert (hands[("snare", 4)], hands[("snare", 12)]) == ("L", "L")
    assert (hands[("kick", 0)], hands[("kick", 8)]) == (None, None)


def test_a_crash_after_a_rest_of_four_steps_is_right_and_a_snare_an_8th_after_a_right_cymbal_is_left():
    hits = [hit(10.0, "hihat_closed"), hit(10.25, "snare"), hit(10.75, "crash"), hit(11.5, "snare")]

    preview = groove.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert [(note.piece, note.step, note.hand) for note in preview.groove.notes] == [
        ("hihat_closed", 0, "R"),
        ("snare", 2, "L"),  # two steps after a right cymbal
        ("crash", 6, "R"),  # four steps after the last hand note: a cymbal, right
        ("snare", 12, "R"),  # six steps after: no cymbal within two
    ]


def test_a_lesson_s_timeline_quantized_back_gives_its_notes_exactly_even_shifted_20_ms_each_way():
    notes = [
        drum_note("kick", 0, None), drum_note("kick", 10, None), drum_note("kick", 16, None), drum_note("kick", 26, None),
        drum_note("snare", 4, "L"), drum_note("snare", 12, "L"), drum_note("snare", 20, "L"), drum_note("snare", 27, "L"),
        drum_note("tom_mid", 30, "R"), drum_note("tom_mid", 31, "L"),
        drum_note("crash", 16, "R"),
    ] + [drum_note("hihat_closed", step, "R") for step in range(0, 30, 2) if step != 16]  # fmt: skip
    lesson = drum_lesson(*notes, bpm=120, bars=2, chapters=[drum_chapter(repeats=1)])
    timing = timeline.build(lesson)
    # The count-in is a bar of four beats at 120: the Groove starts at 2.0 s and its bars are 2.0 s each.
    found = [bar(1, 2.0, 4.0), bar(2, 4.0, 6.0)]
    played = [h for h in timing.hits if h.note != "count"]

    exact = groove.preview([hit(h.at / timeline.RATE, h.piece) for h in played], found, bpm=None, mode="drums")
    shifted = groove.preview([hit(h.at / timeline.RATE + (0.02 if i % 2 else -0.02), h.piece) for i, h in enumerate(played)], found, bpm=None, mode="drums")

    expected = sorted((note.piece, note.step) for note in lesson.groove.notes)
    assert placed(exact.groove) == expected
    assert placed(shifted.groove) == expected
    assert (exact.bpm, exact.dropped) == (120, [])
    lessons.from_song("FILL", "", exact.bpm, exact.groove)  # the rules of `PUT` (video-gen D20) hold


def test_a_hundred_random_activations_give_grooves_that_pass_the_lesson_rules():
    rng = np.random.default_rng(2026)
    found = [bar(1, 0.0, 2.0), bar(2, 2.0, 4.0), bar(3, 4.0, 6.0), bar(4, 6.0, 8.0)]
    for _ in range(100):
        activations = (rng.random((800, 5)) < 0.08).astype(np.float32)  # 8 s at 100 frames/s, a hit on 8 % of frames
        hits = score.drum_hits(activations, start_s=0.0)
        preview = groove.preview(hits, found, bpm=None, mode="drums")

        lessons.from_song("FILL", "", preview.bpm, preview.groove)
        assert all(0 <= note.step < 64 for note in preview.groove.notes)




# --- melody mode (D14) ---


def test_a_melody_preview_puts_the_app_s_kick_on_1_and_3_and_a_closed_hihat_on_every_8th_under_the_snares_with_the_hihat_right_and_the_snare_left():
    found = [bar(1, 10.0, 12.0), bar(2, 12.0, 14.0)]
    preview = groove.preview([hit(10.5, "snare"), hit(11.0, "snare"), hit(12.0, "snare")], found, bpm=None, mode="melody")

    base = [("kick", s) for s in (0, 8, 16, 24)] + [("hihat_closed", s) for s in range(0, 32, 2)]
    assert placed(preview.groove) == sorted(base + [("snare", 4), ("snare", 8), ("snare", 16)])
    hands = {(n.piece, n.step): n.hand for n in preview.groove.notes}
    assert (hands[("hihat_closed", 4)], hands[("snare", 4)], hands[("kick", 0)]) == ("R", "L", None)
    assert (hands[("hihat_closed", 8)], hands[("snare", 8)]) == ("R", "L")
    assert all(n.hit == "normal" for n in preview.groove.notes)
    assert (preview.bpm, preview.dropped) == (120, [])
    lessons.from_song("MELODY", "", preview.bpm, preview.groove)  # the rules of `PUT` (video-gen D20) hold


def test_a_drums_preview_adds_nothing_and_a_melody_snare_on_an_odd_step_is_the_left_hand_s_after_the_hihat():
    found = [bar(1, 0.0, 2.0)]
    drums = groove.preview([hit(0.5, "snare")], found, bpm=None, mode="drums")
    melody = groove.preview([hit(0.5 + 0.125, "snare")], found, bpm=None, mode="melody")  # step 5, a 16th after the hi-hat on 4

    assert placed(drums.groove) == [("snare", 4)]
    assert {(n.piece, n.step): n.hand for n in melody.groove.notes}[("snare", 5)] == "L"  # alternates after the R hi-hat a step before
