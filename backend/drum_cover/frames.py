"""The picture of a reel cover, one frame at a time (drum-cover spec › ภาพของ reel, D25, D26,
reel-picture-sketch.md; ADR 0054): the kit from above with no two pieces on each other, a white
left stick and a pink right one, a lane for each piece the reel plays, and the bar's beat dots.
It is the reel's own: a lesson's clip keeps `video_gen.frames`. A `Scene` draws what stands still
once per render; `frame_at(scene, t)` lays what moves on a copy. Every moving thing is drawn at
twice the size and shrunk, since `ImageDraw` doesn't smooth edges.

Every time is read from `timeline` (ADR 0041, 0051); every letter is `captions`' (ADR 0040). From
video-gen it takes only what isn't a look: the frame size and rate, the background and how a stick
swings (`stick_tip`). Pillow is imported inside the functions, so the backend starts fast.
"""

import functools
from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple

from backend.video_gen import frames as lesson_frames
from backend.video_gen import timeline
from backend.video_gen.frames import FADE_STEPS, FPS, HEIGHT, SCALE, WIDTH, Swings, frame_count, lighter, paste, shrunk
from backend.video_gen.kit import Point
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    from PIL import Image as PilImage

    from backend.video_gen.lessons import Lesson

Shape = Literal["cymbal", "drum", "plain"]


class Drawn(NamedTuple):
    """One piece on the kit (sketch › ชิ้นกลอง): the hi-hat is drawn once for its closed and open hits."""

    label: str
    center: Point
    r: int
    shape: Shape
    color: str

    @property
    def strike(self) -> Point:
        """Where a stick's head lands: the lower half, on the sticks' side."""
        return self.center[0], round(self.center[1] + STRIKE_SHARE * self.r)

    @property
    def probe(self) -> Point:
        """Between the piece's label and its strike point, where nothing but the piece is drawn
        (inside a cymbal's bell): the one spot that shows the piece's own colour, rest or hit.
        The sketch fixes it so the sound-and-picture check (D27) can read the snare there."""
        return self.center[0], round(self.center[1] - PROBE_SHARE * self.r)

    @property
    def label_at(self) -> Point:
        return self.center[0], round(self.center[1] - LABEL_SHARE * self.r)

    @property
    def badge_at(self) -> Point:
        """The centre of the L/R badge a hand's hit shows: on the right rim, clear of the label."""
        return round(self.center[0] + BADGE_X * self.r), round(self.center[1] - BADGE_Y * self.r)


STRIKE_SHARE, PROBE_SHARE, LABEL_SHARE = 0.35, 0.1, 0.55
BADGE_X, BADGE_Y = 0.95, 0.5  # of the radius; the sketch's (0.7, −0.7) touched a long label (D29)
KIT: dict[str, Drawn] = {
    "crash": Drawn("CRASH", (200, 520), 95, "cymbal", "#FB923C"),
    "ride": Drawn("RIDE", (870, 530), 105, "cymbal", "#A3E635"),
    "tom_high": Drawn("TOM 1", (425, 580), 75, "drum", "#C084FC"),
    "tom_mid": Drawn("TOM 2", (640, 580), 75, "drum", "#818CF8"),
    "hihat": Drawn("HI-HAT", (160, 770), 85, "cymbal", "#FACC15"),
    "snare": Drawn("SNARE", (380, 850), 88, "drum", "#60A5FA"),
    "tom_floor": Drawn("FLOOR", (850, 850), 95, "drum", "#2DD4BF"),
    "kick": Drawn("KICK", (615, 945), 110, "drum", "#F87171"),
    "hihat_pedal": Drawn("PEDAL", (160, 960), 40, "plain", "#FACC15"),
}
DRAWN_OF = {piece: piece for piece in KIT} | {"hihat_closed": "hihat", "hihat_open": "hihat"}


def drawn_of(piece: str) -> Drawn:
    """The kit piece a hit's piece is drawn as: every hi-hat hit on the one hi-hat."""
    return KIT[DRAWN_OF[piece]]


def is_stroke(hit: timeline.Hit) -> bool:
    """A hit a stick plays: a hand's, and not a grace note (which moves no stick and gets no letter)."""
    return hit.hand in STICKS and hit.note != "grace"


REST_FILL = 0.30
REST_OUTLINE = 5
HIT_OUTLINE = 8
HIT_S = 0.15  # a hit piece is lit this long, shrinking back
HIT_GROW, ACCENT_GROW = 1.12, 1.2
GHOST_FILL = 0.6
BELL_SHARE = 0.25
RIM_SHARE = 0.82
BELL_LIGHTER = 0.35
OPEN_RING = 1.25  # an open hi-hat's thin white ring, of its radius
BADGE_R = 22


