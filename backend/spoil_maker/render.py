"""The Render job and its results: one at a time, a backend thread that voices the
sentences that need it in an OmniVoice child (`voicing`, holding the GPU), then runs
ffmpeg (`rendering`, without it), and writes `media/spoil-maker/renders/{name}.mp4`,
`.srt` and `.json` (ADR 0010, ADR 0012, ADR 0015).

Steps and rules are in docs/features/spoil-maker/spec.md › Render job (D9, D10,
D30, D31, D40–D42, D45, D51).
"""

import json
import logging
import os
import re
import shutil
import threading
import time
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, disk, fonts, gpu, paths
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import Cancelled, short, stop_process
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.spoil_maker import captions, compose, draft, draft_file, settings, shots, voices
from backend.spoil_maker.captions import Timed
from backend.spoil_maker.compose import Piece
from backend.spoil_maker.draft_file import Draft
from backend.spoil_maker.ffmpeg import FfmpegFailed, probe
from backend.spoil_maker.voices import SentenceVoicer, SentencesPlan

log = logging.getLogger(__name__)

State = Literal["voicing", "rendering", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"voicing", "rendering"})
ErrorCode = Literal["ffmpeg_failed", "crashed", "model_failed", "internal"]

MIN_FREE_BYTES = 1024**3  # 1 GiB (spec › Render job step 1)
NAME = re.compile(r"\d{8}-\d{6}")
NAME_FORMAT = "%Y%m%d-%H%M%S"
PIECES_SHARE = 50  # `percent` 0–50 while the pieces are cut, 50–100 for the final encode
RESULT_SUFFIXES = (".mp4", ".srt", ".json")

# Files in the work folder (`.render/`), named bare for ffmpeg (compose).
PIECES_LIST, NARRATION, CAPTIONS = "pieces.txt", "narration.wav", "captions.ass"


class RenderJobError(BaseModel):
    code: ErrorCode
    message: str


class RenderJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["render"] = "render"
    state: State
    clip_id: None = None
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    error: RenderJobError | None = None
    cancel_requested: bool = False
    started_at: str


class RenderResult(BaseModel):
    """One finished render, as `GET /renders` lists it."""

    name: str
    created_at: str
    duration_s: float
    size_bytes: int
    sources: list[str]  # the Temp clips' titles in EP order, for the clip's description (legal 1)


