"""What every long job shares: one job of a kind at a time, held in memory behind
one lock with a cancel flag its thread checks (ADR 0010), and the child process a
model runs in, reporting through a queue (ADR 0012)."""

import logging
import threading
import time
from collections.abc import Callable
from queue import Empty
from typing import Generic, TypeVar

from pydantic import BaseModel

from backend import gpu
from backend.errors import ApiError, JobFailed
from backend.workers import Worker, type_name

log = logging.getLogger(__name__)

POLL_SECONDS = 0.2  # how often a thread looks at the cancel flag while the child works
TERMINATE_SECONDS = 5  # a child that ignores SIGTERM this long is killed

# The names of the exception types that are a mistake in the code, not trouble with the GPU:
# a child's error of one gets no `gpu.ADVICE` (toon D84). Only the name crosses the queue, so
# the subclasses that the code raises too are listed by their own names (D85).
CODE_ERROR_TYPES = frozenset(
    {
        "TypeError",
        "AttributeError",
        "NameError",
        "UnboundLocalError",
        "KeyError",
        "IndexError",
        "ImportError",
        "ModuleNotFoundError",
        "AssertionError",
    }
)

Job = TypeVar("Job", bound=BaseModel)


class JobSlot(Generic[Job]):
    """Holds the latest job of one kind. Subclasses set `unfinished`, the states
    that keep the slot taken."""

    unfinished: frozenset[str]

    def __init__(self):
        self._lock = threading.Lock()
        self._job: Job | None = None
        self._cancel = threading.Event()

    def current(self) -> Job | None:
        with self._lock:
            return self._job.model_copy(deep=True) if self._job else None

    def running(self) -> Job | None:
        """The unfinished job, or None. One attribute read, without the lock: a caller that
        needs it to hold reads under a lock the job starts under too (as toon's `store.lock`)."""
        job = self._job
        return job if job is not None and job.state in self.unfinished else None

    def _taken(self) -> bool:
        """Whether a job is still running. Call with the lock held."""
        return self.running() is not None

    def update(self, **fields) -> None:
        """Sets fields of the job, as its steps go."""
        with self._lock:
            for name, value in fields.items():
                setattr(self._job, name, value)


