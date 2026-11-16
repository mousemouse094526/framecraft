"""The text of a kalimba reel's render (kalimba-cover spec › ภาพของ reel คาลิมบา step 4, D7, D14,
kalimba-picture-sketch.md; ADR 0040, 0054): one ASS file libass draws over `frames` — the drum
reel's title, line under it and "ห้อง n" (`drum_cover.captions`' own events), the caption over the
columns, each tine's number and letter all clip long, and each bar's number riding its line down
the columns. A falling note carries no letter: its colour says its number (D14). Every time is
read from the `KalimbaTimeline` and every place from `frames`, so the letters never part from what
they sit on."""

from backend import subtitles
from backend.drum_cover import captions as reel_captions
from backend.kalimba_cover import frames
from backend.kalimba_cover.frames import COLUMNS_TOP, PLAY_Y, TINES, Scene
from backend.kalimba_cover.timeline import KalimbaTimeline
from backend.paths import ProjectPaths
from backend.subtitles import BLACK, WHITE, pos, squeeze, style
from backend.video_gen import captions as lesson_captions
from backend.video_gen.captions import TitleFont
from backend.video_gen.lessons import Lesson

CAPTION_SIZE = 34
CAPTION_AT = (540, 455)  # one line between the line under the title and the columns
LETTER_FILL = "&H4DFFFFFF"  # white at 70 %: ASS alpha 4D is 30 % see-through
BAR_NUMBER_SIZE = 22
BAR_NUMBER_RIGHT = frames.COLUMNS_RIGHT


def ass_file(project: ProjectPaths, lesson: Lesson, timing: KalimbaTimeline, title_font: TitleFont = lesson_captions.kanit_bold) -> str:
    """Every line of text of the reel at the sketch's places."""
    scene = Scene(lesson, timing, None)  # its places only: `Scene.still` is drawn lazily, so no background is read
    styles = [
        *reel_captions.text_styles(CAPTION_SIZE),
        reel_captions.bar_style(),
        style("BarNumber", BAR_NUMBER_SIZE, WHITE, BLACK, border=2),
        style("Number", frames.NUMBER_SIZE, WHITE, BLACK, border=3),
        style("Letter", frames.LETTER_SIZE, LETTER_FILL, BLACK, border=0),
    ]
    end = timing.length_s
    font = title_font(project)
    # The drum reel's caption sits under its lanes; here it is one line over the columns.
    events = reel_captions.text_events(project, lesson, end, font, with_caption=False)
    if lesson.caption:
        squeezed = squeeze(font.font_variant(size=CAPTION_SIZE).getlength(lesson.caption), reel_captions.TEXT_MAX_PX)
        events.append(subtitles.event("Caption", 0.0, end, f"\\an5{pos(CAPTION_AT)}{squeezed}", [lesson.caption]))
    events += reel_captions.bar_counter_events(scene.bars, end)
    events += _bar_numbers(scene)
    for tine in TINES:
        events.append(subtitles.event("Number", 0.0, end, "\\an5" + pos(tine.number_at), [str(tine.number)]))
        events.append(subtitles.event("Letter", 0.0, end, "\\an5" + pos(tine.letter_at), [tine.letter]))
    return subtitles.HEADER.format(styles="\n".join(styles)) + "\n".join(events) + "\n"


def _bar_numbers(scene: Scene) -> list[str]:
    """Each bar's n at the right end of its line, falling with it: one `\\move` while the notes
    fall, held still in the tail, cut at the columns' top and the play line as the picture cuts."""
    tags = f"\\an3{{}}\\clip(0,{COLUMNS_TOP},{frames.WIDTH},{PLAY_Y})"
    events = []
    for bar in scene.bars:
        if bar.number == 0:
            continue
        # The line enters at the columns' top and leaves at the play line.
        on_screen = (bar.start - (PLAY_Y - COLUMNS_TOP) / scene.px_per_s, bar.start)
        place = lambda t, bar=bar: (BAR_NUMBER_RIGHT, scene.y_of(bar.start, t))  # noqa: E731
        events += reel_captions.riding("BarNumber", on_screen, (scene.end_s, scene.timing.length_s), place, tags, str(bar.number))
    return events
