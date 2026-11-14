"""The numbers behind the models (drum-notes seam 2, D6, D9, D20): Beat This! chunks stitched,
ADTOF peak picking, beats and downbeats from logits, and the bars found (`songs.bars_of`) — all on synthetic arrays."""

import numpy as np
import pytest

from backend.drum_notes import score, songs
from backend.drum_notes.songs import Analysis
from backend.video_gen import lessons, timeline

from .fakes import drum_chapter, drum_lesson, drum_note

# --- stitch ---


def test_a_short_range_is_one_chunk_padded_six_frames_at_both_ends():
    [chunk] = score.beat_this_chunks(200)

    assert (chunk.first_frame, chunk.frames, chunk.pad_before, chunk.pad_after) == (0, 200, 6, 6)


def test_a_long_range_is_chunks_of_1500_frames_overlapping_six_the_last_shifted_to_end_at_the_end():
    chunks = score.beat_this_chunks(4000)

    assert [(c.first_frame, c.frames, c.pad_before, c.pad_after) for c in chunks] == [
        (0, 1494, 6, 0),
        (1482, 1500, 0, 0),
        (2506, 1494, 0, 6),  # shifted back so its kept frames end at 4000; the first of them repeat the chunk before
    ]
    assert all(c.pad_before + c.frames + c.pad_after <= 1500 for c in chunks)


def test_a_range_six_frames_longer_than_two_chunks_keep_gets_a_third_chunk_moved_back_to_end_with_the_range():
    chunks = score.beat_this_chunks(2982)

    assert [(c.first_frame, c.frames, c.pad_before, c.pad_after) for c in chunks] == [(0, 1494, 6, 0), (1482, 1500, 0, 0), (1488, 1494, 0, 6)]


def test_stitched_logits_equal_the_original_at_every_frame():
    frames = 4000
    original = np.arange(frames, dtype=np.float32)
    outputs = []
    for chunk in score.beat_this_chunks(frames):
        # What the model would give: `pad_before` made-up frames, the chunk's frames, `pad_after` made-up frames.
        body = original[chunk.first_frame : chunk.first_frame + chunk.frames]
        logits = np.concatenate([np.full(chunk.pad_before, -9.0, np.float32), body, np.full(chunk.pad_after, -9.0, np.float32)])
        outputs.append((chunk, logits[None, :]))

    stitched = score.stitch(frames, outputs)

    assert stitched.shape == (frames,)
    assert np.array_equal(stitched, original)


def test_the_samples_a_chunk_needs_are_its_frames_times_441_plus_the_window():
    chunk = score.beat_this_chunks(2982)[2]
    pcm = np.zeros(score.beat_this_frames_to_samples(2982), np.float32)

    assert score.chunk_samples(pcm, chunk).shape == ((1494 - 1) * 441 + 1024,)
    assert score.beat_this_frames(len(pcm)) == 2982


# --- peak picking (ADTOF) ---


def activations(frames: int, hits: dict[int, list[int]]) -> np.ndarray:
    """`[frames, 5]`: 1.0 at each hit frame of each class, 0 elsewhere."""
    act = np.zeros((frames, 5), np.float32)
    for class_index, at in hits.items():
        act[at, class_index] = 1.0
    return act


def test_a_synthetic_activation_gives_hits_at_the_frames_placed_within_10_ms():
    act = activations(300, {0: [50, 150], 1: [100], 2: [200], 3: [50, 100, 150, 200], 4: [250]})

    hits = score.drum_hits(act, start_s=10.0)

    assert [(hit.piece, hit.t, hit.level) for hit in hits] == [
        ("kick", 10.5, "normal"),
        ("hihat_closed", 10.5, "normal"),
        ("snare", 11.0, "normal"),
        ("hihat_closed", 11.0, "normal"),
        ("kick", 11.5, "normal"),
        ("hihat_closed", 11.5, "normal"),
        ("tom_mid", 12.0, "normal"),
        ("hihat_closed", 12.0, "normal"),
        ("crash", 12.5, "normal"),
    ]


def test_two_peaks_10_ms_apart_are_one_hit_and_a_value_under_the_threshold_is_none():
    act = activations(100, {1: [40, 41]})
    act[80, 1] = 0.2  # under snare's 0.24

    hits = score.drum_hits(act, start_s=0.0)

    assert [(hit.piece, hit.t) for hit in hits] == [("snare", 0.4)]


