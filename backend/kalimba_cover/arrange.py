"""A song's melody notes laid on a 17-tine kalimba tuned to C major, C4–E6 (kalimba-cover spec ›
การจัดโน้ตลงคาลิมบา, D4, D14): the bass dropped, the whole stretch moved by the key that puts the
most notes in the scale, the rest bent down a semitone into it, a chord's top note kept, and every
note folded by octaves onto the tines. Pure numbers, the same every time; `analysis.notes` is
never changed.

Imports only `drum_notes.songs`, so `drum_cover.cover` can call it (D8, D14).
"""

from typing import NamedTuple

from backend.drum_notes.songs import Analysis, Note

# The tines' pitches from left to right on screen, index 0–16 (spec › การจัดโน้ตลงคาลิมบา).
TINE_PITCHES = (86, 83, 79, 76, 72, 69, 65, 62, 60, 64, 67, 71, 74, 77, 81, 84, 88)
LOWEST, HIGHEST = min(TINE_PITCHES), max(TINE_PITCHES)  # C4, E6
BASS_BELOW = 48  # C3: lower is the bass, dropped first (D14)
SCALE = frozenset({0, 2, 4, 5, 7, 9, 11})  # C major's pitch classes
TRANSPOSES = range(-6, 6)  # the semitones the whole stretch may move
TOGETHER_S = 0.03  # notes this close to a chord's first are one chord
REPEAT_S = 0.08  # one tine played again this soon after is dropped


class Changes(NamedTuple):
    """What the arranging did to the song, as the reel page tells it (D9): the semitones the key
    moved, the notes dropped and the notes bent into the scale."""

    transpose: int
    dropped: int
    bent: int


class Arranged(NamedTuple):
    """The notes the kalimba plays, at their own times and levels with the tines' pitches, and
    what the arranging changed."""

    notes: list[Note]
    changes: Changes


class _Scaled(NamedTuple):
    """A melody note moved by the key and, when off the scale, bent down into it (steps 2–3)."""

    note: Note
    pitch: int
    bent: bool


def arranged_in(analysis: Analysis, start_s: float, end_s: float) -> Arranged:
    """The kalimba's notes of a song's stretch; none for a song picked before notes were kept."""
    return arranged(analysis.notes or [], start_s, end_s)


def arranged(notes: list[Note], start_s: float, end_s: float) -> Arranged:
    """Spec › การจัดโน้ตลงคาลิมบา steps 1–7, over the notes with `start_s ≤ t < end_s`."""
    inside = sorted((note for note in notes if start_s <= note.t < end_s), key=lambda note: (note.t, note.pitch))
    melody = [note for note in inside if note.pitch >= BASS_BELOW]
    dropped = len(inside) - len(melody)
    transpose = _transpose(melody)
    moved = [(note, note.pitch + transpose) for note in melody]
    in_scale = [_Scaled(note, pitch if pitch % 12 in SCALE else pitch - 1, pitch % 12 not in SCALE) for note, pitch in moved]
    tops = _tops(in_scale)
    dropped += len(in_scale) - len(tops)
    kept: list[Note] = []
    bent = 0
    last_on: dict[int, float] = {}
    for note, pitch, was_bent in tops:
        tine = _folded(pitch)
        if tine in last_on and note.t - last_on[tine] < REPEAT_S:
            dropped += 1
            continue
        last_on[tine] = note.t
        kept.append(Note(t=note.t, pitch=tine, level=note.level))
        bent += was_bent
    return Arranged(notes=kept, changes=Changes(transpose=transpose, dropped=dropped, bent=bent))


def _transpose(melody: list[Note]) -> int:
    """Step 2: the move that puts the most notes in the scale; a tie moves least, then up."""
    if not melody:
        return 0
    return max(TRANSPOSES, key=lambda k: (sum((note.pitch + k) % 12 in SCALE for note in melody), -abs(k), k))


def _tops(in_scale: list[_Scaled]) -> list[_Scaled]:
    """Step 4: of each chord (notes within 30 ms of its first) the highest, before folding; a tie
    keeps the earlier. `in_scale` is in time order, so each chord's first comes first."""
    tops = []
    chord: list[_Scaled] = []
    for item in in_scale:
        if chord and item.note.t - chord[0].note.t > TOGETHER_S:
            tops.append(_top(chord))
            chord = []
        chord.append(item)
    if chord:
        tops.append(_top(chord))
    return tops


def _top(chord: list[_Scaled]) -> _Scaled:
    return max(chord, key=lambda item: item.pitch)  # `max` keeps the first of a tie: the earlier


def _folded(pitch: int) -> int:
    """Step 5: up or down by octaves until on the kalimba."""
    while pitch < LOWEST:
        pitch += 12
    while pitch > HIGHEST:
        pitch -= 12
    return pitch
