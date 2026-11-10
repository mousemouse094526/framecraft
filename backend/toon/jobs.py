"""The Toon job: every job of the การ์ตูนเล่า tab but its render, one at a time in one slot
(toon spec › Toon job, ADR 0010, ADR 0012, ADR 0015). Its kinds so far: `plot` and `cards`,
Qwen writing an EP's plot and splitting it into segments and cards (spec › Plot job, › Cards
job), and `ref`, the reference picture of a character or a background (spec › Ref job).

A job holds the GPU slot as its kind's `gpu_kind`, set as it starts: `toon_write` for Qwen's
writing, `toon_image` for a job that runs Qwen then klein. Its `Child` (`_use`)
follows the step it is in, so `_reply` names that child. A `plot` or `cards`
job locks its EP: edits are `ep_locked` until it ends, and the EP changes only at its end.
"""

import logging
import random
import shutil
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NamedTuple, get_args

from pydantic import BaseModel

from backend import checks, gate_rows, gpu, paths, spoil_maker, toon
from backend.errors import ApiError, JobFailed, Row, invalid_request, require_rows
from backend.jobs import ModelJobSlot, stop_process
from backend.models import KLEIN, KLEIN_GGUF, qwen_for
from backend.paths import ProjectPaths
from backend.spoil_maker import llm, voices
from backend.spoil_maker.llm import Generate, Generated, Ready
from backend.toon import episodes, klein, prompts, series, store, writer
from backend.toon.klein import Draw, Drawn, Encode, Encoded
from backend.toon.store import Background, Character, Ep, Plot, Series

log = logging.getLogger(__name__)

State = Literal["writing", "translating", "drawing", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"writing", "translating", "drawing"})
ErrorCode = Literal["crashed", "model_failed", "write_failed", "ffmpeg_failed", "internal"]
JobKind = Literal["plot", "cards", "ref"]
LOCKS_EP: frozenset[JobKind] = frozenset({"plot", "cards"})

SEED_MAX = 2**31 - 1


class Child(NamedTuple):
    """The child process a step runs: what `_reply` reads from it and names in a failure."""

    worker_error: type
    name: str
    failure: str


WRITER = Child(llm.WorkerError, "ตัวร่างการ์ตูนเล่า", "ร่างการ์ตูนเล่าไม่สำเร็จ")
TRANSLATOR = Child(llm.WorkerError, "ตัวแปลคำบรรยาย", "สร้างภาพไม่สำเร็จ")
DRAWER = Child(klein.WorkerError, "ตัวสร้างภาพ", "สร้างภาพไม่สำเร็จ")


