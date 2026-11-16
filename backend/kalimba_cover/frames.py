"""The picture of a kalimba reel, one frame at a time (kalimba-cover spec › ภาพของ reel คาลิมบา, D7,
D14, kalimba-picture-sketch.md; ADR 0054): a column for each of the 17 tines where notes in the
tine's number's colour fall onto the play line, the kalimba under it whose tine lights up as it is
played, its octave dots, and the drum reel's bar dots. A `Scene` draws what stands still once per
render; `frame_at(scene, t)` lays what moves on a copy. Every moving thing is drawn at twice the
size and shrunk, since `ImageDraw` doesn't smooth edges.

Every time is read from the `KalimbaTimeline` (ADR 0041); every letter (the tines' numbers and
names, the bar numbers) is `captions`' (ADR 0040). The bar counter's dots are `drum_cover.frames`'
own. Pillow is imported inside the functions, so the backend starts fast.
"""

import functools
from bisect import bisect_left, bisect_right
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from backend.drum_cover import frames as reel_frames
from backend.kalimba_cover import arrange
from backend.kalimba_cover.timeline import KalimbaNote, KalimbaTimeline
from backend.video_gen import frames as lesson_frames
from backend.video_gen import timeline
from backend.video_gen.frames import FADE_STEPS, FPS, HEIGHT, SCALE, WIDTH, frame_count, paste, shrunk

if TYPE_CHECKING:
    from PIL import Image as PilImage

    from backend.video_gen.lessons import Lesson

# A tine's number by its pitch class (C major: C is 1), and each number's colour (sketch › สีตามเลขโน้ต).
NUMBER_OF = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
LETTERS = "CDEFGAB"
NUMBER_COLORS = {1: "#F87171", 2: "#FB923C", 3: "#FACC15", 4: "#A3E635", 5: "#2DD4BF", 6: "#60A5FA", 7: "#C084FC"}
OCTAVE_PITCHES = (72, 84)  # C5 and up: one dot; C6 and up: two

# The sketch's places, in px on the 1080×1920 frame.
FIRST_X, TINE_GAP = 92, 56  # tine i's centre x = 92 + 56 i
COLUMNS_TOP, PLAY_Y = 520, 1330
COLUMNS_LEFT, COLUMNS_RIGHT = FIRST_X - TINE_GAP // 2, FIRST_X + TINE_GAP * (len(arrange.TINES) - 1) + TINE_GAP // 2
COLUMN_LINE = "#1F2A3A"
PLAY_LINE_WIDTH = 4
BODY = (40, 1350, 1040, 1800)
BODY_RADIUS, BODY_FILL, BODY_EDGE, BODY_EDGE_W = 60, "#3B2A1E", "#5B4330", 4
BRIDGE = (70, 1380, 1010, 1398)
BRIDGE_FILL = "#9CA3AF"
TINE_TOP, TINE_W, TINE_RADIUS = 1398, 36, 10
LONGEST, SHORTER_BY = 330, 16  # the middle tine's length, and how much shorter each one out from it is
STEEL = "#CBD5E1"
STRIP_H, STRIP_SHARE = 40, 0.6  # the number's colour at 60 % over the steel at the tine's tip, at rest
PROBE_SHARE = 0.35  # of the tine's length from its top: nothing but the tine is drawn there
NUMBER_ABOVE_TIP, LETTER_BELOW_TIP = 70, 28
NUMBER_SIZE, LETTER_SIZE = 34, 22  # `captions` sets them in these sizes
DOT_ABOVE = (108, 122)  # the octave dots' centres above the tip: one dot, then a second
OCTAVE_DOT_R = 5

HIT_S = 0.15  # a played tine is lit this long, shrinking back
HIT_GROW, ACCENT_GROW = 1.15, 1.25  # its width
HIT_OUTLINE = 6
GHOST_FILL = 0.6

NOTE_W, NOTE_H, NOTE_RADIUS = 44, 28, 8
SLOWEST_PX_PER_S = 350  # two notes of a tine 0.08 s apart never overlap (D14)
ACCENT_OUTLINE = 3
GHOST_ALPHA = 0.5
GLOW_S, GLOW_PAD = 0.15, 6
BEAT_LINE = (255, 255, 255, 40)
BAR_LINE = (255, 255, 255, 102)  # 40 %
BAR_WIDTH = 3


class Tine(NamedTuple):
    """One tine as the sketch draws it: its index from the left, pitch, number 1–7 with its letter
    and octave dots, centre x and length down from the bridge."""

    index: int
    pitch: int
    number: int
    letter: str
    dots: int
    cx: int
    length: int

    @property
    def color(self) -> str:
        return NUMBER_COLORS[self.number]

    @property
    def tip(self) -> int:
        return TINE_TOP + self.length

    @property
    def probe(self) -> tuple[int, int]:
        """Over every label and dot: the one spot that shows the tine's own colour, rest or played.
        The sound-and-picture check (D12) reads the tine there."""
        return self.cx, round(TINE_TOP + PROBE_SHARE * self.length)

    @property
    def number_at(self) -> tuple[int, int]:
        return self.cx, self.tip - NUMBER_ABOVE_TIP

    @property
    def letter_at(self) -> tuple[int, int]:
        return self.cx, self.tip + LETTER_BELOW_TIP


