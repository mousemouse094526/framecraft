"""The text of a reel cover's render (drum-cover spec › ภาพของ reel step 5, D25, D26,
reel-picture-sketch.md; ADR 0040, 0054): one ASS file libass draws over `frames` — the title, the
line under it and the caption where a lesson's go (the same styles and cutting), every piece's
name on the kit, the lanes' names, "ห้อง n" and the bar numbers over the lanes, the L/R on the
sticks' heads, on the hands' note heads and on a hit's badge. Every time is read from `timeline`
and every place from `frames.Scene`, so the letters never part from what they sit on."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from backend import subtitles
from backend.drum_cover import frames
from backend.drum_cover.frames import DRAWN_OF, KIT, LANE_NAMES, LANES_LEFT, LANES_RIGHT, STICKS, Scene, drawn_of, is_stroke
from backend.paths import ProjectPaths
from backend.subtitles import BLACK, WHITE, ass_color, at_most_two, pos, squeeze, style
from backend.video_gen import captions as lesson_captions
from backend.video_gen.captions import CAPTION_AT, CAPTION_PER_LINE, CAPTION_SIZE, SUBTITLE_AT, SUBTITLE_SIZE, TITLE_AT, TITLE_SIZE
from backend.video_gen.captions import TitleFont
from backend.video_gen.lessons import Lesson
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    from PIL.ImageFont import FreeTypeFont

TEXT_MAX_PX = 760  # the title and the line under it: clear of the bar counter's column, x 830–1026
SUBTITLE_PER_LINE = 30
LABEL_SIZE, PEDAL_LABEL_SIZE, LANE_NAME_SIZE = 30, 22, 26
BAR_SIZE, BAR_NUMBER_SIZE = 52, 22
BADGE_SIZE, STICK_LETTER_SIZE = 26, 20
NOTE_LETTER_SHARE = 0.55  # of a row's height
BAR_AT = (frames.DOTS_RIGHT, 250)
BAR_NUMBER_GAP = 6  # the bar numbers' bottom, over the lanes
BAR_WORD = "ห้อง"


def ass_file(project: ProjectPaths, lesson: Lesson, timing: Timeline, title_font: TitleFont = lesson_captions.kanit_bold) -> str:
    """Every line of text of the reel at the sketch's places."""
    scene = Scene(lesson, timing, None)  # its places only: `Scene.still` is drawn lazily, so no background is read
    styles = [
        *text_styles(),
        style("Label", LABEL_SIZE, WHITE, BLACK, border=3),
        style("Pedal", PEDAL_LABEL_SIZE, WHITE, BLACK, border=3),
        style("Lane", LANE_NAME_SIZE, WHITE, BLACK, border=2),
        bar_style(),
        style("BarNumber", BAR_NUMBER_SIZE, WHITE, BLACK, border=2),
        style("Badge", BADGE_SIZE, BLACK, BLACK, border=0),
        style("Stick", STICK_LETTER_SIZE, BLACK, BLACK, border=0),
        style("NoteLetter", round(scene.lanes.row_h * NOTE_LETTER_SHARE), WHITE, BLACK, border=2),
    ]
    end = timing.length_s
    events = text_events(project, lesson, end, title_font(project))
    for name, drawn in KIT.items():
        events.append(subtitles.event("Pedal" if name == "hihat_pedal" else "Label", 0.0, end, "\\an5" + pos(drawn.label_at), [drawn.label]))
    for piece in scene.lanes.pieces:
        at = (frames.NAMES_LEFT, round(scene.lanes.y_of(piece)))
        events.append(subtitles.event("Lane", 0.0, end, f"\\an4{pos(at)}\\1c{ass_color(drawn_of(piece).color)}", [lane_name(piece)]))
    events += bar_counter_events(scene.bars, end)
    events += _bar_numbers(scene)
    events += _note_letters(scene)
    events += _badges(scene)
    events += lesson_captions.stick_letters(lambda t: frames.stick_tips(scene.swings, t), scene.frames())
    return subtitles.HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


# --- what the kalimba's reel shares (kalimba-cover D7, D14) ---


def text_styles(caption_size: int = CAPTION_SIZE) -> list[str]:
    """The styles `text_events` writes in: the boxed title, the line under it and the caption."""
    return [
        style("Heading", TITLE_SIZE, BLACK, WHITE, border=lesson_captions.BOX_PAD, boxed=True),
        style("Line", SUBTITLE_SIZE, WHITE, BLACK, border=2),
        style("Caption", caption_size, WHITE, BLACK, border=2),
    ]


