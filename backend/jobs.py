"""What every long job shares: one job of a kind at a time, held in memory behind
one lock with a cancel flag its thread checks (ADR 0010), and the child process a
model runs in, reporting through a queue (ADR 0012)."""

import threading
import time
from queue import Empty
from typing import Generic, TypeVar

from pydantic import BaseModel

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
