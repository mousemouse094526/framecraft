"""Saved voices and the Voice job: one at a time, a backend thread that owns the state
and every file, and a child process that runs OmniVoice (ADR 0010, ADR 0012, ADR 0015).

Rules are in docs/features/spoil-maker/spec.md › Saved voice and › Voice job
(D32, D35, D37, D43, D48). This ticket has `design_preview`; `sentences` needs a
Spoil draft and comes with it.
"""

import json
import logging
import os
import re
import secrets
import shutil
import threading
import time
import wave
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, files, gpu, paths, spoil_maker
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import Cancelled, ModelJobSlot, short
from backend.models import OMNIVOICE
from backend.paths import ProjectPaths
from backend.spoil_maker import draft_file, thai
from backend.spoil_maker.tts import Design, Designed, Ready, WorkerError

log = logging.getLogger(__name__)

# The choices OmniVoice's `instruct` understands (spec › Saved voice step 1).
GENDERS = ("male", "female")
AGES = ("child", "teenager", "young adult", "middle-aged", "elderly")
PITCHES = ("very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch")
SPEED_MIN, SPEED_MAX, SPEED_STEP = 0.8, 1.2, 0.05
NUM_STEP = 16  # D37
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
    clip_id: None = None
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
    in_use: bool  # the Spoil draft uses it, so it can't be deleted (D43)


class VoiceJobs(ModelJobSlot[VoiceJob]):
    """Holds the latest Voice job."""

    unfinished = UNFINISHED
    gpu_kind = "voice"
    nothing_to_cancel = "ไม่มีงานสร้างเสียงที่ยังไม่จบ"
    worker_error = WorkerError
    child_name = "ตัวสร้างเสียง"
    failure = "สร้างเสียงไม่สำเร็จ"

    def start(self, body: dict) -> VoiceJob:
        """Checks the body, then the gate, `busy`, `gpu_busy`, and starts the job's thread."""
        kind = body.get("kind")
        if kind == "sentences":
            # Every id must be in the Spoil draft (spec › Voice job); drafts come in a later ticket,
            # so for now none is.
            raise ApiError(400, "invalid_request", "ยังไม่มี Spoil draft ให้สร้างเสียง")
        if kind != "design_preview":
            raise ApiError(400, "invalid_request", "ไม่รู้จักงานสร้างเสียงแบบนี้")
        instruct, speed = _design_choices(body)
        project = ProjectPaths(paths.ROOT)
        require_rows(_needed_rows(project))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังสร้างเสียงอยู่")
            gpu.slot.take("voice")
            self._job = VoiceJob(kind=kind, state="voicing", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        request = Design(instruct=instruct, text=SAMPLE_SENTENCE, speed=speed, num_step=NUM_STEP)
        thread = threading.Thread(target=self._run, args=(project, request), daemon=True)
        thread.start()
        return job

    def _run(self, project: ProjectPaths, request: Design) -> None:
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        started = time.monotonic()
        log.info("voice design started")
        process = None
        try:
            device = checks.probe_device()
            snapshot = project.snapshot_dir(OMNIVOICE, OMNIVOICE.revision)
            process, requests, replies = spoil_maker.start_tts_worker(snapshot, device)
            self._track(process)
            self._reply(process, replies, (Ready,))
            requests.put(request)
            designed = self._reply(process, replies, (Designed,))
            requests.put(None)
            _write_preview(project, request, designed)
            ending = {"state": "done"}
        except Cancelled:
            ending = {"state": "cancelled"}
        except JobFailed as failure:
            ending = _failed(failure.code, failure.message)
        except Exception as error:
            log.exception("voice design failed")  # the full error, for [api]
            ending = _failed("internal", f"สร้างเสียงไม่สำเร็จ: {short(error)}")
        finally:
            self._finish(process, ending)
            code = ending["error"].code if ending.get("error") else None
            log.info("voice design ended %s %s after %.0f s", ending["state"], code or "", time.monotonic() - started)

# Saving moves the preview's files and a finished job replaces them: one at a time.
_files_lock = threading.Lock()


def _write_preview(project: ProjectPaths, request: Design, designed: Designed) -> None:
    """The new preview replaces the old one (spec › Saved voice step 3)."""
    pending = project.pending_voice_dir
    pending.mkdir(parents=True, exist_ok=True)
    audio = pending / PREVIEW_AUDIO
    _write_wav(audio.with_suffix(".tmp"), designed)
    seconds = _wav_seconds(audio.with_suffix(".tmp"))
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
            in_use = draft is not None and draft.voice_id == path.stem
            found.append((stored["created_at"], path.stat().st_mtime_ns, _voice(path.stem, stored, in_use)))
    return [voice for *_, voice in sorted(found, key=lambda entry: entry[:2], reverse=True)]


def rename(project: ProjectPaths, voice_id: str, name: str) -> Voice:
    name = _checked_name(name)
    with _files_lock:
        path = _voice_file(project, voice_id, ".json")
        stored = json.loads(path.read_text(encoding="utf-8"))
        stored["name"] = name
        files.write_atomic(path, _json(stored))
    return _voice(voice_id, stored, draft_file.uses_voice(project, voice_id))


def delete(project: ProjectPaths, voice_id: str) -> None:
    """Removes the three files; the json goes last, so a half-deleted voice is never listed
    without its sample. The Spoil draft's voice can't go: `voice_in_use` (D43). Under the
    draft's lock, so the draft can't switch to it between the check and the delete."""
    with gpu.slot.draft_lock, _files_lock:
        info = _voice_file(project, voice_id, ".json")
        if draft_file.uses_voice(project, voice_id):
            raise ApiError(409, "voice_in_use", "เสียงนี้ใช้อยู่ใน Spoil draft")
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
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
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


def _write_wav(path: Path, designed: Designed) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(designed.sample_rate)
        audio.writeframes(designed.audio)


def _wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def _failed(code: ErrorCode, message: str) -> dict:
    return {"state": "failed", "error": VoiceJobError(code=code, message=message)}


def _needed_rows(project: ProjectPaths) -> dict[str, Row]:
    """The Status check rows a Voice job needs, by id (spec › Status check)."""
    return {
        "device": ("Device", lambda: checks.check_device(checks.probe_device)),
        OMNIVOICE.check_id: (OMNIVOICE.label, lambda: checks.check_model(project, OMNIVOICE)),
        "pythainlp": ("pythainlp", lambda: checks.check_pinned(checks.probe_pythainlp, checks.PYTHAINLP_VERSION)),
    }


voice_jobs = VoiceJobs()
