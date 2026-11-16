"""A reel cover as every hit it plays, in time (drum-cover spec › Timeline ของ reel, D3, D4, D5,
D21; ADR 0051): the hits found in the stretch at their real times, never quantized, through
`video_gen.timeline.assemble`, so the sound (`mixer`) and the picture (`frames`, `captions`) read
them from one `Timeline` as a lesson's do (ADR 0041). The hands alone come from steps: each hit is
put on its nearest 16th of its bar for drum-notes' sticking rules (`groove.trimmed`, `with_hands`),
which never moves it in time. Pure numbers: tests build an analysis by hand (D13).

The picture and text also want a lesson: `lesson` makes an unsaved one of one chapter with no
label and no focus, whose BPM only sets how fast the lanes scroll (D4).
"""

import math
import statistics

from backend.drum_cover.cover import CoverFields
from backend.drum_notes import groove
from backend.drum_notes.groove import Placed
from backend.drum_notes.songs import Analysis, Hit
from backend.video_gen import kit, lessons, timeline
from backend.video_gen.lessons import Chapter, Groove, Lesson, LessonFields
from backend.video_gen.timeline import Beat, Sound, Span, Timeline

FALLBACK_BAR_S = 2.0  # an analysis written with fewer than two downbeats (D21)
FALLBACK_BPM = 120
# A hit's velocity layer and note head by its level (D3, video-gen D13).
SHOWN = {"accent": ("hard", "accent"), "normal": ("mid", "normal"), "ghost": ("soft", "ghost")}


def build(analysis: Analysis, cover: CoverFields) -> Timeline:
    """Spec › Timeline ของ reel steps 1–6."""
    start, end = cover.start_s, cover.end_s
    found = sorted((hit for hit in analysis.hits if start <= hit.t < end), key=lambda hit: hit.t)
    hands = _hands(found, analysis.downbeats, start)
    sounds: list[Sound] = []
    for index, hit in enumerate(found):
        layer, note = SHOWN[hit.level]
        sounds.append((hit.t - start, hit.piece, hands[index], layer, note))
    beats = [Beat(timeline.to_sample(t - start), number) for t, number in numbered_beats(analysis, start, end)]
    spans = [Span(0, timeline.to_sample(end - start))]
    return timeline.assemble(sounds, beats, spans, end - start + timeline.TAIL_S)


def lesson(analysis: Analysis, cover: CoverFields) -> Lesson:
    """The unsaved lesson `frames` and `captions` draw from (step 7): the cover's texts and
    background, one chapter with no label, no focus and no count-in's speed change."""
    fields = LessonFields(
        title=cover.title,
        subtitle=cover.subtitle,
        caption=cover.caption,
        bpm=scroll_bpm(analysis, cover),
        background=cover.background,
        groove=Groove(bars=1, notes=[]),
        chapters=[Chapter(label="", text="", focus=[], repeats=1, speed=100)],
    )
    return lessons.unsaved(fields)


def scroll_bpm(analysis: Analysis, cover: CoverFields) -> int:
    """`60 / median beat gap` in the stretch, within 40–240; fewer than two beats: 120."""
    beats = [t for t in analysis.beats if cover.start_s <= t < cover.end_s]
    if len(beats) < 2:
        return FALLBACK_BPM
    gap = statistics.median(b - a for a, b in zip(beats, beats[1:]))
    return min(lessons.BPM_RANGE[1], max(lessons.BPM_RANGE[0], round(60 / gap)))


# --- the beats ---


def numbered_beats(analysis: Analysis, start: float, end: float) -> list[tuple[float, int]]:
    """Step 5: each beat in the stretch numbered from the downbeat before it (1 on a downbeat);
    one before every downbeat counts back from the first bar's number of beats, at least 1 (D3, D6)."""
    numbered = []
    downbeats = analysis.downbeats
    for t in analysis.beats:
        if not start <= t < end:
            continue
        before = [d for d in downbeats if d <= t]
        if before:
            number = sum(1 for b in analysis.beats if before[-1] <= b <= t)
        elif downbeats:
            # Back from the first bar's own count: a 3-beat first bar makes the beat before it 3.
            first_bar = sum(1 for b in analysis.beats if downbeats[0] <= b < downbeats[1]) if len(downbeats) > 1 else timeline.BEATS_PER_BAR
            ahead = sum(1 for b in analysis.beats if t < b < downbeats[0])
            number = max(1, first_bar - ahead)
        else:
            number = 1
        numbered.append((t, number))
    return numbered


# --- the hands ---


def _bars(downbeats: list[float], start: float) -> list[tuple[float, float]]:
    """The bars of the whole analysis, by their start and length (D21); fewer than two downbeats:
    2 s bars from the stretch's start."""
    if len(downbeats) < 2:
        return [(start, FALLBACK_BAR_S)]
    return [(a, b - a) for a, b in zip(downbeats, downbeats[1:])]


def _step(t: float, bars: list[tuple[float, float]]) -> int:
    """Step 3: the nearest 16th of the hit's bar, 16 a bar on from the first; before the first bar
    the first bar's length counts back, after the last the last bar's goes on."""
    first_start, first_length = bars[0]
    if t < first_start:
        return math.floor((t - first_start) / (first_length / timeline.STEPS_PER_BAR) + 0.5)
    for index, (bar_start, length) in enumerate(bars):
        if t < bar_start + length or index == len(bars) - 1:
            return math.floor((t - bar_start) / (length / timeline.STEPS_PER_BAR) + 0.5) + timeline.STEPS_PER_BAR * index
    raise AssertionError("unreachable")


def _hands(found: list[Hit], downbeats: list[float], start: float) -> list[str | None]:
    """Step 4: the hand of each hit, in the order of `found`. A piece hit twice on one step: the
    first is placed, the next has no stick; a hand note `trimmed` takes out has no stick either;
    feet never have one. All still sound and show their note head (D5)."""
    bars = _bars(downbeats, start)
    keys = [(hit.piece, _step(hit.t, bars)) for hit in found]
    first_on_step: dict[tuple[str, int], int] = {}
    for index, key in enumerate(keys):
        first_on_step.setdefault(key, index)
    placed = sorted(
        (Placed(kit.BY_ID[piece].id, step, found[index].level) for (piece, step), index in first_on_step.items()),
        key=lambda p: (p.step, kit.PIECES.index(kit.BY_ID[p.piece])),
    )
    kept, _ = groove.trimmed(placed)
    hand_of = {(note.piece, note.step): note.hand for note in groove.with_hands(kept)}
    return [hand_of.get(key) if first_on_step[key] == index else None for index, key in enumerate(keys)]