class RenderJobs(SentenceVoicer[RenderJob]):
    """Holds the latest Render job."""

    unfinished = UNFINISHED
    gpu_kind = "render"
    nothing_to_cancel = "ไม่มีงาน render ที่ยังไม่จบ"

    def start(self) -> RenderJob:
        """Checks in spec order (Render job step 1), then `busy` and, when sentences need
        their voice, `gpu_busy`. The draft's lock covers the checks and the start, so no
        edit slips between them (D51)."""
        project = ProjectPaths(paths.ROOT)
        with self._lock, gpu.slot.draft_lock:
            found = draft_file.read(project)
            if found is None:
                raise ApiError(404, "no_draft", "ยังไม่มี Spoil draft")
            statuses = {s.id: draft.status_of(found, s) for s in found.sentences}
            missing = [sid for sid, status in statuses.items() if status == "no_shot"]
            if missing:
                raise ApiError(400, "missing_shots", "ทุกประโยคต้องมีภาพก่อน render", sentence_ids=missing)
            if disk.free_bytes(project.root) < MIN_FREE_BYTES:
                raise ApiError(507, "disk_full", "ที่ว่างดิสก์ไม่ถึง 1 GiB")
            unvoiced = [sid for sid, status in statuses.items() if status != "ready"]
            require_rows(_needed_rows(project, voicing=bool(unvoiced)))
            if self._taken():
                raise ApiError(409, "busy", "กำลัง render อยู่")
            plan = voices.plan_sentences(project, found, unvoiced) if unvoiced else None
            if plan:
                gpu.slot.take("render", plan.clip_ids, draft=True)
                self._job = RenderJob(state="voicing", done=0, total=len(unvoiced), started_at=checks.now_iso())
            else:
                self._job = RenderJob(state="rendering", percent=0, started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, plan), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, plan: SentencesPlan | None) -> None:
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        started = time.monotonic()
        log.info("render started")
        name = None
        try:
            if plan:
                self._voice_sentences(project, plan)
            with gpu.slot.draft_lock:
                # What this render draws (spec › Render job), its voice copied while
                # the draft is still locked: edits after this don't reach the file.
                snapshot = draft_file.read(project)
                timed, pieces = _timeline(project, snapshot)
                _start_work_folder(project)
                _write_narration(project, snapshot, project.render_work_dir / NARRATION)
            self._free_gpu()
            self._update(state="rendering", percent=0, done=None, total=None)
            name = self._render(project, snapshot, timed, pieces)
            ending = {"state": "done", "percent": 100}
        except Cancelled:
            ending = {"state": "cancelled"}  # voiced sentences stay in the draft
        except FfmpegFailed as error:
            ending = _failed("ffmpeg_failed", f"render ไม่สำเร็จ: {short(error)}")
        except JobFailed as failure:
            ending = _failed(failure.code, failure.message)
        except Exception as error:
            log.exception("render failed")  # the full error, for [api]
            ending = _failed("internal", f"render ไม่สำเร็จ: {short(error)}")
        finally:
            shutil.rmtree(project.render_work_dir, ignore_errors=True)
            _remove_partials(project)
            self._finish(self._running_child(), ending)
            code = ending["error"].code if ending.get("error") else None
            log.info("render %s ended %s %s after %.0f s", name or "", ending["state"], code or "", time.monotonic() - started)

    def _free_gpu(self) -> None:
        """Voicing is over: the TTS child goes and the GPU is free for the next job while
        ffmpeg runs (D51). A render that voiced nothing never took it: `release` then does nothing."""
        process = self._running_child()
        if process is not None:
            stop_process(process)
            self._track(None)
        gpu.slot.release("render")

    def _render(self, project: ProjectPaths, snapshot: Draft, timed: list[Timed], pieces: list[Piece]) -> str:
        """Step 3–4: cut the pieces, join them under the voice and the text, write the result."""
        work = project.render_work_dir
        marks = settings.read(project).watermarks  # every render's, the latest (spec › ค่าที่จำไว้)
        (work / CAPTIONS).write_text(
            captions.ass_file(project, snapshot.layout, snapshot.top_text, timed, marks), encoding="utf-8"
        )
        media = {clip_id: probe(clips.video_file(project, clip_id)) for clip_id in snapshot.clip_ids}
        for index, piece in enumerate(pieces):
            mp4 = clips.video_file(project, piece.clip_id)
            command = compose.piece_command(
                piece, mp4, media[piece.clip_id], snapshot.layout, snapshot.original_volume, f"{index}.mkv"
            )
            compose.run(command, work, self._cancel)
            self._update(percent=PIECES_SHARE * (index + 1) // len(pieces))
        (work / PIECES_LIST).write_text("".join(f"file '{i}.mkv'\n" for i in range(len(pieces))), encoding="utf-8")
        total = timed[-1].end
        project.renders_dir.mkdir(parents=True, exist_ok=True)
        name = _free_name(project)
        mp4_partial = project.renders_dir / f"{name}.mp4.partial"
        command = compose.final_command(
            PIECES_LIST, NARRATION, CAPTIONS, os.path.relpath(project.kanit_dir, work), total, str(mp4_partial)
        )

        def on_progress(seconds: float) -> None:
            share = 100 - PIECES_SHARE
            self._update(percent=PIECES_SHARE + min(share, round(share * seconds / total)))

        compose.run(command, work, self._cancel, on_progress)
        info = {
            "created_at": checks.now_iso(),
            "duration_s": round(probe(mp4_partial).duration_s, 2),
            "sources": [clips.read_clip(project, clip_id).title for clip_id in snapshot.clip_ids],
        }
        srt_partial = project.renders_dir / f"{name}.srt.partial"
        srt_partial.write_text(captions.srt_file(timed), encoding="utf-8")
        json_partial = project.renders_dir / f"{name}.json.partial"
        json_partial.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        # The json goes last: a name is listed once all three are there (spec › Render job).
        for written in (srt_partial, mp4_partial, json_partial):
            os.replace(written, written.with_suffix(""))
        return name


def _timeline(project: ProjectPaths, snapshot: Draft) -> tuple[list[Timed], list[Piece]]:
    """Sentences end to end with no added silence; each Shot plays half its sentence
    from the Shot's start (D31). Cuts land on frames of the 30 fps output counted from
    the start, so the pieces add up to the voice's length."""
    shot_files = {clip_id: shots.read_shots(project, clip_id) for clip_id in snapshot.clip_ids}
    timed: list[Timed] = []
    pieces: list[Piece] = []
    at = 0.0
    for sentence in snapshot.sentences:
        if draft.status_of(snapshot, sentence) != "ready":
            raise JobFailed("internal", "มีประโยคที่ยังไม่มีเสียงหรือภาพ: กด render ใหม่")
        end = at + sentence.audio.duration_s
        timed.append(Timed(sentence.text, at, end))
        middle = at + sentence.audio.duration_s / 2
        for shot_ref, (start, stop) in zip(sentence.shots, ((at, middle), (middle, end))):
            frames = _frame(stop) - _frame(start)
            if frames > 0:
                shot = shot_files[shot_ref.clip_id].shots[shot_ref.n]
                pieces.append(Piece(clip_id=shot_ref.clip_id, start=shot.start, seconds=frames / compose.FPS))
        at = end
    return timed, pieces


def _start_work_folder(project: ProjectPaths) -> None:
    shutil.rmtree(project.render_work_dir, ignore_errors=True)
    project.render_work_dir.mkdir(parents=True)


def _frame(seconds: float) -> int:
    return round(seconds * compose.FPS)


def _write_narration(project: ProjectPaths, snapshot: Draft, target: Path) -> None:
    """Every sentence's wav end to end, as one wav: OmniVoice speaks every one at the
    same sample rate, so their frames join as they are."""
    with wave.open(str(target), "wb") as out:
        for index, sentence in enumerate(snapshot.sentences):
            with wave.open(str(project.draft_audio_dir / f"{sentence.id}.wav"), "rb") as part:
                if index == 0:
                    out.setparams(part.getparams())
                elif (part.getframerate(), part.getnchannels(), part.getsampwidth()) != (
                    out.getframerate(), out.getnchannels(), out.getsampwidth()
                ):  # fmt: skip
                    raise JobFailed("internal", "เสียงของประโยคไม่เข้ากัน: สร้างเสียงทั้งหมดใหม่")
                out.writeframes(part.readframes(part.getnframes()))


def _free_name(project: ProjectPaths) -> str:
    """`YYYYMMDD-HHMMSS` now, or the next free second (two renders in one second)."""
    moment = datetime.now()
    while True:
        name = moment.strftime(NAME_FORMAT)
        if not any(project.renders_dir.glob(f"{name}.*")):
            return name
        moment += timedelta(seconds=1)


# --- The results (D42) ---


def list_results(project: ProjectPaths) -> list[RenderResult]:
    """Every name with its mp4, `.srt` and `.json` and no `.partial`, newest first."""
    if not project.renders_dir.is_dir():
        return []
    found = []
    for meta in project.renders_dir.glob("*.json"):
        name = meta.stem
        if not NAME.fullmatch(name) or not _complete(project, name):
            continue
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
            mp4 = project.renders_dir / f"{name}.mp4"
            found.append(RenderResult(name=name, size_bytes=mp4.stat().st_size, **info))
        except (OSError, ValueError, TypeError):
            log.warning("skipping unreadable render %s", name)
    return sorted(found, key=lambda result: result.name, reverse=True)


def result_file(project: ProjectPaths, name: str, suffix: str) -> Path:
    """Only a well-formed, complete name gets near the disk. Raises `ApiError` 404 `not_found`."""
    if not NAME.fullmatch(name) or not _complete(project, name):
        raise ApiError(404, "not_found", "ไม่พบผล render นี้")
    return project.renders_dir / f"{name}{suffix}"


def delete_result(project: ProjectPaths, name: str) -> None:
    """mp4 first (a player may hold it open: `409` `in_use`), the json last."""
    result_file(project, name, ".json")
    try:
        (project.renders_dir / f"{name}.mp4").unlink(missing_ok=True)
    except PermissionError:
        raise ApiError(409, "in_use", "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง") from None
    (project.renders_dir / f"{name}.srt").unlink(missing_ok=True)
    (project.renders_dir / f"{name}.json").unlink(missing_ok=True)
    log.info("deleted render %s", name)


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart (spec › Ops)."""
    shutil.rmtree(project.render_work_dir, ignore_errors=True)
    _remove_partials(project)


def _complete(project: ProjectPaths, name: str) -> bool:
    folder = project.renders_dir
    return all((folder / f"{name}{suffix}").is_file() for suffix in RESULT_SUFFIXES) and not any(
        folder.glob(f"{name}.*.partial")
    )


def _remove_partials(project: ProjectPaths) -> None:
    if project.renders_dir.is_dir():
        for leftover in project.renders_dir.glob("*.partial"):
            leftover.unlink(missing_ok=True)


def _failed(code: ErrorCode, message: str) -> dict:
    return {"state": "failed", "error": RenderJobError(code=code, message=message)}


def _needed_rows(project: ProjectPaths, voicing: bool) -> dict[str, Row]:
    """The Status check rows a Render job needs, by id; voicing first adds the Voice job's
    (spec › Status check)."""
    rows: dict[str, Row] = {
        "ffmpeg": ("ffmpeg", lambda: checks.check_ffmpeg(checks.probe_ffmpeg)),
        fonts.CHECK_ID: (fonts.LABEL, lambda: fonts.check_kanit(project)),
        "pythainlp": ("pythainlp", lambda: checks.check_pinned(checks.probe_pythainlp, checks.PYTHAINLP_VERSION)),
    }
    return rows | voices.needed_rows(project) if voicing else rows


render_jobs = RenderJobs()
