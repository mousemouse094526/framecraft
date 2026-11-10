"""The Transcribe job: one at a time, a backend thread that owns the state and the
file, and a child process that runs Whisper (ADR 0010, ADR 0012).

Steps and rules are in docs/features/spoil/spec.md › Transcribe (D23, D24, D27, D28, D29).
"""

import logging
import threading
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import checks, clock, files, gate_rows, gpu, paths, spoil, stories
from backend.models import WHISPER
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import ChildGone, ModelJobSlot, next_message, short
from backend.spoil.whisper import Done, Segment, WorkerError
from backend.spoil_maker import draft_file

log = logging.getLogger(__name__)

State = Literal["preparing", "transcribing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"preparing", "transcribing"})
ErrorCode = Literal["no_audio", "model_failed", "crashed", "internal"]



class TranscribeJobError(BaseModel):
    code: ErrorCode
    message: str


class TranscribeJob(BaseModel):
    clip_id: str
    state: State
    percent: int | None = None
    cancel_requested: bool = False
    error: TranscribeJobError | None = None


class TranscriptLine(BaseModel):
    start_s: float
    end_s: float
    text: str
    # The user changed the text (spoil-maker D54); a Transcript from before edits has none.
    edited: bool = False


class Transcript(BaseModel):
    clip_id: str
    language: str | None
    duration_s: int | None
    model: str
    revision: str
    transcribed_at: str
    lines: list[TranscriptLine]


clip_users: list[Callable[[str], bool]] = []
"""Checks that answer True while another feature's job is reading that clip's
Transcript; a line of such a clip can't be edited (`clip_busy`, spoil-maker D54).
spoil-maker's Draft job adds one."""


class Transcriptions(ModelJobSlot[TranscribeJob]):
    """Holds the latest Transcribe job. Its start, a clip delete and a line edit hold
    `clips.files_lock` too (D29)."""

    unfinished = UNFINISHED
    gpu_kind = "transcribe"
    nothing_to_cancel = "ไม่มีงานถอดที่ยังไม่จบ"
    error_type = TranscribeJobError
    failure = "ถอดไม่สำเร็จ"
    ending_fields = {"percent": None}  # `percent` is only for `transcribing` (spec › API)

    def start(self, clip_id: str, confirm_edit_loss: bool = False, confirm_draft_loss: bool = False) -> TranscribeJob:
        """Checks in spec order, then starts the job's thread. Raises `ApiError`.

        A clip with edited lines needs `confirm_edit_loss`: the new Transcript replaces them (spoil-maker D54).
        A clip in the Spoil draft needs `confirm_draft_loss`: a `done` job removes the draft (spoil-maker D49).
        """
        project = paths.project()
        require_rows(_needed_rows(project))
        # The gate just found a GPU and DeviceProbe caches it, so this is that same device.
        device = checks.probe_device()
        with self._lock, clips.files_lock:
            mp4 = clips.video_file(project, clip_id)  # 404 unless both json and mp4 are there
            _refuse_trimming(clip_id)
            if self._taken():
                raise ApiError(409, "busy", "กำลังถอดคลิปอื่นอยู่")
            if not confirm_edit_loss and _has_edits(project, clip_id):
                raise ApiError(409, "has_edits", "ถอดใหม่จะลบบทพูดที่แก้ไว้")
            clip = clips.read_clip(project, clip_id)
            # Last: Whisper can't share the GPU with another model (spoil-maker D45, ADR 0015).
            draft_file.take_gpu_to_redo(project, clip_id, "transcribe", confirm_draft_loss)
            self._job = TranscribeJob(clip_id=clip_id, state="preparing")
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        thread = threading.Thread(target=self._run, args=(project, clip, mp4, device), daemon=True)
        thread.start()
        return job

    def transcribing(self, clip_id: str) -> bool:
        """Whether a Transcribe job of that clip is still running. Call under
        `clips.files_lock`: a job starts only under it, so one can't start meanwhile. Reads
        the job without the slot's lock (one attribute read), so a Trim job can ask under
        `files_lock` without breaking the lock order; a job ending meanwhile reads as running."""
        job = self._job
        return job is not None and job.state in self.unfinished and job.clip_id == clip_id

    def delete_clip(self, clip_id: str) -> None:
        """Deletes a clip's files unless it is being transcribed (D27) or another GPU job
        reads it (`clip_busy`, spoil-maker D49). The checks and the delete share the locks
        the jobs start under, so neither slips between the other (D29)."""
        with clips.files_lock:
            if self.transcribing(clip_id):
                raise ApiError(409, "transcribing", "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ")
            _refuse_trimming(clip_id)
            project = paths.project()
            with gpu.slot.clip_untouched(clip_id):
                clips.delete_clip(project, clip_id)
            # After the slot's lock (its lock comes after the draft's), and only once the clip is gone (D29).
            draft_file.drop_if_uses(project, clip_id)
            # The Story it remembers goes with it; `stories`' lock is the innermost (story-kb D7, D16).
            stories.forget_clip(project, clip_id)

    def edit_line(self, clip_id: str, n: str, text: str) -> TranscriptLine:
        """Replaces line `n`'s text and marks it edited; times and line count stay,
        so whatever points at a line by its index still holds (spoil-maker D54, ADR 0018).
        Under `clips.files_lock`, so neither a Transcribe job's start nor a Trim job's new mp4
        comes between the check and the write."""
        # One line stays one line: a line break would add lines to `.txt` and split an `.srt` cue.
        text = " ".join(text.split())
        if not text:
            raise ApiError(400, "invalid_request", "บรรทัดต้องมีข้อความ")
        project = paths.project()
        with clips.files_lock:
            transcript = read_transcript(project, clip_id)
            # `n` comes as text so `x` and `-1` are 404, not a validation error; ASCII digits only.
            index = int(n) if n.isascii() and n.isdigit() else -1
            if not 0 <= index < len(transcript.lines):
                raise ApiError(404, "not_found", "ไม่พบบรรทัดนี้")
            if self.transcribing(clip_id):
                raise ApiError(409, "transcribing", "กำลังถอดคลิปนี้อยู่ รอให้ถอดเสร็จก่อนแล้วแก้")
            _refuse_trimming(clip_id)
            if any(in_use(clip_id) for in_use in clip_users):
                raise ApiError(409, "clip_busy", "คลิปนี้กำลังถูกใช้ในงานอื่น")
            line = transcript.lines[index]
            line.text, line.edited = text, True
            write_transcript(project, transcript)
            return line

    def _run(self, project: ProjectPaths, clip: clips.TempClip, mp4: Path, device: str) -> None:
        def steps() -> None:
            snapshot = project.snapshot_dir(WHISPER, WHISPER.revision)
            process, queue = spoil.start_worker(mp4, clip.duration_s, snapshot, device)
            self.track(process)
            segments = self._read_segments(process, queue)
            write_transcript(project, _build_transcript(clip, segments))
            draft_file.drop_if_uses(project, clip.id)  # the user confirmed (spoil-maker D49)

        self._run_job(f"transcribing {clip.id}", steps)

    def _read_segments(self, process, queue) -> list[Segment]:
        """Reads the child's messages until `Done`. Raises `Cancelled` or `JobFailed`."""
        segments: list[Segment] = []
        while True:
            try:
                message = next_message(process, queue, self._cancel)
            except ChildGone as gone:
                raise JobFailed("crashed", f"ตัวถอดหยุดทำงานกลางทาง ({gone}). {gpu.ADVICE}") from None
            if isinstance(message, Done):
                return segments
            if isinstance(message, WorkerError):
                raise _worker_error(message)
            if not isinstance(message, Segment):
                raise RuntimeError(f"unknown message from the Whisper process: {message!r}")
            segments.append(message)
            self.update(state="transcribing", percent=(message.index + 1) * 100 // message.total)


def _worker_error(error: WorkerError) -> JobFailed:
    log.error("the Whisper process failed (%s): %s", error.code, error.detail)
    if error.code == "no_audio":
        return JobFailed("no_audio", "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้")
    return JobFailed("model_failed", f"ถอดไม่สำเร็จ: {short(error.detail)}. {gpu.ADVICE}")


def _needed_rows(project: ProjectPaths) -> dict[str, Row]:
    """The Status check rows a transcription needs (D27), by id; the frontend's
    `TRANSCRIBE_ITEMS` gates on the same rows."""
    packages: dict[str, Row] = {
        "torch": ("torch", lambda: checks.check_package("torch")),
        "transformers": ("transformers", lambda: checks.check_package("transformers")),
    }
    whisper: dict[str, Row] = {WHISPER.check_id: (WHISPER.label, lambda: checks.check_model(project, WHISPER))}
    return packages | gate_rows.FFMPEG | whisper | gate_rows.DEVICE


def _refuse_trimming(clip_id: str) -> None:
    """A clip a Trim job cuts can't be transcribed, edited or deleted until it ends (D41)."""
    if gpu.slot.is_trimming(clip_id):
        raise ApiError(409, "trimming", "กำลังตัดคลิปนี้อยู่")


def _has_edits(project: ProjectPaths, clip_id: str) -> bool:
    if not clips.transcript_path(project, clip_id).is_file():
        return False
    return any(line.edited for line in read_transcript(project, clip_id).lines)


def _build_transcript(clip: clips.TempClip, segments: list[Segment]) -> Transcript:
    lines = [
        TranscriptLine(start_s=start, end_s=end, text=text.strip())
        for segment in segments
        for start, end, text in segment.lines
        if text.strip()
    ]
    lines.sort(key=lambda line: line.start_s)
    return Transcript(
        clip_id=clip.id,
        language=_language([segment.language for segment in segments]),
        duration_s=clip.duration_s,
        model=WHISPER.repo_id,
        revision=WHISPER.short_revision,
        transcribed_at=checks.now_iso(),
        lines=lines,
    )


def _language(languages: list[str | None]) -> str | None:
    """What most segments detected; a tie goes to the earlier segment (D29)."""
    counts = Counter(language for language in languages if language)
    if not counts:
        return None
    most = max(counts.values())
    return next(language for language in languages if counts.get(language) == most)


def write_transcript(project: ProjectPaths, transcript: Transcript) -> None:
    """Through a temporary file, so a crash never leaves half a transcript (D27)."""
    target = clips.transcript_path(project, transcript.clip_id)
    files.write_atomic(target, transcript.model_dump_json(indent=2))


def read_transcript(project: ProjectPaths, clip_id: str) -> Transcript:
    """A clip's Transcript. Raises `ApiError` 404 when the clip or its Transcript isn't there."""
    clips.check_known(project, clip_id)
    path = clips.transcript_path(project, clip_id)
    if not path.is_file():
        raise ApiError(404, "not_found", "คลิปนี้ยังไม่ได้ถอดบทพูด")
    try:
        return Transcript.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        log.exception("could not read %s", path)
        raise ApiError(404, "not_found", "อ่าน Transcript ไม่ได้ ถอดใหม่อีกครั้ง") from None


def transcript_txt(project: ProjectPaths, clip_id: str) -> str:
    return to_txt(read_transcript(project, clip_id))


def transcript_srt(project: ProjectPaths, clip_id: str) -> str:
    return to_srt(read_transcript(project, clip_id))


def to_txt(transcript: Transcript) -> str:
    """One `[hh:mm:ss] text` per line (D22)."""
    return "".join(f"[{clock.hms(line.start_s)}] {line.text}\n" for line in transcript.lines)


def to_srt(transcript: Transcript) -> str:
    """Standard SRT, a cue per line."""
    return clock.srt((line.start_s, line.end_s, line.text) for line in transcript.lines)


transcriptions = Transcriptions()
