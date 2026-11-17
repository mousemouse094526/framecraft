"""A kalimba reel's own text (kalimba-cover seam 2 › `kalimba_cover.captions.ass_file`; D7, D14,
kalimba-picture-sketch.md; ADR 0040, 0054): every tine's number and letter, the drum reel's title
and bar counter, and no letter on a falling note."""

import re

import pytest
from PIL import ImageFont

from backend.drum_cover import captions as reel_captions
from backend.kalimba_cover import captions, frames
from backend.paths import ProjectPaths
from backend.video_gen import captions as lesson_captions

from .fakes import drum_lesson, kalimba_timing_of as timing_of, timing_of as drum_timing_of

C4 = 8  # the middle tine


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def font(_project):
    return ImageFont.load_default(lesson_captions.TITLE_SIZE)  # the fake root's Kanit is a name only


def ass_of(project: ProjectPaths, timing, caption: str = "") -> str:
    return captions.ass_file(project, drum_lesson(bpm=120, title="Yellow", subtitle="DRUMMATE", caption=caption), timing, font)


def events(ass: str, style: str) -> list[tuple[str, str, str]]:
    """Each Dialogue of `style`: its start, end and text (tags and all)."""
    return re.findall(rf"^Dialogue: 0,([^,]+),([^,]+),{style},,0,0,0,,(.*)$", ass, re.MULTILINE)


def texts(ass: str, style: str) -> list[str]:
    return [re.sub(r"\{[^}]*\}", "", text) for _start, _end, text in events(ass, style)]


def test_every_tine_has_its_number_and_letter_under_it_all_clip_long_whatever_the_notes(project):
    few = ass_of(project, timing_of())
    many = ass_of(project, timing_of(*((n / 10, n % 17, "normal") for n in range(40))))

    for ass in (few, many):
        assert len(events(ass, "Number")) + len(events(ass, "Letter")) == 34
        assert {(start, end) for start, end, _text in events(ass, "Number") + events(ass, "Letter")} == {("0:00:00.00", "0:00:05.50")}
    assert texts(few, "Number") == [str(tine.number) for tine in frames.TINES]
    assert texts(few, "Letter") == list("DBGECAFDCEGBDFACE")
    [middle] = [text for _s, _e, text in events(few, "Number") if f"\\pos({frames.TINES[C4].cx}," in text]
    assert f"\\pos({frames.TINES[C4].cx},{frames.TINES[C4].tip - 70})" in middle
    assert many.count("\nDialogue:") == few.count("\nDialogue:")  # 40 falling notes add no event


def test_the_title_line_and_bar_counter_are_the_drum_reel_s_and_the_caption_sits_over_the_columns(project):
    ass = ass_of(project, timing_of((1.0, C4, "normal")), caption="เล่นตามได้เลย")
    lesson = drum_lesson(bpm=120, title="Yellow", subtitle="DRUMMATE")
    drums = reel_captions.ass_file(project, lesson, drum_timing_of((1.0, "snare", "L", "normal")), font)

    for style in ("Heading", "Line", "Bar"):
        assert events(ass, style) == events(drums, style), style
    assert texts(ass, "Bar")[0] == "ห้อง 1"
    [(_start, _end, caption)] = events(ass, "Caption")
    assert caption.startswith("{\\an5\\pos(540,455)") and caption.endswith("เล่นตามได้เลย")


def test_a_long_caption_stays_one_line_squeezed_to_760_px(project):
    caption = "W" * 40
    [(_start, _end, text)] = events(ass_of(project, timing_of(), caption=caption), "Caption")

    width = ImageFont.load_default(captions.CAPTION_SIZE).getlength(caption)
    assert "\\N" not in text and width > 760 and width * int(re.search(r"\\fscx(\d+)", text).group(1)) / 100 <= 760


def test_each_bar_s_number_rides_its_line_down_the_columns(project):
    ass = ass_of(project, timing_of(beats=[(1.0, 1), (1.5, 2), (2.0, 3), (2.5, 4), (3.0, 1), (3.5, 2)]))

    numbers = events(ass, "BarNumber")
    assert [re.sub(r"\{[^}]*\}", "", text) for _s, _e, text in numbers][:2] == ["1", "2"]
    assert all("\\move(1016," in text and f"\\clip(0,{frames.COLUMNS_TOP},1080,{frames.PLAY_Y})" in text for _s, _e, text in numbers if "\\move" in text)