class Stick(NamedTuple):
    color: str
    grip: Point
    rest: Point  # where its head waits, off every piece


STICKS: dict[str, Stick] = {"L": Stick("#FFFFFF", (300, 1150), (300, 1080)), "R": Stick("#FF4FD8", (800, 1150), (780, 1080))}
STICK_WIDTH = 12
STICK_HEAD_R = 16

# The lanes (sketch › เลนโน้ต): one row for each piece the reel plays, in this order, top down.
LANE_ORDER = ("crash", "ride", "hihat_open", "hihat_closed", "tom_high", "tom_mid", "snare", "tom_floor", "hihat_pedal", "kick")
LANE_NAMES = {"hihat_open": "HH OPEN", "hihat_closed": "HI-HAT"}
LANES_LEFT, LANES_RIGHT = 210, 1026
LANES_TOP, LANES_BOTTOM = 1180, 1600
NAMES_LEFT = 54
PLAYHEAD_X = 330
ROW_MAX = 84
WINDOW_BARS = 1.5
FULL_SPEED = 100  # percent: a reel plays as recorded, never slowed like a lesson chapter
ROW_LINE = "#2A3A50"
BEAT_LINE = (255, 255, 255, 40)
BAR_LINE = (255, 255, 255, 102)  # 40 %
BAR_WIDTH = 3
PLAYHEAD_WIDTH = 4
NOTE_HEAD_SHARE = 0.7  # a note head's width, of its row's height
NOTE_HEAD_SIZE = {"kick": 1.15, "hihat_pedal": 0.7}
ACCENT, GHOST = 1.25, 0.8
ACCENT_OUTLINE = 3
GHOST_ALPHA = 0.5
GLOW_S = 0.15

# The beat dots (sketch › ตัวนับ), right-aligned under the bar's number.
DOTS_RIGHT, DOTS_Y = 1026, 345
DOT_R, DOT_GAP = 12, 36
MAX_DOTS = 4
DOT_DIM = 64  # 25 % white


class Lanes(NamedTuple):
    """Where the rows sit: centred as one block in the lanes' frame."""

    pieces: tuple[str, ...]
    row_h: float
    top: float
    bottom: float

    def y_of(self, piece: str) -> float:
        return self.top + self.row_h * (self.pieces.index(piece) + 0.5)


def lanes_of(timing: Timeline) -> Lanes:
    played = {hit.piece for hit in timing.hits}
    pieces = tuple(piece for piece in LANE_ORDER if piece in played)
    row_h = min(ROW_MAX, (LANES_BOTTOM - LANES_TOP) / max(1, len(pieces)))
    top = LANES_TOP + (LANES_BOTTOM - LANES_TOP - row_h * len(pieces)) / 2
    return Lanes(pieces, row_h, top, top + row_h * len(pieces))


class Bar(NamedTuple):
    """A bar of the clip: its first beat's time, its number from 1 at the clip's first downbeat
    (0 before it) and how many dots it shows."""

    start: float
    number: int
    dots: int


def bars_of(beats: Sequence[timeline.Beat]) -> list[Bar]:
    """A timeline's beats cut into bars at every beat numbered 1; the kalimba's reel counts its
    bars with this too (kalimba-cover D14). A bar a downbeat ends shows as many dots as it has
    beats (4 at most). The clip's last bar may be cut short, so it shows as many as the bar before
    it (4 when there is none), or more when it already has more beats than that."""
    runs: list[list[timeline.Beat]] = []
    for beat in beats:
        if beat.number == 1 or not runs:
            runs.append([])
        runs[-1].append(beat)
    found, number = [], 0
    for index, run in enumerate(runs):
        number += run[0].number == 1
        size = run[-1].number if index < len(runs) - 1 else max(run[-1].number, found[-1].dots if found else MAX_DOTS)
        found.append(Bar(run[0].at / timeline.RATE, number, min(MAX_DOTS, size)))
    return found