class LostCards(BaseModel):
    """What re-splitting one act throws away (D15, D43)."""

    id: str
    name: str
    edited: int
    images: int
    audio: int


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
    nothing_to_cancel = "ไม่มีงานการ์ตูนเล่าที่ยังไม่จบ"
    error_type = ToonJobError

    def __init__(self):
        super().__init__()
        self._model = None  # (process, requests, replies) of Qwen's running child, while writing

    def start(self, body: dict) -> ToonJob:
        if body.get("kind") == "plot":
            return self._start_plot(body)
        if body.get("kind") == "cards":
            return self._start_cards(body)
        if body.get("kind") == "ref":
            return self._start_ref(body)
        raise ApiError(400, "invalid_request", "ไม่รู้จักงานแบบนี้")

    def ep_use(self) -> tuple[str, bool] | None:
        """The EP an unfinished job works on, and whether it locks it (`episodes.ep_jobs`).
        One attribute read, without the slot's lock: an edit asks under `store.lock`."""
        job = self._job
        if job is None or job.state not in UNFINISHED or job.ep_id is None:
            return None
        return job.ep_id, job.kind in LOCKS_EP

    def delete_series(self, project: ProjectPaths, series_id: str, body: dict | None) -> None:
        """Deletes the Series unless an unfinished job works on it (D26). Holds the slot's
        lock throughout, so no job can start on the Series halfway."""
        with self._lock:
            busy = {self._job.series_id} if self._taken() else set()
            series.delete(project, series_id, body, busy)

    def _start_plot(self, body: dict) -> ToonJob:
        project, ep_id = paths.project(), body.get("ep_id")

        def plan() -> tuple[str, int | None, Callable[[], None]]:
            found = _plot_checks(project, ep_id)
            return found.series.id, None, lambda: self._plot(project, found.series.id, ep_id, found.chars_per_s)

        return self._start_writing("plot", ep_id, plan)

    def _start_cards(self, body: dict) -> ToonJob:
        project, ep_id, confirm_loss = paths.project(), body.get("ep_id"), body.get("confirm_loss", False)
        if not isinstance(confirm_loss, bool):
            raise invalid_request()

        def plan() -> tuple[str, int | None, Callable[[], None]]:
            cards = _cards_checks(project, ep_id, confirm_loss)
            return cards.series.id, len(cards.act_ids), lambda: self._cards(project, cards)

        return self._start_writing("cards", ep_id, plan)

    def _start_writing(self, kind: JobKind, ep_id: str, plan: Callable[[], tuple[str, int | None, Callable[[], None]]]) -> ToonJob:
        """Step 1 of the Plot or Cards job in spec order: `plan`'s checks of the EP, the gate,
        `busy`, `gpu_busy`. `plan` runs again under the store's lock with the job set there, so
        no edit slips in between; it gives the Series, the job's `total`, and its steps."""
        plan()
        require_rows(gate_rows.qwen_jobs(paths.project()))
        with self._lock:
            if self._taken():
                raise ApiError(409, "busy", "มีงานการ์ตูนเล่าที่ยังไม่จบ")
            with store.lock:
                series_id, total, steps = plan()
                gpu.slot.take("toon_write")
                self._use("toon_write", WRITER)
                self._job = ToonJob(
                    kind=kind,
                    state="writing",
                    series_id=series_id,
                    ep_id=ep_id,
                    done=None if total is None else 0,
                    total=total,
                    started_at=checks.now_iso(),
                )
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run_writing, args=(f"toon job {kind} {ep_id}", steps), daemon=True).start()
        return job

    def _use(self, gpu_kind: gpu.Kind, child: Child) -> None:
        """The GPU slot's kind this job holds, and the child `_reply` reads from now."""
        self.gpu_kind = gpu_kind
        self.worker_error, self.child_name, self.failure = child

    def _run_writing(self, what: str, steps) -> None:
        """A cancelled, failed or crashed job leaves the EP as it was: it is written at the end only."""

        def clean_up(state: str) -> None:
            self._model = None  # `_finish` stops its process

        self._run_job(what, steps, clean_up)

    def _plot(self, project: ProjectPaths, series_id: str, ep_id: str, chars_per_s: float) -> None:
        """Steps 2–5 of the Plot job: up to three tries, then the title, the summaries and
        the plot's cast are written; new characters and backgrounds stay in the plot (D13)."""
        with store.lock:
            series_now, ep = store.read_series(project, series_id), store.read_ep(project, series_id, ep_id)
        prompt = writer.plot_prompt(
            series_now, ep.idea, [act.name for act in ep.acts], round(episodes.TARGET_S * chars_per_s)
        )
        written = None
        for attempt in range(1, writer.ATTEMPTS + 1):
            reply = self._write(project, prompt, writer.PLOT_MAX_TOKENS, attempt)
            written = writer.parse_plot(reply, series_now, len(ep.acts)) if reply is not None else None
            if written is not None:
                break
            log.warning("plot attempt %d is not the JSON asked for", attempt)
        if written is None:
            raise JobFailed("write_failed", f"AI ร่างพล็อตไม่สำเร็จ {writer.ATTEMPTS} ครั้ง")
        with store.lock:
            ep = store.read_ep(project, series_id, ep_id)
            if ep is None:
                raise JobFailed("internal", "อ่าน EP นี้ไม่ได้แล้ว")
            ep.title = written.title
            for act, summary in zip(ep.acts, written.summaries, strict=True):
                act.summary = summary
            ep.plot = Plot(characters=written.characters, backgrounds=written.backgrounds)
            store.write_ep(project, series_id, ep)

    def _cards(self, project: ProjectPaths, plan: "CardsPlan") -> None:
        """Steps 2–6 of the Cards job: each act to split is asked up to three times; all are
        written at once at the end, with the plot's new characters and backgrounds entering
        the Series (D13, D15). An act with no card after three tries fails the job."""
        series_now, ep = plan.series, plan.ep
        taken = {item.id for item in [*series_now.characters, *series_now.backgrounds]}
        added: dict[str, list] = {"characters": [], "backgrounds": []}
        for kind, model in (("characters", Character), ("backgrounds", Background)):
            for item in getattr(ep.plot, kind):
                if item.new:
                    item.id, item.new = store.new_id(kind[0], taken), False
                    taken.add(item.id)
                    fields = {"id", "name", "description", "tag"} if kind == "characters" else {"id", "name", "description"}
                    added[kind].append(model(**item.model_dump(include=fields)))
        cast = series_now.model_copy(
            update={kind: [*getattr(series_now, kind), *added[kind]] for kind in ("characters", "backgrounds")}
        )
        characters = writer.known(ep.plot.characters, cast, "characters")
        backgrounds = writer.known(ep.plot.backgrounds, cast, "backgrounds")
        sounds = store.read_sounds(project)
        target = round(episodes.TARGET_S / len(ep.acts) * plan.chars_per_s)
        ids = {i.id for act in ep.acts for segment in act.segments for i in [segment, *segment.cards]}
        written: dict[str, list] = {}
        for done, act_id in enumerate(plan.act_ids, start=1):
            index = next(i for i, act in enumerate(ep.acts) if act.id == act_id)
            prompt = writer.cards_prompt(cast.tone, ep.acts, index, characters, backgrounds, sounds, target)
            for attempt in range(1, writer.ATTEMPTS + 1):
                reply = self._write(project, prompt, writer.CARDS_MAX_TOKENS, attempt)
                segments = (
                    writer.parse_cards(
                        reply, [b.id for b in backgrounds], {c.id for c in characters}, {s.id for s in sounds}, ids
                    )
                    if reply is not None
                    else None
                )
                if segments is not None:
                    written[act_id] = segments
                    break
                log.warning("cards attempt %d of act %d is not the JSON asked for", attempt, index + 1)
            else:
                raise JobFailed("write_failed", f"AI แตกการ์ดองก์ {ep.acts[index].name} ไม่สำเร็จ {writer.ATTEMPTS} ครั้ง")
            self._update(done=done)
        with store.lock:
            series_now = store.read_series(project, plan.series.id)
            for kind in ("characters", "backgrounds"):
                getattr(series_now, kind).extend(added[kind])
            ep_now = store.read_ep(project, plan.series.id, ep.id)
            gone = []
            for act in ep_now.acts:
                if act.id in written:
                    gone.extend(card for segment in act.segments for card in segment.cards)
                    act.segments, act.cards_from = written[act.id], act.summary
            ep_now.plot, ep_now.stage = ep.plot, "cards"
            store.write_series(project, series_now)
            store.write_ep(project, series_now.id, ep_now)
            episodes.remove_card_files(project, series_now.id, ep_now.id, gone)

    def _write(self, project: ProjectPaths, prompt: str, max_tokens: int, attempt: int) -> str | None:
        """One answer from Qwen, starting its child first if none runs; None when it took
        longer than a try may: its child stops and the next try starts one (spec › Plot job)."""
        timeout = llm.timeouts().write
        if self._model is None:
            qwen = qwen_for(checks.this_platform())
            process, requests, replies = spoil_maker.start_worker(project.snapshot_dir(qwen, qwen.revision))
            self._model = (process, requests, replies)
            self._track(process)
            self._reply(process, replies, (Ready,))  # loading has no timeout
        process, requests, replies = self._model
        requests.put(Generate(prompt, None, max_tokens, writer.TEMPERATURE))
        try:
            return self._reply(process, replies, (Generated,), timeout).text
        except TimeoutError:
            log.warning("attempt %d took longer than %g s", attempt, timeout)
            self._model = None
            self._track(None)
            stop_process(process)
            return None

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
            self._use("toon_image", DRAWER)
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
        self._use("toon_image", TRANSLATOR)
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
            self._use("toon_image", DRAWER)
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


