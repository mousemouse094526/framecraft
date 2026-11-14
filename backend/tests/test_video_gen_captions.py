"""The ASS and SRT text over a lesson's frames (video-gen seam 2 › `captions`)."""

import re

import pytest
from PIL import ImageFont

from backend.paths import ProjectPaths
from backend.video_gen import captions, kit, timeline

from .fakes import drum_chapter as chapter
from .fakes import drum_lesson as lesson
from .fakes import drum_note as note


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
