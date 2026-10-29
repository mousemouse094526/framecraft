"""The Transcribe job: one at a time, a backend thread that owns the state and the
file, and a child process that runs Whisper (ADR 0010, ADR 0012).

Steps and rules are in docs/features/spoil/spec.md › Transcribe (D23, D24, D27, D28, D29).
"""

import logging
import threading
from collections import Counter
from pathlib import Path
from queue import Empty
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import checks, paths, spoil
from backend.models import WHISPER
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.spoil.errors import JobFailed, SpoilError, require_rows
from backend.spoil.job_slot import JobSlot
from backend.spoil.whisper import Done, Segment, WorkerError

log = logging.getLogger(__name__)

State = Literal["preparing", "transcribing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"preparing", "transcribing"})
ErrorCode = Literal["no_audio", "model_failed", "crashed", "internal"]

POLL_SECONDS = 0.2  # how often the thread looks at the cancel flag while the child works
TERMINATE_SECONDS = 5  # a child that ignores SIGTERM this long is killed

GPU_ADVICE = "ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง"


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


class Transcript(BaseModel):
    clip_id: str
    language: str | None
    duration_s: int | None
    model: str
    revision: str
    transcribed_at: str
    lines: list[TranscriptLine]


class _Cancelled(Exception):
    pass


class Transcriptions(JobSlot[TranscribeJob]):
    """Holds the latest Transcribe job. Its lock also guards every clip delete (D29)."""

    unfinished = UNFINISHED

    def __init__(self):
        super().__init__()
        self._process = None  # the running child, for shutdown

    def start(self, clip_id: str) -> TranscribeJob:
        """Checks in spec order, then starts the job's thread. Raises `SpoilError`."""
        project = ProjectPaths(paths.ROOT)
        require_rows(_needed_rows(project))
        # The gate just found a GPU and DeviceProbe caches it, so this is that same device.
        device = checks.probe_device()
        with self._lock:
            mp4 = clips.video_file(project, clip_id)  # 404 unless both json and mp4 are there
            if self._taken():
                raise SpoilError(409, "busy", "กำลังถอดคลิปอื่นอยู่")
            clip = clips.read_clip(project, clip_id)
            self._job = TranscribeJob(clip_id=clip_id, state="preparing")
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        thread = threading.Thread(target=self._run, args=(project, clip, mp4, device), daemon=True)
        thread.start()
        return job

    def cancel(self) -> TranscribeJob:
        """Asks the thread to terminate the child; the job ends as `cancelled`."""
        with self._lock:
            if not self._taken():
                raise SpoilError(404, "not_found", "ไม่มีงานถอดที่ยังไม่จบ")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def delete_clip(self, clip_id: str) -> None:
        """Deletes a clip's files unless it is being transcribed (D27). The check and
        the delete share the lock `start` holds, so neither slips between the other (D29)."""
        with self._lock:
            if self._taken() and self._job.clip_id == clip_id:
                raise SpoilError(409, "transcribing", "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ")
            clips.delete_clip(ProjectPaths(paths.ROOT), clip_id)

    def stop_on_shutdown(self) -> None:
        """Ctrl+C must not leave a child holding the GPU (D28). A child started after
        this sees the cancel flag at its first poll and is stopped by its thread."""
        self._cancel.set()
        with self._lock:
            process = self._process
        if process is not None:
            _stop(process)

    def _run(self, project: ProjectPaths, clip: clips.TempClip, mp4: Path, device: str) -> None:
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        process = None
        try:
            snapshot = project.snapshot_dir(WHISPER, WHISPER.revision)
            process, queue = spoil.start_worker(mp4, clip.duration_s, snapshot, device)
            with self._lock:
                self._process = process
            segments = self._read_segments(process, queue)
            write_transcript(project, _build_transcript(clip, segments))
            ending = {"state": "done"}
        except _Cancelled:
            ending = {"state": "cancelled"}
        except JobFailed as failure:
            error = TranscribeJobError(code=failure.code, message=failure.message)
            ending = {"state": "failed", "error": error}
        except Exception as error:
            log.exception("transcribing %s failed", clip.id)  # the full error, for [api]
            message = f"ถอดไม่สำเร็จ: {_short(error)}"
            ending = {"state": "failed", "error": TranscribeJobError(code="internal", message=message)}
        finally:
            # Whatever happened, the job must end, or every later POST is `busy` (D29).
            if process is not None:
                try:
                    _stop(process)
                except Exception:
                    log.exception("could not stop the Whisper process")
            with self._lock:
                self._process = None
            # `percent` is only for `transcribing` (spec › API), so a finished job has none.
            self._update(percent=None, **ending)

    def _read_segments(self, process, queue) -> list[Segment]:
        """Reads the child's messages until `Done`. Raises `_Cancelled` or `JobFailed`."""
        segments: list[Segment] = []
        while True:
            if self._cancel.is_set():
                raise _Cancelled()
            try:
                message = queue.get(timeout=POLL_SECONDS)
            except Empty:
                if process.is_alive():
                    continue
                # The child is gone. A queue flushes before its process exits, so one
                # more read gets anything it sent last; nothing there means it crashed.
                try:
                    message = queue.get(timeout=POLL_SECONDS)
                except Empty:
                    raise JobFailed(
                        "crashed", f"ตัวถอดหยุดทำงานกลางทาง (exit {process.exitcode}). {GPU_ADVICE}"
                    ) from None
            if isinstance(message, Done):
                return segments
            if isinstance(message, WorkerError):
                raise _worker_error(message)
            if not isinstance(message, Segment):
                raise RuntimeError(f"unknown message from the Whisper process: {message!r}")
            segments.append(message)
            self._update(state="transcribing", percent=(message.index + 1) * 100 // message.total)


def _stop(process) -> None:
    """Terminates a child that is still running, then kills it if it won't go."""
    if process.is_alive():
        process.terminate()
        process.join(TERMINATE_SECONDS)
        if process.is_alive():
            process.kill()
    process.join(TERMINATE_SECONDS)


def _worker_error(error: WorkerError) -> JobFailed:
    log.error("the Whisper process failed (%s): %s", error.code, error.detail)
    if error.code == "no_audio":
        return JobFailed("no_audio", "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้")
    return JobFailed("model_failed", f"ถอดไม่สำเร็จ: {_short(error.detail)}. {GPU_ADVICE}")


def _short(error: Exception | str) -> str:
    """The first line of an error, for a message; the full one goes to the log."""
    text = str(error).strip()
    return text.splitlines()[0][:200] if text else type(error).__name__


def _needed_rows(project: ProjectPaths) -> dict[str, checks.Check]:
    """The Status check rows a transcription needs (D27), by label; the frontend's
    `TRANSCRIBE_ITEMS` gates on the same rows.

    `device` is a warning on `cpu`, which doesn't pass here (ADR 0006).
    """
    return {
        "torch": lambda: checks.check_package("torch"),
        "transformers": lambda: checks.check_package("transformers"),
        "ffmpeg": lambda: checks.check_ffmpeg(checks.probe_ffmpeg),
        WHISPER.label: lambda: checks.check_model(project, WHISPER),
        "Device": lambda: checks.check_device(checks.probe_device),
    }


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
    clips.write_atomic(target, transcript.model_dump_json(indent=2))


def read_transcript(project: ProjectPaths, clip_id: str) -> Transcript:
    """A clip's Transcript. Raises `SpoilError` 404 when the clip or its Transcript isn't there."""
    clips.check_known(project, clip_id)
    path = clips.transcript_path(project, clip_id)
    if not path.is_file():
        raise SpoilError(404, "not_found", "คลิปนี้ยังไม่ได้ถอดบทพูด")
    try:
        return Transcript.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        log.exception("could not read %s", path)
        raise SpoilError(404, "not_found", "อ่าน Transcript ไม่ได้ ถอดใหม่อีกครั้ง") from None


def transcript_txt(project: ProjectPaths, clip_id: str) -> str:
    return to_txt(read_transcript(project, clip_id))


def transcript_srt(project: ProjectPaths, clip_id: str) -> str:
    return to_srt(read_transcript(project, clip_id))


def to_txt(transcript: Transcript) -> str:
    """One `[hh:mm:ss] text` per line (D22)."""
    return "".join(f"[{_clock(line.start_s)}] {line.text}\n" for line in transcript.lines)


def to_srt(transcript: Transcript) -> str:
    """Standard SRT: numbered from 1, `hh:mm:ss,mmm --> hh:mm:ss,mmm`, a blank line between cues."""
    cues = [
        f"{number}\n{_srt_time(line.start_s)} --> {_srt_time(line.end_s)}\n{line.text}\n"
        for number, line in enumerate(transcript.lines, start=1)
    ]
    return "\n".join(cues)


def _clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"


def _srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    return f"{_clock(millis // 1000)},{millis % 1000:03d}"


transcriptions = Transcriptions()
