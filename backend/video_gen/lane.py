"""The note lanes' window in time (video-gen spec › Layout, D13): the playhead stands still at
x 250 and the notes slide past it, the lanes as wide as 1.5 bars at the playing chapter's speed.
`frames` draws the note heads and beat lines where this puts them, and `captions` moves the beat
numbers the same way, so the two never part. Times are read from `timeline` (ADR 0041)."""

from typing import TYPE_CHECKING, NamedTuple

from backend.video_gen import timeline
from backend.video_gen.timeline import Timeline

if TYPE_CHECKING:
    from backend.video_gen.lessons import Lesson

LEFT, RIGHT = 54, 1026
TOP, BOTTOM = 1245, 1575
PLAYHEAD_X = 250
WINDOW_BARS = 1.5
LANE_Y = {"cymbals": 1330, "middle": 1420, "bottom": 1510}


class Segment(NamedTuple):
    """A stretch of the clip whose lanes scroll at one speed: the count-in and each chapter,
    then the tail, where the lanes hold still at `frozen_at` (D21)."""

    start_s: float
    end_s: float
    px_per_s: float
    chapter_index: int  # the chapter whose kit shows: the first through the count-in, the last through the tail
    frozen_at: float | None = None


def segments(lesson: "Lesson", timing: Timeline) -> list[Segment]:
    def px_per_s(speed: int) -> float:
        return (RIGHT - LEFT) / (WINDOW_BARS * timeline.BEATS_PER_BAR * timeline.beat_s(lesson.bpm, speed))

    spans = [(span.start / timeline.RATE, span.end / timeline.RATE) for span in timing.chapters]
    found = [Segment(0.0, spans[0][0], px_per_s(lesson.chapters[0].speed), chapter_index=0)]
    found += [
        Segment(start, end, px_per_s(c.speed), chapter_index=index)
        for index, ((start, end), c) in enumerate(zip(spans, lesson.chapters, strict=True))
    ]
    last_end = spans[-1][1]
    found.append(Segment(last_end, timing.length_s, found[-1].px_per_s, chapter_index=len(spans) - 1, frozen_at=last_end))
    return found


def segment_at(found: list[Segment], t: float) -> Segment:
    """The segment playing at `t`; past the end, the tail."""
    return next((segment for segment in found if t < segment.end_s), found[-1])


def x_of(at_s: float, t: float, segment: Segment) -> float:
    """Where something at `at_s` sits at time `t`: on the playhead when `t` reaches it."""
    now = segment.frozen_at if segment.frozen_at is not None else t
    return PLAYHEAD_X + (at_s - now) * segment.px_per_s
