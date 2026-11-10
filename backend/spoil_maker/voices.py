"""Saved voices and the Voice job: one at a time, a backend thread that owns the state
and every file, and a child process that runs OmniVoice (ADR 0010, ADR 0012, ADR 0015).

Rules are in docs/features/spoil-maker/spec.md › Saved voice and › Voice job
(D30, D32, D35, D36, D37, D43, D48). `SentenceVoicer` voices the Spoil draft's
sentences for the Voice job `sentences` and the Render job's `voicing` alike.
"""

import json
import logging
import os
import re
import secrets
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel

from backend import checks, files, gate_rows, gpu, paths
from backend.errors import ApiError, Row, require_rows
from backend.jobs import Job
from backend.models import OMNIVOICE
from backend.speaking import NUM_STEP, Speaker, wav_seconds, write_wav
from backend.paths import ProjectPaths
from backend.spoil_maker import draft_file, thai
from backend.spoil_maker.draft_file import Audio, Draft
from backend.json_values import is_number
from backend.spoil_maker.tts import Design, Designed, Spoken, WorkerError

log = logging.getLogger(__name__)

# The choices OmniVoice's `instruct` understands (spec › Saved voice step 1).
GENDERS = ("male", "female")
AGES = ("child", "teenager", "young adult", "middle-aged", "elderly")
PITCHES = ("very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch")
SPEED_MIN, SPEED_MAX, SPEED_STEP = 0.8, 1.2, 0.05
NAME_MAX = 40

SAMPLE_SENTENCE = "ชายคนหนึ่งตื่นขึ้นมาในห้องที่ไม่รู้จัก และพบจดหมายที่เขียนด้วยลายมือของตัวเอง"
VOICE_ID = re.compile(r"v_[0-9a-f]{8}")

