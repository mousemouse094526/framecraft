"""A drum lesson from a song (drum-notes spec › Score steps 2–8 and API; D11, D12, D13, D21;
ADR 0044): the user picks consecutive 4/4 bars of what was found and a BPM; `preview` shows the
Groove the Score makes of them, `listen` mixes it through video-gen's timeline and mixer from a
lesson that is nowhere on disk, and `create` writes it through `video_gen.lessons` with the rules
of `PUT`, then the song remembers the lesson's id. `songs.lock` is never held while
`video_gen.lessons` works (fastapi-api › lock order: it is innermost).
"""

from typing import NamedTuple

from pydantic import BaseModel

from backend import gate_rows, json_values
from backend.drum_notes import score, songs
from backend.drum_notes.songs import FoundBar, Song
from backend.errors import ApiError, invalid_request, require_rows
from backend.paths import ProjectPaths
from backend.video_gen import lessons, mixer, timeline
from backend.video_gen.lessons import BARS_RANGE, BPM_RANGE, LessonFields

NO_ANALYSIS = "ยังไม่ได้แกะโน้ต ตั้งช่วงแล้วกด แกะโน้ต"
# Said for a bar that isn't 4/4 and for a pick that runs past the last bar alike (ticket 03 › Score):
# the page only offers counts that fit, so the second case is a stale page's.
NOT_FOUR_FOUR = "ห้องนี้ไม่ใช่ 4/4"


class Choice(NamedTuple):
    """What the body of the three routes says: the first bar (from 0), how many, and the BPM
    (None: the Score's default, which only `preview` allows). Not the Pick job (`drum_notes.pick`),
    which finds the bars this chooses from."""

    bar: int
    bars: int
    bpm: int | None


class DroppedNote(BaseModel):
    piece: str
    step: int


class Preview(BaseModel):
    """What `POST /preview` answers: the Groove, its BPM, and the notes dropped (spec › API)."""

    groove: lessons.Groove
    bpm: int
    dropped: list[DroppedNote]


class Created(BaseModel):
    """What `POST /lessons` answers: the new lesson's id and how many notes the Score dropped (D20)."""

    lesson_id: str
    dropped: int


def preview(project: ProjectPaths, song_id: str, body: dict) -> Preview:
    """`POST /preview`. Raises `ApiError` 404, 409 `no_analysis`, or 400 `invalid_request` with its field."""
    choice = checked_choice(body, bpm_optional=True)
    scored = _scored(songs.get(project, song_id), choice)
    return Preview(groove=scored.groove, bpm=scored.bpm, dropped=[DroppedNote(piece=d.piece, step=d.step) for d in scored.dropped])


def listen(project: ProjectPaths, song_id: str, body: dict) -> bytes:
    """`POST /listen`: the wav of the chosen Groove as a new lesson would play it (D21). Raises
    `ApiError` 503 `not_ready` without the drum samples first, then as `preview`, then 422 `too_long`."""
    require_rows(gate_rows.drum_kit_row(project))
    _, fields = _lesson_fields(project, song_id, body)
    lesson = lessons.unsaved(fields)
    lessons.require_short(lesson)
    return mixer.mix(project, timeline.build(lesson))


def create(project: ProjectPaths, song_id: str, body: dict) -> Created:
    """`POST /lessons`: the lesson written through `video_gen.lessons` (D12), its id added to the
    song's `lessons`. Raises `ApiError` as `preview` does; a song that went meanwhile takes the
    new lesson with it, so none is left that no song lists (the lesson is seconds old, so it has
    no render and no job that could stop the delete)."""
    scored, fields = _lesson_fields(project, song_id, body)
    lesson = lessons.create_from(project, fields)
    try:
        songs.add_lesson(project, song_id, lesson.id)
    except ApiError:
        lessons.delete(project, lesson.id)
        raise
    return Created(lesson_id=lesson.id, dropped=len(scored.dropped))


def checked_choice(body: dict, bpm_optional: bool) -> Choice:
    """`bar` an int from 0, `bars` 1–4, `bpm` 40–240 (or left out when `bpm_optional`); anything
    else raises 400 `invalid_request`, with the field when the value is a number out of range.
    Whether the bars exist and are 4/4 is `chosen_bars`' to say."""
    bar, bars, bpm = body.get("bar"), body.get("bars"), body.get("bpm")
    if not json_values.is_int(bar) or bar < 0:
        raise invalid_request()
    if not json_values.is_int(bars) or not BARS_RANGE[0] <= bars <= BARS_RANGE[1]:
        raise songs.invalid("bars", f"จำนวนห้องต้องเป็นจำนวนเต็ม {BARS_RANGE[0]}–{BARS_RANGE[1]}")
    if bpm is None and bpm_optional:
        return Choice(bar, bars, None)
    if not json_values.is_int(bpm) or not BPM_RANGE[0] <= bpm <= BPM_RANGE[1]:
        raise songs.invalid("bpm", f"BPM ต้องเป็นจำนวนเต็ม {BPM_RANGE[0]}–{BPM_RANGE[1]}")
    return Choice(bar, bars, bpm)


def chosen_bars(song: Song, choice: Choice) -> list[FoundBar]:
    """Score step 2: the `choice.bars` bars found from `choice.bar`, each 4/4. Raises 409 `no_analysis`
    for a song not picked yet, or 400 at field `bar` when a bar is past the last or not 4/4 (D20)."""
    if song.analysis is None:
        raise ApiError(409, "no_analysis", NO_ANALYSIS)
    found = songs.bars_of(song.analysis)
    chosen = found[choice.bar : choice.bar + choice.bars]
    if len(chosen) < choice.bars or not all(bar.four_four for bar in chosen):
        raise songs.invalid("bar", NOT_FOUR_FOUR)
    return chosen


def _lesson_fields(project: ProjectPaths, song_id: str, body: dict) -> tuple[score.Scored, LessonFields]:
    """What `listen` and `create` share: the body checked with its BPM, the song scored, and the
    fields of the lesson that would make (`lessons.from_song`)."""
    choice = checked_choice(body, bpm_optional=False)
    song = songs.get(project, song_id)
    scored = _scored(song, choice)
    return scored, lessons.from_song(song.title, song.subtitle, scored.bpm, scored.groove)


def _scored(song: Song, choice: Choice) -> score.Scored:
    chosen = chosen_bars(song, choice)
    assert song.analysis is not None  # `chosen_bars` raised otherwise
    return score.preview(song.analysis.hits, chosen, choice.bpm)
