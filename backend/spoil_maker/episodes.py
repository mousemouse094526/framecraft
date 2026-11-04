"""A described Temp clip cut into EPs by time, at Shot edges: `media/temp/episodes/{id}.json`
(spoil-maker spec › EP, D66, D67, D69–D71). The file belongs to the Temp clip (ADR 0018):
deleting the clip deletes it, and a Describe job's new Shots remove it.

Every read-change-write of the file is under the GPU slot's lock, with the check that the
clip is still there and described (D71).
"""

import logging
import math
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from backend import files, gate_rows, gpu, spoil_maker
from backend.errors import ApiError, require_rows
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import clips, transcribe
from backend.spoil.transcribe import Transcript
from backend.spoil_maker import draft_file, script, settings, shots
from backend.spoil_maker.draft_file import Ep
from backend.spoil_maker.script import NumberedLine
from backend.spoil_maker.shots import ShotsFile

log = logging.getLogger(__name__)

MINUTES_MIN, MINUTES_MAX, MINUTES_STEP = 5, 60, 5  # D69
MIN_EP_SECONDS = 60  # when there are two EPs or more (D70, D71)
TOKEN_LIMIT = 32_000  # D46
# The jobs that read a clip's Shots or Transcript to make it or a draft: the cut can't change
# meanwhile (D71). A Voice or Render job reads the draft's own copy of its EP, so they may.
READERS: tuple[gpu.Kind, ...] = ("describe", "transcribe", "draft")


class Cuts(BaseModel):
    """The file's shape (spec › EP)."""

    minutes: int
    cuts: list[float]
    custom: bool


class Episode(Ep):
    thumb_shot: int  # the Shot that starts the EP
    lines: int
    tokens: int | None  # None without Qwen's tokenizer (D60, D71)
    renders: int
    in_draft: bool


class Episodes(BaseModel):
    """`GET /clips/{id}/episodes`."""

    clip_id: str
    minutes: int
    custom: bool
    episodes: list[Episode]
    limit: int = TOKEN_LIMIT


class Span(Ep):
    """One EP of the cut as it is now."""

    # A Transcript line may start after the last Shot ends (the clip's length): it is the last EP's.
    last: bool


def view(project: ProjectPaths, clip_id: str) -> Episodes:
    """The clip's cut with each EP's lines, tokens, renders and whether the Spoil draft is of it.
    Cuts the clip by `ep_minutes` the first time and keeps that (D71)."""
    minutes = _remembered_minutes(project)
    with gpu.slot.clip_files():
        shot_file, cuts = _current(project, clip_id, minutes)
    return _view(project, clip_id, shot_file, cuts)


def change(project: ProjectPaths, clip_id: str, body: dict) -> Episodes:
    """`PUT`: `{minutes}` cuts by length (`custom` false), `{minutes, cuts}` takes the user's
    cuts, each moved to the nearest Shot start (`custom` true). Raises `ApiError` 400
    `invalid_episodes`, or 409 `clip_busy` while a job reads the clip (D71)."""
    minutes = body.get("minutes")
    if not _is_minutes(minutes):
        raise invalid()
    with gpu.slot.clip_untouched(clip_id, by=READERS):
        found = _ready_shots(project, clip_id)
        if "cuts" in body:
            cuts = Cuts(minutes=minutes, cuts=_users_cuts(body["cuts"], found), custom=True)
        else:
            cuts = Cuts(minutes=minutes, cuts=cut_by_minutes(found, minutes), custom=False)
        old = _stored(project, clip_id, found)
        _write(project, clip_id, cuts)
    # After the slot's lock, which is always the innermost (`backend.gpu`).
    if old is None or old.minutes != minutes:
        settings.remember(project, ep_minutes=minutes)
    return _view(project, clip_id, found, cuts)


def span(project: ProjectPaths, clip_id: str, n: object) -> Span | None:
    """EP `n` of the clip's cut now, or None when there is no such EP. The clip must be described."""
    minutes = _remembered_minutes(project)
    with gpu.slot.clip_files():
        shot_file, cuts = _current(project, clip_id, minutes)
    spans = _spans(cuts.cuts, _length(shot_file))
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(spans):
        return None
    return spans[n - 1]


