"""The text of a drum lesson's render (video-gen spec › Layout, D3, D12, D13, D22): one ASS file
libass draws over the frames — the title or the chapter's label in its box, the line under it,
the beat counter, the caption, the L/R and RF/LF letters, and the beat numbers sliding over the
lanes with the notes (`lane`) — and the `.srt` saved beside the mp4. Every time is read from
`timeline` (ADR 0038)."""

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from backend import subtitles
from backend.paths import ProjectPaths
from backend.subtitles import BLACK, WHITE, Timed
from backend.video_gen import frames, kit, lane, timeline
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    from PIL.ImageFont import FreeTypeFont

    from backend.video_gen.lessons import Chapter, Lesson

NAVY = "&H002B1A0E"  # #0E1A2B, the background's top
TITLE_SIZE, SUBTITLE_SIZE, COUNTER_SIZE, CAPTION_SIZE = 64, 34, 72, 40
LETTER_SIZE, FOOT_SIZE, BEAT_SIZE, STICK_LETTER_SIZE = 34, 20, 28, 20
TITLE_MAX_PX = 860  # wider is squeezed with `\fscx` onto one line (D22)
BOX_PAD = 10  # the box around the title, past the letters
TITLE_AT = (54 + BOX_PAD, 240 + BOX_PAD)  # its top-left: the box starts at x 54, y 240
SUBTITLE_AT = (54, 340)
COUNTER_AT = (1000, 282)
CAPTION_AT = (54, 1656)
BEAT_Y = lane.TOP - 6  # the numbers' bottom, over the lanes
LINES = 2  # the line under the title and the caption, at most (D22)
SUBTITLE_PER_LINE = 40  # letters that take space, about 860 px at each size
CAPTION_PER_LINE = 34
DARK_TEXT_OVER = 0.6  # a box this light (0–1) takes black letters, a darker one white

# Measures a line of the title at TITLE_SIZE in px: Kanit Bold's, unless a test gives another font.
TitleFont = Callable[[ProjectPaths], "FreeTypeFont"]


def kanit_bold(project: ProjectPaths) -> "FreeTypeFont":
    from PIL import ImageFont

    return ImageFont.truetype(str(project.kanit_dir / "Kanit-Bold.ttf"), TITLE_SIZE)


class Section(NamedTuple):
    """What the top of the screen says from `start` to `end`: a heading in its box (box and letter
    colours as ASS colours) and the line under it."""

    start: float
    end: float
    heading: str
    box: str
    letters: str
    line: str


def sections(lesson: "Lesson", timing: Timeline) -> list[Section]:
    """The count-in shows the title and subtitle; a chapter its label on the box of its first focused
    piece, and its text under it (D12). A chapter with no label shows the title, and the subtitle when
    it has no text either. The last chapter holds through the tail (D21)."""
    found = [Section(0.0, timing.chapters[0].start / timeline.RATE, lesson.title, WHITE, BLACK, lesson.subtitle)]
    for index, (chapter, span) in enumerate(zip(lesson.chapters, timing.chapters, strict=True)):
        end = timing.length_s if index == len(lesson.chapters) - 1 else span.end / timeline.RATE
        found.append(_chapter_section(lesson, chapter, span.start / timeline.RATE, end))
    return found


def _chapter_section(lesson: "Lesson", chapter: "Chapter", start: float, end: float) -> Section:
    if not chapter.label:
        return Section(start, end, lesson.title, WHITE, BLACK, chapter.text or lesson.subtitle)
    if not chapter.focus:
        return Section(start, end, chapter.label, WHITE, BLACK, chapter.text)
    color = kit.BY_ID[chapter.focus[0]].color
    letters = BLACK if _lightness(color) > DARK_TEXT_OVER else WHITE
    return Section(start, end, chapter.label, ass_color(color), letters, chapter.text)


def ass_file(project: ProjectPaths, lesson: "Lesson", timing: Timeline, title_font: TitleFont = kanit_bold) -> str:
    """Every line of text of the clip at spec › Layout's places."""
    font = title_font(project)
    styles = [
        _style("Heading", TITLE_SIZE, BLACK, WHITE, border=BOX_PAD, boxed=True),
        _style("Line", SUBTITLE_SIZE, WHITE, BLACK, border=2),
        _style("Counter", COUNTER_SIZE, WHITE, BLACK, border=3),
        _style("Caption", CAPTION_SIZE, WHITE, BLACK, border=2),
        _style("Letter", LETTER_SIZE, NAVY, NAVY, border=0),
        _style("Foot", FOOT_SIZE, NAVY, NAVY, border=0),
        _style("Stick", STICK_LETTER_SIZE, NAVY, NAVY, border=0),
        _style("Beat", BEAT_SIZE, WHITE, BLACK, border=0),
    ]
    end = timing.length_s
    events: list[str] = []
    for section in sections(lesson, timing):
        squeeze = _squeeze(font.getlength(section.heading))
        tags = f"\\an7{_pos(TITLE_AT)}\\1c{section.letters}\\3c{section.box}{squeeze}"
        events.append(subtitles.event("Heading", section.start, section.end, tags, [section.heading]))
        if section.line:
            lines = _at_most_two(project, section.line, SUBTITLE_PER_LINE)
            events.append(subtitles.event("Line", section.start, section.end, "\\an7" + _pos(SUBTITLE_AT), lines))
    beats = [beat.at / timeline.RATE for beat in timing.beats]
    for beat, start, until in zip(timing.beats, beats, [*beats[1:], end], strict=True):
        events.append(subtitles.event("Counter", start, until, "\\an9" + _pos(COUNTER_AT), [str(beat.number)]))
    if lesson.caption:
        lines = _at_most_two(project, lesson.caption, CAPTION_PER_LINE)
        events.append(subtitles.event("Caption", 0.0, end, "\\an7" + _pos(CAPTION_AT), lines))
    for hand, at in frames.LR_CIRCLES.items():
        events.append(subtitles.event("Letter", 0.0, end, "\\an5" + _pos(at), [hand]))
    for foot in kit.FEET:
        events.append(subtitles.event("Foot", 0.0, end, "\\an5" + _pos(foot.center), [foot.name]))
    events += _stick_letters(timing)
    events += _beat_numbers(lesson, timing)
    return subtitles.HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


