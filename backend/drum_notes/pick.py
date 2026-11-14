"""The Pick job of the แกะเพลง tab (drum-notes spec › Pick job, D5, D6, D8, D14, D18, D20; ADR 0043):
one at a time for the whole tab, a plain `JobSlot` in a thread that holds no GPU slot. It reads the
song's range once, has ffmpeg decode that stretch of `audio.m4a` as raw PCM at the rates the models
take (`preparing`), runs the mode's model — ADTOF once over the whole stretch in drums mode, Basic
Pitch window by window in melody mode — then Beat This! chunk by chunk (`picking`, `percent` per
model run, cancel checked between them), turns the arrays into an `analysis` through `score`, and
writes it into `song.json` in place of the old one (`done`).
"""

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import BaseModel

from backend import checks, ffmpeg, gate_rows, models, paths
from backend.checks import now_iso
from backend.drum_notes import onnx_runner, score, songs
from backend.drum_notes.onnx_runner import OpenSession, Session
from backend.drum_notes.songs import Analysis, Hit, Mode, Range, Song
from backend.errors import ApiError, JobFailed, require_rows
from backend.ffmpeg import CaptureRunner, FfmpegFailed
from backend.jobs import Cancelled, JobSlot, short
from backend.models import ModelSpec
from backend.paths import ProjectPaths

if TYPE_CHECKING:
    import numpy as np

log = logging.getLogger(__name__)

T = TypeVar("T")
State = Literal["preparing", "picking", "done", "failed", "cancelled"]
ErrorCode = Literal["no_beats", "model_broken", "model_failed", "internal"]

ADTOF_RATE = 44_100
MODELS_RATE = score.BASIC_PITCH_RATE  # 22,050 Hz: Beat This! and Basic Pitch both take it, so melody mode decodes once
NOT_RUNNING = "ไม่มีงานแกะโน้ตที่ยังไม่จบ"
BUSY = "กำลังแกะ {title} อยู่ รอให้เสร็จก่อน"  # the song being picked, by title (spec › Design: `busy` names it)
NO_BEATS = "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น"
MODEL_BROKEN = "ไฟล์โมเดลเสีย รัน Setup script ใหม่"
MODEL_FAILED = "โมเดลทำงานผิดพลาด"
FAILED = "แกะโน้ตไม่สำเร็จ"


