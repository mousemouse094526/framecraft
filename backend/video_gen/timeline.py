"""A drum lesson as every hit it plays, in time (video-gen spec › Timeline and audio, ADR 0041):
the one place a note's time is worked out. The sound (`mixer`) and the picture read it from
here, rounded to a sample at 44.1 kHz once, so they never drift apart (D14, D19)."""

from typing import TYPE_CHECKING, Literal, NamedTuple

from backend import drum_kit
from backend.drum_kit import Layer
from backend.video_gen import kit

if TYPE_CHECKING:
    from backend.video_gen.lessons import Chapter, Lesson

RATE = 44_100
STEPS_PER_BAR = 16
BEATS_PER_BAR = 4
TAIL_S = 1.5  # the last cymbal rings out (D21)
FLAM_GAP_S = 0.03  # the grace note comes this long before the main one (D13)
# A note's velocity layer by its hit; a flam's main note is `mid`, its grace note `soft` (D13).
LAYER_OF_HIT: dict[str, Layer] = {"accent": "hard", "normal": "mid", "ghost": "soft", "flam": "mid"}
COUNT_IN_PIECE = "hihat_closed"
OTHER_HAND = {"R": "L", "L": "R"}
# What a hit is on screen: a count-in tick (no note head, no stick), a flam's grace note, or a note by its hit.
NoteKind = Literal["count", "grace", "normal", "accent", "ghost", "flam"]


class Hit(NamedTuple):
    """One sample played: where it starts (a sample at RATE), the piece, the hand that plays it
    (None for a foot and the count-in), its velocity layer and round-robin (1 up), and what it
    is on screen."""

    at: int
    piece: str
    hand: str | None
    layer: Layer
    round_robin: int
    note: NoteKind


class Beat(NamedTuple):
    """A beat starting at sample `at`: the count-in's and every bar's, numbered 1–4 (D13)."""

    at: int
    number: int


class Span(NamedTuple):
    """Where a chapter plays, from sample `start` up to `end`."""

    start: int
    end: int


class Timeline(NamedTuple):
    hits: tuple[Hit, ...]
    beats: tuple[Beat, ...]
    chapters: tuple[Span, ...]
    length_s: float

    @property
    def samples(self) -> int:
        """The clip's length in samples: the listen wav's and the render's sound."""
        return to_sample(self.length_s)


def to_sample(seconds: float) -> int:
    return round(seconds * RATE)


def beat_s(bpm: int, speed: int) -> float:
    """A beat at a chapter's speed (50–100 % of the lesson's BPM)."""
    return 60 / (bpm * speed / 100)


def length_s(bpm: int, bars: int, chapters: "list[Chapter]") -> float:
    """Count-in, every chapter, and the tail (spec › Data, D21): what the 90 s cap, the wav,
    the frame count and the disk estimate all use."""
    count_in = BEATS_PER_BAR * beat_s(bpm, chapters[0].speed)
    chapters_s = sum(c.repeats * bars * BEATS_PER_BAR * beat_s(bpm, c.speed) for c in chapters)
    return count_in + chapters_s + TAIL_S


def build(lesson: "Lesson") -> Timeline:
    """Every hit, beat and chapter span of the lesson, in time order (spec › Timeline and audio)."""
    sounds: list[tuple[float, str, str | None, Layer, NoteKind]] = []
    beats: list[Beat] = []
    spans: list[Span] = []

    count_in_beat = beat_s(lesson.bpm, lesson.chapters[0].speed)
    for number in range(BEATS_PER_BAR):
        sounds.append((number * count_in_beat, COUNT_IN_PIECE, None, "soft", "count"))
        beats.append(Beat(to_sample(number * count_in_beat), number + 1))

    start = BEATS_PER_BAR * count_in_beat
    notes = sorted(lesson.groove.notes, key=lambda n: n.step)
    for chapter in lesson.chapters:
        beat = beat_s(lesson.bpm, chapter.speed)
        chapter_start = start
        for _ in range(chapter.repeats):
            for bar in range(lesson.groove.bars):
                bar_start = start + bar * BEATS_PER_BAR * beat
                for number in range(BEATS_PER_BAR):
                    beats.append(Beat(to_sample(bar_start + number * beat), number + 1))
            for note in notes:
                at = start + note.step * beat / 4
                if note.hit == "flam":
                    sounds.append((at - FLAM_GAP_S, note.piece, OTHER_HAND[note.hand], "soft", "grace"))
                sounds.append((at, note.piece, note.hand, LAYER_OF_HIT[note.hit], note.hit))
            start += lesson.groove.bars * BEATS_PER_BAR * beat
        spans.append(Span(to_sample(chapter_start), to_sample(start)))

    return Timeline(
        hits=_with_round_robins(sounds),
        beats=tuple(beats),
        chapters=tuple(spans),
        length_s=length_s(lesson.bpm, lesson.groove.bars, lesson.chapters),
    )


def _with_round_robins(sounds: list[tuple[float, str, str | None, Layer, NoteKind]]) -> tuple[Hit, ...]:
    """Each piece and layer cycles through its round-robins in the order it is hit from the
    clip's start, so a render of the same lesson mixes the same wav (D13). Hits on the same
    sample go in kit order, so the order never depends on how the notes were listed."""
    order = {piece.id: index for index, piece in enumerate(kit.PIECES)}
    timed = sorted(((to_sample(t), *rest) for t, *rest in sounds), key=lambda h: (h[0], order[h[1]]))
    counts: dict[tuple[str, Layer], int] = {}
    for sample in drum_kit.SAMPLES:
        counts[(sample.piece, sample.layer)] = counts.get((sample.piece, sample.layer), 0) + 1
    seen: dict[tuple[str, Layer], int] = {}
    hits = []
    for at, piece, hand, layer, note in timed:
        nth = seen.get((piece, layer), 0)
        seen[(piece, layer)] = nth + 1
        hits.append(Hit(at, piece, hand, layer, nth % counts[(piece, layer)] + 1, note))
    return tuple(hits)
