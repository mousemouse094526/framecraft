"""The Describe job: one at a time, a backend thread that owns the state and every
file, ffmpeg for the cuts and frames, and a child process that runs Qwen (ADR 0010,
ADR 0012, ADR 0015). Also reads the Shots it leaves, for the API.

Steps and rules are in docs/features/spoil-maker/spec.md › Describe job (D15, D16, D17, D51).
"""

import logging
import re
import shutil
import threading
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, gate_rows, gpu, paths, spoil_maker
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.errors import ApiError, JobFailed, require_rows
from backend.jobs import Cancelled, ModelJobSlot
from backend.spoil_maker import draft_file, episodes, frames, shots
from backend.ffmpeg import FfmpegFailed
from backend.spoil_maker.llm import Generate, Generated, Ready, WorkerError

log = logging.getLogger(__name__)

State = Literal["cutting", "describing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"cutting", "describing"})
ErrorCode = Literal["crashed", "model_failed", "ffmpeg_failed", "internal"]

# llm-trial › รอบ 2: English, short, one frame at a time.
DESCRIBE_PROMPT = "Describe this frame in English in no more than 30 words."
DESCRIBE_MAX_TOKENS = 80
DESCRIBE_TEMPERATURE = 0.0
DESCRIBE_TIMEOUT_SECONDS = 60  # per Shot; longer and the child is terminated (spec › ค่าการสร้างข้อความ)

SHOT_IMAGE = re.compile(r"(\d{1,5})\.jpg")


class DescribeJobError(BaseModel):
    code: ErrorCode
    message: str


class DescribeJob(BaseModel):
    """Every spoil-maker job has these fields; the ones a kind doesn't use stay null (spec › API)."""

    kind: Literal["describe"] = "describe"
    state: State
    clip_id: str
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    error: DescribeJobError | None = None
    cancel_requested: bool = False
    started_at: str


class Describes(ModelJobSlot[DescribeJob]):
    """Holds the latest Describe job."""

    unfinished = UNFINISHED
    gpu_kind = "describe"
    nothing_to_cancel = "ไม่มีงานบรรยายฉากที่ยังไม่จบ"
    worker_error = WorkerError
    child_name = "ตัวบรรยายฉาก"
    failure = "บรรยายฉากไม่สำเร็จ"
    error_type = DescribeJobError

    def __init__(self, find_cuts: frames.CutFinder = frames.find_cuts):
        """`find_cuts` reads the scene cuts; a test passes one that pauses or makes up cuts."""
        super().__init__()
        self._find_cuts = find_cuts

    def start(self, clip_id: str, confirm_draft_loss: bool = False) -> DescribeJob:
        """Checks in spec order (404, the gate, `busy`, `in_draft`, `gpu_busy`), then starts the job's thread.

        A clip in the Spoil draft needs `confirm_draft_loss`: new Shots make the draft's
        Shot numbers point at other pictures, so a `done` job removes it (D49).
        """
        project = paths.project()
        clips.video_file(project, clip_id)
        require_rows(gate_rows.qwen_jobs(project))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "กำลังบรรยายฉากคลิปอื่นอยู่")
            draft_file.take_gpu_to_redo(project, clip_id, "describe", confirm_draft_loss)
            try:
                # Again under the slot: a delete may have run since the first look, and none can now.
                mp4 = clips.video_file(project, clip_id)
                clip = clips.read_clip(project, clip_id)
            except ApiError:
                gpu.slot.release("describe")
                raise
            self._job = DescribeJob(clip_id=clip_id, state="cutting", percent=0, started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        thread = threading.Thread(target=self._run, args=(project, clip, mp4), daemon=True)
        thread.start()
        return job

    def _run(self, project: ProjectPaths, clip: clips.TempClip, mp4: Path) -> None:
        new = project.new_shots_dir(clip.id)

        def clean_up(state: str) -> None:
            if state != "done":
                shutil.rmtree(new, ignore_errors=True)  # the old Shots stay (D51)

        def steps() -> None:
            try:
                self._describe(project, clip, mp4, new)
            except FfmpegFailed as error:
                log.error("ffmpeg failed on %s: %s", clip.id, error)
                raise JobFailed("ffmpeg_failed", "อ่านภาพจากคลิปไม่ได้") from None

        self._run_job(f"describing {clip.id}", steps, clean_up)

    def _describe(self, project: ProjectPaths, clip: clips.TempClip, mp4: Path, new: Path) -> None:
        shutil.rmtree(new, ignore_errors=True)
        (new / "frames").mkdir(parents=True)
        spans = self._cut(mp4, clip.duration_s)
        self._update(state="describing", percent=None, done=0, total=len(spans))
        process, requests, replies = spoil_maker.start_worker(project.snapshot_dir(QWEN, QWEN.revision))
        self._track(process)
        self._reply(process, replies, (Ready,))  # loading has no timeout
        described = []
        for n, (start, end) in enumerate(spans):
            frame = new / "frames" / f"{n}.jpg"
            # The middle frame: the start and end of a Shot blur into its neighbours (D17).
            frames.extract_frame(mp4, (start + end) / 2, thumbnail=new / f"{n}.jpg", llm_frame=frame)
            requests.put(Generate(DESCRIBE_PROMPT, frame, DESCRIBE_MAX_TOKENS, DESCRIBE_TEMPERATURE))
            try:
                reply = self._reply(process, replies, (Generated,), DESCRIBE_TIMEOUT_SECONDS)
            except TimeoutError:
                raise JobFailed("model_failed", f"บรรยายภาพเกิน {DESCRIBE_TIMEOUT_SECONDS:g} วินาที. {gpu.ADVICE}") from None
            described.append(shots.Shot(n=n, start=round(start, 3), end=round(end, 3), description=reply.text.strip()))
            self._update(done=n + 1)
        requests.put(None)
        result = shots.ShotsFile(clip_id=clip.id, shots=described)
        (new / shots.SHOTS_FILE).write_text(result.model_dump_json(indent=2), encoding="utf-8")
        shutil.rmtree(new / "frames")
        _swap(project, clip.id)
        draft_file.drop_if_uses(project, clip.id)  # the user confirmed (D49)

    def _cut(self, mp4: Path, duration_s: int | None) -> list[tuple[float, float]]:
        """`cutting`: the scene filter's cut times, as Shot spans. Raises `Cancelled`."""

        def on_progress(at_s: float) -> None:
            # 100 waits for the cut list: ffmpeg reads the last second before it ends.
            if duration_s:
                self._update(percent=min(99, int(at_s * 100 / duration_s)))

        cuts, duration = self._find_cuts(mp4, on_progress, self._cancel)
        if self._cancel.is_set():
            raise Cancelled()
        return shots.plan_shots(cuts, duration)

def _swap(project: ProjectPaths, clip_id: str) -> None:
    """The new Shots replace the old ones only now, at the end (D51). The clip's EP cuts sit
    on the old Shots' edges, so they go under the same lock (spec › EP, D71)."""
    target = project.clip_shots_dir(clip_id)
    with gpu.slot.clip_files_lock():
        shutil.rmtree(target, ignore_errors=True)
        project.new_shots_dir(clip_id).rename(target)
        episodes.remove(project, clip_id)


def clip_shots(project: ProjectPaths, clip_id: str) -> shots.ShotsFile:
    """A described clip's Shots. Raises `ApiError` 404 `not_found` for an unknown
    clip, `not_described` for one never described."""
    clips.check_known(project, clip_id)
    found = shots.read_shots(project, clip_id)
    if found is None:
        raise ApiError(404, "not_described", "คลิปนี้ยังไม่ได้บรรยายฉาก")
    return found


def shot_image(project: ProjectPaths, clip_id: str, name: str) -> Path:
    """`{n}.jpg` of a described clip. Only a Shot number of that clip gets near the disk."""
    clips.check_known(project, clip_id)
    found = shots.read_shots(project, clip_id)
    match = SHOT_IMAGE.fullmatch(name)
    path = project.clip_shots_dir(clip_id) / name
    if found is None or match is None or int(match.group(1)) >= len(found.shots) or not path.is_file():
        raise ApiError(404, "not_found", "ไม่พบภาพนี้")
    return path


describes = Describes()