class Steps:
    """The model runs of one job — the mode's model (one run of ADTOF, or one per Basic Pitch window) and
    one per Beat This! chunk — and how many are done: the job's `percent` is their ratio (D18, D20)."""

    def __init__(self, total: int):
        self.total, self.done = total, 0

    def done_one(self) -> int:
        """One more run finished: the percent to show, 99 at most until the analysis is written."""
        self.done += 1
        return min(99, self.done * 100 // self.total)


class PickJob(BaseModel):
    """`GET /api/songs/pick`: the latest job."""

    song_id: str
    state: State
    percent: int
    error: ErrorCode | None = None
    message: str | None = None
    rows: list[str] | None = None  # `model_broken`: the Status check row of the file that won't open
    fix: str | None = None  # `model_broken`: the Setup script's command
    cancel_requested: bool = False
    started_at: str


class ModelBroken(JobFailed):
    """A model file onnxruntime can't open: `failed` `model_broken` with the row and the fix (D20)."""

    def __init__(self, model: ModelSpec):
        super().__init__("model_broken", f"{MODEL_BROKEN} ({model.label})")
        self.rows, self.fix = [model.check_id], checks.setup_fix()


class PickJobs(JobSlot[PickJob]):
    """Holds the latest Pick job. `open_session` opens a model file and `run_ffmpeg` decodes the
    stretch; a test passes stand-ins (`fastapi-api` › testing, D17)."""

    unfinished = frozenset({"preparing", "picking"})
    nothing_to_cancel = NOT_RUNNING
    cancel_refusal = (409, "not_running")  # spec › API; `cancel` kills ffmpeg, or the next model call never starts

    def __init__(self, open_session: OpenSession = onnx_runner.open_session, run_ffmpeg: CaptureRunner = ffmpeg.run_capture):
        super().__init__()
        self._open_session = open_session
        self._run_ffmpeg = run_ffmpeg
        self._steps = Steps(0)  # the running job's, set when it starts picking: a `JobSlot` runs one job at a time

    def song_use(self) -> str | None:
        """The song an unfinished job works on (`songs.song_jobs`): it can't be deleted meanwhile (D18)."""
        job = self.running()
        return job.song_id if job else None

    def start(self, song_id: str) -> PickJob:
        """Spec › Pick job steps 1–5, in order: the song (404; a MIDI song has nothing to pick, 409
        `not_applicable`), the gate of its mode (503), `busy` (409 with the running song), its range
        (400), then the thread. The job is set under `songs.lock` too (this slot's lock first, as the
        lock order says), so a delete that checks `song_busy` under that lock never slips between the
        song's read and the job's start. The range is read once here: a `PUT /range` meanwhile reaches the next job."""
        project = paths.project()
        with songs.lock:
            range_ = _pickable(songs.read_under_lock(project, song_id))
        require_rows(gate_rows.PICK_GATES[range_.mode](project))
        with self._lock:
            running = self.running()
            if running is not None:
                raise ApiError(409, "busy", BUSY.format(title=_title_of(project, running.song_id)), song_id=running.song_id)
            with songs.lock:
                song = songs.read_under_lock(project, song_id)  # again: it may have gone or changed since the checks above
                range_ = _pickable(song)
                self._job = PickJob(song_id=song_id, state="preparing", percent=0, started_at=now_iso())
                self._cancel.clear()
                job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, song, range_), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, song: Song, range_: Range) -> None:
        started = time.monotonic()
        ending: dict = {"state": "failed", "error": "internal", "message": FAILED}
        try:
            analysis = self._pick(project, song, range_)
            songs.set_analysis(project, song.id, analysis)
            ending = {"state": "done", "percent": 100}
        except Cancelled:
            ending = {"state": "cancelled"}
        except ModelBroken as broken:
            ending = {"state": "failed", "error": "model_broken", "message": broken.message, "rows": broken.rows, "fix": broken.fix}
        except JobFailed as failed:
            ending = {"state": "failed", "error": failed.code, "message": failed.message}
        except FfmpegFailed as error:
            ending = {"state": "failed", "error": "internal", "message": f"{FAILED}: {error.last_line}"}
        except Exception as error:
            log.exception("pick of %s failed", song.id)
            ending = {"state": "failed", "error": "internal", "message": f"{FAILED}: {short(error)}"}
        finally:
            self.update(**ending)
            log.info("pick of %s ended %s after %.1f s", song.id, ending["state"], time.monotonic() - started)

    def _pick(self, project: ProjectPaths, song: Song, range_: Range) -> Analysis:
        """`preparing` then `picking`: the arrays of the mode's model and of Beat This!, scored into
        an analysis in seconds of the song. Raises `Cancelled`, `ModelBroken`, `JobFailed`
        (`model_failed`, `no_beats`), `FfmpegFailed`."""
        import numpy as np

        audio = songs.audio_file(project, song.id)
        pcm22 = np.frombuffer(self._run_ffmpeg(_decode(audio, range_, MODELS_RATE), self._cancel), np.float32)
        frames = score.beat_this_frames(len(pcm22))
        chunks = score.beat_this_chunks(frames)
        hits = HITS_BY_MODE[range_.mode](self, project, audio, range_, pcm22, len(chunks))

        self._check_cancel()
        beat_this = self._open(project, models.BEAT_THIS)
        outputs = []
        for chunk in chunks:
            self._check_cancel()
            samples = score.chunk_samples(pcm22, chunk)
            outputs.append((chunk, _run_model(lambda: onnx_runner.run_beat_this(beat_this, samples, chunk.pad_before, chunk.pad_after))))
            self._step_done()

        self._check_cancel()  # a cancel that came during the last chunk: nothing is written (D20)
        beat = score.stitch(frames, [(chunk, logits[0]) for chunk, logits in outputs])
        downbeat = score.stitch(frames, [(chunk, logits[1]) for chunk, logits in outputs])
        beats, downbeats = score.beats_and_downbeats(beat, downbeat, range_.start_s)
        if len(downbeats) < 2:
            raise JobFailed("no_beats", NO_BEATS)
        return Analysis(mode=range_.mode, start_s=range_.start_s, end_s=range_.end_s, beats=beats, downbeats=downbeats, hits=hits, picked_at=now_iso())

    def _drum_hits(self, project: ProjectPaths, audio: Path, range_: Range, pcm22: "np.ndarray", chunks: int) -> list[Hit]:
        """Drums mode: the stretch decoded again at ADTOF's rate, then ADTOF over the whole of it in
        one run (an RNN, D20), peak-picked into hits; `picking` counts that run and the `chunks` of Beat This!."""
        import numpy as np

        pcm44 = np.frombuffer(self._run_ffmpeg(_decode(audio, range_, ADTOF_RATE), self._cancel), np.float32)
        self._start_picking(1 + chunks)
        self._check_cancel()
        adtof = self._open(project, models.ADTOF)
        activations = _run_model(lambda: onnx_runner.run_adtof(adtof, pcm44))
        self._step_done()
        return score.drum_hits(activations, range_.start_s)

    def _melody_hits(self, project: ProjectPaths, audio: Path, range_: Range, pcm22: "np.ndarray", chunks: int) -> list[Hit]:
        """Melody mode: Basic Pitch window by window over the 22.05 kHz stretch Beat This! takes too,
        cancel checked before each, its onsets as snares (D14); `picking` counts the windows and the `chunks`."""
        windows = score.basic_pitch_windows(len(pcm22))
        self._start_picking(len(windows) + chunks)
        self._check_cancel()
        basic_pitch = self._open(project, models.BASIC_PITCH)
        outputs = []
        for window in windows:
            self._check_cancel()
            samples = score.window_samples(pcm22, window)
            outputs.append((window, _run_model(lambda: onnx_runner.run_basic_pitch(basic_pitch, samples))))
            self._step_done()
        return score.melody_hits(outputs, len(pcm22), range_.start_s)

    def _start_picking(self, runs: int) -> None:
        """ffmpeg is done: `picking` from 0 %, over `runs` model runs."""
        self._steps = Steps(runs)
        self.update(state="picking", percent=0)

    def _step_done(self) -> None:
        self.update(percent=self._steps.done_one())

    def _open(self, project: ProjectPaths, model: ModelSpec) -> Session:
        """A session of the model's one file in its snapshot; a file that won't open is `ModelBroken`."""
        [pattern] = model.allow_patterns
        try:
            return self._open_session(project.snapshot_dir(model, model.revision) / pattern)
        except Exception as error:
            log.error("%s won't open: %s", model.label, short(error))
            raise ModelBroken(model) from None

    def _check_cancel(self) -> None:
        if self._cancel.is_set():
            raise Cancelled()