def _tine(index: int, pitch: int) -> Tine:
    number = NUMBER_OF[pitch % 12]
    dots = sum(pitch >= octave for octave in OCTAVE_PITCHES)
    length = LONGEST - SHORTER_BY * abs(index - len(arrange.TINES) // 2)
    return Tine(index, pitch, number, LETTERS[number - 1], dots, FIRST_X + TINE_GAP * index, length)


TINES = tuple(_tine(index, pitch) for index, pitch in enumerate(arrange.TINES))


def tine_box(tine: Tine, grow: float = 1.0) -> tuple[float, float, float, float]:
    """The tine's rectangle at `grow` times its width."""
    half = TINE_W * grow / 2
    return tine.cx - half, TINE_TOP, tine.cx + half, tine.tip


class Scene:
    """What every frame of one render shares: the notes' times, how fast they fall, the bars and
    the picture that stands still (the background, the columns, the play line and the kalimba at
    rest), drawn the first time a frame needs it; `captions` reads the places alone."""

    def __init__(self, lesson: "Lesson", timing: KalimbaTimeline, background: Path | None):
        self.timing = timing
        self.background = background
        # The columns show 1.5 bars of 4 at the lesson's BPM, as the drum reel's lanes do, but never slower than 350 px/s.
        window_s = reel_frames.WINDOW_BARS * timeline.BEATS_PER_BAR * timeline.beat_s(lesson.bpm, reel_frames.FULL_SPEED)
        self.px_per_s = max(SLOWEST_PX_PER_S, (PLAY_Y - COLUMNS_TOP) / window_s)
        self.end_s = timing.length_s - timeline.TAIL_S
        # A note shows from entering the columns' top to sinking under the play line.
        self.ahead_s = (PLAY_Y - COLUMNS_TOP + NOTE_H + GLOW_PAD) / self.px_per_s
        self.behind_s = (NOTE_H + GLOW_PAD) / self.px_per_s
        self.notes = timing.notes
        self.times = [note.at / timeline.RATE for note in timing.notes]
        self.bars = reel_frames.bars_of(timing.beats)
        self.beat_times = [beat.at / timeline.RATE for beat in timing.beats]

    @functools.cached_property
    def still(self) -> "PilImage.Image":
        return _still_layer(lesson_frames.background_image(self.background))

    def frames(self) -> int:
        return frame_count(self.timing)  # it reads `length_s` alone, which a kalimba's timeline has

    def y_of(self, at_s: float, t: float) -> float:
        """Where the bottom of something at `at_s` is at `t`: on the play line when `t` reaches it,
        held still in the tail."""
        return PLAY_Y - (at_s - min(t, self.end_s)) * self.px_per_s


def frame_at(scene: Scene, t: float) -> bytes:
    """The frame at `t` seconds as raw RGB, 1080×1920: the same `t` gives the same bytes."""
    frame = scene.still.copy()
    _columns(frame, scene, t)
    _played_tines(frame, scene, t)
    reel_frames.beat_dots(frame, scene.bars, scene.beat_times, scene.timing.beats, t)
    return frame.tobytes()


# --- What stands still ---


def _still_layer(background: "PilImage.Image") -> "PilImage.Image":
    from PIL import ImageDraw

    layer = background.copy()
    draw = ImageDraw.Draw(layer)
    for x in range(COLUMNS_LEFT, COLUMNS_RIGHT + 1, TINE_GAP):
        draw.line([(x, COLUMNS_TOP), (x, PLAY_Y)], fill=COLUMN_LINE, width=1)
    _play_line(layer)
    paste(layer, _body(), _middle(BODY))
    draw.rectangle(BRIDGE, fill=BRIDGE_FILL)
    for tine in TINES:
        paste(layer, _tine_sprite(tine, 1.0, False, 1.0), _middle(tine_box(tine)))
        _octave_dots(layer, tine)
    return layer


def _play_line(frame: "PilImage.Image") -> None:
    from PIL import ImageDraw

    ImageDraw.Draw(frame).line([(COLUMNS_LEFT, PLAY_Y), (COLUMNS_RIGHT, PLAY_Y)], fill="white", width=PLAY_LINE_WIDTH)


def _body() -> "PilImage.Image":
    from PIL import Image, ImageDraw

    w, h = (BODY[2] - BODY[0]) * SCALE, (BODY[3] - BODY[1]) * SCALE
    sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=BODY_RADIUS * SCALE, fill=BODY_FILL, outline=BODY_EDGE, width=BODY_EDGE_W * SCALE
    )
    return shrunk(sprite)


