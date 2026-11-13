"""A lesson's picture and text (video-gen seam 2 › `frames.frame_at`, and `captions`): the
kit drawn by Pillow, the rings on the beat, the focus, the hold in the tail, and the ASS file."""

import re

import pytest
from PIL import Image, ImageFont

from backend.paths import ProjectPaths
from backend.video_gen import captions, frames, kit, timeline

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
    [snare] = [hit for hit in scene.played.hits if hit.piece == "snare"]
    at = snare.at / RATE

    assert is_red(picture(scene, at).getpixel(SNARE))
    assert not is_red(picture(scene, at - 1 / frames.FPS).getpixel(SNARE))


def test_a_piece_outside_the_chapter_s_focus_is_darker():
    chapters = [chapter(focus=["kick"]), chapter()]
    scene = scene_of(lesson(chapters=chapters))  # no notes: nothing moves over the snare
    first, second = (span.start / RATE + 0.1 for span in scene.played.chapters)

    focused_on_kick = sum(picture(scene, first).getpixel(SNARE))
    all_lit = sum(picture(scene, second).getpixel(SNARE))
    assert focused_on_kick < all_lit


def test_the_same_time_draws_the_same_bytes():
    scene = scene_of(lesson(note("snare", 4, "L"), note("hihat_closed", 0, "R", "accent"), note("tom_high", 8, "R", "flam")))

    assert frames.frame_at(scene, 2.51) == frames.frame_at(scene, 2.51)


def test_the_tail_holds_the_last_chapter_with_the_sticks_at_rest():
    scene = scene_of(lesson(note("snare", 15, "R")))
    end = scene.played.chapters[-1].end / RATE
    tail = (end + 0.4, scene.played.length_s - 0.01)

    first, last = (picture(scene, t) for t in tail)
    assert first.tobytes() == last.tobytes()
    rest, grip = kit.STICKS["R"]
    halfway = ((rest[0] + grip[0]) // 2, (rest[1] + grip[1]) // 2)
    assert first.getpixel(halfway) == (255, 255, 255)  # on the stick, lying at rest


def test_the_clip_has_ceil_length_times_30_frames():
    scene = scene_of(lesson(bpm=100))  # 2.4 + 2.4 + 1.5 = 6.3 s

    assert scene.frames() == 189


# --- captions ---


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


@pytest.fixture
def title_font():
    """Pillow's own font stands in for Kanit, which the fake root only names."""
    return lambda _project: ImageFont.load_default(captions.TITLE_SIZE)


def events(ass: str, style: str) -> list[tuple[str, str, str]]:
    """Each Dialogue of `style`: its start, end and text."""
    found = re.findall(rf"^Dialogue: 0,([^,]+),([^,]+),{style},,0,0,0,,(.*)$", ass, re.MULTILINE)
    return [(start, end, text) for start, end, text in found]


def test_the_count_in_shows_the_title_and_subtitle_and_a_labelled_chapter_its_label_and_text(project, title_font):
    chapters = [chapter(), chapter(label="KICK", text="On 1e and 2a", focus=["kick"])]
    played_lesson = lesson(note("kick", 0, None), chapters=chapters, title="SMELLS", subtitle="Nirvana")
    ass = captions.ass_file(project, played_lesson, timeline.build(played_lesson), title_font)

    headings = [text.rsplit("}", 1)[1] for _, _, text in events(ass, "Heading")]
    assert headings == ["SMELLS", "SMELLS", "KICK"]  # the first chapter's label is empty: the title
    kick_box = captions.ass_color(kit.BY_ID["kick"].color)
    assert f"\\3c{kick_box}" in events(ass, "Heading")[2][2]
    lines = [text.rsplit("}", 1)[1] for _, _, text in events(ass, "Line")]
    assert lines == ["Nirvana", "Nirvana", "On 1e and 2a"]
    assert [text[-1] for _, _, text in events(ass, "Counter")] == list("1234" * 3)
    assert [text.rsplit("}", 1)[1] for _, _, text in events(ass, "Letter")] == ["L", "R"]
    assert [text.rsplit("}", 1)[1] for _, _, text in events(ass, "Foot")] == ["RF", "LF"]
    beats = {text.rsplit("}", 1)[1] for _, _, text in events(ass, "Beat")}
    assert beats == {"BAR", "2", "3", "4"}


def test_a_heading_wider_than_860_px_is_squeezed_onto_one_line(project, title_font):
    wide = lesson(title="W" * 40)
    narrow = lesson(title="FILL")

    [*_, (_, _, squeezed)] = events(captions.ass_file(project, wide, timeline.build(wide), title_font), "Heading")
    [*_, (_, _, plain)] = events(captions.ass_file(project, narrow, timeline.build(narrow), title_font), "Heading")
    assert re.search(r"\\fscx\d+", squeezed) and "\\N" not in squeezed
    assert "\\fscx" not in plain


def test_a_long_thai_subtitle_and_caption_are_cut_into_two_lines_at_most(project, title_font):
    long_line = "ตีกลองสแนร์สองครั้งแล้วตามด้วยกระเดื่องหนึ่งครั้งในจังหวะที่สองและสี่ของทุกห้อง"[:60]
    played_lesson = lesson(subtitle=long_line, caption=long_line)
    ass = captions.ass_file(project, played_lesson, timeline.build(played_lesson), title_font)

    for style in ("Line", "Caption"):
        text = events(ass, style)[0][2]
        assert text.count("\\N") == 1, text


def test_the_srt_has_a_cue_per_section_with_its_heading_line_and_caption():
    chapters = [chapter(), chapter(label="ลองเล่นเอง")]
    played_lesson = lesson(chapters=chapters, subtitle="Nirvana", caption="ช้าๆ ก่อน")

    srt = captions.srt_file(played_lesson, timeline.build(played_lesson))
    assert srt.count(" --> ") == 3
    assert "FILL\nNirvana\nช้าๆ ก่อน" in srt
    assert "ลองเล่นเอง\nช้าๆ ก่อน" in srt