State = Literal["voicing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"voicing"})
ErrorCode = Literal["crashed", "model_failed", "internal"]

# A preview is these three files in `.pending/`; the json goes last, so it marks a whole one.
PREVIEW_AUDIO, PREVIEW_PROMPT, PREVIEW_INFO = "preview.wav", "preview.pt", "preview.json"


class VoiceJobError(BaseModel):
    code: ErrorCode
    message: str


class VoiceJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["design_preview", "sentences"]
    state: State
    clip_id: None = None  # every job reads the same shape; this one is of no single clip
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    error: VoiceJobError | None = None
    cancel_requested: bool = False
    started_at: str


class Voice(BaseModel):
    """One Saved voice, as `GET /voices` lists it."""

    id: str
    name: str
    speed: float
    chars_per_s: float
    created_at: str
    in_use: bool  # the Spoil draft or an unfinished Draft job uses it: it can't be deleted (D43, D87)


class SavedVoice(NamedTuple):
    speed: float
    prompt: bytes  # the clone prompt (`{voice_id}.pt`)


class SentencesPlan(NamedTuple):
    """What voicing some of the Spoil draft's sentences needs, read under the draft's lock."""

    voice_id: str
    voice: SavedVoice
    clip_id: str  # the draft's clip: deleting it is `clip_busy` meanwhile (D49)
    sentences: list[tuple[str, str]]  # (id, text as written), in the draft's order


def saved_voice(project: ProjectPaths, voice_id: str) -> SavedVoice | None:
    """What speaking in a Saved voice needs, or None when the voice is gone."""
    voice = project.voices_dir / f"{voice_id}.json"
    prompt = project.voices_dir / f"{voice_id}.pt"
    if not VOICE_ID.fullmatch(voice_id) or not voice.is_file() or not prompt.is_file():
        return None
    return SavedVoice(json.loads(voice.read_text(encoding="utf-8"))["speed"], prompt.read_bytes())


def plan_sentences(project: ProjectPaths, draft: Draft, sentence_ids: list[str]) -> SentencesPlan:
    """The sentences in the draft's order with the draft's voice. Raises `ApiError` 400
    `voice_not_found` when that voice is gone. Call with the draft's lock held."""
    voice = saved_voice(project, draft.voice_id)
    if voice is None:
        raise ApiError(400, "voice_not_found", "ไม่พบเสียงของ Spoil draft: เลือกเสียงใหม่")
    wanted = set(sentence_ids)
    return SentencesPlan(
        voice_id=draft.voice_id,
        voice=voice,
        clip_id=draft.clip_id,
        sentences=[(sentence.id, sentence.text) for sentence in draft.sentences if sentence.id in wanted],
    )


class SentenceVoicer(Speaker[Job]):
    """A job slot whose job voices Spoil draft sentences: the Voice job `sentences` and
    the Render job's `voicing`."""

    worker_error = WorkerError
    child_name = "ตัวสร้างเสียง"
    failure = "สร้างเสียงไม่สำเร็จ"

    def _voice_sentences(self, project: ProjectPaths, plan: SentencesPlan) -> None:
        """One sentence at a time, each written as soon as it is spoken (spec › Voice job);
        `done` counts them. The draft is locked meanwhile, so every sentence is still there."""
        tts_texts = [thai.spoken(text) for _, text in plan.sentences]
        spoken_each = self._speak(project, tts_texts, plan.voice)
        # The speaker first: `zip` asks it once more after the last text, so it ends its child.
        for done, (spoken, (sentence_id, _), tts_text) in enumerate(zip(spoken_each, plan.sentences, tts_texts), start=1):
            _write_sentence_audio(project, plan.voice_id, sentence_id, tts_text, spoken)
            self._update(done=done)


class VoiceJobs(SentenceVoicer[VoiceJob]):
    """Holds the latest Voice job."""

    unfinished = UNFINISHED
    gpu_kind = "voice"
    error_type = VoiceJobError
    nothing_to_cancel = "ไม่มีงานสร้างเสียงที่ยังไม่จบ"

    def start(self, body: dict) -> VoiceJob:
        kind = body.get("kind")
        if kind == "sentences":
            return self._start_sentences(body.get("sentence_ids"))
        if kind != "design_preview":
            raise ApiError(400, "invalid_request", "ไม่รู้จักงานสร้างเสียงแบบนี้")
        return self._start_design(body)

    def _start_design(self, body: dict) -> VoiceJob:
        """Checks the body, then the gate, `busy`, `gpu_busy`, and starts the job's thread."""
        instruct, speed = _design_choices(body)
        project = paths.project()
        require_rows(needed_rows(project))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังสร้างเสียงอยู่")
            gpu.slot.take("voice")
            self._job = VoiceJob(kind="design_preview", state="voicing", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        request = Design(instruct=instruct, text=SAMPLE_SENTENCE, speed=speed, num_step=NUM_STEP)
        threading.Thread(target=self._run, args=(lambda: self._design(project, request),), daemon=True).start()
        return job

    def _start_sentences(self, sentence_ids: object) -> VoiceJob:
        """`busy`, then the ids, the gate and the GPU under the draft's lock, so no edit
        slips in before the draft is locked (D51)."""
        project = paths.project()
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังสร้างเสียงอยู่")
            with gpu.slot.draft_lock:
                draft = draft_file.read(project)
                if draft is None:
                    raise ApiError(400, "invalid_request", "ยังไม่มี Spoil draft ให้สร้างเสียง")
                known = {sentence.id for sentence in draft.sentences}
                if (
                    not isinstance(sentence_ids, list)
                    or not sentence_ids
                    or len(set(map(str, sentence_ids))) < len(sentence_ids)
                    or not all(isinstance(sid, str) and sid in known for sid in sentence_ids)
                ):
                    raise ApiError(400, "invalid_request", "เลือกประโยคที่มีใน Spoil draft โดยไม่ซ้ำ")
                plan = plan_sentences(project, draft, sentence_ids)
                require_rows(needed_rows(project))
                gpu.slot.take("voice", [plan.clip_id], locks_draft=True)
            self._job = VoiceJob(
                kind="sentences", state="voicing", done=0, total=len(plan.sentences), started_at=checks.now_iso()
            )
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(lambda: self._voice_sentences(project, plan),), daemon=True).start()
        return job

    def _design(self, project: ProjectPaths, request: Design) -> None:
        process, requests, replies = self._start_tts(project)
        requests.put(request)
        designed = self._reply(process, replies, (Designed,))
        requests.put(None)
        _write_preview(project, request, designed)

    def _run(self, steps) -> None:
        self._run_job(f"voice job {self.current().kind}", steps)


def _write_sentence_audio(project: ProjectPaths, voice_id: str, sentence_id: str, tts_text: str, spoken: Spoken) -> None:
    """The sentence's wav, then its `audio` in the draft: what was spoken and how long (D30)."""
    project.draft_audio_dir.mkdir(parents=True, exist_ok=True)
    target = project.draft_audio_dir / f"{sentence_id}.wav"
    temporary = target.with_name(target.name + ".tmp")
    write_wav(temporary, spoken)
    seconds = round(wav_seconds(temporary), 3)
    with gpu.slot.draft_lock:
        os.replace(temporary, target)
        draft = draft_file.read(project)
        sentence = next(s for s in draft.sentences if s.id == sentence_id)
        sentence.audio = Audio(tts_text=tts_text, voice_id=voice_id, duration_s=seconds)
        draft_file.write(project, draft)


# Saving moves the preview's files and a finished job replaces them: one at a time.
_files_lock = threading.Lock()

voice_users: list[Callable[[str], bool]] = []
"""Checks that answer True while a job will write a draft with that voice, so it can't be
deleted (`voice_in_use`, D87). `spoil_maker.draft` adds the Draft job's when it is imported,
`toon.series` its Series' (toon D25). Each runs under `gpu.slot.draft_lock`, so it takes no
lock but one that comes after it (the Draft job's none, `toon.store.lock`)."""


def _job_uses(voice_id: str) -> bool:
    return any(uses(voice_id) for uses in voice_users)


def _write_preview(project: ProjectPaths, request: Design, designed: Designed) -> None:
    """The new preview replaces the old one (spec › Saved voice step 3)."""
    pending = project.pending_voice_dir
    pending.mkdir(parents=True, exist_ok=True)
    audio = pending / PREVIEW_AUDIO
    write_wav(audio.with_suffix(".tmp"), designed)
    seconds = wav_seconds(audio.with_suffix(".tmp"))
    info = {
        "instruct": request.instruct,
        "speed": request.speed,
        # Letters after numbers become words, per second of the sample (D35, D36).
        "chars_per_s": thai.letters(thai.spoken(request.text)) / seconds,
    }
    with _files_lock:
        (pending / PREVIEW_INFO).unlink(missing_ok=True)
        os.replace(audio.with_suffix(".tmp"), audio)
        (pending / PREVIEW_PROMPT).write_bytes(designed.prompt)
        files.write_atomic(pending / PREVIEW_INFO, _json(info))


def preview_audio(project: ProjectPaths) -> Path:
    """The preview not saved yet. Raises `ApiError` 404 when there is none."""
    with _files_lock:
        if not (project.pending_voice_dir / PREVIEW_INFO).is_file():
            raise ApiError(404, "not_found", "ยังไม่มีเสียงที่สุ่มไว้")
        return project.pending_voice_dir / PREVIEW_AUDIO


def save_preview(project: ProjectPaths, name: str) -> Voice:
    """Moves the latest preview into a new Saved voice (spec › Saved voice step 4)."""
    name = _checked_name(name)
    pending = project.pending_voice_dir
    with _files_lock:
        info_path = pending / PREVIEW_INFO
        if not info_path.is_file():
            raise ApiError(409, "no_preview", "กดสุ่มเพื่อฟังเสียงก่อนบันทึก")
        info = json.loads(info_path.read_text(encoding="utf-8"))
        voice_id = _new_id(project)
        stored = {
            "name": name,
            "kind": "design",  # `clone` is kept for the next round (D48)
            "speed": info["speed"],
            "chars_per_s": info["chars_per_s"],
            "created_at": checks.now_iso(),
            "instruct": info["instruct"],
        }
        project.voices_dir.mkdir(parents=True, exist_ok=True)
        os.replace(pending / PREVIEW_PROMPT, project.voices_dir / f"{voice_id}.pt")
        os.replace(pending / PREVIEW_AUDIO, project.voices_dir / f"{voice_id}.wav")
        files.write_atomic(project.voices_dir / f"{voice_id}.json", _json(stored))
        info_path.unlink()
    log.info("saved voice %s", voice_id)
    return _voice(voice_id, stored, in_use=False)


def list_voices(project: ProjectPaths) -> list[Voice]:
    """Newest first; voices saved in the same second by the order their files were written."""
    draft = draft_file.read(project)
    found = []
    for path in project.voices_dir.glob("v_*.json"):
        if VOICE_ID.fullmatch(path.stem):
            stored = json.loads(path.read_text(encoding="utf-8"))
            in_use = (draft is not None and draft.voice_id == path.stem) or _job_uses(path.stem)
            found.append((stored["created_at"], path.stat().st_mtime_ns, _voice(path.stem, stored, in_use)))
    return [voice for *_, voice in sorted(found, key=lambda entry: entry[:2], reverse=True)]


def rename(project: ProjectPaths, voice_id: str, name: str) -> Voice:
    name = _checked_name(name)
    with _files_lock:
        path = _voice_file(project, voice_id, ".json")
        stored = json.loads(path.read_text(encoding="utf-8"))
        stored["name"] = name
        files.write_atomic(path, _json(stored))
    return _voice(voice_id, stored, draft_file.uses_voice(project, voice_id) or _job_uses(voice_id))


def delete(project: ProjectPaths, voice_id: str) -> None:
    """Removes the three files; the json goes last, so a half-deleted voice is never listed
    without its sample. The Spoil draft's voice, or the one of an unfinished Draft job, can't
    go: `voice_in_use` (D43, D87). Under the draft's lock, so the draft can't switch to it
    between the check and the delete, and a Draft job either is set already or checks the
    voice after this delete (both under the draft's lock)."""
    with gpu.slot.draft_lock, _files_lock:
        info = _voice_file(project, voice_id, ".json")
        if _job_uses(voice_id) or draft_file.uses_voice(project, voice_id):
            raise ApiError(409, "voice_in_use", "เสียงนี้ใช้อยู่ใน Spoil draft งานร่างบท หรือ Series ของการ์ตูนเล่า")
        for suffix in (".pt", ".wav"):
            (project.voices_dir / f"{voice_id}{suffix}").unlink(missing_ok=True)
        info.unlink()
    log.info("deleted voice %s", voice_id)


def chars_per_s(project: ProjectPaths, voice_id: str) -> float | None:
    """The voice's measured speaking speed (D35), or None when it is gone."""
    path = project.voices_dir / f"{voice_id}.json"
    if not VOICE_ID.fullmatch(voice_id) or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["chars_per_s"]


def sample_audio(project: ProjectPaths, voice_id: str) -> Path:
    _voice_file(project, voice_id, ".json")
    return _voice_file(project, voice_id, ".wav")


def clean_on_start(project: ProjectPaths) -> None:
    """A preview never saved goes: jobs don't survive a restart (spec › Ops)."""
    shutil.rmtree(project.pending_voice_dir, ignore_errors=True)


def _design_choices(body: dict) -> tuple[str, float]:
    """The `instruct` and speed of a design. Raises `ApiError` 400 `invalid_voice`."""
    gender, age, pitch, speed = (body.get(key) for key in ("gender", "age", "pitch", "speed"))
    if gender not in GENDERS or age not in AGES or pitch not in PITCHES or not _on_speed_scale(speed):
        raise ApiError(400, "invalid_voice", "เลือกเพศ วัย ระดับเสียง และความเร็ว 0.8–1.2 ทีละ 0.05")
    return f"{gender}, {age}, {pitch}", round(speed, 2)


def _on_speed_scale(speed: object) -> bool:
    """0.8–1.2 in steps of 0.05, allowing for how floats add up (0.8 + 3 × 0.05)."""
    if not is_number(speed):
        return False
    steps = (speed - SPEED_MIN) / SPEED_STEP
    return -1e-6 <= steps <= (SPEED_MAX - SPEED_MIN) / SPEED_STEP + 1e-6 and abs(steps - round(steps)) < 1e-6


def _checked_name(name: object) -> str:
    """1–40 letters once the spaces around it are cut; names may repeat (spec › Saved voice)."""
    name = name.strip() if isinstance(name, str) else ""
    if not 1 <= len(name) <= NAME_MAX:
        raise ApiError(400, "invalid_voice", f"ชื่อเสียงต้องยาว 1–{NAME_MAX} ตัวอักษร")
    return name


def _voice_file(project: ProjectPaths, voice_id: str, suffix: str) -> Path:
    """Only a well-formed id gets near the disk. Raises `ApiError` 404 `not_found`."""
    path = project.voices_dir / f"{voice_id}{suffix}"
    if not VOICE_ID.fullmatch(voice_id) or not path.is_file():
        raise ApiError(404, "not_found", "ไม่พบเสียงนี้")
    return path


def _new_id(project: ProjectPaths) -> str:
    while True:
        voice_id = f"v_{secrets.token_hex(4)}"
        if not (project.voices_dir / f"{voice_id}.json").exists():
            return voice_id


def _voice(voice_id: str, stored: dict, in_use: bool) -> Voice:
    return Voice(
        id=voice_id,
        name=stored["name"],
        speed=stored["speed"],
        chars_per_s=stored["chars_per_s"],
        created_at=stored["created_at"],
        in_use=in_use,
    )


def _json(content: dict) -> str:
    return json.dumps(content, ensure_ascii=False, indent=2)


def needed_rows(project: ProjectPaths) -> dict[str, Row]:
    """The Status check rows a Voice job needs, by id (spec › Status check)."""
    omnivoice: dict[str, Row] = {OMNIVOICE.check_id: (OMNIVOICE.label, lambda: checks.check_model(project, OMNIVOICE))}
    return gate_rows.DEVICE | omnivoice | gate_rows.PYTHAINLP


voice_jobs = VoiceJobs()
