"""A reel cover's timeline from a hand-made analysis (drum-cover seam 2; D3, D4, D5, D19,
D21; ADR 0051): hits at their real times, the hands from drum-notes' rules, the beats numbered, and
`timeline.assemble` giving a lesson the same timeline `build` always gave it."""

import pytest

from backend.drum_cover import timeline as reel
from backend.drum_cover.cover import Backing, CoverFields
from backend.drum_notes.songs import Analysis, Hit
from backend.video_gen import timeline
from backend.video_gen.timeline import Span

from .fakes import drum_chapter, drum_lesson, drum_note


def analysis(hits: list[tuple[float, str, str]] = (), downbeats=(10.0, 12.0, 14.0), beats=None, mode: str = "drums") -> Analysis:
    """Bars 2.0 s long from 8.0 (a downbeat at 8.0 when the default isn't given), beats every 0.5 s."""
    beats = beats if beats is not None else [8.0 + n / 2 for n in range(17)]
    return Analysis(
        mode=mode, start_s=8.0, end_s=16.0, beats=beats, downbeats=list(downbeats),
        hits=[Hit(t=t, piece=piece, level=level) for t, piece, level in hits], picked_at="2026-11-15T00:00:00Z",
    )  # fmt: skip


def cover(start_s: float = 10.0, end_s: float = 14.0) -> CoverFields:
    return CoverFields(
        start_s=start_s, end_s=end_s, title="Yellow", subtitle="DRUMMATE", caption="",
        background="color", backing=Backing(on=False, volume=35),
    )  # fmt: skip


def hands(timing) -> list[tuple[str, str | None]]:
    return [(hit.piece, hit.hand) for hit in timing.hits]


# --- times ---


def test_hits_play_at_their_real_times_from_the_stretch_s_start_and_the_clip_ends_after_the_tail():
    timing = reel.build(analysis([(11.0, "snare", "normal"), (11.013, "kick", "normal"), (9.9, "snare", "normal"), (14.0, "crash", "normal")]), cover())

    assert timing.length_s == 5.5
    assert [(hit.at, hit.piece) for hit in timing.hits] == [(44_100, "snare"), (44_673, "kick")]  # 1.013 s: not on a step
    assert timing.chapters == (Span(0, timeline.to_sample(4.0)),)


def test_beats_count_from_the_downbeat_before_them_and_one_before_every_downbeat_counts_back():
    timing = reel.build(analysis(), cover())
    assert [(beat.at, beat.number) for beat in timing.beats[:5]] == [(0, 1), (22_050, 2), (44_100, 3), (66_150, 4), (88_200, 1)]

    early = reel.build(analysis(), cover(start_s=9.0))  # beat 9.5 comes before the first downbeat (10.0)
    assert [(beat.at, beat.number) for beat in early.beats[:3]] == [(0, 3), (22_050, 4), (44_100, 1)]


def test_a_stretch_with_no_hit_is_silent_but_as_long_as_the_stretch_and_the_tail():
    timing = reel.build(analysis(), cover(10.0, 12.5))
    assert timing.hits == () and timing.length_s == 4.0


# --- hands (D5) ---


def test_sixteenth_hi_hats_alternate_hands():
    hits = [(10.0 + n * 0.125, "hihat_closed", "normal") for n in range(8)]
    assert [hand for _, hand in hands(reel.build(analysis(hits), cover()))] == ["R", "L"] * 4


def test_a_third_hand_note_on_one_step_still_sounds_but_has_no_stick():
    timing = reel.build(analysis([(12.0, "snare", "normal"), (12.0, "crash", "normal"), (12.01, "hihat_closed", "normal")]), cover())
    assert sorted(hands(timing)) == [("crash", "R"), ("hihat_closed", None), ("snare", "L")]


def test_a_piece_hit_twice_on_one_step_has_a_stick_only_the_first_time():
    timing = reel.build(analysis([(11.0, "snare", "normal"), (11.02, "snare", "normal")]), cover())
    assert hands(timing) == [("snare", "R"), ("snare", None)]


def test_feet_have_no_hand():
    timing = reel.build(analysis([(10.0, "kick", "normal"), (10.5, "hihat_pedal", "normal")]), cover())
    assert hands(timing) == [("kick", None), ("hihat_pedal", None)]


def test_bars_for_the_hands_come_from_the_whole_analysis_not_only_the_stretch():
    # A 3 s stretch inside one bar: the bar is still 2.0 s from 12.0, so 12.125 is the next 16th (L after R).
    timing = reel.build(analysis([(12.0, "hihat_closed", "normal"), (12.125, "hihat_closed", "normal")]), cover(11.5, 13.9))
    assert hands(timing) == [("hihat_closed", "R"), ("hihat_closed", "L")]


# --- levels and modes ---


@pytest.mark.parametrize(("level", "layer"), [("accent", "hard"), ("normal", "mid"), ("ghost", "soft")])
def test_a_hit_s_level_gives_its_layer_and_note_head(level, layer):
    [hit] = reel.build(analysis([(11.0, "snare", level)]), cover()).hits
    assert (hit.layer, hit.note) == (layer, level)


def test_a_melody_mode_song_plays_its_snares_as_found_with_nothing_added():
    timing = reel.build(analysis([(10.5, "snare", "normal"), (11.0, "snare", "normal")], mode="melody"), cover())
    assert [hit.piece for hit in timing.hits] == ["snare", "snare"]


# --- the lesson the picture reads ---


def test_the_picture_s_lesson_has_the_cover_s_texts_one_bare_chapter_and_the_beats_bpm():
    drawn = reel.lesson(analysis(), cover())
    assert (drawn.title, drawn.subtitle, drawn.background, drawn.bpm) == ("Yellow", "DRUMMATE", "color", 120)
    assert [(c.label, c.focus, c.repeats, c.speed) for c in drawn.chapters] == [("", [], 1, 100)]
    assert reel.scroll_bpm(analysis(beats=[10.0, 10.4, 10.8, 11.2]), cover()) == 150
    assert reel.scroll_bpm(analysis(beats=[10.0, 20.0]), cover()) == 120  # one beat in the stretch


# --- assemble (the prefactor) ---


def test_assemble_gives_a_lesson_the_timeline_build_always_gave_it():
    lesson = drum_lesson(drum_note("snare", 0), drum_note("kick", 4, None), drum_note("hihat_closed", 2, hit="flam"), chapters=[drum_chapter(repeats=2, speed=75)])
    built = timeline.build(lesson)
    assert built.hits[0] == timeline.Hit(0, "snare", "R", "mid", 1, "normal")  # no count-in (reels-only D15)
    assert len(built.hits) == 2 * 4 and built.length_s == timeline.length_s(lesson.bpm, 1, lesson.chapters)


def test_a_beat_before_a_three_beat_first_bar_counts_back_from_three():
    # Downbeats 10.0 and 11.5: the first bar holds three beats, so 9.5 is its 3.
    timing = reel.build(analysis(downbeats=(10.0, 11.5, 13.5)), cover(start_s=9.5))
    assert [beat.number for beat in timing.beats[:4]] == [3, 1, 2, 3]