def text_events(project: ProjectPaths, lesson: Lesson, end_s: float, font: "FreeTypeFont", with_caption: bool = True) -> list[str]:
    """The title, the line under it and the caption, all clip long where a lesson's go: the title
    and the line squeezed to 760 px, the line and the caption cut into two at most. A reel that
    places its caption elsewhere (the kalimba's) leaves it out."""
    events = [subtitles.event("Heading", 0.0, end_s, f"\\an7{pos(TITLE_AT)}{squeeze(font.getlength(lesson.title), TEXT_MAX_PX)}", [lesson.title])]
    if lesson.subtitle:
        lines = at_most_two(project, lesson.subtitle, SUBTITLE_PER_LINE)
        widest = max(font.font_variant(size=SUBTITLE_SIZE).getlength(line) for line in lines)
        events.append(subtitles.event("Line", 0.0, end_s, f"\\an7{pos(SUBTITLE_AT)}{squeeze(widest, TEXT_MAX_PX)}", lines))
    if with_caption and lesson.caption:
        events.append(subtitles.event("Caption", 0.0, end_s, "\\an7" + pos(CAPTION_AT), at_most_two(project, lesson.caption, CAPTION_PER_LINE)))
    return events


def bar_style() -> str:
    return style("Bar", BAR_SIZE, WHITE, BLACK, border=3)


def bar_counter_events(bars: list[frames.Bar], length_s: float) -> list[str]:
    """"ห้อง n" top right from each downbeat to the next bar; the last to the clip's end."""
    events = []
    for bar, until in zip(bars, [*(bar.start for bar in bars[1:]), length_s], strict=True):
        if bar.number == 0:
            continue  # before the clip's first downbeat: the dots alone
        events.append(subtitles.event("Bar", bar.start, until, "\\an9" + pos(BAR_AT), [f"{BAR_WORD} {bar.number}"]))
    return events


# --- the drums' own ---


def lane_name(piece: str) -> str:
    return LANE_NAMES.get(piece, drawn_of(piece).label)


def _bar_numbers(scene: Scene) -> list[str]:
    """Each bar's n over its line in the lanes, sliding with it."""
    if not scene.lanes.pieces:
        return []
    events = []
    y = round(scene.lanes.top) - BAR_NUMBER_GAP
    for bar in scene.bars:
        if bar.number != 0:
            events += _sliding(scene, "BarNumber", bar.start, y, "\\an2", str(bar.number))
    return events


def _note_letters(scene: Scene) -> list[str]:
    """The hand's L or R in its colour on each note head a hand plays, sliding with it."""
    events = []
    for hit, at in zip(scene.hits, scene.times, strict=True):
        if is_stroke(hit):
            tags = f"\\an5\\1c{ass_color(STICKS[hit.hand].color)}"
            events += _sliding(scene, "NoteLetter", at, round(scene.lanes.y_of(hit.piece)), tags, hit.hand)
    return events


def _sliding(scene: Scene, style_name: str, at: float, y: int, tags: str, text: str) -> list[str]:
    """Text that rides the lanes with something at `at`, cut at the lanes' edges as the picture
    cuts its note heads."""
    clip = f"\\clip({LANES_LEFT},0,{LANES_RIGHT},{frames.HEIGHT})"
    on_screen = (at - scene.ahead_s, at + scene.behind_s)
    return riding(style_name, on_screen, (scene.end_s, scene.timing.length_s), lambda t: (scene.x_of(at, t), y), tags + "{}" + clip, text)


def riding(style_name: str, on_screen: tuple[float, float], end_and_length: tuple[float, float],
           place: Callable[[float], tuple[float, float]], tags: str, text: str) -> list[str]:
    """Text that rides the picture while it is `on_screen` (enters, leaves): one `\\move` between
    `place`'s points while the picture moves, held still in the tail (from `end_s` to the clip's
    length) when it is still on screen then. `tags` holds `{}` where the move or pos goes."""
    (enters, leaves), (end_s, length_s) = on_screen, end_and_length
    events = []
    start, until = max(enters, 0.0), min(leaves, end_s)
    if start < until:
        (x1, y1), (x2, y2) = place(start), place(until)
        events.append(subtitles.event(style_name, start, until, tags.format(f"\\move({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})"), [text]))
    if enters <= end_s < leaves:
        x, y = place(end_s)
        events.append(subtitles.event(style_name, end_s, length_s, tags.format(f"\\pos({x:.0f},{y:.0f})"), [text]))
    return events


def _badges(scene: Scene) -> list[str]:
    """The hand's letter on a hit piece's badge for 0.15 s, or until the piece's next hit — any
    hit, a foot's or a handless one too, since the picture shows only a piece's latest hit."""
    events = []
    next_on: dict[str, float] = {}
    for hit, at in reversed(list(zip(scene.hits, scene.times, strict=True))):
        name = DRAWN_OF[hit.piece]
        if hit.hand in STICKS:
            until = min(at + frames.HIT_S, next_on.get(name, at + frames.HIT_S))
            if until > at:  # empty when the next hit of this piece is on the same sample: only the last one's letter shows, as in the picture
                events.append(subtitles.event("Badge", at, until, "\\an5" + pos(KIT[name].badge_at), [hit.hand]))
        next_on[name] = at
    return events[::-1]