# The mode's model run, before Beat This!: what hears the hits and how many `picking` steps it takes (D14).
HitsRun = Callable[[PickJobs, ProjectPaths, Path, Range, "np.ndarray", int], list[Hit]]
HITS_BY_MODE: dict[Mode, HitsRun] = {"drums": PickJobs._drum_hits, "melody": PickJobs._melody_hits}


def _pickable(song: Song) -> Range:
    """The range a Pick job of the song would work on. A MIDI song has none (its hits are its analysis
    already: 409 `not_applicable`, D18); an audio song's is checked against the rules once more, as a
    `song.json` written by hand may break them (spec › Pick job step 4)."""
    if song.source.kind == "midi" or song.range is None:
        raise ApiError(409, "not_applicable", songs.NOT_APPLICABLE)
    return songs.checked_range(song.range.model_dump(), song.duration_s)


def _title_of(project: ProjectPaths, song_id: str) -> str:
    """The title of the song a job is picking, for `busy`; a song that went meanwhile is "เพลงอื่น"."""
    try:
        with songs.lock:
            return songs.read_under_lock(project, song_id).title
    except ApiError:
        return "เพลงอื่น"


def _run_model(run: Callable[[], T]) -> T:
    """One model call: anything it raises ends the job `model_failed` with the error's first line (D18)."""
    try:
        return run()
    except Exception as error:
        raise JobFailed("model_failed", f"{MODEL_FAILED}: {short(error)}") from error


def _decode(audio: Path, range_: Range, rate: int) -> list[str]:
    """ffmpeg: the stretch `[start_s, end_s)` of the song as float32 mono at `rate` on stdout
    (docs/library-notes/ffmpeg.md: `-ss` before `-i` seeks, `-t` after it limits the length)."""
    return [
        ffmpeg.exe(), "-hide_banner", "-nostdin", "-v", "error",
        "-ss", f"{range_.start_s:.3f}", "-t", f"{range_.end_s - range_.start_s:.3f}", "-i", str(audio),
        "-vn", "-ac", "1", "-ar", str(rate), "-f", "f32le", "-",
    ]  # fmt: skip


pick_jobs = PickJobs()
songs.song_jobs.append(lambda: pick_jobs.song_use())
