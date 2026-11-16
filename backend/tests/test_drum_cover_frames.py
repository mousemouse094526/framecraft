"""A reel cover's own picture (drum-cover seam 2 › `drum_cover.frames.frame_at`; D25, D26, D29,
reel-picture-sketch.md; ADR 0054): the kit from above with no piece on another, a stick in each
hand's colour, a lane for each piece played, and the bar's dots. Its text is `test_drum_cover_captions.py`."""

import itertools
import math

from PIL import Image

from backend.drum_cover import frames
from backend.video_gen import frames as lesson_frames
from .fakes import END_S, drum_lesson, timing_of

SNARE = frames.KIT["snare"]
SNARE_FILL = (0x60, 0xA5, 0xFA)  # the sketch's snare colour, written out so a changed table shows here
PINK = (0xFF, 0x4F, 0xD8)  # the sketch's right stick


def scene_of(timing) -> frames.Scene:
    return frames.Scene(drum_lesson(bpm=120), timing, None)


def picture(scene: frames.Scene, t: float) -> Image.Image:
    return Image.frombytes("RGB", (frames.WIDTH, frames.HEIGHT), frames.frame_at(scene, t))


def near(a: tuple[int, ...], b: tuple[int, ...], by: int) -> bool:
    return all(abs(x - y) <= by for x, y in zip(a, b, strict=True))


def blacked_out(image: Image.Image, *boxes: tuple[int, int, int, int]) -> bytes:
    """The frame with `boxes` painted black: what's left must not move."""
    image = image.copy()
    for box in boxes:
        image.paste((0, 0, 0), box)
    return image.tobytes()


def around(center: tuple[float, float], r: float) -> tuple[int, int, int, int]:
    return round(center[0] - r), round(center[1] - r), round(center[0] + r), round(center[1] + r)


# --- the kit ---


def test_no_two_pieces_touch_at_an_accent_s_size_and_every_one_and_the_resting_sticks_stay_clear():
    grown = frames.ACCENT_GROW
    for a, b in itertools.combinations(frames.KIT.values(), 2):
        assert math.dist(a.center, b.center) > (a.r + b.r) * grown, (a.label, b.label)
    for drawn in frames.KIT.values():
        (x, y), r = drawn.center, drawn.r * grown
        assert 54 <= x - r and x + r <= 1026 and 400 <= y - r and y + r <= 1090, drawn.label
        for stick in frames.STICKS.values():
            assert math.dist(stick.rest, drawn.center) > drawn.r * grown + frames.STICK_HEAD_R, drawn.label
    colors = {name: drawn.color for name, drawn in frames.KIT.items()}
    assert colors["hihat_pedal"] == colors["hihat"]  # the hi-hat's three hits share one colour
    assert len(set(colors.values())) == 8


def test_a_hit_piece_is_filled_in_full_at_its_probe_and_one_at_rest_at_thirty_percent():
    scene = scene_of(timing_of((1.0, "snare", "L", "normal")))

    assert picture(scene, 1.0).getpixel(SNARE.probe) == SNARE_FILL
    background = lesson_frames.background_image(None).getpixel(SNARE.probe)
    resting = tuple(round(c * 0.3 + g * 0.7) for c, g in zip(SNARE_FILL, background, strict=True))
    assert near(picture(scene, 0.5).getpixel(SNARE.probe), resting, 2)
    assert near(picture(scene, 1.0 + frames.HIT_S + 0.01).getpixel(SNARE.probe), resting, 2)
    assert frames.frame_at(scene, 1.0) == frames.frame_at(scene, 1.0)


