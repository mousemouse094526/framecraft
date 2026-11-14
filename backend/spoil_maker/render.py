"""The Render job and its results: one at a time, a backend thread that voices the
sentences that need it in an OmniVoice child (`voicing`, holding the GPU), then runs
ffmpeg (`rendering`, without it), and writes `media/spoil-maker/renders/{name}.mp4`,
`.srt` and `.json` (ADR 0010, ADR 0012, ADR 0015).

Steps and rules are in docs/features/spoil-maker/spec.md › Render job (D10, D30,
D31, D40–D42, D45, D51) and, for the background sound, sound-library spec › Render job
ของสปอย (D5, D8, D12).
"""

import logging
import os
import shutil
import threading
import wave
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend import checks, disk, ffmpeg, gate_rows, gpu, paths, renders, sounds
from backend.errors import ApiError, JobFailed, require_rows
from backend.ffmpeg import FfmpegFailed, Runner, probe
from backend.jobs import short
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.spoil_maker import captions, compose, draft, draft_file, settings, shots, voices
from backend.spoil_maker.captions import Timed
from backend.spoil_maker.compose import Background, Piece
from backend.spoil_maker.draft_file import Draft
from backend.spoil_maker.voices import SentenceVoicer, SentencesPlan

log = logging.getLogger(__name__)

State = Literal["voicing", "rendering", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"voicing", "rendering"})
ErrorCode = Literal["ffmpeg_failed", "crashed", "model_failed", "sound_not_found", "internal"]

# Files in the work folder (`.render/`), named bare for ffmpeg (compose).
PIECES_LIST, NARRATION, CAPTIONS, SOUND = "pieces.txt", "narration.wav", "captions.ass", "sound.m4a"
SOUND_NOT_FOUND = "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render"


class RenderJobError(BaseModel):
    code: ErrorCode
    message: str


class RenderJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["render"] = "render"
    state: State
    clip_id: None = None  # every job reads the same shape; this one is of no single clip
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
    sources: list[str]  # the Temp clip's title, for the clip's description (legal 1)
    # The background sound's name at render time, for the description too (sound-library legal 1).
    sound_name: str | None = None
    # The draft's EP (D70); a render from before EPs has none.
    clip_id: str | None = None
    ep: int | None = None
    start_s: float | None = Field(default=None, exclude=True)  # what `GET /clips/{id}/episodes` matches by
    end_s: float | None = Field(default=None, exclude=True)


class RenderJobs(SentenceVoicer[RenderJob]):
    """Holds the latest Render job."""

    unfinished = UNFINISHED
    gpu_kind = "render"
    error_type = RenderJobError
    nothing_to_cancel = "ไม่มีงาน render ที่ยังไม่จบ"

    def __init__(self, run_ffmpeg: Runner = ffmpeg.run):
        """`run_ffmpeg` runs each ffmpeg command; a test passes one that pauses (`fastapi-api` › testing)."""
        super().__init__()
        self._run_ffmpeg = run_ffmpeg

    def start(self) -> RenderJob:
        """Checks in spec order (Render job step 1), then `busy` and, when sentences need
        their voice, `gpu_busy`. The draft's lock covers the checks and the start, so no
        edit slips between them (D51)."""
        project = paths.project()
        with self._lock, gpu.slot.draft_lock:
            found = draft_file.read(project)
            if found is None:
                raise ApiError(404, "no_draft", "ยังไม่มี Spoil draft")
            statuses = {s.id: draft.status_of(found, s) for s in found.sentences}
            missing = [sid for sid, status in statuses.items() if status == "no_shot"]
            if missing:
                raise ApiError(400, "missing_shots", "ทุกประโยคต้องมีภาพก่อน render", sentence_ids=missing)
            if found.sound is not None and not sounds.exists(project, found.sound.sound_id):
                raise ApiError(400, "sound_not_found", SOUND_NOT_FOUND)  # sound-library D8
            disk.require_free(project.root)  # spec › Render job step 1
            unvoiced = [sid for sid, status in statuses.items() if status != "ready"]
            require_rows(gate_rows.render(project, voices_first=bool(unvoiced)))
            if self._taken():
                raise ApiError(409, "busy", "กำลัง render อยู่")
            plan = voices.plan_sentences(project, found, unvoiced) if unvoiced else None
            # Every render reads the draft's clip to its end, with the GPU or not (spoil D42).
            gpu.slot.begin_render(found.clip_id)
            if plan:
                try:
                    gpu.slot.take("render", [plan.clip_id], locks_draft=True)
                except ApiError:
                    gpu.slot.end_render()
                    raise
                self._job = RenderJob(state="voicing", done=0, total=len(unvoiced), started_at=checks.now_iso())
            else:
                self._job = RenderJob(state="rendering", percent=0, started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, plan), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, plan: SentencesPlan | None) -> None:
        """A cancel keeps the sentences already voiced in the draft (spec › Render job)."""

        def clean_up(state: str) -> None:
            # First, before anything here can fail: the job reads as finished right after.
            gpu.slot.end_render()
            shutil.rmtree(project.render_work_dir, ignore_errors=True)
            renders.remove_partials(project.renders_dir)

        self._run_job("render", lambda: self._voice_and_render(project, plan), clean_up, failure="render ไม่สำเร็จ")

    def _voice_and_render(self, project: ProjectPaths, plan: SentencesPlan | None) -> dict:
        if plan:
            self._voice_sentences(project, plan)
        try:
            with gpu.slot.draft_lock:
                # What this render draws (spec › Render job), its voice copied while
                # the draft is still locked: edits after this don't reach the file.
                drawn = draft_file.read(project)
                timed, pieces = _timeline(project, drawn)
                _start_work_folder(project)
                _write_narration(project, drawn, project.render_work_dir / NARRATION)
                sound_name = _copy_sound(project, drawn)
            self.free_gpu()  # voicing is over: the GPU is free for the next job while ffmpeg runs (D51)
            self.update(state="rendering", percent=0, done=None, total=None)
            name = self._render(project, drawn, timed, pieces, sound_name)
        except FfmpegFailed as error:
            raise JobFailed("ffmpeg_failed", f"render ไม่สำเร็จ: {short(error)}") from None
        log.info("render wrote %s", name)
        return {"percent": 100}

    def _render(
        self, project: ProjectPaths, drawn: Draft, timed: list[Timed], pieces: list[Piece], sound_name: str | None
    ) -> str:
        """Step 3–4: cut the pieces, join them under the voice and the text, write the result."""
        work = project.render_work_dir
        marks = settings.read(project).watermarks  # every render's, the latest (spec › ค่าที่จำไว้)
        (work / CAPTIONS).write_text(
            captions.ass_file(project, drawn.layout, drawn.top_text, timed, marks), encoding="utf-8"
        )
        media = {drawn.clip_id: probe(clips.video_file(project, drawn.clip_id))}
        for index, piece in enumerate(pieces):
            mp4 = clips.video_file(project, piece.clip_id)
            command = compose.piece_command(
                piece, mp4, media[piece.clip_id], drawn.layout, drawn.original_volume, f"{index}.mkv"
            )
            self._run_ffmpeg(command, work, self._cancel)
            self.update(percent=renders.pieces_percent(index + 1, len(pieces)))
        (work / PIECES_LIST).write_text("".join(f"file '{i}.mkv'\n" for i in range(len(pieces))), encoding="utf-8")
        total = timed[-1].end
        project.renders_dir.mkdir(parents=True, exist_ok=True)
        render = renders.next_free(project.renders_dir)
        mp4_partial = render.file(".mp4.partial")
        background = Background(file=SOUND, volume=drawn.sound.volume) if drawn.sound else None
        command = compose.final_command(
            PIECES_LIST, NARRATION, CAPTIONS, os.path.relpath(project.kanit_dir, work), total, str(mp4_partial), background
        )
        self._run_ffmpeg(command, work, self._cancel, renders.encode_progress(self.update, total))
        info = {
            "created_at": checks.now_iso(),
            "duration_s": round(probe(mp4_partial).duration_s, 2),
            "sources": [clips.read_clip(project, drawn.clip_id).title],
            "sound_name": sound_name,
            "clip_id": drawn.clip_id,
            "ep": drawn.ep.n,
            "start_s": drawn.ep.start_s,
            "end_s": drawn.ep.end_s,
        }
        render.finish(captions.srt_file(timed), info)  # spec › Render job
        return render.name


