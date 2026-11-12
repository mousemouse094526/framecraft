"""The ASS file every render draws its text from, and the `.srt` beside the mp4
(spoil-maker spec › ข้อความบนวิดีโอ, seam 1 › Render)."""

import re

import pytest

from backend.paths import ProjectPaths
from backend.spoil_maker import captions, thai
from backend.spoil_maker.captions import Timed
from backend.spoil_maker.settings import Watermark

LONG = "ชายคนหนึ่งตื่นขึ้นมาในห้องที่ไม่รู้จักและพบจดหมายที่เขียนด้วยลายมือของตัวเอง"


@pytest.fixture
def project(tmp_path) -> ProjectPaths:
    return ProjectPaths(tmp_path / "framecraft")


def events(ass: str, style: str) -> list[tuple[float, float, str]]:
    """(start, end, text) of every Dialogue line in `style`."""
    found = []
    for line in ass.splitlines():
        if line.startswith("Dialogue:"):
            fields = line.split(",", 9)
            if fields[3] == style:
                found.append((_seconds(fields[1]), _seconds(fields[2]), fields[9]))
    return found


def _seconds(stamp: str) -> float:
    hours, minutes, seconds = stamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def plain(text: str) -> str:
    """The text without its override blocks."""
    return re.sub(r"(?<!\\)\{[^}]*\}", "", text)


def test_layout_a_subtitles_are_at_most_four_words_of_at_most_fifteen_letters(project):
    ass = captions.ass_file(project, "A", "", [Timed(LONG, 0.0, 3.0)], [])

    chunks = events(ass, "Sub")
    assert len(chunks) > 1
    assert "".join(plain(text) for *_, text in chunks) == LONG
    for *_, text in chunks:
        # One word alone is a chunk only when the next would pass 15 letters (spec › ข้อความบนวิดีโอ, D62).
        assert thai.width(plain(text)) <= 15
        assert 1 <= len(thai.words(project, plain(text))) <= 4
    assert any(len(thai.words(project, plain(text))) >= 2 for *_, text in chunks)
    assert chunks[0][0] == 0.0
    assert chunks[-1][1] == pytest.approx(3.0, abs=0.01)
    assert all(a[1] == pytest.approx(b[0], abs=0.01) for a, b in zip(chunks, chunks[1:]))


def test_subtitles_follow_the_timeline(project):
    ass = captions.ass_file(project, "B", "", [Timed("ประโยคแรก", 0.0, 2.0), Timed("ประโยคสอง", 2.0, 3.5)], [])

    assert [(start, end) for start, end, _ in events(ass, "Sub")] == [(0.0, 2.0), (2.0, 3.5)]


def test_layout_b_puts_at_most_two_lines_of_28_letters_on_screen(project):
    ass = captions.ass_file(project, "B", "", [Timed(LONG + LONG, 0.0, 6.0)], [])

    shown = events(ass, "Sub")
    assert len(shown) > 1
    assert "".join(plain(text).replace("\\N", "") for *_, text in shown) == LONG + LONG
    for *_, text in shown:
        lines = plain(text).split("\\N")
        assert len(lines) <= 2
        assert all(thai.width(line) <= 28 for line in lines)


def test_layout_c_draws_the_title_and_no_subtitles(project):
    ass = captions.ass_file(project, "C", "ตอนจบที่ไม่มีใครคาดคิดของเรื่องนี้เลย", [Timed("ประโยค", 0.0, 2.0)], [])

    ((start, end, title),) = events(ass, "Title")
    assert (start, end) == (0.0, 2.0)
    assert all(thai.width(line) <= 20 for line in plain(title).split("\\N"))
    assert "\\an8\\pos(540,160)" in title
    assert events(ass, "Sub") == []


def test_an_empty_top_text_draws_nothing(project):
    ass = captions.ass_file(project, "A", "", [Timed("ประโยค", 0.0, 2.0)], [])

    assert events(ass, "Hook") == []


def test_user_text_is_escaped_and_kept_on_one_line(project):
    mark = Watermark(text="{\\b1}ลาย", position="top_left", size="small")

    ass = captions.ass_file(project, "A", "hook {\\b1}\nสอง", [Timed("ประโยค {\\b1}\nสอง", 0.0, 2.0)], [mark])

    assert "\\{\\\\b1\\}" in ass
    for line in ass.splitlines():
        if line.startswith("Dialogue:"):
            assert "\n" not in line and "\r" not in line
    assert "\\{\\\\b1\\}ลาย" in events(ass, "Mark")[0][2]


@pytest.mark.parametrize(
    ("position", "anchor"),
    [
        ("top_left", "\\an7\\pos(60,60)"),
        ("top_center", "\\an8\\pos(540,60)"),
        ("top_right", "\\an9\\pos(1020,60)"),
        ("bottom_left", "\\an1\\pos(60,1860)"),
        ("bottom_center", "\\an2\\pos(540,1860)"),
        ("bottom_right", "\\an3\\pos(1020,1860)"),
    ],
)
def test_watermarks_sit_in_their_corner_for_the_whole_clip(project, position, anchor):
    mark = Watermark(text="@ช่อง", position=position, size="medium")

    ass = captions.ass_file(project, "B", "", [Timed("หนึ่ง", 0.0, 2.0), Timed("สอง", 2.0, 5.0)], [mark])

    ((start, end, text),) = events(ass, "Mark")
    assert (start, end) == (0.0, 5.0)
    assert anchor in text
    assert "\\fs52" in text


def test_the_srt_has_a_cue_per_sentence_as_written():
    srt = captions.srt_file([Timed("ปี 1968", 0.0, 2.0), Timed("10:30 น.", 2.0, 63.25)])

    assert srt == "1\n00:00:00,000 --> 00:00:02,000\nปี 1968\n\n2\n00:00:02,000 --> 00:01:03,250\n10:30 น.\n"
