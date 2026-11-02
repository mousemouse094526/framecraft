"""What every long job shares: one job of a kind at a time, held in memory behind
one lock with a cancel flag its thread checks (ADR 0010), and the child process a
model runs in, reporting through a queue (ADR 0012)."""

import logging
import threading
import time
from queue import Empty
from typing import Generic, TypeVar

from pydantic import BaseModel

from backend import gpu
from backend.errors import ApiError, JobFailed

log = logging.getLogger(__name__)

POLL_SECONDS = 0.2  # how often a thread looks at the cancel flag while the child works
TERMINATE_SECONDS = 5  # a child that ignores SIGTERM this long is killed

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

    def _taken(self) -> bool:
        """Whether a job is still running. Call with the lock held."""
        return self._job is not None and self._job.state in self.unfinished

    def _update(self, **fields) -> None:
        with self._lock:
            for name, value in fields.items():
                setattr(self._job, name, value)


class ModelJobSlot(JobSlot[Job]):
    """A job slot whose job runs a model in a child process and holds the GPU slot
    as `gpu_kind` (ADR 0012, ADR 0015). Subclasses also set `nothing_to_cancel`, the
    message of a cancel with no running job, and for `_reply`: the child's
    `worker_error` message type, `child_name` ("ตัวบรรยายฉาก") and `failure`
    ("บรรยายฉากไม่สำเร็จ"), the words a failed job's message is made of."""

    gpu_kind: gpu.Kind
    nothing_to_cancel: str
    worker_error: type
    child_name: str
    failure: str

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

    def _reply(self, process, replies, expected: tuple[type, ...], timeout: float | None = None):
        """The child's next message, one of `expected`. Raises `Cancelled`, `TimeoutError`
        after `timeout` seconds (None: no limit), or `JobFailed` when the child errs or dies."""
        try:
            message = next_message(process, replies, self._cancel, timeout)
        except ChildGone as gone:
            raise JobFailed("crashed", f"{self.child_name}หยุดทำงานกลางทาง ({gone}). {gpu.ADVICE}") from None
        if isinstance(message, self.worker_error):
            log.error("the %s process failed (%s): %s", self.gpu_kind, message.code, message.detail)
            raise JobFailed("model_failed", f"{self.failure}: {short(message.detail)}. {gpu.ADVICE}")
        if not isinstance(message, expected):
            raise RuntimeError(f"unknown message from the {self.gpu_kind} process: {message!r}")
        return message

    def _track(self, process) -> None:
        """Remembers the running child, so shutdown can stop it."""
        with self._lock:
            self._process = process

    def _finish(self, process, ending: dict) -> None:
        """Every ending of the job's thread: stops the child, frees the GPU before the
        job reads as finished (so a job started after that never meets `gpu_busy`), and
        sets the ending's fields. Never raises: the job must end, or every later POST is refused."""
        if process is not None:
            try:
                stop_process(process)
            except Exception:
                log.exception("could not stop the %s process", self.gpu_kind)
        self._track(None)
        gpu.slot.release(self.gpu_kind)
        self._update(**ending)


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