class Scene:
    """What every frame of one render shares: where the lanes, bars and swings fall, and the picture
    that stands still (the background, the kit at rest, the lanes and the playhead), drawn the
    first time a frame needs it; `captions` reads the places alone."""

    def __init__(self, lesson: "Lesson", timing: Timeline, background: Path | None):
        self.timing = timing
        self.background = background
        self.lanes = lanes_of(timing)
        self.bars = bars_of(timing.beats)
        # The lanes show 1.5 bars of 4 at the lesson's BPM, played at full speed, across their width and
        # hold still in the tail. Only the scroll speed assumes 4 beats: bar lines come from the downbeats.
        self.px_per_s = (LANES_RIGHT - LANES_LEFT) / (WINDOW_BARS * timeline.BEATS_PER_BAR * timeline.beat_s(lesson.bpm, FULL_SPEED))
        self.end_s = timing.chapters[-1].end / timeline.RATE
        # Something in the lanes is at most this far ahead of the playhead (it entered on the right),
        # and at most this far behind it (it leaves on the left).
        self.ahead_s = (LANES_RIGHT - PLAYHEAD_X) / self.px_per_s
        self.behind_s = (PLAYHEAD_X - LANES_LEFT) / self.px_per_s
        self.hits = timing.hits
        self.times = [hit.at / timeline.RATE for hit in timing.hits]
        self.beat_times = [beat.at / timeline.RATE for beat in timing.beats]
        self.swings = stick_swings(timing)

    @functools.cached_property
    def still(self) -> "PilImage.Image":
        return _still_layer(lesson_frames.background_image(self.background), self.lanes)

    def frames(self) -> int:
        return frame_count(self.timing)

    def x_of(self, at_s: float, t: float) -> float:
        """Where something at `at_s` sits in the lanes at `t`: on the playhead when `t` reaches it."""
        return PLAYHEAD_X + (at_s - min(t, self.end_s)) * self.px_per_s


def frame_at(scene: Scene, t: float) -> bytes:
    """The frame at `t` seconds as raw RGB, 1080×1920: the same `t` gives the same bytes."""
    frame = scene.still.copy()
    _lanes(frame, scene, t)
    _hit_pieces(frame, scene, t)
    for hand, tip in stick_tips(scene.swings, t).items():
        _stick(frame, hand, tip)
    _badges(frame, scene, t)
    beat_dots(frame, scene.bars, scene.beat_times, scene.timing.beats, t)
    return frame.tobytes()


# --- What stands still ---


def _still_layer(background: "PilImage.Image", lanes: Lanes) -> "PilImage.Image":
    from PIL import ImageDraw

    layer = background.copy()
    for drawn in KIT.values():
        paste(layer, _piece(drawn, 1.0, REST_FILL, rgb(drawn.color), REST_OUTLINE, False), drawn.center)
    draw = ImageDraw.Draw(layer)
    for piece in lanes.pieces:
        y = lanes.y_of(piece)
        draw.line([(LANES_LEFT, y), (LANES_RIGHT, y)], fill=ROW_LINE, width=2)
    if lanes.pieces:
        draw.rectangle([LANES_LEFT, lanes.top, LANES_RIGHT, lanes.bottom], outline=ROW_LINE, width=2)
        draw.line([(PLAYHEAD_X, lanes.top), (PLAYHEAD_X, lanes.bottom)], fill="white", width=PLAYHEAD_WIDTH)
    return layer


