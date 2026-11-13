"""The picture of a drum lesson, one frame at a time (video-gen spec › Layout, kit-sketch.md, D3,
D13, D17, D18). A `Scene` draws what stands still once per render: the background, the kit for
each set of focused pieces, the lanes and the playhead. `frame_at(scene, t)` lays what moves on a
copy: the sticks, the rings, the note heads, the beat lines, the feet and the L/R circles. Every
moving thing is drawn at twice the size and shrunk, since `ImageDraw` doesn't smooth edges.

Every time is read from `timeline` (ADR 0038). Every letter is `captions`' (ADR 0037): it puts
the L or R on a stick's head where `stick_tips` says the head is, frame by frame (D31).
Pillow is imported inside the functions, so the backend starts fast.
"""

import functools
import math
from bisect import bisect_left, bisect_right
from pathlib import Path
from typing import TYPE_CHECKING

from backend.video_gen import kit, lane, timeline
from backend.video_gen.kit import Drawn, Point
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    from PIL import Image as PilImage

    from backend.video_gen.lessons import Lesson

WIDTH, HEIGHT = 1080, 1920
FPS = 30
SCALE = 2  # moving things are drawn this much larger, then shrunk (D18)
TOP_COLOR, BOTTOM_COLOR = "#0E1A2B", "#07090D"
BLUR_RADIUS = 24
DARKEN = 0.55  # a picture background under 55 % black
KIT_TOP, KIT_BOTTOM = 390, 1170
DIM = 0.35  # a piece outside the chapter's focus (D13)
DRUM_FILL_ALPHA = 0.45
CYMBAL_FILL_ALPHA = 0.70
BELL_LIGHTER = 0.35
OUTLINE = 4
GRID_COLOR = "#1C2A3D"
LANE_LINE = "#2A3A50"
BAR_LINE = "#4A5A70"
PLAYHEAD_WIDTH = 4

RING_S = 0.15  # a ring fades this long after its hit (D13)
FADE_STEPS = 15  # a fading ring or shrinking foot is drawn in this many steps, so `lru_cache` keeps each one
RING_WIDTH = 6
FLASH_SHARE = 0.45  # the filled red at the strike point, of the ring's radius
GRACE_SHARE = 0.6  # a flam's grace note: a smaller ring, no stick (kit-sketch › ไม้กลอง)
HIT_RED = (232, 48, 48)
FOOT_PULSE = 1.35  # a foot's circle grows this much as it plays, back over RING_S

RISE_S, HOLD_S, BACK_S = 0.12, 0.05, 0.15  # a stick's tip: out to the strike, held, back to rest
# Notes closer than a swing (RISE_S) start each swing from where the last one had got to, which
# depends on the one before, and so on back; past 4 swings the stick starts from the last note's
# piece instead, so a long fast roll costs no deeper recursion and looks the same.
CHAIN_DEPTH = 4
STICK_WIDTH = 10
HEAD_R = 14

LR_CIRCLES = {"L": (816, 1149), "R": (900, 1149)}
LR_R = 30
LR_BRIGHT, LR_FAINT = 230, 60  # alpha of the circle of a hand playing, and of one at rest

HEAD_SIZE = 28  # a note head's width
ACCENT = 1.25
GHOST_ALPHA = 0.5
GLOW_S = 0.15


class Scene:
    """What every frame of one render shares. The kit is drawn once per set of focused pieces
    (one per chapter that has its own), the first time a frame needs it."""

    def __init__(self, lesson: "Lesson", played: Timeline, background: Path | None):
        self.lesson = lesson
        self.played = played
        self.segments = lane.segments(lesson, played)
        self._background = _background(background)
        self._still: dict[frozenset[str], PilImage.Image] = {}
        shown = [hit for hit in played.hits if hit.note != "count"]
        self.heads = shown
        self.head_times = [hit.at / timeline.RATE for hit in shown]
        self.swings = stick_swings(played)
        self.beat_times = [beat.at / timeline.RATE for beat in played.beats]

    def still(self, focus: frozenset[str]) -> "PilImage.Image":
        if focus not in self._still:
            self._still[focus] = _still_layer(self._background, focus)
        return self._still[focus]

    def frames(self) -> int:
        """`ceil(length_s × 30)` (D21)."""
        return math.ceil(round(self.played.length_s * FPS, 6))