@functools.lru_cache(maxsize=512)
def _tine_sprite(tine: Tine, grow: float, lit: bool, fill: float) -> "PilImage.Image":
    """A tine at `grow` times its width: at rest steel with its number's colour
    at the tip; played, filled with its colour at `fill` over the steel and outlined white."""
    from PIL import Image, ImageDraw

    x0, y0, x1, y1 = tine_box(tine, grow)
    w, h = round((x1 - x0) * SCALE), (y1 - y0) * SCALE
    sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    r, box = TINE_RADIUS * SCALE, [0, 0, w - 1, h - 1]
    color = reel_frames.rgb(tine.color)
    if not lit:
        draw.rounded_rectangle(box, radius=r, fill=STEEL)
        strip = _mixed(color, STRIP_SHARE)
        draw.rounded_rectangle([0, h - STRIP_H * SCALE, w - 1, h - 1], radius=r, fill=strip, corners=(False, False, True, True))
    else:
        draw.rounded_rectangle(box, radius=r, fill=_mixed(color, fill), outline="white", width=HIT_OUTLINE * SCALE)
    return shrunk(sprite)


def _mixed(color: tuple[int, int, int], share: float) -> tuple[int, int, int]:
    """`color` at `share` over the steel."""
    steel = reel_frames.rgb(STEEL)
    return tuple(round(c * share + s * (1 - share)) for c, s in zip(color, steel, strict=True))


def _octave_dots(frame: "PilImage.Image", tine: Tine) -> None:
    for above in DOT_ABOVE[: tine.dots]:
        paste(frame, reel_frames.dot_sprite(OCTAVE_DOT_R, (255, 255, 255, 255)), (tine.cx, tine.tip - above))


# --- What moves ---


def _columns(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """The beat and bar lines and the falling notes, in the columns only: what sinks under the
    play line is cut."""
    from PIL import Image, ImageDraw

    box = (COLUMNS_LEFT, COLUMNS_TOP, COLUMNS_RIGHT, PLAY_Y)
    region = frame.crop(box)
    lines = Image.new("RGBA", region.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(lines)
    for beat, at in zip(scene.timing.beats, scene.beat_times, strict=True):
        y = scene.y_of(at, t) - COLUMNS_TOP
        if 0 <= y < region.height:
            bar = beat.number == 1
            draw.line([(0, y), (region.width, y)], fill=BAR_LINE if bar else BEAT_LINE, width=BAR_WIDTH if bar else 1)
    region.paste(lines, (0, 0), lines)
    now = min(t, scene.end_s)
    first = bisect_left(scene.times, now - scene.behind_s)
    last = bisect_right(scene.times, now + scene.ahead_s)
    for note, at in zip(scene.notes[first:last], scene.times[first:last], strict=True):
        sprite = _note_sprite(TINES[note.tine].color, note.level, at <= t < at + GLOW_S)
        paste(region, sprite, (TINES[note.tine].cx - COLUMNS_LEFT, scene.y_of(at, t) - NOTE_H / 2 - COLUMNS_TOP))
    frame.paste(region, box[:2])
    _play_line(frame)


@functools.lru_cache(maxsize=64)
def _note_sprite(color: str, level: str, glow: bool) -> "PilImage.Image":
    """A falling note in its tine's colour: an accent outlined white, a ghost faint, a white glow
    around it while it plays. No letter on it: the colour says its number (D14)."""
    from PIL import Image, ImageDraw

    pad = GLOW_PAD * SCALE
    w, h = NOTE_W * SCALE + 2 * pad, NOTE_H * SCALE + 2 * pad
    sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    r = NOTE_RADIUS * SCALE
    if glow:
        draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r + pad, fill=(255, 255, 255, 90))
    outline = "white" if level == "accent" else None
    draw.rounded_rectangle(
        [pad, pad, w - pad - 1, h - pad - 1], radius=r, fill=color, outline=outline, width=ACCENT_OUTLINE * SCALE if outline else 0
    )
    if level == "ghost":
        sprite.putalpha(sprite.getchannel("A").point(lambda a: round(a * GHOST_ALPHA)))
    return shrunk(sprite)


def _latest_played(scene: Scene, t: float) -> dict[int, tuple[KalimbaNote, float]]:
    """The latest note of each tine in its first 0.15 s, by the tine."""
    first, last = bisect_left(scene.times, t - HIT_S), bisect_right(scene.times, t)
    lit = {}
    for note, at in zip(scene.notes[first:last], scene.times[first:last], strict=True):
        if at <= t < at + HIT_S:
            lit[note.tine] = (note, at)
    return lit


def _played_tines(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """Each tine played in the last 0.15 s filled in its colour (60 % for a ghost) and outlined
    white, 1.15 times as wide (1.25 for an accent), narrowing back and fading to steel in
    `FADE_STEPS` steps; its octave dots stay on top."""
    for index, (note, at) in _latest_played(scene, t).items():
        tine = TINES[index]
        step = round(FADE_STEPS * (1 - (t - at) / HIT_S))
        peak = ACCENT_GROW if note.level == "accent" else HIT_GROW
        grow = 1 + (peak - 1) * step / FADE_STEPS
        fill = (GHOST_FILL if note.level == "ghost" else 1.0) * step / FADE_STEPS
        paste(frame, _tine_sprite(tine, grow, True, fill), _middle(tine_box(tine, grow)))
        _octave_dots(frame, tine)


def _middle(box: tuple[float, float, float, float]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2