def test_each_stick_is_its_hand_s_colour_on_its_way_to_the_piece_it_hits():
    scene = scene_of(timing_of((1.0, "hihat_closed", "R", "normal"), (1.5, "snare", "L", "normal")))

    for t, hand, piece, color in ((1.0, "R", "hihat", PINK), (1.5, "L", "snare", (255, 255, 255))):
        grip, strike = frames.STICKS[hand].grip, frames.KIT[piece].strike
        halfway = ((grip[0] + strike[0]) // 2, (grip[1] + strike[1]) // 2)
        assert picture(scene, t).getpixel(halfway) == color, hand


# --- the lanes ---


def test_a_lane_for_each_piece_played_in_kit_order_with_the_snare_s_head_on_the_playhead_as_it_plays():
    scene = scene_of(timing_of((0.5, "kick", None, "normal"), (1.0, "snare", "L", "normal"), (1.0, "hihat_closed", "R", "normal")))
    # Three rows of 84 px, centred in y 1180–1600: HI-HAT at 1306, SNARE at 1390, KICK at 1474.
    playing = picture(scene, 1.0)

    beside_playhead = 330 + 12  # off the white playhead itself
    assert near(playing.getpixel((beside_playhead, 1306 + 12)), (0xFA, 0xCC, 0x15), 40)  # on the hi-hat X's diagonal
    assert playing.getpixel((beside_playhead, 1390)) == SNARE_FILL
    assert picture(scene, 0.5).getpixel((beside_playhead, 1474)) == (0xF8, 0x71, 0x71)
    assert picture(scene, 0.5).getpixel((beside_playhead, 1390)) != SNARE_FILL


def test_the_lanes_hold_still_in_the_tail_so_only_a_piece_still_lit_changes():
    scene = scene_of(timing_of((1.0, "snare", "L", "normal"), (END_S - 0.05, "kick", None, "normal")))
    lit, later, last = (picture(scene, t) for t in (END_S + 0.05, END_S + 0.6, scene.timing.length_s - 0.01))

    assert later.tobytes() == last.tobytes()
    # 0.1 s after the kick only the kick's piece and its glowing note head may differ from later on.
    kick = frames.KIT["kick"]
    kick_box = around(kick.center, kick.r * frames.ACCENT_GROW + frames.HIT_OUTLINE)
    # Two rows of 84 px centred in y 1180–1600: SNARE y 1306–1390, KICK y 1390–1474; the box
    # around their boundary holds the kick's whole note head, glow and all.
    head_box = around((330 - 0.05 * scene.px_per_s, 1390), 84)
    assert blacked_out(lit, kick_box, head_box) == blacked_out(later, kick_box, head_box)


# --- the bar counter ---


def test_a_bar_shows_a_dot_a_beat_and_a_fifth_beat_lights_the_fourth():
    beats = [(0.0, 1), (0.5, 2), (1.0, 3), (1.5, 4), (2.0, 5), (2.5, 1), (3.0, 2), (3.5, 3), (3.75, 1)]
    scene = scene_of(timing_of(beats=beats))
    white = (255, 255, 255)

    fifth = picture(scene, 2.1)
    assert fifth.getpixel(frames.dot_center(3, 4)) == white
    assert fifth.getpixel(frames.dot_center(0, 4)) != white
    three = picture(scene, 2.6)  # a three-beat bar: three dots, the first lit, nothing where a fourth would be
    assert three.getpixel(frames.dot_center(0, 3)) == white
    assert three.getpixel(frames.dot_center(0, 4)) == picture(scene_of(timing_of(beats=[])), 2.6).getpixel(frames.dot_center(0, 4))
    assert [bar.dots for bar in scene.bars][-1] == 3  # the last bar, cut by the clip, takes the bar before's


def test_beats_before_the_clip_s_first_downbeat_count_no_bar_and_show_the_bar_ahead_s_dots():
    scene = scene_of(timing_of(beats=[(0.0, 3), (0.5, 4), (1.0, 1), (1.5, 2), (2.0, 3), (2.5, 4)]))

    assert picture(scene, 0.6).getpixel(frames.dot_center(3, 4)) == (255, 255, 255)
    assert [bar.number for bar in scene.bars] == [0, 1]
