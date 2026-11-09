"""The Toon job: every job of the การ์ตูนเล่า tab but its render, one at a time in one slot
(toon spec › Toon job, ADR 0010, ADR 0012, ADR 0015). This ticket's kind is `ref`: the
reference picture of a character or a background, three to pick from (spec › Ref job).

A job that runs Qwen then klein holds the GPU slot as `toon_image` throughout; its
`child_name` and `worker_error` follow the step it is in, so `_reply` names that child.
"""

import logging
import random
import shutil
import threading
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel

from backend import checks, gate_rows, gpu, paths, spoil_maker, toon
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import ModelJobSlot, stop_process
from backend.models import KLEIN, KLEIN_GGUF, qwen_for
from backend.paths import ProjectPaths
from backend.spoil_maker import llm
from backend.spoil_maker.llm import Generate, Generated, Ready
from backend.toon import klein, prompts, series
from backend.toon.klein import Draw, Drawn, Encode, Encoded

log = logging.getLogger(__name__)

State = Literal["translating", "drawing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"translating", "drawing"})
ErrorCode = Literal["crashed", "model_failed", "write_failed", "ffmpeg_failed", "internal"]
JobKind = Literal["ref"]

SEED_MAX = 2**31 - 1


class ToonJobError(BaseModel):
    code: ErrorCode
    message: str


class ToonJob(BaseModel):
    """Every Toon job has these fields; the ones a kind doesn't use stay null (spec › Toon job)."""

    kind: JobKind
    state: State
    series_id: str
    ep_id: str | None = None
    item_id: str | None = None  # the character or background a `ref` job draws (D48)
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    skipped: int | None = None
    error: ToonJobError | None = None
    cancel_requested: bool = False
    started_at: str


class ToonJobs(ModelJobSlot[ToonJob]):
    unfinished = UNFINISHED
    gpu_kind = "toon_image"
    nothing_to_cancel = "ไม่มีงานการ์ตูนเล่าที่ยังไม่จบ"
    error_type = ToonJobError
    worker_error = klein.WorkerError
    child_name = "ตัวสร้างภาพ"
    failure = "สร้างภาพไม่สำเร็จ"

    def start(self, body: dict) -> ToonJob:
        if body.get("kind") == "ref":
            return self._start_ref(body)
        raise ApiError(400, "invalid_request", "ไม่รู้จักงานแบบนี้")

    def delete_series(self, project: ProjectPaths, series_id: str, body: dict | None) -> None:
        """Deletes the Series unless an unfinished job works on it (D26). Holds the slot's
        lock throughout, so no job can start on the Series halfway."""
        with self._lock:
            busy = {self._job.series_id} if self._taken() else set()
            series.delete(project, series_id, body, busy)

    def _start_ref(self, body: dict) -> ToonJob:
        """Step 1 in spec order: the item, the gate, `busy`, `gpu_busy`, the disk. The item is
        read again under the slot's lock, so a Series deleted meanwhile is `not_found`."""
        project = paths.project()
        series_id, kind, item_id = body.get("series_id"), body.get("item_kind"), body.get("item_id")
        if not all(isinstance(value, str) for value in (series_id, kind, item_id)) or kind not in get_args(series.Kind):
            raise ApiError(400, "invalid_request", "เลือกตัวละครหรือฉากหลังที่จะสร้างภาพ")
        series.ref_plan(project, series_id, kind, item_id)
        require_rows(image_rows(project))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "มีงานการ์ตูนเล่าที่ยังไม่จบ")
            plan = series.ref_plan(project, series_id, kind, item_id)
            gpu.slot.take("toon_image")
            try:
                series.require_free_disk(project)
            except ApiError:
                gpu.slot.release("toon_image")
                raise
            self._job = ToonJob(
                kind="ref", state="translating", series_id=series_id, item_id=item_id, started_at=checks.now_iso()
            )
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, series_id, plan), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, series_id: str, plan: series.RefPlan) -> None:
        work = project.pending_refs_dir(series_id) / f".new-{plan.item_id}"

        def clean_up(state: str) -> None:
            shutil.rmtree(work, ignore_errors=True)

        self._run_job(f"toon job ref {plan.item_id}", lambda: self._ref(project, series_id, plan, work), clean_up)

    def _ref(self, project: ProjectPaths, series_id: str, plan: series.RefPlan, work: Path) -> None:
        """Steps 2–3: Qwen writes the scene, its child ends, then klein draws three pictures
        with different seeds; they become the item's waiting set only once all three are in."""
        scene = self._scene(project, prompts.ref_scene_prompt(plan.kind, plan.name, plan.description))
        if scene is None:
            scene = plan.description or plan.name  # D48: the description as it was written
        prompt = prompts.ref_prompt(plan.kind, scene, plan.style)
        self._update(state="drawing", done=0, total=series.PICTURES)
        process, requests, replies = self._start_klein(project)
        requests.put(Encode([prompt]))
        self._klein_reply(process, replies, Encoded)
        work.mkdir(parents=True, exist_ok=True)
        pictures = []
        width, height = plan.size
        for n in range(1, series.PICTURES + 1):
            requests.put(Draw(index=0, ref_paths=[], width=width, height=height, seed=random.randint(0, SEED_MAX)))
            drawn = self._klein_reply(process, replies, Drawn)
            picture = work / f"{n}.png"
            picture.write_bytes(drawn.png)
            pictures.append(picture)
            self._update(done=n)
        requests.put(None)
        if not series.put_pending(project, series_id, plan.kind, plan.item_id, pictures):
            log.info("the reference pictures of %s are dropped: it was deleted", plan.item_id)

    def _scene(self, project: ProjectPaths, prompt: str) -> str | None:
        """Qwen's English scene, or None when its answer isn't one or takes too long; its
        child ends either way, before klein loads (D36)."""
        self.worker_error, self.child_name = llm.WorkerError, "ตัวแปลคำบรรยาย"
        qwen = qwen_for(checks.this_platform())
        process, requests, replies = spoil_maker.start_worker(project.snapshot_dir(qwen, qwen.revision))
        self._track(process)
        try:
            self._reply(process, replies, (Ready,))
            requests.put(Generate(prompt, None, prompts.SCENE_MAX_TOKENS, prompts.SCENE_TEMPERATURE))
            reply = self._reply(process, replies, (Generated,), llm.timeouts().pick)
            scene = prompts.parse_scene(reply.text)
        except TimeoutError:
            log.warning("the scene took longer than %g s", llm.timeouts().pick)
            scene = None
        finally:
            # klein's names again, however Qwen's step ended: a failure names the child that ran.
            self.worker_error, self.child_name = klein.WorkerError, "ตัวสร้างภาพ"
        if scene is None:
            log.warning("no scene from Qwen: the description goes in as written")
        self._track(None)
        stop_process(process)
        return scene

    def _start_klein(self, project: ProjectPaths):
        device = checks.probe_device()
        process, requests, replies = toon.start_klein_worker(
            project.snapshot_dir(KLEIN, KLEIN.revision), project.snapshot_dir(KLEIN_GGUF, KLEIN_GGUF.revision), device
        )
        self._track(process)
        return process, requests, replies

    def _klein_reply(self, process, replies, expected: type):
        """klein's next message; one that takes longer than a picture may fails the job."""
        try:
            return self._reply(process, replies, (expected,), klein.draw_timeout())
        except TimeoutError:
            raise JobFailed("model_failed", f"สร้างภาพเกิน {klein.draw_timeout() / 60:g} นาที. {gpu.ADVICE}") from None


def image_rows(project: ProjectPaths) -> dict[str, Row]:
    """What a Ref job and an Image job need (spec › Status check)."""
    return gate_rows.qwen_jobs(project) | gate_rows.klein(project)


toon_jobs = ToonJobs()
