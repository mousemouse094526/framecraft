"""The ten drum pieces a lesson's notes name (video-gen spec › Drum kit, D11, D12): in
note-lane order, with the lane, colour, and whether a foot plays it."""

from typing import Literal, NamedTuple

Lane = Literal["cymbals", "middle", "bottom"]


class Piece(NamedTuple):
    id: str
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