def lines_of(transcript: Transcript, ep: Span) -> list[NumberedLine]:
    """The EP's lines with their index in the whole Transcript: those that start in its range."""
    return [
        (index, line)
        for index, line in enumerate(transcript.lines)
        if ep.start_s <= line.start_s and (line.start_s < ep.end_s or ep.last)
    ]


def tokens(project: ProjectPaths, lines: Sequence[NumberedLine]) -> int:
    """How many tokens the lines are to Qwen, as the Draft job sends them. Raises
    `ApiError` 503 `not_ready` without Qwen's tokenizer (D60)."""
    require_rows(gate_rows.qwen_model(project))
    try:
        return spoil_maker.count_tokens(project.snapshot_dir(QWEN, QWEN.revision), script.transcript_block(lines))
    except OSError:
        # A marker without its snapshot, or with files transformers can't read: the install is broken the same way.
        raise ApiError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {QWEN.label}", rows=[QWEN.check_id]) from None


def cut_by_minutes(found: ShotsFile, minutes: int) -> list[float]:
    """Every `k × minutes` minutes before the clip's end, moved to the nearest Shot start;
    one that lands on another or on 0 goes, and a last EP shorter than a minute joins
    the one before (spec › EP)."""
    length = _length(found)
    cuts: list[float] = []
    for k in range(1, math.ceil(length / (minutes * 60))):
        at = _snap(k * minutes * 60, found)
        if at > 0 and at not in cuts:
            cuts.append(at)
    if cuts and length - cuts[-1] < MIN_EP_SECONDS:
        cuts.pop()
    return cuts


def remove(project: ProjectPaths, clip_id: str) -> None:
    """The clip's cut. A Describe job calls it under the slot's lock as it swaps in new Shots (D71)."""
    project.episodes_file(clip_id).unlink(missing_ok=True)


def clean_on_start(project: ProjectPaths, described_ids: set[str]) -> None:
    """Half-written files go, and so does the cut of a clip that is gone or not described (spec › Ops)."""
    if not project.episodes_dir.is_dir():
        return
    for path in project.episodes_dir.iterdir():
        if path.is_file() and (path.suffix == ".tmp" or path.name.removesuffix(".json") not in described_ids):
            path.unlink(missing_ok=True)


def _current(project: ProjectPaths, clip_id: str, minutes: int) -> tuple[ShotsFile, Cuts]:
    """The clip's Shots and cut, writing the cut by `minutes` when it has none. Call with
    the slot's lock held."""
    found = _ready_shots(project, clip_id)
    cuts = _stored(project, clip_id, found)
    if cuts is None:
        cuts = Cuts(minutes=minutes, cuts=cut_by_minutes(found, minutes), custom=False)
        _write(project, clip_id, cuts)
    return found, cuts


def _ready_shots(project: ProjectPaths, clip_id: str) -> ShotsFile:
    """Raises `ApiError` 404 `not_found` for an unknown clip, 400 `clip_not_ready` for one
    not transcribed or not described."""
    clips.check_known(project, clip_id)
    found = shots.read_shots(project, clip_id)
    if found is None or not found.shots or not clips.transcript_path(project, clip_id).is_file():
        raise not_ready(clip_id)
    return found


def not_ready(clip_id: object) -> ApiError:
    """`clip_not_ready`: the clip must be transcribed and described to cut or draft from (D16)."""
    return ApiError(400, "clip_not_ready", "คลิปนี้ยังไม่ได้ถอดบทพูดหรือบรรยายฉาก", clip_ids=[clip_id])


def is_number(value: object) -> bool:
    """An int or float that is not a boolean: JSON `true` is an int to Python."""
    return isinstance(value, int | float) and not isinstance(value, bool)


def _stored(project: ProjectPaths, clip_id: str, found: ShotsFile) -> Cuts | None:
    """The file, or None when there is none or it breaks the `PUT` rules (D71)."""
    path = project.episodes_file(clip_id)
    if not path.is_file():
        return None
    try:
        cuts = Cuts.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        log.warning("cutting %s again: its EP file can't be read", clip_id)
        return None
    starts = {shot.start for shot in found.shots}
    if not _is_minutes(cuts.minutes) or not all(cut in starts for cut in cuts.cuts) or not _allowed(cuts.cuts, found):
        log.warning("cutting %s again: its EP file doesn't fit its Shots", clip_id)
        return None
    return cuts


