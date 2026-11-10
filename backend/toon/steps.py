"""What the kinds of the Toon job share (toon spec › Toon job, ADR 0012, ADR 0015): `Work`, how
the slot starts and runs one kind; `Run`, what a kind's steps ask of the slot; and the steps
that talk to a child: Qwen writing (`Qwen`) or translating (`scenes`), klein drawing (`open_klein`, `draw`).

A job holds the GPU slot as its kind's `gpu_kind`, set as it starts: `toon_write` for Qwen's
writing, `toon_image` for a job that runs Qwen then klein, `toon_voice` for OmniVoice. Its
`Child` follows the step it is in (`Run.use_child`), so a failure names the child that ran.
"""

import logging
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from typing import Any, NamedTuple, Protocol, TypeVar

from backend import checks, gate_rows, gpu, speaking, spoil_maker
from backend.errors import JobFailed, Row
from backend.models import KLEIN, KLEIN_GGUF, qwen_for
from backend.paths import ProjectPaths
from backend.spoil_maker import llm, tts
from backend.spoil_maker.llm import Generate, Generated, Ready
from backend.toon import klein, prompts, writer
from backend.toon.klein import Draw, Encode, Encoded
from backend.workers import Worker

log = logging.getLogger(__name__)

SEED_MAX = 2**31 - 1

T = TypeVar("T")


class Child(NamedTuple):
    """The child process a step runs: what `Run.reply` reads from it and names in a failure."""

    worker_error: type
    name: str
    failure: str


WRITER = Child(llm.WorkerError, "ตัวร่างการ์ตูนเล่า", "ร่างการ์ตูนเล่าไม่สำเร็จ")
# Translating is the first step of making a picture: the user sees the picture fail.
TRANSLATOR = Child(llm.WorkerError, "ตัวแปลคำบรรยาย", "สร้างภาพไม่สำเร็จ")
DRAWER = Child(klein.WorkerError, "ตัวสร้างภาพ", "สร้างภาพไม่สำเร็จ")
VOICER = Child(tts.WorkerError, "ตัวสร้างเสียง", "สร้างเสียงไม่สำเร็จ")


class Run(Protocol):
    """The Toon job slot, as a kind's steps see it (`jobs.ModelJobSlot` and `ToonJobs`)."""

    speaker: speaking.Speaker

    def update(self, **fields) -> None: ...

    def use_child(self, gpu_kind: gpu.Kind, child: Child) -> None: ...

    def start_child(self, worker: Worker, first: type, timeout: float | None = None) -> Worker: ...

    def ask(self, worker: Worker, request, expected: tuple[type, ...], timeout: float | None = None): ...

    def stop_child(self) -> None: ...


class Work(NamedTuple):
    """How the slot starts and runs one kind of Toon job. Step 1 of the kind's spec section
    (spec › Plot job, › Cards job, …), in order: `plan`'s refusals, the gate (`rows`), `busy`,
    then under `locks` and the store's lock `plan` again, `gpu_busy` and `ready`; the job is set
    there too, so no edit or Series delete slips in between. The first `plan` only refuses
    early: the job takes the second."""

    gpu_kind: gpu.Kind
    child: Child  # the child a failure names until a step changes it (`Run.use_child`)
    plan: Callable[[ProjectPaths, dict], Any]  # the checks of the body; what the job works on
    rows: Callable[[ProjectPaths], dict[str, Row]]
    job: Callable[[Any], dict]  # the job's fields as it starts, its `state` among them
    run: Callable[[Run, ProjectPaths, Any], None]  # the job's steps after step 1, in its thread
    log_name: Callable[[Any], str]  # the job, as the log names it
    locks: Callable[[], AbstractContextManager] = nullcontext  # after the slot's lock, before the store's
    ready: Callable[[ProjectPaths, Any], None] | None = None  # refusals once the GPU is taken
    clean_up: Callable[[ProjectPaths, Any], None] | None = None  # however the job ended