def test_a_steady_activation_that_rises_a_little_is_not_a_hit():
    act = np.full((100, 5), 0.5, np.float32)
    act[50, 0] = 0.6  # 0.1 over the average, under kick's 0.22

    assert score.drum_hits(act, start_s=0.0) == []


# --- beats and downbeats (Beat This!) ---


def logits(frames: int, every: int, offset: int = 0) -> np.ndarray:
    out = np.full(frames, -5.0, np.float32)
    out[offset::every] = 3.0
    return out


def test_synthetic_beat_and_downbeat_logits_give_beats_every_half_second_and_downbeats_every_two():
    frames = 500  # 10 s at 50 frames/s
    beat = logits(frames, 25)  # every 0.5 s
    downbeat = logits(frames, 100)  # every 2.0 s

    beats, downbeats = score.beats_and_downbeats(beat, downbeat, start_s=5.0)

    assert beats == pytest.approx([5.0 + 0.5 * n for n in range(20)], abs=0.01)
    assert downbeats == pytest.approx([5.0, 7.0, 9.0, 11.0, 13.0], abs=0.01)


def test_adjacent_peak_frames_are_one_beat_and_a_downbeat_moves_to_the_nearest_beat():
    beat = np.full(200, -5.0, np.float32)
    beat[[50, 51, 52, 100, 150]] = 2.0  # frames 50 to 52 all as high: one beat, at the first
    downbeat = np.full(200, -5.0, np.float32)
    downbeat[[53, 148]] = 2.0  # off the beats by 2–3 frames

    beats, downbeats = score.beats_and_downbeats(beat, downbeat, start_s=0.0)

    assert beats == [1.0, 2.0, 3.0]
    assert downbeats == [1.0, 3.0]


def test_a_logit_that_never_rises_over_zero_gives_no_beats():
    beats, downbeats = score.beats_and_downbeats(np.full(100, -1.0, np.float32), np.full(100, -1.0, np.float32), start_s=0.0)

    assert (beats, downbeats) == ([], [])


# --- the bars found ---


def analysis_of(beats: list[float], downbeats: list[float], hits: list[float] = ()) -> Analysis:
    return Analysis(
        mode="drums",
        start_s=0.0,
        end_s=10.0,
        beats=beats,
        downbeats=downbeats,
        hits=[{"t": t, "piece": "kick", "level": "normal"} for t in hits],
        picked_at="2026-11-14T10:30:00+07:00",
    )


def test_bars_lie_between_consecutive_downbeats_and_one_without_four_beats_is_not_4_4():
    beats = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 14.0, 14.5, 15.0, 15.5, 16.0]
    found = analysis_of(beats, [10.0, 12.0, 14.0, 16.0], hits=[10.0, 10.49, 11.94, 12.1, 15.9])

    bars = songs.bars_of(found)

    assert [(bar.n, bar.start_s, bar.end_s, bar.beats, bar.hits, bar.four_four) for bar in bars] == [
        (1, 10.0, 12.0, 4, 3, True),
        (2, 12.0, 14.0, 3, 1, False),
        (3, 14.0, 16.0, 4, 1, True),
    ]


# --- a lesson's Groove from the bars picked (Score steps 3–8; D11, D13, D20) ---


def bar(n: int, start_s: float, end_s: float, four_four: bool = True) -> songs.FoundBar:
    return songs.FoundBar(n=n, start_s=start_s, end_s=end_s, beats=4 if four_four else 3, hits=0, four_four=four_four)


def hit(t: float, piece: str = "kick", level: str = "normal") -> songs.Hit:
    return songs.Hit(t=t, piece=piece, level=level)


def placed(groove) -> list[tuple[str, int]]:
    return sorted((note.piece, note.step) for note in groove.notes)


