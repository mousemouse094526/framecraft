"""The Toon job slot: every job of the การ์ตูนเล่า tab but its render, one at a time (toon spec ›
Toon job, ADR 0010, ADR 0012, ADR 0015). Each kind's work is its own module's `WORK`: `plot`
and `cards`, Qwen writing an EP's plot and splitting it into segments and cards (spec › Plot
job, › Cards job); `ref`, the reference pictures of a character or a background (spec › Ref
job); `image`, the pictures of one card or of every card a scope takes (spec › Image job);
and `voice`, one card's narration (spec › Voice job).

A `plot` or `cards` job locks its EP: edits are `ep_locked` until it ends.
"""

import threading
from typing import Literal

from pydantic import BaseModel

from backend import checks, gpu, paths, speaking
from backend.errors import ApiError, require_rows
from backend.jobs import ModelJobSlot
from backend.paths import ProjectPaths
from backend.toon import cards, episodes, images, plot, refs, series, store, voicing
from backend.toon.steps import Child, Work

State = Literal["writing", "translating", "drawing", "voicing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"writing", "translating", "drawing", "voicing"})
ErrorCode = Literal["crashed", "model_failed", "write_failed", "internal"]
JobKind = Literal["plot", "cards", "ref", "image", "voice"]
LOCKS_EP: frozenset[JobKind] = frozenset({"plot", "cards"})

WORKS: dict[JobKind, Work] = {
    "plot": plot.WORK,
    "cards": cards.WORK,
    "ref": refs.WORK,
    "image": images.WORK,
    "voice": voicing.WORK,
}


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
    # The cards an `image` or `voice` job works on, in order; while `drawing`, `card_ids[done]`
    # is the one klein draws now (`done` counts translations while `translating`, D55).
    card_ids: list[str] | None = None
    scope: images.Scope | None = None  # an `image` job of every card the scope takes, not of one
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    skipped: int | None = None
    missing_refs: list[images.MissingRef] | None = None  # what made an `image` job skip cards (D13)
    failed_cards: list[str] | None = None  # the cards klein failed to draw; the job went on
    error: ToonJobError | None = None
    cancel_requested: bool = False
    started_at: str


class ToonJobs(ModelJobSlot[ToonJob]):
    """The slot itself: it starts and ends every kind's job the same way (`WORKS`), and is the
    `steps.Run` a kind's steps call. Its `speaker` speaks the Voice job's text."""

    unfinished = UNFINISHED
    nothing_to_cancel = "ไม่มีงานการ์ตูนเล่าที่ยังไม่จบ"
    error_type = ToonJobError

    def __init__(self):
        super().__init__()
        self.speaker = speaking.Speaker(self)

    def start(self, body: dict) -> ToonJob:
        """Step 1 of the kind's spec section (Plot job, Cards job, …) in the order `steps.Work`
        gives, then the kind's later steps in the job's thread."""
        kind = body.get("kind")
        work = WORKS.get(kind) if isinstance(kind, str) else None
        if work is None:
            raise ApiError(400, "invalid_request", "ไม่รู้จักงานแบบนี้")
        project = paths.project()
        work.plan(project, body)  # refused before the gate and `busy`; read again under the locks below
        require_rows(work.rows(project))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "มีงานการ์ตูนเล่าที่ยังไม่จบ")
            with work.locks(), store.lock:
                plan_now = work.plan(project, body)
                gpu.slot.take(work.gpu_kind)
                self.gpu_kind = work.gpu_kind
                self.use_child(work.child)
                if work.ready is not None:
                    try:
                        work.ready(project, plan_now)
                    except Exception:
                        gpu.slot.release(work.gpu_kind)  # no job holds it yet (ADR 0015)
                        raise
                self._job = ToonJob(kind=kind, started_at=checks.now_iso(), **work.job(plan_now))
            self._cancel.clear()
            job = self._job.model_copy(deep=True)

        def clean_up(_state: str) -> None:  # however it ended
            if work.clean_up is not None:
                work.clean_up(project, plan_now)

        def run() -> None:
            work.run(self, project, plan_now)

        threading.Thread(target=self._run_job, args=(work.log_name(plan_now), run, clean_up), daemon=True).start()
        return job

    def ep_use(self) -> episodes.EpUse | None:
        """The EP an unfinished job works on, and whether it locks it (`episodes.ep_jobs`)."""
        job = self.running()
        return episodes.EpUse(job.ep_id, "locks" if job.kind in LOCKS_EP else "works") if job is not None and job.ep_id is not None else None

    def use_child(self, child: Child) -> None:
        """Which child `reply` reads from now (and names in a failure): an Image job moves from
        Qwen to klein (`steps.Run`). The GPU slot's kind stays the one the job took."""
        self.worker_error, self.child_name, self.failure = child


def clean_on_start(project: ProjectPaths) -> None:
    """What a Toon job leaves half-done: Ref pictures never picked, uploads never received in
    full, an Image job's copies and its pictures no `ep.json` names."""
    series.clean_on_start(project)
    images.clean_on_start(project)


toon_jobs = ToonJobs()
episodes.ep_jobs.append(lambda: toon_jobs.ep_use())
series.series_jobs.append(lambda: toon_jobs)
