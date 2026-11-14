"""A lesson's picture (video-gen seam 2 › `frames.frame_at`): the kit drawn by Pillow, the
rings on the beat, the focus and the hold in the tail. Its text is `test_video_gen_captions.py`."""

from PIL import Image

from backend.video_gen import frames, kit, timeline

from .fakes import drum_chapter as chapter
from .fakes import drum_lesson as lesson
from .fakes import drum_note as note

SNARE = kit.STRIKE["snare"].center
RATE = 44_100


def picture(scene: frames.Scene, t: float) -> Image.Image:
    return Image.frombytes("RGB", (frames.WIDTH, frames.HEIGHT), frames.frame_at(scene, t))


def scene_of(played_lesson) -> frames.Scene:
    return frames.Scene(played_lesson, timeline.build(played_lesson), None)


def is_red(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return r > 180 and g < 110 and b < 110


def test_the_snare_s_strike_point_is_red_on_its_note_and_not_a_frame_before():
    # BPM 120: the count-in is 2.0 s, and the snare on step 4 plays at 2.5 s.
    scene = scene_of(lesson(note("snare", 4, "L")))
    [snare] = [hit for hit in scene.timing.hits if hit.piece == "snare"]
    at = snare.at / RATE

    assert is_red(picture(scene, at).getpixel(SNARE))
    assert not is_red(picture(scene, at - 1 / frames.FPS).getpixel(SNARE))


def test_a_piece_outside_the_chapter_s_focus_is_darker():
    chapters = [chapter(focus=["kick"]), chapter()]
    scene = scene_of(lesson(chapters=chapters))  # no notes: nothing moves over the snare
    first, second = (span.start / RATE + 0.1 for span in scene.timing.chapters)

    focused_on_kick = sum(picture(scene, first).getpixel(SNARE))
    all_lit = sum(picture(scene, second).getpixel(SNARE))
    assert focused_on_kick < all_lit


def test_the_same_time_draws_the_same_bytes():
    scene = scene_of(lesson(note("snare", 4, "L"), note("hihat_closed", 0, "R", "accent"), note("tom_high", 8, "R", "flam")))

    assert frames.frame_at(scene, 2.51) == frames.frame_at(scene, 2.51)


def test_the_tail_holds_the_last_chapter_with_the_sticks_at_rest():
    scene = scene_of(lesson(note("snare", 15, "R")))
    end = scene.timing.chapters[-1].end / RATE
    tail = (end + 0.4, scene.timing.length_s - 0.01)

    first, last = (picture(scene, t) for t in tail)
    assert first.tobytes() == last.tobytes()
    rest, grip = kit.STICKS["R"]
    halfway = ((rest[0] + grip[0]) // 2, (rest[1] + grip[1]) // 2)
    assert first.getpixel(halfway) == (255, 255, 255)  # on the stick, lying at rest


def test_the_clip_has_ceil_length_times_30_frames():
    scene = scene_of(lesson(bpm=100))  # 2.4 + 2.4 + 1.5 = 6.3 s

    assert scene.frames() == 189
