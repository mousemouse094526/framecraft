"""The text of a render: the ASS file libass draws on the video, and the `.srt` saved
beside the mp4 (spoil-maker spec › ข้อความบนวิดีโอ, D10, D19–D22, D36, D41, D51).

Both take each sentence as written: numbers stay digits (D36). Every position is a
pixel of the 1080×1920 video (`PlayResX`/`PlayResY`, docs/library-notes/ffmpeg.md).
What any render's text shares (`chunks`, the ASS header, `event`, the `.srt`) is in
`backend.subtitles`.
"""

from typing import NamedTuple

from backend.paths import ProjectPaths
from backend.spoil_maker import thai
from backend.subtitles import BLACK, FONT, HEADER, WHITE, Timed, chunks, cut_lines, event, split_time, srt_file
from backend.spoil_maker.draft_file import Layout
from backend.spoil_maker.settings import Watermark


# Letters that take space per line before a line is cut at a word (spec › ข้อความบนวิดีโอ).
HOOK_PER_LINE = 18
TITLE_PER_LINE = 20
SUB_B_PER_LINE = 28
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


def ass_file(project: ProjectPaths, layout: Layout, top_text: str, timed: list[Timed], watermarks: list[Watermark]) -> str:
    """The whole ASS file of a render: the hook (A) or title (C) and the switched-on watermarks
    for the whole clip, and the subtitles (A in short chunks, B by sentence)."""
    total = timed[-1].end if timed else 0.0
    styles = [_style("Mark", MARK_LOOK)]
    events: list[str] = []
    if layout in TOP_TEXTS and top_text.strip():
        style, look, tags, per_line = TOP_TEXTS[layout]
        styles.append(_style(style, look))
        events.append(event(style, 0.0, total, tags, cut_lines(project, top_text, per_line)))
    if layout in SUBTITLES:
        look, tags = SUBTITLES[layout]
        styles.append(_style("Sub", look))
        for sentence in timed:
            pieces = _subtitle_pieces(project, layout, sentence.text)
            for (start, end), piece in zip(split_time(sentence, pieces), pieces):
                events.append(event("Sub", start, end, tags, piece))
    for mark in (m for m in watermarks if m.enabled):  # a switched-off one is only remembered (D64)
        row, column = mark.position.split("_")
        tags = f"\\an{MARK_ANCHORS[mark.position]}\\pos({MARK_X[column]},{MARK_Y[row]})\\fs{MARK_SIZES[mark.size]}"
        events.append(event("Mark", 0.0, total, tags, [mark.text]))
    return HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


def _style(name: str, look: Look) -> str:
    fill, outline = look.fill, look.outline
    return f"Style: {name},{FONT},{look.size},{fill},{fill},{outline},{BLACK},-1,0,0,0,100,100,0,0,1,{look.border},0,8,0,0,0,1"


def _subtitle_pieces(project: ProjectPaths, layout: Layout, text: str) -> list[list[str]]:
    """What shows at once: A a short chunk (D20), B up to two lines; each piece is its lines."""
    if layout == "A":
        return [[chunk] for chunk in chunks(project, text)]
    cut = cut_lines(project, text, SUB_B_PER_LINE)
    return [cut[i : i + SUB_B_LINES] for i in range(0, len(cut), SUB_B_LINES)]