def frame_at(scene: Scene, t: float) -> bytes:
    """The frame at `t` seconds as raw RGB, 1080×1920: the same `t` gives the same bytes."""
    segment = lane.segment_at(scene.segments, t)
    chapter = scene.lesson.chapters[segment.chapter]
    frame = scene.still(frozenset(chapter.focus)).copy()
    _beat_lines(frame, scene, t, segment)
    _note_heads(frame, scene, t, segment)
    _feet(frame, scene, t)
    tips = stick_tips(scene.swings, t)
    for hand, tip in tips.items():
        _stick(frame, hand, tip)
    _rings(frame, scene, t)
    for hand, at in LR_CIRCLES.items():
        _paste(frame, _lr_circle(LR_BRIGHT if tips[hand] != kit.STICKS[hand].rest else LR_FAINT), at)
    return frame.tobytes()


# --- What stands still ---


def _background(picture: Path | None) -> "PilImage.Image":
    """`color`: navy fading down to near black; `image`: the picture blurred and darkened."""
    from PIL import Image, ImageFilter

    if picture is None:
        mask = Image.linear_gradient("L").resize((WIDTH, HEIGHT))
        return Image.composite(Image.new("RGB", (WIDTH, HEIGHT), BOTTOM_COLOR), Image.new("RGB", (WIDTH, HEIGHT), TOP_COLOR), mask)
    with Image.open(picture) as opened:
        image = opened.convert("RGB").resize((WIDTH, HEIGHT))
    blurred = image.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
    return Image.blend(blurred, Image.new("RGB", (WIDTH, HEIGHT), "black"), DARKEN)


def _still_layer(background: "PilImage.Image", focus: frozenset[str]) -> "PilImage.Image":
    """The background, the kit (pieces outside `focus` at 35 %; no focus lights all), the lanes and the playhead."""
    from PIL import Image, ImageDraw

    height = KIT_BOTTOM - KIT_TOP
    drawing = Image.new("RGBA", (WIDTH * SCALE, height * SCALE), (0, 0, 0, 0))
    _floor(drawing)
    for drawn in kit.DRAWN:
        lit = not focus or any(piece in focus for piece in drawn.pieces)
        _stand(drawing, drawn, lit)
        if drawn.height:
            _drum(drawing, drawn, lit)
        else:
            _cymbal(drawing, drawn, lit)
    for foot in kit.FEET:
        lit = not focus or foot.pieces[0] in focus
        _circle(drawing, foot.center, foot.radii[0], _color(kit.BY_ID[foot.pieces[0]].color, lit), CYMBAL_FILL_ALPHA)
    layer = background.convert("RGBA")
    layer.alpha_composite(drawing.resize((WIDTH, height), Image.Resampling.LANCZOS), (0, KIT_TOP))
    draw = ImageDraw.Draw(layer)
    for y in lane.LANE_Y.values():
        draw.line([(lane.LEFT, y), (lane.RIGHT, y)], fill=LANE_LINE, width=2)
    draw.rectangle([lane.LEFT, lane.TOP, lane.RIGHT, lane.BOTTOM], outline=LANE_LINE, width=2)
    x = lane.PLAYHEAD_X
    draw.line([(x, lane.TOP), (x, lane.BOTTOM)], fill="white", width=PLAYHEAD_WIDTH)
    return layer.convert("RGB")


def _at(point: Point) -> tuple[float, float]:
    """A point of the frame on the kit's 2× drawing."""
    return point[0] * SCALE, (point[1] - KIT_TOP) * SCALE


