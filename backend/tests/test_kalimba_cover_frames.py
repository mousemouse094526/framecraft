"""A kalimba reel's own picture (kalimba-cover seam 2 › `kalimba_cover.frames.frame_at`; D7, D14,
kalimba-picture-sketch.md; ADR 0054): notes falling down each tine's column onto the line, the tine
played lit in its number's colour, and the drums' bar dots. Its text is `test_kalimba_cover_captions.py`."""

import itertools

from PIL import Image

from backend.drum_cover import frames as reel_frames
from backend.kalimba_cover import frames
from backend.kalimba_cover.timeline import KalimbaTimeline
from backend.video_gen import timeline

from .fakes import drum_lesson, kalimba_timing_of as timing_of

C4 = 8  # the middle tine (spec › การจัดโน้ตลงคาลิมบา)
RED = (0xF8, 0x71, 0x71)  # the sketch's colour of a 1 (C), written out so a changed table shows here
STEEL = (0xCB, 0xD5, 0xE1)
LENGTH_S = 4.0 + timeline.TAIL_S  # `kalimba_timing_of`'s


def scene_of(timing: KalimbaTimeline, bpm: int = 120) -> frames.Scene:
    return frames.Scene(drum_lesson(bpm=bpm), timing, None)


def picture(scene: frames.Scene, t: float) -> Image.Image:
    return Image.frombytes("RGB", (frames.WIDTH, frames.HEIGHT), frames.frame_at(scene, t))


def near(a: tuple[int, ...], b: tuple[int, ...], by: int = 12) -> bool:
    return all(abs(x - y) <= by for x, y in zip(a, b, strict=True))


def test_a_played_tine_is_filled_with_its_number_s_colour_at_its_probe_and_rests_as_steel_after():
    scene = scene_of(timing_of((1.0, C4, "normal")))
    probe = frames.TINES[C4].probe

    assert near(picture(scene, 1.0).getpixel(probe), RED)
    assert not near(picture(scene, 1.1).getpixel(probe), RED)  # fading back to steel
    assert near(picture(scene, 1.2).getpixel(probe), STEEL)
    assert near(picture(scene, 0.5).getpixel(probe), STEEL)
    assert frames.frame_at(scene, 1.0) == frames.frame_at(scene, 1.0)


def test_the_sketch_s_tines_stay_apart_at_an_accent_s_size_inside_the_body_and_label_under_their_probe():
    for a, b in itertools.pairwise(frames.TINES):
        assert frames.tine_box(a, frames.ACCENT_GROW)[2] < frames.tine_box(b, frames.ACCENT_GROW)[0], (a.letter, b.letter)
    left, top, right, bottom = frames.BODY
    for tine in frames.TINES:
        x0, y0, x1, y1 = frames.tine_box(tine, frames.ACCENT_GROW)
        assert left < x0 and x1 < right and top < y0 and y1 < bottom, tine
        highest_dot = tine.tip - frames.DOT_ABOVE[-1] - frames.OCTAVE_DOT_R
        number_top = tine.number_at[1] - frames.NUMBER_SIZE / 2
        assert tine.probe[1] < highest_dot and tine.probe[1] < number_top, tine
        assert tine.letter_at[1] + frames.LETTER_SIZE / 2 < bottom, tine
    assert len(set(frames.NUMBER_COLORS.values())) == 7
    assert [tine.number for tine in frames.TINES] == [2, 7, 5, 3, 1, 6, 4, 2, 1, 3, 5, 7, 2, 4, 6, 1, 3]
    assert [tine.dots for tine in frames.TINES] == [2, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2]


def test_at_60_bpm_two_c4s_0_08_s_apart_fall_one_above_the_other_without_overlapping():
    shown = picture(scene_of(timing_of((2.0, C4, "normal"), (2.08, C4, "normal")), bpm=60), 1.0)
    # At the slowest 350 px/s, 1.0 s ahead: the first note's bottom at 1330 − 350 = 980, the second's 28 px higher at 952.
    column = frames.TINES[C4].cx

    assert near(shown.getpixel((column, 980 - 14)), RED) and near(shown.getpixel((column, 952 - 14)), RED)
    assert not near(shown.getpixel((column - 20, 952)), RED, 40)  # their round corners part where they meet


def test_a_note_lands_on_the_play_line_as_it_plays_and_the_notes_hold_still_in_the_tail():
    scene = scene_of(timing_of((1.0, C4, "normal"), (3.9, 16, "normal")))

    # 120 BPM: 810 px for 1.5 bars of 4 (3 s) is 270 px/s, under the slowest, so 350 px/s.
    assert near(picture(scene, 1.0).getpixel((frames.TINES[C4].cx, 1330 - 14)), RED)
    assert near(picture(scene, 0.9).getpixel((frames.TINES[C4].cx, 1330 - 35 - 14)), RED)
    assert picture(scene, 4.3).tobytes() == picture(scene, LENGTH_S - 0.01).tobytes()


def test_the_bar_s_dots_are_the_drum_reel_s():
    scene = scene_of(timing_of())

    assert picture(scene, 1.6).getpixel(reel_frames.dot_center(3, 4)) == (255, 255, 255)
    assert picture(scene, 1.6).getpixel(reel_frames.dot_center(0, 4)) != (255, 255, 255)
