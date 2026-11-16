"""A reel cover's own text (drum-cover seam 2 › `drum_cover.captions.ass_file`; D25, D26, D29,
reel-picture-sketch.md; ADR 0040, 0054): every piece named, the lanes of the pieces played, the
bar counter, and the hands' letters on the note heads, badges and sticks."""

import re

import pytest
from PIL import ImageFont

from backend.drum_cover import captions, frames
from backend.paths import ProjectPaths
from backend.video_gen import captions as lesson_captions

from .fakes import drum_lesson
from .test_drum_cover_frames import timing_of


@pytest.fixture
def project(fake_root) -> ProjectPaths:
    return ProjectPaths(fake_root)


def ass_of(project: ProjectPaths, timing, title: str = "Yellow", subtitle: str = "DRUMMATE", caption: str = "") -> str:
    font = lambda _project: ImageFont.load_default(lesson_captions.TITLE_SIZE)  # noqa: E731 – the fake root's Kanit is a name only
    lesson = drum_lesson(bpm=120, title=title, subtitle=subtitle, caption=caption)
    return captions.ass_file(project, lesson, timing, font)


def events(ass: str, style: str) -> list[tuple[str, str, str]]:
    """Each Dialogue of `style`: its start, end and text (tags and all)."""
    return re.findall(rf"^Dialogue: 0,([^,]+),([^,]+),{style},,0,0,0,,(.*)$", ass, re.MULTILINE)


def texts(ass: str, style: str) -> list[str]:
    return [re.sub(r"\{[^}]*\}", "", text) for _start, _end, text in events(ass, style)]


def test_the_text_names_every_piece_all_clip_long_and_the_lanes_of_the_pieces_played(project):
    ass = ass_of(project, timing_of((0.5, "hihat_open", "R", "normal"), (1.0, "snare", "L", "normal")))

    labels = events(ass, "Label") + events(ass, "Pedal")
    assert sorted(re.sub(r"\{[^}]*\}", "", text) for _s, _e, text in labels) == ["CRASH", "FLOOR", "HI-HAT", "KICK", "PEDAL", "RIDE", "SNARE", "TOM 1", "TOM 2"]
    assert {(start, end) for start, end, _text in labels} == {("0:00:00.00", "0:00:05.50")}
    assert texts(ass, "Lane") == ["HH OPEN", "SNARE"]


def test_bars_are_counted_from_each_downbeat_and_numbered_over_the_lanes(project):
    ass = ass_of(project, timing_of((1.0, "snare", "L", "normal")))

    assert [(start, text) for start, _end, text in events(ass, "Bar")] == [
        ("0:00:00.00", "{\\an9\\pos(1026,250)}ห้อง 1"),
        ("0:00:02.00", "{\\an9\\pos(1026,250)}ห้อง 2"),
    ]
    assert texts(ass, "BarNumber")[:2] == ["1", "2"]


def test_a_hand_s_note_head_carries_its_letter_in_its_colour_and_a_foot_s_or_a_handless_one_none(project):
    timing = timing_of((0.5, "hihat_closed", "R", "normal"), (1.0, "snare", "L", "normal"), (1.0, "kick", None, "normal"), (1.5, "hihat_closed", None, "normal"))
    ass = ass_of(project, timing)

    letters = events(ass, "NoteLetter")
    assert [re.sub(r"\{[^}]*\}", "", text) for _s, _e, text in letters] == ["R", "L"]
    pink = "&H00D84FFF"  # #FF4FD8 as ASS writes it, blue-green-red
    assert f"\\1c{pink}" in letters[0][2] and "\\move(" in letters[0][2] and "\\clip(210," in letters[0][2]
    assert texts(ass, "Badge") == ["R", "L"]
    assert set(texts(ass, "Stick")) == {"L", "R"}


def test_the_title_line_and_caption_sit_where_a_lesson_s_do_and_a_long_title_is_squeezed_to_760_px(project):
    title = "Smells Like Teen Spirit (Live at the Paramount, 1991) — drum cover"
    ass = ass_of(project, timing_of(), title=title, caption="ตีตามได้เลย")

    [(start, end, heading)] = events(ass, "Heading")  # one, from the first frame: nothing drawn over it
    assert (start, end) == ("0:00:00.00", "0:00:05.50")
    squeezed = int(re.search(r"\\fscx(\d+)", heading).group(1))
    width = ImageFont.load_default(lesson_captions.TITLE_SIZE).getlength(title)
    assert width > 760 and width * squeezed / 100 <= 760
    assert texts(ass, "Line") == ["DRUMMATE"] and texts(ass, "Caption") == ["ตีตามได้เลย"]


def test_a_line_under_the_title_wider_than_760_px_is_squeezed_too(project):
    ass = ass_of(project, timing_of(), subtitle="WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW")  # 30 wide letters: one line past 760 px

    [(_start, _end, line)] = events(ass, "Line")
    width = ImageFont.load_default(lesson_captions.SUBTITLE_SIZE).getlength("W" * 30)
    assert width > 760 and width * int(re.search(r"\\fscx(\d+)", line).group(1)) / 100 <= 760


@pytest.mark.parametrize("first, second", [("L", "R"), ("R", "L")])
def test_a_badge_lasts_until_the_piece_s_next_hit(project, first, second):
    ass = ass_of(project, timing_of((1.0, "snare", first, "normal"), (1.05, "snare", second, "normal")))

    assert [(start, end) for start, end, _text in events(ass, "Badge")] == [("0:00:01.00", "0:00:01.05"), ("0:00:01.05", "0:00:01.20")]
    assert texts(ass, "Badge") == [first, second]