def _timeline(project: ProjectPaths, drawn: Draft) -> tuple[list[Timed], list[Piece]]:
    """Sentences end to end with no added silence; each Shot plays half its sentence
    from the Shot's start (D31). Cuts land on frames of the 30 fps output counted from
    the start, so the pieces add up to the voice's length."""
    shot_files = {drawn.clip_id: shots.read_shots(project, drawn.clip_id)}
    timed: list[Timed] = []
    pieces: list[Piece] = []
    at = 0.0
    for sentence in drawn.sentences:
        if draft.status_of(drawn, sentence) != "ready":
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


def _copy_sound(project: ProjectPaths, drawn: Draft) -> str | None:
    """Copies the background sound into the work folder, so a delete after this doesn't
    reach the render (sound-library D12); returns its name. Call with the draft's lock held."""
    if drawn.sound is None:
        return None
    name = sounds.name_of(project, drawn.sound.sound_id)
    source = sounds.path(project, drawn.sound.sound_id)
    if name is None or not source.is_file():
        raise JobFailed("sound_not_found", SOUND_NOT_FOUND)
    shutil.copyfile(source, project.render_work_dir / SOUND)
    return name


def _frame(seconds: float) -> int:
    return round(seconds * compose.FPS)


def _write_narration(project: ProjectPaths, drawn: Draft, target: Path) -> None:
    """Every sentence's wav end to end, as one wav: OmniVoice speaks every one at the
    same sample rate, so their frames join as they are."""
    with wave.open(str(target), "wb") as out:
        for index, sentence in enumerate(drawn.sentences):
            with wave.open(str(project.draft_audio_dir / f"{sentence.id}.wav"), "rb") as part:
                if index == 0:
                    out.setparams(part.getparams())
                elif (part.getframerate(), part.getnchannels(), part.getsampwidth()) != (
                    out.getframerate(), out.getnchannels(), out.getsampwidth()
                ):  # fmt: skip
                    raise JobFailed("internal", "เสียงของประโยคไม่เข้ากัน: สร้างเสียงทั้งหมดใหม่")
                out.writeframes(part.readframes(part.getnframes()))


# --- The results (D42) ---


def list_results(project: ProjectPaths) -> list[RenderResult]:
    """Every name with its mp4, `.srt` and `.json` and no `.partial`, newest first."""
    return renders.listed(project.renders_dir, RenderResult)


def result_file(project: ProjectPaths, name: str, suffix: str) -> Path:
    """Only a well-formed, complete name gets near the disk. Raises `ApiError` 404 `not_found`."""
    render = renders.Render(project.renders_dir, name)
    render.require()
    return render.file(suffix)


def delete_result(project: ProjectPaths, name: str) -> None:
    """`404` `not_found`, or `409` `in_use` while a player holds the mp4 open."""
    renders.Render(project.renders_dir, name).delete()


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart (spec › Ops)."""
    shutil.rmtree(project.render_work_dir, ignore_errors=True)
    renders.remove_partials(project.renders_dir)


render_jobs = RenderJobs()