class CardsPlan(BaseModel):
    """What a Cards job splits, read once under the store's lock as it starts."""

    series: Series
    ep: Ep
    act_ids: list[str]
    chars_per_s: float


class Writable(NamedTuple):
    series: Series
    ep: Ep
    chars_per_s: float  # the EP's voice's speed


def _plot_checks(project: ProjectPaths, ep_id: object) -> Writable:
    """Step 1 of the Plot job up to the gate: the EP, its idea, its voice, its stage."""
    found = _writable(project, ep_id)
    if found.ep.stage == "cards":
        raise ApiError(409, "plot_confirmed", "ยืนยันพล็อตแล้ว: แก้พล็อตแล้วแตกการ์ดใหม่แทน")
    return found


def _cards_checks(project: ProjectPaths, ep_id: object, confirm_loss: bool) -> CardsPlan:
    """Step 1 of the Cards job up to the gate: the acts to split, and what they would lose
    (D15, D43). The first split takes every act; later ones those whose summary changed."""
    series_now, ep, chars_per_s = _writable(project, ep_id)
    if not ep.plot.backgrounds:
        raise ApiError(400, "invalid_request", "พล็อตต้องมีฉากหลังอย่างน้อยหนึ่ง")
    acts = [act for act in ep.acts if ep.stage == "plot" or act.summary != act.cards_from]
    if not acts:
        raise ApiError(400, "nothing_to_split", "ไม่มีองก์ที่พล็อตเปลี่ยน")
    lost = [_lost(act) for act in acts]
    if not confirm_loss and any(act.edited or act.images or act.audio for act in lost):
        raise ApiError(
            409, "cards_will_be_lost", "การ์ดที่แก้เอง ภาพ หรือเสียงขององก์ที่แตกใหม่จะหาย", acts=[a.model_dump() for a in lost]
        )
    return CardsPlan(series=series_now, ep=ep, act_ids=[act.id for act in acts], chars_per_s=chars_per_s)