def _floor(drawing: "PilImage.Image") -> None:
    """A faint grid in perspective under the kit."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(drawing)
    for y in (1000, 1040, 1080, kit.FLOOR_Y):
        draw.line([_at((120, y)), _at((960, y))], fill=GRID_COLOR, width=2 * SCALE)
    for x in range(120, 961, 120):
        draw.line([_at((540 + (x - 540) * 0.6, 1000)), _at((x, kit.FLOOR_Y))], fill=GRID_COLOR, width=2 * SCALE)


def _stand(drawing: "PilImage.Image", drawn: Drawn, lit: bool) -> None:
    from PIL import ImageDraw

    if drawn.name == "kick":
        return
    x, y = drawn.center
    bottom = y + drawn.height + drawn.radii[1]
    if bottom < kit.FLOOR_Y:
        ImageDraw.Draw(drawing).line([_at((x, bottom)), _at((x, kit.FLOOR_Y))], fill=_color(_piece_color(drawn), lit), width=OUTLINE * SCALE)


def _drum(drawing: "PilImage.Image", drawn: Drawn, lit: bool) -> None:
    """Top ellipse, a body down its height, a bottom ellipse: filled at 45 %, outlined in full."""
    from PIL import Image, ImageDraw

    color = _color(_piece_color(drawn), lit)
    (cx, cy), (rx, ry), h = _at(drawn.center), (drawn.radii[0] * SCALE, drawn.radii[1] * SCALE), drawn.height * SCALE
    body = Image.new("RGBA", drawing.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(body)
    fill = (*color, 255)
    draw.ellipse([cx - rx, cy + h - ry, cx + rx, cy + h + ry], fill=fill)
    draw.rectangle([cx - rx, cy, cx + rx, cy + h], fill=fill)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)
    body.putalpha(body.getchannel("A").point(lambda a: round(a * DRUM_FILL_ALPHA)))
    draw = ImageDraw.Draw(body)
    width = OUTLINE * SCALE
    draw.arc([cx - rx, cy + h - ry, cx + rx, cy + h + ry], 0, 180, fill=fill, width=width)
    draw.line([(cx - rx + width / 2, cy), (cx - rx + width / 2, cy + h)], fill=fill, width=width)
    draw.line([(cx + rx - width / 2, cy), (cx + rx - width / 2, cy + h)], fill=fill, width=width)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=fill, width=width)
    drawing.alpha_composite(body)


def _cymbal(drawing: "PilImage.Image", drawn: Drawn, lit: bool) -> None:
    """An ellipse at 70 % with a lighter bell in the middle."""
    color = _color(_piece_color(drawn), lit)
    _ellipse(drawing, drawn.center, drawn.radii, color, CYMBAL_FILL_ALPHA)
    bell = tuple(round(c + (255 - c) * BELL_LIGHTER) for c in color)
    _ellipse(drawing, drawn.center, (drawn.radii[0] // 4, drawn.radii[1] // 4), bell, 1.0)


def _circle(drawing: "PilImage.Image", center: Point, r: int, color: tuple[int, int, int], alpha: float) -> None:
    _ellipse(drawing, center, (r, r), color, alpha)


def _ellipse(drawing: "PilImage.Image", center: Point, radii: tuple[int, int], color: tuple[int, int, int], alpha: float) -> None:
    from PIL import Image, ImageDraw

    (cx, cy), rx, ry = _at(center), radii[0] * SCALE, radii[1] * SCALE
    shape = Image.new("RGBA", drawing.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(*color, round(255 * alpha)), outline=(*color, 255), width=OUTLINE * SCALE)
    drawing.alpha_composite(shape)


def _piece_color(drawn: Drawn) -> str:
    return kit.BY_ID[drawn.pieces[0]].color


def _color(hex_color: str, lit: bool = True) -> tuple[int, int, int]:
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return rgb if lit else tuple(round(c * DIM) for c in rgb)


# --- What moves ---


def _paste(frame: "PilImage.Image", sprite: "PilImage.Image", center: tuple[float, float]) -> None:
    """A 1× sprite laid on the frame, centred on `center`."""
    frame.paste(sprite, (round(center[0] - sprite.width / 2), round(center[1] - sprite.height / 2)), sprite)


def _shrunk(sprite: "PilImage.Image") -> "PilImage.Image":
    from PIL import Image

    return sprite.resize((sprite.width // SCALE, sprite.height // SCALE), Image.Resampling.LANCZOS)


def _beat_lines(frame: "PilImage.Image", scene: Scene, t: float, segment: lane.Segment) -> None:
    from PIL import ImageDraw

    draw = ImageDraw.Draw(frame)
    for beat, at in zip(scene.played.beats, scene.beat_times, strict=True):
        x = lane.x_of(at, t, segment)
        if lane.LEFT < x < lane.RIGHT:
            bar = beat.number == 1
            draw.line([(x, lane.TOP + 2), (x, lane.BOTTOM - 2)], fill=BAR_LINE if bar else LANE_LINE, width=2 if bar else 1)


def _note_heads(frame: "PilImage.Image", scene: Scene, t: float, segment: lane.Segment) -> None:
    now = segment.frozen_at if segment.frozen_at is not None else t
    first = bisect_left(scene.head_times, now - (lane.PLAYHEAD_X - lane.LEFT) / segment.px_per_s)
    last = bisect_right(scene.head_times, now + (lane.RIGHT - lane.PLAYHEAD_X) / segment.px_per_s)
    for hit, at in zip(scene.heads[first:last], scene.head_times[first:last], strict=True):
        x = lane.x_of(at, t, segment)
        glow = at <= t < at + GLOW_S
        _paste(frame, _head(hit.piece, hit.note, glow), (x, lane.LANE_Y[kit.BY_ID[hit.piece].lane]))


@functools.lru_cache(maxsize=256)
def _head(piece: str, note: str, glow: bool) -> "PilImage.Image":
    """A note head as kit-sketch › หัวโน้ตในเลนโน้ต draws it: larger for an accent, faint for a
    ghost, small for a flam's grace note, glowing while it plays."""
    from PIL import Image, ImageDraw

    size = HEAD_SIZE * {"accent": ACCENT, "grace": GRACE_SHARE}.get(note, 1.0) * SCALE
    box = round(size * 2)
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    c, r = box / 2, size / 2
    color = (*_color(kit.BY_ID[piece].color), 255)
    line = max(2, round(size / 7))
    if glow:
        draw.ellipse([c - r * 1.6, c - r * 1.6, c + r * 1.6, c + r * 1.6], fill=(255, 255, 255, 90))
    if piece in ("hihat_closed", "hihat_open", "hihat_pedal"):
        s = r * (0.65 if piece == "hihat_pedal" else 1.0)
        draw.line([(c - s, c - s), (c + s, c + s)], fill=color, width=line)
        draw.line([(c - s, c + s), (c + s, c - s)], fill=color, width=line)
        if piece == "hihat_open":
            draw.ellipse([c - r * 1.4, c - r * 1.4, c + r * 1.4, c + r * 1.4], outline=color, width=line // 2 + 1)
    elif piece in ("crash", "ride"):
        draw.line([(c, c), (c, c + r)], fill=color, width=line // 2 + 1)
        draw.ellipse([c - r, c - r * 0.45, c + r, c + r * 0.1], fill=color)
    elif piece == "kick":
        draw.ellipse([c - r * 1.3, c - r * 1.3, c + r * 1.3, c + r * 1.3], outline=color, width=line)
    else:  # snare and toms: a small drum
        draw.ellipse([c - r, c, c + r, c + r * 0.8], fill=color)
        draw.rectangle([c - r, c - r * 0.4, c + r, c + r * 0.4], fill=color)
        draw.ellipse([c - r, c - r * 0.8, c + r, c], fill=(*_lighter(color[:3]), 255))
    if note == "ghost":
        sprite.putalpha(sprite.getchannel("A").point(lambda a: round(a * GHOST_ALPHA)))
    return _shrunk(sprite)


def _lighter(color: tuple[int, ...]) -> tuple[int, int, int]:
    return tuple(round(c + (255 - c) * BELL_LIGHTER) for c in color)


Swings = dict[str, tuple[list[float], list[Point]]]


def stick_swings(played: Timeline) -> Swings:
    """For each hand, when it strikes and where, in order; a grace note moves no stick (kit-sketch)."""
    swings = {}
    for hand in kit.STICKS:
        hits = [hit for hit in played.hits if hit.hand == hand and hit.note != "grace"]
        swings[hand] = ([hit.at / timeline.RATE for hit in hits], [kit.STRIKE[hit.piece].center for hit in hits])
    return swings


def stick_tips(swings: Swings, t: float) -> dict[str, Point]:
    """Where each stick's tip (its head) is at `t`: the picture draws the stick to it, the ASS file letters it."""
    return {hand: _tip_before(times, targets, kit.STICKS[hand].rest, t, len(times), 0) for hand, (times, targets) in swings.items()}


def _tip_before(times: list[float], targets: list[Point], rest: Point, t: float, limit: int, depth: int) -> Point:
    """Where the stick's tip is at `t`, from the first `limit` hits only: rising (ease-out) to the
    next one from wherever it was, held on the last one, then back to rest. A hit whose rise
    starts before the stick got back starts from where it is (kit-sketch › ไม้กลอง)."""
    i = bisect_right(times, t, 0, limit)
    if i < limit and t >= times[i] - RISE_S:
        start_t = times[i] - RISE_S
        start = targets[i - 1] if depth >= CHAIN_DEPTH and i else _tip_before(times, targets, rest, start_t, i, depth + 1)
        p = (t - start_t) / RISE_S
        return _between(start, targets[i], 1 - (1 - p) ** 2)
    if i == 0:
        return rest
    since = t - times[i - 1]
    if since < HOLD_S:
        return targets[i - 1]
    if since < HOLD_S + BACK_S:
        return _between(targets[i - 1], rest, (since - HOLD_S) / BACK_S)
    return rest


def _between(a: Point, b: Point, p: float) -> Point:
    return round(a[0] + (b[0] - a[0]) * p), round(a[1] + (b[1] - a[1]) * p)


def _stick(frame: "PilImage.Image", hand: str, tip: Point) -> None:
    """A white stick from its grip to `tip`, round at both ends, with a round head (its letter is `captions`')."""
    from PIL import Image, ImageDraw

    grip = kit.STICKS[hand].grip
    pad = STICK_WIDTH
    left, top = min(grip[0], tip[0]) - pad, min(grip[1], tip[1]) - pad
    right, bottom = max(grip[0], tip[0]) + pad, max(grip[1], tip[1]) + pad
    sprite = Image.new("RGBA", ((right - left) * SCALE, (bottom - top) * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    a = ((grip[0] - left) * SCALE, (grip[1] - top) * SCALE)
    b = ((tip[0] - left) * SCALE, (tip[1] - top) * SCALE)
    w = STICK_WIDTH * SCALE
    draw.line([a, b], fill="white", width=w)
    draw.ellipse([a[0] - w / 2, a[1] - w / 2, a[0] + w / 2, a[1] + w / 2], fill="white")
    frame.paste(shrunk := _shrunk(sprite), (left, top), shrunk)
    _paste(frame, _stick_head(), tip)


@functools.lru_cache(maxsize=1)
def _stick_head() -> "PilImage.Image":
    from PIL import Image, ImageDraw

    box = HEAD_R * 2 * SCALE + 4
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).ellipse([2, 2, box - 2, box - 2], fill="white")
    return _shrunk(sprite)


def _rings(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """A red ring and a red flash at the strike point of every hit in its first 0.15 s,
    fading; a grace note's is smaller (D13). Drawn over the sticks."""
    first = bisect_left(scene.head_times, t - RING_S)
    last = bisect_right(scene.head_times, t)
    for hit, at in zip(scene.heads[first:last], scene.head_times[first:last], strict=True):
        if at <= t < at + RING_S:
            drawn = kit.STRIKE[hit.piece]
            radius = drawn.ring * (GRACE_SHARE if hit.note == "grace" else 1.0)
            fade = round(FADE_STEPS * (1 - (t - at) / RING_S))
            _paste(frame, _ring(round(radius), fade), drawn.center)


@functools.lru_cache(maxsize=256)
def _ring(radius: int, fade: int) -> "PilImage.Image":
    """`fade` 0–FADE_STEPS: how much of the ring is left."""
    from PIL import Image, ImageDraw

    alpha = round(255 * fade / FADE_STEPS)
    r, box = radius * SCALE, (radius + RING_WIDTH) * SCALE * 2
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    c = box / 2
    draw.ellipse([c - r, c - r, c + r, c + r], outline=(*HIT_RED, alpha), width=RING_WIDTH * SCALE)
    f = r * FLASH_SHARE
    draw.ellipse([c - f, c - f, c + f, c + f], fill=(*HIT_RED, alpha))
    return _shrunk(sprite)


def _feet(frame: "PilImage.Image", scene: Scene, t: float) -> None:
    """A foot's circle swells as it plays and shrinks back over 0.15 s (D13)."""
    first = bisect_left(scene.head_times, t - RING_S)
    last = bisect_right(scene.head_times, t)
    for hit, at in zip(scene.heads[first:last], scene.head_times[first:last], strict=True):
        foot = kit.FOOT_OF.get(hit.piece)
        if foot is not None and at <= t < at + RING_S:
            grow = round(FADE_STEPS * (FOOT_PULSE - 1) * (1 - (t - at) / RING_S))
            _paste(frame, _foot(hit.piece, grow), foot.center)


@functools.lru_cache(maxsize=32)
def _foot(piece: str, grow: int) -> "PilImage.Image":
    from PIL import Image, ImageDraw

    r = kit.FOOT_R * (1 + grow / FADE_STEPS) * SCALE
    box = round(r * 2) + 4
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).ellipse([2, 2, box - 2, box - 2], fill=(*_color(kit.BY_ID[piece].color), 255))
    return _shrunk(sprite)


@functools.lru_cache(maxsize=2)
def _lr_circle(alpha: int) -> "PilImage.Image":
    from PIL import Image, ImageDraw

    box = LR_R * 2 * SCALE
    sprite = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    ImageDraw.Draw(sprite).ellipse([0, 0, box - 1, box - 1], fill=(255, 255, 255, alpha))
    return _shrunk(sprite)
