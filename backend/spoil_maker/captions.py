"""The text of a render: the ASS file libass draws on the video, and the `.srt` saved
beside the mp4 (spoil-maker spec › ข้อความบนวิดีโอ, D10, D19–D22, D36, D41, D51).

Both take each sentence as written: numbers stay digits (D36). Every position is a
pixel of the 1080×1920 video (`PlayResX`/`PlayResY`, docs/library-notes/ffmpeg.md).
"""

from typing import NamedTuple

from backend import clock
from backend.paths import ProjectPaths
from backend.spoil_maker import thai
from backend.spoil_maker.draft_file import Layout
from backend.spoil_maker.settings import Watermark

FONT = "Kanit"  # Kanit-Bold.ttf, found through the filter's `fontsdir` (D21)

# Letters that take space per line before a line is cut at a word (spec › ข้อความบนวิดีโอ).
HOOK_PER_LINE = 18
TITLE_PER_LINE = 20
SUB_A_PER_CHUNK = 15
SUB_B_PER_LINE = 28
SUB_A_MAX_WORDS = 4  # D20
SUB_B_LINES = 2

# Watermarks (D41, D51): x by column, y by row, the ASS anchor by both.
MARK_SIZES = {"small": 36, "medium": 52}
MARK_X = {"left": 60, "center": 540, "right": 1020}
MARK_Y = {"top": 60, "bottom": 1860}
MARK_ANCHORS = {
    "top_left": 7, "top_center": 8, "top_right": 9,
    "bottom_left": 1, "bottom_center": 2, "bottom_right": 3,
}  # fmt: skip

class Look(NamedTuple):
    """An ASS style: size, fill and outline colour, outline width. Colours are &HAABBGGRR,
    alpha 00 opaque: #FFD400 is &H0000D4FF, #D7262E &H002E26D7."""

    size: int
    fill: str
    outline: str
    border: int


WHITE, BLACK = "&H00FFFFFF", "&H00000000"

# The text on top of each layout that has one (D19, D22): style, look, anchor, letters per line.
TOP_TEXTS: dict[str, tuple[str, Look, str, int]] = {
    "A": ("Hook", Look(76, WHITE, BLACK, 6), "\\an8\\pos(540,70)", HOOK_PER_LINE),
    "C": ("Title", Look(80, "&H0000D4FF", "&H002E26D7", 6), "\\an8\\pos(540,160)", TITLE_PER_LINE),
}
# The subtitles of each layout that has them (D20, D22): look and anchor. C has none.
SUBTITLES: dict[str, tuple[Look, str]] = {
    "A": (Look(92, WHITE, BLACK, 8), "\\an5\\pos(540,1300)"),
    "B": (Look(56, WHITE, BLACK, 0), "\\an8\\pos(540,1300)"),
}
MARK_LOOK = Look(MARK_SIZES["small"], "&H33FFFFFF", "&H33000000", 3)  # 80% opaque (alpha 0x33); `\\fs` sets the size

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, \
Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, \
MarginV, Encoding
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


class Timed(NamedTuple):
    """A sentence on the timeline, in seconds."""

    text: str
    start: float
    end: float


def ass_file(project: ProjectPaths, layout: Layout, top_text: str, timed: list[Timed], watermarks: list[Watermark]) -> str:
    """The whole ASS file of a render: the hook (A) or title (C) and the watermarks
    for the whole clip, and the subtitles (A in short chunks, B by sentence)."""
    total = timed[-1].end if timed else 0.0
    styles = [_style("Mark", MARK_LOOK)]
    events: list[str] = []
    if layout in TOP_TEXTS and top_text.strip():
        style, look, tags, per_line = TOP_TEXTS[layout]
        styles.append(_style(style, look))
        events.append(_event(style, 0.0, total, tags, _lines(project, top_text, per_line)))
    if layout in SUBTITLES:
        look, tags = SUBTITLES[layout]
        styles.append(_style("Sub", look))
        for sentence in timed:
            pieces = _subtitle_pieces(project, layout, sentence.text)
            for (start, end), piece in zip(_split_time(sentence, pieces), pieces):
                events.append(_event("Sub", start, end, tags, piece))
    for mark in watermarks:
        row, column = mark.position.split("_")
        tags = f"\\an{MARK_ANCHORS[mark.position]}\\pos({MARK_X[column]},{MARK_Y[row]})\\fs{MARK_SIZES[mark.size]}"
        events.append(_event("Mark", 0.0, total, tags, [mark.text]))
    return HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


def srt_file(timed: list[Timed]) -> str:
    """One cue per sentence, as written (D10, D36)."""
    return clock.srt((t.start, t.end, t.text) for t in timed)


def escape(text: str) -> str:
    """One line, and nothing libass reads as a tag: `\\`, `{`, `}` escaped (D51)."""
    text = " ".join(text.split())
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _style(name: str, look: Look) -> str:
    fill, outline = look.fill, look.outline
    return f"Style: {name},{FONT},{look.size},{fill},{fill},{outline},{BLACK},-1,0,0,0,100,100,0,0,1,{look.border},0,8,0,0,0,1"


def _event(style: str, start: float, end: float, tags: str, lines: list[str]) -> str:
    """One Dialogue line: `lines` escaped and joined by ASS line breaks, after the position tags."""
    text = "\\N".join(escape(line) for line in lines)
    return f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},{style},,0,0,0,,{{{tags}}}{text}"


def _subtitle_pieces(project: ProjectPaths, layout: Layout, text: str) -> list[list[str]]:
    """What shows at once: A a short chunk (D20), B up to two lines; each piece is its lines."""
    if layout == "A":
        return [[chunk] for chunk in _chunks(project, text)]
    lines = _lines(project, text, SUB_B_PER_LINE)
    return [lines[i : i + SUB_B_LINES] for i in range(0, len(lines), SUB_B_LINES)]


def _lines(project: ProjectPaths, text: str, per_line: int) -> list[str]:
    """`text` cut at `newmm` word edges so no line has more than `per_line` letters that
    take space; a word longer than that is a line of its own."""
    lines: list[str] = []
    current = ""
    for word in thai.words(project, " ".join(text.split())):
        if current and thai.width((current + word).strip()) > per_line:
            lines.append(current.strip())
            current = ""
        current += word
    if current.strip():
        lines.append(current.strip())
    return lines


def _chunks(project: ProjectPaths, text: str) -> list[str]:
    """Layout A's short subtitles (D20): words gathered until 4, or until the next word
    would pass 15 letters that take space; a longer word alone is a chunk."""
    chunks: list[str] = []
    current: list[str] = []
    for word in thai.words(project, " ".join(text.split())):
        if current and (len(current) == SUB_A_MAX_WORDS or thai.width("".join(current + [word]).strip()) > SUB_A_PER_CHUNK):
            chunks.append("".join(current).strip())
            current = []
        current.append(word)
    if current:
        chunks.append("".join(current).strip())
    return chunks


def _split_time(sentence: Timed, pieces: list[list[str]]) -> list[tuple[float, float]]:
    """The sentence's time shared out by letters that take space (spec › ข้อความบนวิดีโอ)."""
    sizes = [max(1, sum(thai.width(line) for line in piece)) for piece in pieces]
    total, length = sum(sizes), sentence.end - sentence.start
    spans, done = [], 0
    for size in sizes:
        start = sentence.start + length * done / total
        done += size
        spans.append((start, sentence.start + length * done / total))
    return spans


def _ass_time(seconds: float) -> str:
    """`H:MM:SS.cc`, centiseconds."""
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

