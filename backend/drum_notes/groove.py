"""The sticking of a reel cover's hits (drum-notes spec › Score steps 6–7; D13, D20; drum-cover D4):
the trim to what two hands play, then which hand plays each note. Pure functions on hits already
placed on 16 steps a bar: `drum_cover.timeline` places them and calls `trimmed` and `with_hands`.
The lesson made from picked bars is gone (reels-only D7).
"""

from collections.abc import Iterator
from typing import Literal, NamedTuple

from backend.drum_notes.songs import Level
from backend.video_gen import kit
from backend.video_gen.kit import PieceId
from backend.video_gen.lessons import Note


# Step 6: of more than two hand notes in a step, the first two of this order stay (D13): the snare
# and the crash carry the beat, so they outrank the time-keeping cymbals, which outrank the toms.
KEEP_ORDER = ("snare", "crash", "hihat_closed", "hihat_open", "ride", "tom_high", "tom_mid", "tom_floor")
# Step 7: of two hand notes in a step, the first of this order is the right hand's (D13): the kit
# seen from the drummer's stool, right to left — ride, hi-hat, crash, floor tom, mid tom, high tom,
# snare — so the hands don't cross.
RIGHT_ORDER = ("ride", "hihat_closed", "hihat_open", "crash", "tom_floor", "tom_mid", "tom_high", "snare")
CYMBALS = frozenset({"hihat_closed", "hihat_open", "crash", "ride"})
LEFT_AFTER_CYMBAL = frozenset({"snare", "tom_high"})
# Steps are 16ths. A single hand note one 16th (one step) after the last hand note alternates hands;
# from two steps (an 8th) on, the piece decides (D13 as D20 fixed it) ...
ALTERNATE_STEP = 1
# ... and a snare or high tom up to an 8th (two steps) after a right-hand cymbal is the left hand's.
CYMBAL_WITHIN = 2
Hand = Literal["R", "L"]


class Placed(NamedTuple):
    """A hit on a step of the Groove, before the hands are chosen."""

    piece: PieceId
    step: int
    level: Level


def trimmed(placed: list[Placed]) -> list[Placed]:
    """Step 6: on each step, an open hi-hat beside a closed one goes first, then hand notes past
    two by `KEEP_ORDER` (D13, D20, D25); what goes still sounds in a reel, with no stick (drum-cover D5)."""
    kept: list[Placed] = []
    for _, feet, hands in _by_step(placed):
        if {"hihat_open", "hihat_closed"} <= {p.piece for p in hands}:
            hands = [p for p in hands if p.piece != "hihat_open"]
        hands.sort(key=lambda p: KEEP_ORDER.index(p.piece))
        kept.extend(feet + hands[:2])
    return kept


def with_hands(placed: list[Placed]) -> list[Note]:
    """Step 7, the sticking of D13 as D20 fixed it (`_hand` has the rules for a single note). Two
    hand notes on a step: R to the one further right on the kit (`RIGHT_ORDER`), L to the other,
    and the R one is what the next step's rule looks back at. Feet have no hand. In step order."""
    notes: list[Note] = []
    last: Note | None = None  # the hand note before this step: the R one when its step had two
    for step, feet, hands in _by_step(placed):
        hands.sort(key=lambda p: RIGHT_ORDER.index(p.piece))
        notes.extend(Note(piece=p.piece, step=step, hand=None, hit=p.level) for p in feet)
        if len(hands) == 2:
            right, left = hands
            last = Note(piece=right.piece, step=step, hand="R", hit=right.level)
            notes.extend([last, Note(piece=left.piece, step=step, hand="L", hit=left.level)])
        elif len(hands) == 1:
            [one] = hands
            last = Note(piece=one.piece, step=step, hand=_hand(one.piece, step, last), hit=one.level)
            notes.append(last)
    return notes


def _by_step(placed: list[Placed]) -> Iterator[tuple[int, list[Placed], list[Placed]]]:
    """Each step that has a hit, in order, with its foot notes and its hand notes (kit order)."""
    for step in sorted({p.step for p in placed}):
        on_step = [p for p in placed if p.step == step]
        yield step, [p for p in on_step if kit.BY_ID[p.piece].foot], [p for p in on_step if not kit.BY_ID[p.piece].foot]


def _hand(piece: str, step: int, last: Note | None) -> Hand:
    """The hand of a single hand note on `step`, after `last` (D13 as D20 fixed it): one 16th after
    the last hand note, the other hand (a 16th run alternates: R L R L); a cymbal is R; a snare or
    high tom is L when the right hand played a cymbal up to an 8th before (it is still up there),
    else R, as is any other tom."""
    if last is not None and step - last.step <= ALTERNATE_STEP:
        return "L" if last.hand == "R" else "R"
    if piece in CYMBALS:
        return "R"
    if piece in LEFT_AFTER_CYMBAL and last is not None and step - last.step <= CYMBAL_WITHIN and last.piece in CYMBALS and last.hand == "R":
        return "L"
    return "R"
