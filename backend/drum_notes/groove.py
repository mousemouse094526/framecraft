"""A lesson's Groove from the bars picked (drum-notes spec › Score steps 3–8; D11, D13, D14, D20):
the default BPM, the hits quantized onto 16 steps a bar, melody mode's base groove under them, the
trim to what two hands play, and the sticking. Pure functions on the hits and bars an analysis holds:
`drum_notes.lesson` calls `preview` with the bars the user chose, tests with hand-made hits (D17).
The signal numbers before this (chunks, peaks, windows, beats) are `drum_notes.score`.
"""

import math
import statistics
from collections.abc import Callable, Iterator
from typing import Literal, NamedTuple

from backend.drum_notes.songs import FoundBar, Hit, Level, Mode
from backend.video_gen import kit
from backend.video_gen.kit import PieceId
from backend.video_gen.lessons import BPM_RANGE, Groove, Note
from backend.video_gen.timeline import STEPS_PER_BAR


LEVEL_RANK: dict[Level, int] = {"ghost": 0, "normal": 1, "accent": 2}
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


class Dropped(NamedTuple):
    """A hand note step 6 took out, as a third hand would be needed for it (video-gen D20)."""

    piece: PieceId
    step: int


class Scored(NamedTuple):
    """What the Score made of the bars picked: the Groove, its BPM, and the notes dropped."""

    groove: Groove
    bpm: int
    dropped: list[Dropped]


def preview(hits: list[Hit], bars: list[FoundBar], bpm: int | None, mode: Mode) -> Scored:
    """Score steps 3–8 over `bars`, the consecutive 4/4 bars the user picked: `bpm` is the
    default of step 3 when None; the hits quantized, put over the mode's base groove (step 5:
    nothing in drums mode, the app's kick and hi-hat in melody mode), trimmed to what two hands
    play, and handed."""
    placed = sorted(quantize(hits, bars) + BASE_GROOVES[mode](len(bars)), key=_kit_order)
    kept, dropped = trimmed(placed)
    groove = Groove(bars=len(bars), notes=with_hands(kept))
    return Scored(groove=groove, bpm=default_bpm(bars) if bpm is None else bpm, dropped=dropped)


def default_bpm(bars: list[FoundBar]) -> int:
    """Step 3: `240 / median(bar length)` rounded half up as the steps are (D25), within 40–240 (D20)."""
    median = statistics.median(bar.end_s - bar.start_s for bar in bars)
    return min(BPM_RANGE[1], max(BPM_RANGE[0], math.floor(4 * 60 / median + 0.5)))


def quantize(hits: list[Hit], bars: list[FoundBar]) -> list[Placed]:
    """Step 4: a hit belongs to bar `i` from half a step before its downbeat to half a step
    before the next, and lands on its nearest step, `16 × i` on; so a hit at the last bar's end,
    which would round up to one step past it, belongs to no bar and is left out; the same piece
    twice on a step keeps the loudest (D11, D20). In step order, then kit order."""
    kept: dict[tuple[str, int], Placed] = {}
    for index, bar in enumerate(bars):
        slot = (bar.end_s - bar.start_s) / STEPS_PER_BAR
        for hit in hits:
            if not bar.start_s - slot / 2 <= hit.t < bar.end_s - slot / 2:
                continue
            step = math.floor((hit.t - bar.start_s) / slot + 0.5) + STEPS_PER_BAR * index
            before = kept.get((hit.piece, step))
            if before is None or LEVEL_RANK[hit.level] > LEVEL_RANK[before.level]:
                kept[(hit.piece, step)] = Placed(kit.BY_ID[hit.piece].id, step, hit.level)  # a known piece: `songs.checked_analysis`
    return sorted(kept.values(), key=_kit_order)


def _kit_order(placed: Placed) -> tuple[int, int]:
    return placed.step, kit.PIECES.index(kit.BY_ID[placed.piece])


# Step 5 (D14): under the melody's snares, a kick on beats 1 and 3 and a closed hi-hat on every 8th.
BASE_KICK_STEPS = (0, 8)
BASE_HIHAT_STEPS = tuple(range(0, STEPS_PER_BAR, 2))


def base_groove(bars: int) -> list[Placed]:
    """The notes the app adds in melody mode over `bars` bars, all `normal` (D14)."""
    base = []
    for bar in range(bars):
        base.extend(Placed("kick", step + STEPS_PER_BAR * bar, "normal") for step in BASE_KICK_STEPS)
        base.extend(Placed("hihat_closed", step + STEPS_PER_BAR * bar, "normal") for step in BASE_HIHAT_STEPS)
    return base


# What each mode puts under the hits found, by the number of bars (D14): the drums mode's hits are the whole groove.
BASE_GROOVES: dict[Mode, Callable[[int], list[Placed]]] = {"drums": lambda bars: [], "melody": base_groove}


def trimmed(placed: list[Placed]) -> tuple[list[Placed], list[Dropped]]:
    """Step 6: on each step, an open hi-hat beside a closed one goes first, then hand notes past
    two by `KEEP_ORDER`; what went is listed as `dropped` in that order, step by step (D13, D20, D25)."""
    kept: list[Placed] = []
    dropped: list[Dropped] = []
    for step, feet, hands in _by_step(placed):
        if {"hihat_open", "hihat_closed"} <= {p.piece for p in hands}:
            hands = [p for p in hands if p.piece != "hihat_open"]
            dropped.append(Dropped("hihat_open", step))
        hands.sort(key=lambda p: KEEP_ORDER.index(p.piece))
        dropped.extend(Dropped(p.piece, step) for p in hands[2:])
        kept.extend(feet + hands[:2])
    return kept, dropped


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
