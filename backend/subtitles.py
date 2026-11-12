"""What the text of every render shares (spoil-maker D20, D21, D51; toon D22): the ASS header
at the video's own 1080×1920 pixels, a Dialogue line with its text escaped, cutting Thai text
into lines or short chunks at word edges and sharing a sentence's time out among them, and the
`.srt` saved beside the mp4. spoil_maker's `captions` and toon's `compose` lay them out.
"""

from typing import NamedTuple

from backend import clock
from backend.paths import ProjectPaths
from backend.spoil_maker import thai

FONT = "Kanit"  # Kanit-Bold.ttf, found through the filter's `fontsdir` (spoil-maker D21)
WHITE, BLACK = "&H00FFFFFF", "&H00000000"  # &HAABBGGRR, alpha 00 opaque

# A short subtitle (spoil-maker D20): up to 4 words, or 15 letters that take space.
SUB_A_PER_CHUNK = 15
SUB_A_MAX_WORDS = 4

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


def srt_file(timed: list[Timed]) -> str:
    """One cue per sentence, as written (D10, D36)."""
    return clock.srt((t.start, t.end, t.text) for t in timed)


def escape(text: str) -> str:
    """One line, and nothing libass reads as a tag: `\\`, `{`, `}` escaped (D51)."""
    text = " ".join(text.split())
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def event(style: str, start: float, end: float, tags: str, lines: list[str]) -> str:
    """One Dialogue line: `lines` escaped and joined by ASS line breaks, after the position tags."""
    text = "\\N".join(escape(line) for line in lines)
    return f"Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{{{tags}}}{text}"


def cut_lines(project: ProjectPaths, text: str, per_line: int) -> list[str]:
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


def chunks(project: ProjectPaths, text: str) -> list[str]:
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


def split_time(sentence: Timed, pieces: list[list[str]]) -> list[tuple[float, float]]:
    """The sentence's time shared out by letters that take space (spec › ข้อความบนวิดีโอ)."""
    sizes = [max(1, sum(thai.width(line) for line in piece)) for piece in pieces]
    total, length = sum(sizes), sentence.end - sentence.start
    spans, done = [], 0
    for size in sizes:
        start = sentence.start + length * done / total
        done += size
        spans.append((start, sentence.start + length * done / total))
    return spans


def ass_time(seconds: float) -> str:
    """`H:MM:SS.cc`, centiseconds."""
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
