"""The one Spoil draft on disk: `media/spoil-maker/draft.json`, written through `.tmp`
on every change, and a `{sentence_id}.wav` per voiced sentence in `draft-audio/`
(spoil-maker spec › Spoil draft, D28).

Knows no job and no Transcript, so `backend.spoil` asks it whether a clip is in the
draft and drops the draft when that clip changes (D29, D49). Callers that read,
change and write it hold `gpu.slot.draft_lock` (D51).
"""

import logging
import shutil
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from backend import files, gpu
from backend.errors import ApiError
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

Style = Literal["fast", "drama", "chrono"]
Layout = Literal["A", "B", "C"]


class Ref(BaseModel):
    """A Transcript line the sentence tells about: `line` is its index in that clip's Transcript."""

    clip_id: str
    line: int


class ShotRef(BaseModel):
    clip_id: str
    n: int


class Audio(BaseModel):
    """What the sentence's wav was made from: the text after numbers became words, and the voice."""

    tts_text: str
    voice_id: str
    duration_s: float


class Sentence(BaseModel):
    id: str
    text: str
    refs: list[Ref]
    shots: list[ShotRef | None] = Field(min_length=2, max_length=2)  # an empty one is null
    audio: Audio | None = None


class Draft(BaseModel):
    """The file's shape is part of the decision (spec › Spoil draft)."""

    version: Literal[1] = 1
    clip_ids: list[str]
    style: Style
    layout: Layout
    target_s: int
    voice_id: str
    original_volume: int
    top_text: str
    sentences: list[Sentence]


def read(project: ProjectPaths) -> Draft | None:
    """The Spoil draft, or None when there is none: no file, a file that can't be read,
    another `version`, or one that names a Temp clip that is gone (spec › Spoil draft)."""
    draft = _stored(project)
    if draft is None:
        return None
    missing = [clip_id for clip_id in draft.clip_ids if not project.clip_json(clip_id).is_file()]
    if missing:
        log.warning("no Spoil draft: its clips %s are gone", ", ".join(missing))
        return None
    return draft


def _stored(project: ProjectPaths) -> Draft | None:
    """The file as it is, whether its clips are there or not."""
    path = project.draft_file
    if not path.is_file():
        return None
    try:
        return Draft.model_validate_json(path.read_bytes())
    except (OSError, ValidationError) as error:
        log.warning("no Spoil draft: %s can't be read (%s)", path.name, type(error).__name__)
        return None


def write(project: ProjectPaths, draft: Draft) -> None:
    project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
    files.write_atomic(project.draft_file, draft.model_dump_json(indent=2))


def remove(project: ProjectPaths) -> None:
    """The draft and its voice."""
    project.draft_file.unlink(missing_ok=True)
    remove_audio(project)


def remove_audio(project: ProjectPaths) -> None:
    """Every sentence's wav. One Windows still holds open goes with the next draft."""
    shutil.rmtree(project.draft_audio_dir, ignore_errors=True)


def clip_ids(project: ProjectPaths) -> set[str]:
    """The Temp clips the Spoil draft is made from; none without a draft."""
    draft = read(project)
    return set(draft.clip_ids) if draft else set()


def uses_clip(project: ProjectPaths, clip_id: str) -> bool:
    return clip_id in clip_ids(project)


def uses_voice(project: ProjectPaths, voice_id: str) -> bool:
    draft = read(project)
    return draft is not None and draft.voice_id == voice_id


def drop_if_uses(project: ProjectPaths, clip_id: str) -> None:
    """Removes the Spoil draft when it is made from `clip_id`: that clip was deleted,
    or its new Transcript or Shots make the draft's line and Shot numbers point
    elsewhere (D29, D49)."""
    with gpu.slot.draft_lock:
        stored = _stored(project)  # a deleted clip is gone already, so `read` would find no draft
        if stored is not None and clip_id in stored.clip_ids:
            remove(project)
            log.info("removed the Spoil draft: its clip %s changed", clip_id)


def take_gpu_to_redo(project: ProjectPaths, clip_id: str, kind: gpu.Kind, confirm_draft_loss: bool) -> None:
    """Takes the GPU for a job that makes a clip's Transcript or Shots again. Raises
    `ApiError` 409 `in_draft` first when the Spoil draft is made from that clip and the
    user hasn't confirmed losing it (D49); under the draft's lock, so no draft appears
    between the check and the start."""
    with gpu.slot.draft_lock:
        if not confirm_draft_loss and uses_clip(project, clip_id):
            raise ApiError(409, "in_draft", "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft")
        gpu.slot.take(kind, [clip_id])