def test_a_hit_rounds_to_its_nearest_step_one_just_before_the_bar_lands_on_step_0_and_one_at_the_next_bar_is_dropped_silently():
    # A 2.0 s bar from 10.0: a step is 0.125 s. 10.49 → 3.92 → step 4; 9.95 is 50 ms early, under half a step; 11.94 → 15.5 → 16, past the bar.
    preview = score.preview([hit(9.95), hit(10.49, "snare"), hit(11.94, "crash")], [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert placed(preview.groove) == [("kick", 0), ("snare", 4)]
    assert preview.dropped == []
    assert preview.groove.bars == 1


def test_the_same_piece_twice_in_a_step_keeps_the_loudest_and_a_second_bar_s_steps_start_at_16():
    preview = score.preview([hit(10.0, "snare", "ghost"), hit(10.02, "snare", "accent"), hit(12.25)], [bar(1, 10.0, 12.0), bar(2, 12.0, 14.0)], bpm=None, mode="drums")

    assert [(note.piece, note.step, note.hit) for note in preview.groove.notes] == [("snare", 0, "accent"), ("kick", 18, "normal")]
    assert preview.groove.bars == 2


def test_the_default_bpm_is_240_over_the_median_bar_length_within_40_to_240():
    assert score.preview([], [bar(1, 10.0, 12.0)], bpm=None, mode="drums").bpm == 120
    assert score.preview([], [bar(1, 0.0, 2.0), bar(2, 2.0, 4.0), bar(3, 4.0, 7.0)], bpm=None, mode="drums").bpm == 120
    assert score.preview([], [bar(1, 0.0, 0.5)], bpm=None, mode="drums").bpm == 240
    assert score.preview([], [bar(1, 0.0, 10.0)], bpm=None, mode="drums").bpm == 40
    assert score.preview([], [bar(1, 0.0, 2.0)], bpm=95, mode="drums").bpm == 95


def test_a_third_hand_note_in_a_step_is_dropped_by_the_keep_order_and_an_open_hihat_beside_a_closed_one_goes():
    hits = [hit(10.0, "hihat_closed"), hit(10.0, "snare"), hit(10.0, "crash"), hit(10.0, "hihat_open"), hit(10.5, "hihat_open"), hit(10.5, "hihat_closed"), hit(10.5, "kick")]

    preview = score.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert placed(preview.groove) == [("crash", 0), ("hihat_closed", 4), ("kick", 4), ("snare", 0)]
    # On a step the open hi-hat beside a closed one is listed first, then what the keep order cut (D25).
    assert [(d.piece, d.step) for d in preview.dropped] == [("hihat_open", 0), ("hihat_closed", 0), ("hihat_open", 4)]


def test_eight_sixteenth_hihats_alternate_hands_from_the_right():
    preview = score.preview([hit(10.0 + n * 0.125, "hihat_closed") for n in range(8)], [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    assert [note.hand for note in preview.groove.notes] == ["R", "L", "R", "L", "R", "L", "R", "L"]


def test_a_rock_groove_keeps_the_hihat_in_the_right_hand_and_the_snare_in_the_left():
    hits = [hit(10.0 + n * 0.25, "hihat_closed") for n in range(8)] + [hit(10.5, "snare"), hit(11.5, "snare"), hit(10.0), hit(11.0)]

    preview = score.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

    hands = {(note.piece, note.step): note.hand for note in preview.groove.notes}
    assert all(hands[("hihat_closed", step)] == "R" for step in range(0, 16, 2))
    assert (hands[("snare", 4)], hands[("snare", 12)]) == ("L", "L")
    assert (hands[("kick", 0)], hands[("kick", 8)]) == (None, None)


def test_a_crash_after_a_rest_of_four_steps_is_right_and_a_snare_an_8th_after_a_right_cymbal_is_left():
    hits = [hit(10.0, "hihat_closed"), hit(10.25, "snare"), hit(10.75, "crash"), hit(11.5, "snare")]

    preview = score.preview(hits, [bar(1, 10.0, 12.0)], bpm=None, mode="drums")

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

    exact = score.preview([hit(h.at / timeline.RATE, h.piece) for h in played], found, bpm=None, mode="drums")
    shifted = score.preview([hit(h.at / timeline.RATE + (0.02 if i % 2 else -0.02), h.piece) for i, h in enumerate(played)], found, bpm=None, mode="drums")

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
        preview = score.preview(hits, found, bpm=None, mode="drums")

        lessons.from_song("FILL", "", preview.bpm, preview.groove)
        assert all(0 <= note.step < 64 for note in preview.groove.notes)


# --- Basic Pitch windows and melody hits (D14) ---

HOP, PAD, WINDOW = score.BASIC_PITCH_HOP, score.BASIC_PITCH_PAD, score.BASIC_PITCH_WINDOW


def onsets(frames: list[int], note: int = 60) -> np.ndarray:
    """One window's onset output: 1.0 at `frames` on `note`, 0.0 elsewhere."""
    onset = np.zeros((score.BASIC_PITCH_FRAMES, score.BASIC_PITCH_NOTES), np.float32)
    onset[frames, note] = 1.0
    return onset


def test_a_range_is_cut_into_windows_of_43844_samples_every_36164_the_first_starting_3840_before_it():
    one = score.basic_pitch_windows(HOP - PAD)  # the padded range fits one window's hop
    three = score.basic_pitch_windows(2 * HOP - PAD + 1)  # one sample over two hops

    assert [w.first_sample for w in one] == [-PAD]
    assert [w.first_sample for w in three] == [-PAD, HOP - PAD, 2 * HOP - PAD]


def test_a_window_s_samples_are_zero_padded_before_the_range_and_past_its_end():
    pcm = np.arange(1, HOP + 1, dtype=np.float32)
    first, second = score.basic_pitch_windows(HOP)

    before = score.window_samples(pcm, first)
    after = score.window_samples(pcm, second)

    assert len(before) == len(after) == WINDOW
    assert (before[:PAD] == 0).all() and before[PAD] == 1.0 and before[PAD + HOP - 1] == pcm[-1] and (before[PAD + HOP :] == 0).all()
    assert after[0] == pcm[HOP - PAD] and after[PAD - 1] == pcm[-1] and (after[PAD:] == 0).all()


def test_an_onset_frame_is_a_snare_at_the_frame_s_time_the_15_frames_cut_from_each_side_and_frames_past_the_range_dropped():
    windows = score.basic_pitch_windows(HOP + 10 * 256)  # two windows; the second's frames soon run past the range
    # Window 0: frame 14 is cut; frame 15 is the range's first sample; frame 100 is sample 85 × 256.
    # Window 1: frame 15 is sample HOP; frame 30 is sample HOP + 15 × 256, past the range's end at HOP + 10 × 256.
    outputs = [(windows[0], onsets([14, 15, 100])), (windows[1], onsets([15, 30, 157]))]

    hits = score.melody_hits(outputs, samples=HOP + 10 * 256, start_s=5.0)

    assert [(h.piece, h.level) for h in hits] == [("snare", "normal")] * 3
    assert [h.t for h in hits] == pytest.approx([5.0, 5.0 + 85 * 256 / 22_050, 5.0 + HOP / 22_050], abs=0.0005)


def test_onsets_on_adjacent_frames_are_one_hit_at_the_first_also_across_two_windows_and_two_frames_apart_are_two():
    windows = score.basic_pitch_windows(2 * HOP)
    # Window 0's frame 156 (its last kept) and window 1's frame 15 (its first kept) are 68 samples apart: the same instant.
    outputs = [(windows[0], onsets([20, 21, 22, 40, 42, 156])), (windows[1], onsets([15, 16])), (windows[2], onsets([]))]

    hits = score.melody_hits(outputs, samples=2 * HOP, start_s=0.0)

    assert [h.t for h in hits] == pytest.approx([5 * 256 / 22_050, 25 * 256 / 22_050, 27 * 256 / 22_050, 141 * 256 / 22_050], abs=0.0005)


def test_a_melody_preview_puts_the_app_s_kick_on_1_and_3_and_a_closed_hihat_on_every_8th_under_the_snares_with_the_hihat_right_and_the_snare_left():
    found = [bar(1, 10.0, 12.0), bar(2, 12.0, 14.0)]
    preview = score.preview([hit(10.5, "snare"), hit(11.0, "snare"), hit(12.0, "snare")], found, bpm=None, mode="melody")

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
    drums = score.preview([hit(0.5, "snare")], found, bpm=None, mode="drums")
    melody = score.preview([hit(0.5 + 0.125, "snare")], found, bpm=None, mode="melody")  # step 5, a 16th after the hi-hat on 4

    assert placed(drums.groove) == [("snare", 4)]
    assert {(n.piece, n.step): n.hand for n in melody.groove.notes}[("snare", 5)] == "L"  # alternates after the R hi-hat a step before