@functools.lru_cache(maxsize=512)
def _piece(drawn: Drawn, grow: float, fill: float, outline: tuple[int, int, int], width: int, opened: bool) -> "PilImage.Image":
    """A piece from above at `grow` times its size: a disc filled at `fill`, outlined in `outline`;
    a cymbal has a lighter bell, a drum a rim; `opened` adds an open hi-hat's thin white ring."""
    from PIL import Image, ImageDraw

    r = drawn.r * grow * SCALE
    box = round(r * OPEN_RING * 2) + 8 * SCALE
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    c, color = box / 2, rgb(drawn.color)
    w = width * SCALE
    draw.ellipse(_disc(c, r), fill=(*color, round(255 * fill)), outline=(*outline, 255), width=w)
    if drawn.shape == "cymbal":
        draw.ellipse(_disc(c, r * BELL_SHARE), fill=(*lighter(color), 255))
    elif drawn.shape == "drum":
        draw.ellipse(_disc(c, r * RIM_SHARE), outline=(*color, 255), width=max(SCALE, w // 3))
    if opened:
        draw.ellipse(_disc(c, r * OPEN_RING), outline=(255, 255, 255, 255), width=2 * SCALE)
    return shrunk(sprite)


# --- What moves ---


def _lanes(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """The beat and bar lines and the note heads, on the lanes only: what slides past either edge is cut."""
    from PIL import Image, ImageDraw

    lanes = scene.lanes
    if not lanes.pieces:
        return
    # Inside the lanes' 2 px outline, which the still layer drew and nothing here may cover.
    box = (LANES_LEFT + 2, round(lanes.top) + 2, LANES_RIGHT - 1, round(lanes.bottom) - 1)
    region = frame.crop(box)
    lines = Image.new("RGBA", region.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(lines)
    for beat, at in zip(scene.timing.beats, scene.beat_times, strict=True):
        x = scene.x_of(at, t) - box[0]
        if 0 <= x < region.width:
            bar = beat.number == 1
            draw.line([(x, 0), (x, region.height)], fill=BAR_LINE if bar else BEAT_LINE, width=BAR_WIDTH if bar else 1)
    region.paste(lines, (0, 0), lines)
    now = min(t, scene.end_s)
    first = bisect_left(scene.times, now - scene.behind_s)
    last = bisect_right(scene.times, now + scene.ahead_s)
    for hit, at in zip(scene.hits[first:last], scene.times[first:last], strict=True):
        head = _note_head(hit.piece, hit.note, at <= t < at + GLOW_S, lanes.row_h)
        paste(region, head, (scene.x_of(at, t) - box[0], lanes.y_of(hit.piece) - box[1]))
    frame.paste(region, box[:2])
    ImageDraw.Draw(frame).line([(PLAYHEAD_X, lanes.top), (PLAYHEAD_X, lanes.bottom)], fill="white", width=PLAYHEAD_WIDTH)


@functools.lru_cache(maxsize=256)
def _note_head(piece: str, note: str, glow: bool, row_h: float) -> "PilImage.Image":
    """A note head in its piece's colour (sketch › เลนโน้ต): a disc for the snare and toms, a bigger
    one for the kick, an X for the hi-hat (in a ring when open, smaller for the pedal), a diamond
    for a cymbal; an accent bigger and outlined white, a ghost smaller and faint, a white glow while it plays."""
    from PIL import Image, ImageDraw

    size = row_h * NOTE_HEAD_SHARE * NOTE_HEAD_SIZE.get(piece, 1.0) * {"accent": ACCENT, "ghost": GHOST}.get(note, 1.0) * SCALE
    box = round(size * 2)
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    c, r = box / 2, size / 2
    color = (*rgb(drawn_of(piece).color), 255)
    edge = (255, 255, 255, 255) if note == "accent" else None
    edge_w = ACCENT_OUTLINE * SCALE
    if glow:
        draw.ellipse(_disc(c, r * 1.5), fill=(255, 255, 255, 90))
    if piece in ("hihat_closed", "hihat_open", "hihat_pedal"):
        line, s = max(SCALE * 2, round(size / 5)), r * 0.8
        if edge:
            for a, b in (((c - s, c - s), (c + s, c + s)), ((c - s, c + s), (c + s, c - s))):
                draw.line([a, b], fill=edge, width=line + 2 * edge_w)
        draw.line([(c - s, c - s), (c + s, c + s)], fill=color, width=line)
        draw.line([(c - s, c + s), (c + s, c - s)], fill=color, width=line)
        if piece == "hihat_open":
            draw.ellipse(_disc(c, r * 1.2), outline=color, width=max(SCALE, line // 2))
    elif piece in ("crash", "ride"):
        draw.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=color, outline=edge, width=edge_w if edge else 0)
    else:
        draw.ellipse(_disc(c, r), fill=color, outline=edge, width=edge_w if edge else 0)
    if note == "ghost":
        sprite.putalpha(sprite.getchannel("A").point(lambda a: round(a * GHOST_ALPHA)))
    return shrunk(sprite)


def _latest_hits(scene: Scene, t: float) -> dict[str, tuple[timeline.Hit, float]]:
    """The latest hit of each drawn piece in its first 0.15 s, by the drawn piece."""
    first, last = bisect_left(scene.times, t - HIT_S), bisect_right(scene.times, t)
    lit = {}
    for hit, at in zip(scene.hits[first:last], scene.times[first:last], strict=True):
        if at <= t < at + HIT_S:
            lit[DRAWN_OF[hit.piece]] = (hit, at)
    return lit


def _hit_pieces(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """Each piece hit in the last 0.15 s filled in full (60 % for a ghost) and outlined white,
    swollen 1.12 times (1.2 for an accent) and shrinking back in `FADE_STEPS` steps."""
    for name, (hit, at) in _latest_hits(scene, t).items():
        drawn = KIT[name]
        step = round(FADE_STEPS * (1 - (t - at) / HIT_S))
        peak = ACCENT_GROW if hit.note == "accent" else HIT_GROW
        grow = 1 + (peak - 1) * step / FADE_STEPS
        fill = GHOST_FILL if hit.note == "ghost" else 1.0
        paste(frame, _piece(drawn, grow, fill, (255, 255, 255), HIT_OUTLINE, hit.piece == "hihat_open"), drawn.center)


def stick_swings(timing: Timeline) -> Swings:
    """For each hand, when it strikes and where, in order; a hit with no hand moves no stick."""
    swings = {}
    for hand in STICKS:
        hits = [hit for hit in timing.hits if is_stroke(hit) and hit.hand == hand]
        swings[hand] = ([hit.at / timeline.RATE for hit in hits], [drawn_of(hit.piece).strike for hit in hits])
    return swings


def stick_tips(swings: Swings, t: float) -> dict[str, Point]:
    """Where each stick's head is at `t`, swinging as a lesson's do: the picture draws it, the ASS file letters it."""
    return {hand: lesson_frames.stick_tip(times, targets, STICKS[hand].rest, t) for hand, (times, targets) in swings.items()}


def _stick(frame: "PilImage.Image", hand: str, tip: Point) -> None:
    """The hand's stick from its grip to `tip` in its colour, round at both ends, with a round head
    (its letter is `captions`')."""
    from PIL import Image, ImageDraw

    stick = STICKS[hand]
    grip, pad = stick.grip, STICK_HEAD_R + 2
    left, top = min(grip[0], tip[0]) - pad, min(grip[1], tip[1]) - pad
    right, bottom = max(grip[0], tip[0]) + pad, max(grip[1], tip[1]) + pad
    sprite = Image.new("RGBA", ((right - left) * SCALE, (bottom - top) * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    a = ((grip[0] - left) * SCALE, (grip[1] - top) * SCALE)
    b = ((tip[0] - left) * SCALE, (tip[1] - top) * SCALE)
    w, color = STICK_WIDTH * SCALE, stick.color
    draw.line([a, b], fill=color, width=w)
    draw.ellipse(_disc(a, w / 2), fill=color)
    draw.ellipse(_disc(b, STICK_HEAD_R * SCALE), fill=color)
    frame.paste(drawn := shrunk(sprite), (left, top), drawn)


def _badges(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """The hand's coloured badge on a piece a hand hit in the last 0.15 s (its letter is `captions`')."""
    for name, (hit, _at) in _latest_hits(scene, t).items():
        if hit.hand in STICKS:
            paste(frame, dot_sprite(BADGE_R, (*rgb(STICKS[hit.hand].color), 255)), KIT[name].badge_at)


def bar_at(bars: list[Bar], t: float) -> Bar | None:
    """The bar playing at `t`; before the clip's first beat, the first bar."""
    if not bars:
        return None
    return bars[max(0, bisect_right([bar.start for bar in bars], t) - 1)]


def beat_dots(frame: "PilImage.Image", bars: list[Bar], beat_times: list[float], beats: Sequence[timeline.Beat], t: float) -> None:
    """The bar's beat dots, the one of the beat playing white: past the fourth, the fourth. Reads
    the bars and beats alone, so the kalimba's reel draws its counter with it (kalimba-cover D14)."""
    bar = bar_at(bars, t)
    if bar is None:
        return
    playing = bisect_right(beat_times, t) - 1
    number = beats[playing].number if playing >= 0 and beat_times[playing] >= bar.start else 0
    for index in range(bar.dots):
        # Beat n lights dot n; a fifth or later beat keeps the last (fourth) dot lit. Beat 0 (before the bar's first) lights none.
        lit = index == min(number, MAX_DOTS) - 1
        paste(frame, dot_sprite(DOT_R, (255, 255, 255, 255 if lit else DOT_DIM)), dot_center(index, bar.dots))


def dot_center(index: int, dots: int) -> Point:
    return DOTS_RIGHT - DOT_R - DOT_GAP * (dots - 1 - index), DOTS_Y


@functools.lru_cache(maxsize=8)
def dot_sprite(r: int, fill: tuple[int, int, int, int]) -> "PilImage.Image":
    """A filled disc: a hand's badge, a beat dot, or a kalimba tine's octave dot."""
    from PIL import Image, ImageDraw

    box = (r + 1) * 2 * SCALE
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).ellipse(_disc(box / 2, r * SCALE), fill=fill)
    return shrunk(sprite)


# --- Helpers ---


def _disc(c: float | tuple[float, float], r: float) -> list[float]:
    x, y = (c, c) if isinstance(c, (int, float)) else c
    return [x - r, y - r, x + r, y + r]


def rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