class Qwen:
    """Qwen writing one answer at a time in one child, started at the first ask; a try that
    takes longer than it may stops the child, and the next try starts another (spec › Plot job).
    The slot's end stops the child that runs then."""

    def __init__(self, run: Run, project: ProjectPaths):
        self._run, self._project = run, project
        self._model: Worker | None = None  # the running child

    def answer(self, prompt: str, max_tokens: int, parse: Callable[[str], T | None], what: str) -> T | None:
        """`parse` of Qwen's answer, asked up to `writer.ATTEMPTS` times; None when no answer
        parsed. `what` names the ask in the log."""
        for attempt in range(1, writer.ATTEMPTS + 1):
            reply = self._write(prompt, max_tokens, attempt)
            parsed = parse(reply) if reply is not None else None
            if parsed is not None:
                return parsed
            log.warning("%s attempt %d is not the JSON asked for", what, attempt)
        return None

    def _write(self, prompt: str, max_tokens: int, attempt: int) -> str | None:
        """One answer, or None when it took too long."""
        timeout = llm.timeouts().write
        if self._model is None:
            self._model = start_qwen(self._run, self._project)
        request = Generate(prompt, None, max_tokens, writer.TEMPERATURE)
        try:
            return self._run.ask(self._model, request, (Generated,), timeout).text
        except TimeoutError:
            log.warning("attempt %d took longer than %g s", attempt, timeout)
            self._model = None
            self._run.stop_child()
            return None


def start_qwen(run: Run, project: ProjectPaths) -> Worker:
    """Starts Qwen's child and waits until it is loaded (no timeout)."""
    qwen = qwen_for(checks.this_platform())
    return run.start_child(spoil_maker.start_worker(project.snapshot_dir(qwen, qwen.revision)), Ready)


def scenes(run: Run, project: ProjectPaths, asks: list[str | None], counted: bool = False) -> list[str | None]:
    """Qwen's English scene for each ask, in one child that ends before klein loads (D36);
    None for an ask that is None (nothing to translate), an answer that isn't one, or one
    that takes too long, after which the next ask starts a new child. `counted`: the job's
    `done` counts the asks answered (an Image job's `translating`; a Ref job has one ask)."""
    run.use_child("toon_image", TRANSLATOR)
    # A scene is one short answer: it may take as long as a sentence's Shots take to pick.
    timeout, found = llm.timeouts().pick, []
    qwen: Worker | None = None  # started at the first ask it answers
    try:
        for done, ask in enumerate(asks, start=1):
            scene = None
            if ask is not None:
                if qwen is None:
                    qwen = start_qwen(run, project)
                request = Generate(ask, None, prompts.SCENE_MAX_TOKENS, prompts.SCENE_TEMPERATURE)
                try:
                    scene = prompts.parse_scene(run.ask(qwen, request, (Generated,), timeout).text)
                except TimeoutError:
                    log.warning("a scene took longer than %g s", timeout)
                    run.stop_child()
                    qwen = None
                if scene is None:
                    log.warning("no scene from Qwen: the fallback goes in")
            found.append(scene)
            if counted:
                run.update(done=done)
    finally:
        # klein's names again, however Qwen's step ended: a failure names the child that ran.
        run.use_child("toon_image", DRAWER)
    if qwen is not None:
        run.stop_child()
    return found


def open_klein(run: Run, project: ProjectPaths, texts: list[str]) -> Worker:
    """Starts klein's child and encodes every prompt of the job (`texts`), which its `Draw`s name by
    index (spec › Ref job, › Image job: klein draws). `Worker.end` ends it."""
    worker = klein.start_worker(
        project.snapshot_dir(KLEIN, KLEIN.revision),
        project.snapshot_dir(KLEIN_GGUF, KLEIN_GGUF.revision),
        checks.probe_device(),
    )
    worker.requests.put(Encode(texts))  # klein says nothing until it has the prompts
    with _drawing_time():
        return run.start_child(worker, Encoded, klein.draw_timeout())


def draw(run: Run, worker: Worker, request: Draw, expected: tuple[type, ...]):
    """klein's answer to `request`, one of `expected`; one that takes longer than a picture may fails the job."""
    with _drawing_time():
        return run.ask(worker, request, expected, klein.draw_timeout())


@contextmanager
def _drawing_time() -> Iterator[None]:
    try:
        yield
    except TimeoutError:
        raise JobFailed("model_failed", f"สร้างภาพเกิน {klein.draw_timeout() / 60:g} นาที. {gpu.ADVICE}") from None


def image_rows(project: ProjectPaths) -> dict[str, Row]:
    """What a Ref job and an Image job need (spec › Status check)."""
    return gate_rows.qwen_jobs(project) | gate_rows.klein(project)
