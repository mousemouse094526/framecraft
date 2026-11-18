"""The text of a drum lesson's render (video-gen spec › Layout, D3, D12, D13, D22): one ASS file
libass draws over the frames — the title or the chapter's label in its box, the line under it,
the beat counter, the caption, the L/R and RF/LF letters, and the beat numbers sliding over the
lanes with the notes (`lane`) — and the `.srt` saved beside the mp4. Every time is read from
`timeline` (ADR 0041)."""

from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from backend import subtitles
from backend.paths import ProjectPaths
from backend.subtitles import BLACK, WHITE, Timed, ass_color, at_most_two, pos, squeeze, style
from backend.video_gen import frames, kit, lane, timeline
from backend.video_gen.kit import Point
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
    """A chapter shows its label on the box of its first focused piece, and its text under it (D12),
    from 0 s for the first (no count-in, reels-only D15). A chapter with no label shows the title, and
    the subtitle when it has no text either. The last chapter holds through the tail (D21)."""
    found = []
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
        style("Heading", TITLE_SIZE, BLACK, WHITE, border=BOX_PAD, boxed=True),
        style("Line", SUBTITLE_SIZE, WHITE, BLACK, border=2),
        style("Counter", COUNTER_SIZE, WHITE, BLACK, border=3),
        style("Caption", CAPTION_SIZE, WHITE, BLACK, border=2),
        style("Letter", LETTER_SIZE, NAVY, NAVY, border=0),
        style("Foot", FOOT_SIZE, NAVY, NAVY, border=0),
        style("Stick", STICK_LETTER_SIZE, NAVY, NAVY, border=0),
        style("Beat", BEAT_SIZE, WHITE, BLACK, border=0),
    ]
    end = timing.length_s
    events: list[str] = []
    for section in sections(lesson, timing):
        squeezed = squeeze(font.getlength(section.heading), TITLE_MAX_PX)
        tags = f"\\an7{pos(TITLE_AT)}\\1c{section.letters}\\3c{section.box}{squeezed}"
        events.append(subtitles.event("Heading", section.start, section.end, tags, [section.heading]))
        if section.line:
            lines = at_most_two(project, section.line, SUBTITLE_PER_LINE)
            events.append(subtitles.event("Line", section.start, section.end, "\\an7" + pos(SUBTITLE_AT), lines))
    beats = [beat.at / timeline.RATE for beat in timing.beats]
    for beat, start, until in zip(timing.beats, beats, [*beats[1:], end], strict=True):
        events.append(subtitles.event("Counter", start, until, "\\an9" + pos(COUNTER_AT), [str(beat.number)]))
    if lesson.caption:
        lines = at_most_two(project, lesson.caption, CAPTION_PER_LINE)
        events.append(subtitles.event("Caption", 0.0, end, "\\an7" + pos(CAPTION_AT), lines))
    for hand, at in frames.LR_CIRCLES.items():
        events.append(subtitles.event("Letter", 0.0, end, "\\an5" + pos(at), [hand]))
    for foot in kit.FEET:
        events.append(subtitles.event("Foot", 0.0, end, "\\an5" + pos(foot.center), [foot.name]))
    swings = frames.stick_swings(timing)
    events += stick_letters(lambda t: frames.stick_tips(swings, t), frames.frame_count(timing))
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


def stick_letters(tips_at: Callable[[float], dict[str, Point]], total: int) -> list[str]:
    """L and R on the sticks' heads, where `tips_at(t)` says the picture draws them (ADR 0040, D31):
    one event per stretch of frames the head stays put, each frame's time in the middle of its
    event so libass can't show the one before. A reel cover's sticks go through here too (drum-cover D25)."""
    events = []
    for hand in tips_at(0.0):  # the hands the picture has sticks for
        first, at = 0, None
        for n in range(total + 1):
            tip = tips_at(n / frames.FPS)[hand] if n < total else None
            if tip != at:
                if at is not None:
                    start, until = (first - 0.5) / frames.FPS, (n - 0.5) / frames.FPS
                    events.append(subtitles.event("Stick", max(start, 0.0), until, "\\an5" + pos(at), [hand]))
                first, at = n, tip
    return events


def _lightness(hex_color: str) -> float:
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b
