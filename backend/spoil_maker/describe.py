"""The Describe job: one at a time, a backend thread that owns the state and every
file, ffmpeg for the cuts and frames, and a child process that runs Qwen (ADR 0010,
ADR 0012, ADR 0015). Also reads the Shots it leaves, for the API.

Steps and rules are in docs/features/spoil-maker/spec.md › Describe job (D15, D16, D17, D51).
"""

import logging
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, gpu, paths, spoil_maker
from backend.models import QWEN
from backend.paths import ProjectPaths
from backend.spoil import clips
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import Cancelled, ModelJobSlot, short
from backend.spoil_maker import draft_file, frames, shots
from backend.spoil_maker.frames import FfmpegFailed
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

    def start(self, clip_id: str, confirm_draft_loss: bool = False) -> DescribeJob:
        """Checks in spec order (404, the gate, `busy`, `in_draft`, `gpu_busy`), then starts the job's thread.

        A clip in the Spoil draft needs `confirm_draft_loss`: new Shots make the draft's
        Shot numbers point at other pictures, so a `done` job removes it (D49).
        """
        project = ProjectPaths(paths.ROOT)
        clips.video_file(project, clip_id)
        require_rows(needed_rows(project))
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
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        started = time.monotonic()
        log.info("describing %s started", clip.id)
        new = project.new_shots_dir(clip.id)
        process = None
        try:
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
            ending = {"state": "done"}
        except Cancelled:
            ending = {"state": "cancelled"}
        except FfmpegFailed as error:
            log.error("ffmpeg failed on %s: %s", clip.id, error)
            ending = _failed("ffmpeg_failed", "อ่านภาพจากคลิปไม่ได้")
        except JobFailed as failure:
            ending = _failed(failure.code, failure.message)
        except Exception as error:
            log.exception("describing %s failed", clip.id)  # the full error, for [api]
            ending = _failed("internal", f"บรรยายฉากไม่สำเร็จ: {short(error)}")
        finally:
            if ending["state"] != "done":
                shutil.rmtree(new, ignore_errors=True)  # the old Shots stay (D51)
            self._finish(process, ending)
            # No Shot description in the log: only what happened and how long (spec › Ops).
            code = ending["error"].code if ending.get("error") else None
            log.info("describing %s ended %s %s after %.0f s", clip.id, ending["state"], code or "", time.monotonic() - started)

    def _cut(self, mp4: Path, duration_s: int | None) -> list[tuple[float, float]]:
        """`cutting`: the scene filter's cut times, as Shot spans. Raises `Cancelled`."""

        def on_progress(at_s: float) -> None:
            # 100 waits for the cut list: ffmpeg reads the last second before it ends.
            if duration_s:
                self._update(percent=min(99, int(at_s * 100 / duration_s)))

        cuts, duration = spoil_maker.find_cuts(mp4, on_progress, self._cancel)
        if self._cancel.is_set():
            raise Cancelled()
        return shots.plan_shots(cuts, duration)

def _swap(project: ProjectPaths, video_id: str) -> None:
    """The new Shots replace the old ones only now, at the end (D51)."""
    target = project.clip_shots_dir(video_id)
    shutil.rmtree(target, ignore_errors=True)
    project.new_shots_dir(video_id).rename(target)


def _failed(code: ErrorCode, message: str) -> dict:
    return {"state": "failed", "error": DescribeJobError(code=code, message=message)}


def needed_rows(project: ProjectPaths) -> dict[str, Row]:
    """The Status check rows a Describe job and a Draft job need, by id (spec › Status check).

    Off a Mac the two LLM rows are never ok (D50).
    """
    return {
        "ffmpeg": ("ffmpeg", lambda: checks.check_ffmpeg(checks.probe_ffmpeg)),
        "device": ("Device", lambda: checks.check_device(checks.probe_device)),
        QWEN.check_id: (QWEN.label, lambda: checks.check_model_on_platform(project, QWEN, checks.this_platform())),
        "mlx_vlm": ("mlx-vlm", lambda: checks.check_mlx_vlm(checks.probe_mlx_vlm, checks.this_platform())),
    }


def clip_shots(project: ProjectPaths, video_id: str) -> shots.ShotsFile:
    """A described clip's Shots. Raises `ApiError` 404 `not_found` for an unknown
    clip, `not_described` for one never described."""
    clips.check_known(project, video_id)
    found = shots.read_shots(project, video_id)
    if found is None:
        raise ApiError(404, "not_described", "คลิปนี้ยังไม่ได้บรรยายฉาก")
    return found


def shot_image(project: ProjectPaths, video_id: str, name: str) -> Path:
    """`{n}.jpg` of a described clip. Only a Shot number of that clip gets near the disk."""
    clips.check_known(project, video_id)
    found = shots.read_shots(project, video_id)
    match = SHOT_IMAGE.fullmatch(name)
    path = project.clip_shots_dir(video_id) / name
    if found is None or match is None or int(match.group(1)) >= len(found.shots) or not path.is_file():
        raise ApiError(404, "not_found", "ไม่พบภาพนี้")
    return path


describes = Describes()