class ModelJobSlot(JobSlot[Job]):
    """A job slot whose job runs a model in a child process and holds the GPU slot
    as `gpu_kind` (ADR 0012, ADR 0015). Subclasses also set `nothing_to_cancel`, the
    message of a cancel with no running job, `error_type`, the job's `{code, message}`
    error, and for `reply`: the child's `worker_error` message type, `child_name`
    ("ตัวบรรยายฉาก") and `failure` ("บรรยายฉากไม่สำเร็จ"), the words a failed job's
    message is made of.

    A step starts its child with `start_child` and `ask`s it. One child runs at a time, the
    one tracked: a step whose child is done with stops it with `stop_child` (a job that runs
    Qwen then klein), or with `free_gpu` when the rest of the job needs no GPU (a render's
    ffmpeg); otherwise the job's end stops it."""

    gpu_kind: gpu.Kind
    nothing_to_cancel: str
    error_type: type[BaseModel]
    worker_error: type
    child_name: str
    failure: str
    ending_fields: dict = {}  # set by every ending, whatever the state

    def __init__(self):
        super().__init__()
        self._process = None  # the running child, for shutdown

    def cancel(self) -> Job:
        """Asks the thread to stop its child; the job ends as `cancelled`. Raises
        `ApiError` 404 `not_found` when no job is running."""
        with self._lock:
            if not self._taken():
                raise ApiError(404, "not_found", self.nothing_to_cancel)
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def stop_on_shutdown(self) -> None:
        """Ctrl+C must not leave a child holding the GPU. A child started after this
        sees the cancel flag at its first poll and is stopped by its thread."""
        self._cancel.set()
        with self._lock:
            process = self._process
        if process is not None:
            stop_process(process)

    def _run_job(
        self,
        what: str,
        steps: Callable[[], dict | None],
        clean_up: Callable[[str], None] | None = None,
        failure: str | None = None,
    ) -> None:
        """The body of every job's thread. Runs `steps`, then ends the job however they went:
        `done` with the fields `steps` returns, `cancelled`, `failed` with a `JobFailed`'s
        error, or `internal` for anything else (`failure`, default the class's, starts its
        message). `clean_up` gets the end state before the child stops and the GPU frees.
        The log says `what` started and how it ended, never what the model wrote (spec › Ops)."""
        # Stays `failed` only if something escapes every handler below.
        ending: dict = {"state": "failed"}
        started = time.monotonic()
        log.info("%s started", what)
        try:
            ending = {"state": "done", **(steps() or {})}
        except Cancelled:
            ending = {"state": "cancelled"}
        except JobFailed as failed:
            ending = self._failed(failed.code, failed.message)
        except Exception as error:
            log.exception("%s failed", what)  # the full error, for [api]
            ending = self._failed("internal", f"{failure or self.failure}: {short(error)}")
        finally:
            if clean_up is not None:
                try:
                    clean_up(ending["state"])
                except Exception:
                    log.exception("%s: clean-up failed", what)
            self._finish({**self.ending_fields, **ending})
            state = f"{ending['state']} {ending['error'].code}" if ending.get("error") else ending["state"]
            log.info("%s ended %s after %.0f s", what, state, time.monotonic() - started)

    def _failed(self, code: str, message: str) -> dict:
        return {"state": "failed", "error": self.error_type(code=code, message=message)}

    def start_child(self, worker: Worker, first: type, timeout: float | None = None) -> Worker:
        """A child just started: tracked first (so shutdown and the job's end stop it), then
        its first message, `first`, waited for (`Ready` once loaded). Loading has no timeout
        unless `timeout`; a child that dies or errs instead fails the job as `reply` says, and
        its end frees the GPU. A child that says nothing until asked (klein's) is only `track`ed."""
        self.track(worker.process)
        self.reply(worker, (first,), timeout)
        return worker

    def ask(self, worker: Worker, request, expected: tuple[type, ...], timeout: float | None = None):
        """Sends `request` to the child and returns its answer, as `reply`."""
        worker.requests.put(request)
        return self.reply(worker, expected, timeout)

    def stop_child(self) -> None:
        """Stops the child `track` remembers (the one `start_child` started last), if one runs,
        before the job ends: a try that took too long, or a step that is over. Forgotten first,
        so shutdown doesn't stop it twice."""
        process = self._child()
        self.track(None)
        if process is not None:
            stop_process(process)

    def free_gpu(self) -> None:
        """The model's part of the job is over: its child goes and the GPU is free for the next
        job while the rest runs (a render's ffmpeg). A job that never took it: `release` does nothing."""
        self.stop_child()
        gpu.slot.release(self.gpu_kind)

    def reply(self, worker: Worker, expected: tuple[type, ...], timeout: float | None = None):
        """The child's next message, one of `expected`. Raises `Cancelled`, `TimeoutError`
        after `timeout` seconds (None: no limit), or `JobFailed` when the child dies or errs —
        unless `expected` holds its `worker_error`, which is then returned like any other."""
        try:
            message = next_message(worker.process, worker.replies, self._cancel, timeout)
        except ChildGone as gone:
            raise JobFailed("crashed", f"{self.child_name}หยุดทำงานกลางทาง ({gone}). {gpu.ADVICE}") from None
        if isinstance(message, expected):
            return message
        if isinstance(message, self.worker_error):
            log.error("the %s process failed (%s): %s", self.gpu_kind, message.code, message.detail)
            raise JobFailed("model_failed", worker_failure(self.failure, message.detail))
        raise RuntimeError(f"unknown message from the {self.gpu_kind} process: {message!r}")

    def track(self, process) -> None:
        """Remembers the running child, so shutdown can stop it and the job's end does."""
        with self._lock:
            self._process = process

    def _child(self):
        """The running child `track` remembers, or None."""
        with self._lock:
            return self._process

    def _finish(self, ending: dict) -> None:
        """Every ending of the job's thread: stops the child, frees the GPU before the
        job reads as finished (so a job started after that never meets `gpu_busy`), and
        sets the ending's fields. Never raises: the job must end, or every later POST is refused."""
        try:  # `free_gpu`, but a child that won't stop still frees the GPU
            self.stop_child()
        except Exception:
            log.exception("could not stop the %s process", self.gpu_kind)
        gpu.slot.release(self.gpu_kind)
        self.update(**ending)


class Cancelled(Exception):
    """The user cancelled: the job ends as `cancelled`."""


class ChildGone(Exception):
    """The child process exited without a last message: a Metal or CUDA crash, or killed."""

    def __init__(self, exitcode: int | None):
        super().__init__(f"exit {exitcode}")
        self.exitcode = exitcode


def next_message(process, queue, cancel: threading.Event, timeout: float | None = None):
    """The child's next message. Raises `Cancelled` once `cancel` is set, `ChildGone`
    when the child is gone, `TimeoutError` after `timeout` seconds (None: no limit)."""
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        if cancel.is_set():
            raise Cancelled()
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError()
        try:
            return queue.get(timeout=POLL_SECONDS)
        except Empty:  # multiprocessing queues raise `queue.Empty` too
            if process.is_alive():
                continue
            # A queue flushes before its process exits, so one more read gets
            # anything it sent last; nothing there means it crashed.
            try:
                return queue.get(timeout=POLL_SECONDS)
            except Empty:
                raise ChildGone(process.exitcode) from None


def stop_process(process) -> None:
    """Terminates a child that is still running, then kills it if it won't go."""
    if process.is_alive():
        process.terminate()
        process.join(TERMINATE_SECONDS)
        if process.is_alive():
            process.kill()
    process.join(TERMINATE_SECONDS)


def short(error: Exception | str) -> str:
    """The first line of an error, for a message; the full one goes to the log."""
    text = str(error).strip()
    return text.splitlines()[0][:200] if text else type(error).__name__


def worker_failure(failure: str, detail: str) -> str:
    """The message of a job whose child sent a `WorkerError` with `detail` (`workers.error_detail`):
    `failure` and the error's first line, then `gpu.ADVICE` unless its type is one of `CODE_ERROR_TYPES`.
    A child that dies or a timeout is the GPU's: those messages end with `gpu.ADVICE` themselves."""
    message = f"{failure}: {short(detail)}"
    return message if type_name(detail) in CODE_ERROR_TYPES else f"{message}. {gpu.ADVICE}"