def srt_file(lesson: "Lesson", timing: Timeline) -> str:
    """One cue per section: its heading, the line under it, and the caption (spec › Render job step 9)."""
    cues = []
    for section in sections(lesson, timing):
        text = "\n".join(line for line in (section.heading, section.line, lesson.caption) if line)
        cues.append(Timed(text, section.start, section.end))
    return subtitles.srt_file(cues)


def _beat_numbers(lesson: "Lesson", timing: Timeline) -> list[str]:
    """`BAR` over each bar's first beat, 2 3 4 over the others, sliding with the notes: one
    `\\move` per stretch at one speed, still in the tail."""
    events = []
    for segment in lane.segments(lesson, timing):
        for beat in timing.beats:
            at = beat.at / timeline.RATE
            text = "BAR" if beat.number == 1 else str(beat.number)
            if segment.frozen_at is not None:
                x = lane.x_of(at, segment.start_s, segment)
                if lane.LEFT <= x <= lane.RIGHT:
                    events.append(subtitles.event("Beat", segment.start_s, segment.end_s, f"\\an2\\pos({x:.0f},{BEAT_Y})", [text]))
                continue
            enters = at - (lane.RIGHT - lane.PLAYHEAD_X) / segment.px_per_s
            leaves = at + (lane.PLAYHEAD_X - lane.LEFT) / segment.px_per_s
            start, until = max(enters, segment.start_s), min(leaves, segment.end_s)
            if start < until:
                x1, x2 = lane.x_of(at, start, segment), lane.x_of(at, until, segment)
                tags = f"\\an2\\move({x1:.0f},{BEAT_Y},{x2:.0f},{BEAT_Y})"
                events.append(subtitles.event("Beat", start, until, tags, [text]))
    return events


def _stick_letters(timing: Timeline) -> list[str]:
    """L and R on the sticks' heads, where `frames` draws them (ADR 0037, D31): one event per stretch
    of frames the head stays put, each frame's time in the middle of its event so libass can't
    show the one before."""
    swings = frames.stick_swings(timing)
    total = frames.frame_count(timing)
    events = []
    for hand in kit.STICKS:
        first, at = 0, None
        for n in range(total + 1):
            tip = frames.stick_tips(swings, n / frames.FPS)[hand] if n < total else None
            if tip != at:
                if at is not None:
                    start, until = (first - 0.5) / frames.FPS, (n - 0.5) / frames.FPS
                    events.append(subtitles.event("Stick", max(start, 0.0), until, "\\an5" + _pos(at), [hand]))
                first, at = n, tip
    return events


def _squeeze(width_px: float) -> str:
    """`\\fscx` that brings a heading wider than 860 px down to it, on one line (D22)."""
    if width_px <= TITLE_MAX_PX:
        return ""
    return f"\\fscx{math.floor(TITLE_MAX_PX / width_px * 100)}"


def _at_most_two(project: ProjectPaths, text: str, per_line: int) -> list[str]:
    """Cut at word edges (`subtitles.cut_lines`); words that would make a third line widen both
    lines a little at a time instead, so no line runs far past the others (D32)."""
    lines = subtitles.cut_lines(project, text, per_line)
    while len(lines) > LINES:
        per_line += 2
        lines = subtitles.cut_lines(project, text, per_line)
    return lines


def _pos(at: tuple[int, int]) -> str:
    return f"\\pos({at[0]},{at[1]})"


def ass_color(hex_color: str) -> str:
    """`#RRGGBB` as ASS's `&H00BBGGRR`, opaque."""
    return f"&H00{hex_color[5:7]}{hex_color[3:5]}{hex_color[1:3]}".upper()


def _lightness(hex_color: str) -> float:
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def _style(name: str, size: int, fill: str, outline: str, border: int, boxed: bool = False) -> str:
    """ASS BorderStyle 3 when `boxed`: an opaque box in the outline colour, `border` px past the letters."""
    return (
        f"Style: {name},{subtitles.FONT},{size},{fill},{fill},{outline},{outline},-1,0,0,0,"
        f"100,100,0,0,{3 if boxed else 1},{border},0,7,0,0,0,1"
    )
