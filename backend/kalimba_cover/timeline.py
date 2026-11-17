"""A kalimba reel as every note it plays, in time (kalimba-cover spec › Timeline ของคาลิมบา, D6;
ADR 0041): the song's melody notes in the stretch arranged onto the tines (`arrange`), each rounded
to a sample at 44.1 kHz once, so the sound (`sound`) and the picture read them from one
`KalimbaTimeline` and never drift apart. The beats are numbered by `drum_cover.timeline`'s own
rule, and the picture's lesson is `drum_cover.timeline.lesson`. Pure numbers.
"""

from typing import NamedTuple

from backend.drum_cover import timeline as reel_timeline
from backend.drum_cover.cover import CoverFields
from backend.drum_notes.songs import Analysis, Level
from backend.kalimba_cover import arrange
from backend.video_gen import timeline
from backend.video_gen.timeline import Beat


class KalimbaNote(NamedTuple):
    """One tine struck: where it starts (a sample at `timeline.RATE`), the tine's index on screen
    (0–16, `arrange.TINE_PITCHES`), its pitch and its level."""

    at: int
    tine: int
    pitch: int
    level: Level


class KalimbaTimeline(NamedTuple):
    notes: tuple[KalimbaNote, ...]
    beats: tuple[Beat, ...]
    length_s: float
    changes: arrange.Changes

    @property
    def samples(self) -> int:
        """The clip's length in samples: the listen wav's and the render's sound."""
        return timeline.to_sample(self.length_s)


def build(analysis: Analysis, cover: CoverFields) -> KalimbaTimeline:
    """The stretch's arranged notes in sample, then tine order; the beats as the drum reel numbers
    them; the stretch and the tail long. A song picked before its notes were kept has none."""
    start, end = cover.start_s, cover.end_s
    arranged = arrange.arranged_in(analysis, start, end)
    notes = sorted(
        (KalimbaNote(timeline.to_sample(note.t - start), arrange.TINE_PITCHES.index(note.pitch), note.pitch, note.level) for note in arranged.notes),
        key=lambda note: (note.at, note.tine),
    )
    beats = tuple(Beat(timeline.to_sample(t - start), number) for t, number in reel_timeline.numbered_beats(analysis, start, end))
    return KalimbaTimeline(
        notes=tuple(notes),
        beats=beats,
        length_s=end - start + timeline.TAIL_S,
        changes=arranged.changes,
    )