def _writable(project: ProjectPaths, ep_id: object) -> Writable:
    """The EP with its Series, and its voice's speed. Raises `not_found`, `invalid_request`
    for an idea out of 1–500, `voice_not_found`."""
    found = store.find_ep(project, ep_id) if isinstance(ep_id, str) else None
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบ EP นี้")
    if not 1 <= len(found[1].idea) <= episodes.IDEA_MAX:
        raise ApiError(400, "invalid_request", f"ไอเดียต้องยาว 1–{episodes.IDEA_MAX} ตัวอักษร")
    chars_per_s = voices.chars_per_s(project, found[1].voice_id)
    if chars_per_s is None:
        raise ApiError(400, "voice_not_found", "ไม่พบเสียงเล่าของ EP นี้: เลือกเสียงที่บันทึกไว้")
    return Writable(*found, chars_per_s)


def _lost(act) -> LostCards:
    cards = [card for segment in act.segments for card in segment.cards]
    return LostCards(
        id=act.id,
        name=act.name,
        edited=sum(card.edited for card in cards),
        images=sum(card.image is not None for card in cards),
        audio=sum(card.audio is not None for card in cards),
    )


def image_rows(project: ProjectPaths) -> dict[str, Row]:
    """What a Ref job and an Image job need (spec › Status check)."""
    return gate_rows.qwen_jobs(project) | gate_rows.klein(project)


toon_jobs = ToonJobs()
episodes.ep_jobs.append(lambda: toon_jobs.ep_use())
