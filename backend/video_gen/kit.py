"""The ten drum pieces a lesson's notes name (video-gen spec › Drum kit, D11, D12): in
note-lane order, with the lane, colour, and whether a foot plays it."""

from typing import Literal, NamedTuple

Lane = Literal["cymbals", "middle", "bottom"]


PieceId = Literal["hihat_closed", "hihat_open", "crash", "ride", "snare", "tom_high", "tom_mid", "tom_floor", "kick", "hihat_pedal"]


class Piece(NamedTuple):
    id: PieceId
    lane: Lane
    color: str
    foot: bool  # kick and hi-hat pedal: no hand, no flam (D20)


PIECES: tuple[Piece, ...] = (
    Piece("hihat_closed", "cymbals", "#E8C547", False),
    Piece("hihat_open", "cymbals", "#E8C547", False),
    Piece("crash", "cymbals", "#E8894A", False),
    Piece("ride", "cymbals", "#E8894A", False),
    Piece("snare", "middle", "#4A7FE8", False),
    Piece("tom_high", "middle", "#2E8C82", False),
    Piece("tom_mid", "middle", "#2E8C82", False),
    Piece("tom_floor", "middle", "#6B4FC2", False),
    Piece("kick", "bottom", "#E84A6B", True),
    Piece("hihat_pedal", "bottom", "#E8C547", True),
)
BY_ID = {piece.id: piece for piece in PIECES}

# --- The diagram (kit-sketch.md, D17): every value at 1080×1920 ---

Point = tuple[int, int]


class Drawn(NamedTuple):
    """One thing drawn on the diagram and the pieces it stands for: the hi-hat is drawn once for
    three. A drum has a body `height` below its top ellipse; a cymbal has 0; a foot is a small
    circle of radius `radii[0]` with its label. The stick strikes, and the ring shows, at `center`."""

    name: str
    pieces: tuple[str, ...]
    center: Point
    radii: tuple[int, int]
    height: int
    ring: int  # the radius of the red ring a hit shows


FOOT_R = 18
# In drawing order, back to front; the stands and pedals go last (kit-sketch › ชิ้นที่วาด).
DRAWN: tuple[Drawn, ...] = (
    Drawn("ride", ("ride",), (744, 660), (132, 90), 0, 64),
    Drawn("crash", ("crash",), (267, 480), (123, 84), 0, 60),
    Drawn("tom_high", ("tom_high",), (405, 696), (66, 54), 60, 40),
    Drawn("tom_mid", ("tom_mid",), (564, 696), (66, 54), 60, 40),
    Drawn("tom_floor", ("tom_floor",), (714, 900), (102, 84), 120, 56),
    Drawn("kick", ("kick",), (510, 930), (120, 96), 150, 70),
    Drawn("hihat", ("hihat_closed", "hihat_open", "hihat_pedal"), (225, 684), (102, 72), 0, 50),
    Drawn("snare", ("snare",), (417, 864), (96, 78), 60, 52),
)
FEET: tuple[Drawn, ...] = (
    Drawn("RF", ("kick",), (477, 1080), (FOOT_R, FOOT_R), 0, 26),
    Drawn("LF", ("hihat_pedal",), (276, 1104), (FOOT_R, FOOT_R), 0, 26),
)
FLOOR_Y = 1110  # where the stands reach
# Where a hit's ring shows: at the piece's drawing, but the hi-hat pedal's at its foot.
STRIKE: dict[str, Drawn] = {piece: drawn for drawn in DRAWN for piece in drawn.pieces} | {"hihat_pedal": FEET[1]}
FOOT_OF: dict[str, Drawn] = {foot.pieces[0]: foot for foot in FEET}


class Stick(NamedTuple):
    rest: Point  # where its tip waits
    grip: Point  # the pivot


STICKS: dict[str, Stick] = {"L": Stick((336, 954), (300, 1050)), "R": Stick((528, 954), (560, 1050))}