def _write(project: ProjectPaths, clip_id: str, cuts: Cuts) -> None:
    project.episodes_dir.mkdir(parents=True, exist_ok=True)
    # Its own `.tmp` name, so a writer never renames another's half-written file (D71).
    files.write_atomic(project.episodes_file(clip_id), cuts.model_dump_json(), unique=True)


def _users_cuts(value: object, found: ShotsFile) -> list[float]:
    """Finite numbers, at most one a minute of the clip, each moved to the nearest Shot start;
    then they must go up, inside the clip, and leave every EP a minute or more."""
    length = _length(found)
    if not isinstance(value, list) or len(value) > math.floor(length / MIN_EP_SECONDS):
        raise invalid()
    if not all(is_number(at) and math.isfinite(at) for at in value):
        raise invalid()
    cuts = [_snap(at, found) for at in value]
    if not _allowed(cuts, found):
        raise invalid()
    return cuts


def _allowed(cuts: list[float], found: ShotsFile) -> bool:
    """One EP is always allowed; with more, each is a minute or more (D71)."""
    edges = [0.0, *cuts, _length(found)]
    if any(later <= earlier for earlier, later in zip(edges, edges[1:])):
        return False
    return not cuts or all(later - earlier >= MIN_EP_SECONDS for earlier, later in zip(edges, edges[1:]))


def _snap(at: float, found: ShotsFile) -> float:
    """The start of the Shot nearest `at`; a tie goes to the earlier Shot."""
    return min((shot.start for shot in found.shots), key=lambda start: (abs(start - at), start))


def _length(found: ShotsFile) -> float:
    return found.shots[-1].end  # D71


def _spans(cuts: list[float], length: float) -> list[Span]:
    """EP `n` is [`cuts[n-2]` or 0, `cuts[n-1]` or the length): open at the end."""
    edges = [0.0, *cuts, length]
    last = len(edges) - 1
    return [Span(n=n, start_s=edges[n - 1], end_s=edges[n], last=n == last) for n in range(1, last + 1)]


def _view(project: ProjectPaths, clip_id: str, found: ShotsFile, cuts: Cuts) -> Episodes:
    # render → draft → episodes, so render can't be imported at the top.
    from backend.spoil_maker import render

    transcript = transcribe.read_transcript(project, clip_id)
    rendered = [result for result in render.list_results(project) if result.clip_id == clip_id]
    drafted = draft_file.read(project)
    shot_at = {shot.start: shot.n for shot in found.shots}
    episodes = []
    for ep in _spans(cuts.cuts, _length(found)):
        lines = lines_of(transcript, ep)
        try:
            counted = tokens(project, lines)
        except ApiError:
            counted = None  # the page shows `not_ready` on the draft button, not on the whole list (D71)
        episodes.append(
            Episode(
                n=ep.n,
                start_s=ep.start_s,
                end_s=ep.end_s,
                thumb_shot=shot_at.get(ep.start_s, found.shots[0].n),
                lines=len(lines),
                tokens=counted,
                renders=sum(1 for result in rendered if ep.matches(result.start_s, result.end_s)),
                in_draft=drafted is not None
                and drafted.clip_id == clip_id
                and ep.matches(drafted.ep.start_s, drafted.ep.end_s),
            )
        )
    return Episodes(clip_id=clip_id, minutes=cuts.minutes, custom=cuts.custom, episodes=episodes)


def _remembered_minutes(project: ProjectPaths) -> int:
    """`ep_minutes` from settings; one edited by hand outside 5–60 in fives reads as 30."""
    minutes = settings.read(project).ep_minutes
    return minutes if _is_minutes(minutes) else settings.Settings().ep_minutes


def _is_minutes(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and MINUTES_MIN <= value <= MINUTES_MAX
        and value % MINUTES_STEP == 0
    )


def invalid() -> ApiError:
    return ApiError(400, "invalid_episodes", "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา")
