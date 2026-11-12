"""A model's child process as the job that started it holds it (ADR 0012): `spoil_maker.llm`,
`spoil_maker.tts` and `toon.klein` return one, and job slots read its replies (`jobs`). No
import beyond the standard library: a child imports its adapter, and this with it."""

import faulthandler
import signal
import sys
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, NamedTuple


def as_worker_error(error_type: type, code: str, error: Exception):
    """A child's `error` as its adapter's `error_type` (`WorkerError`) with `code`, after printing
    it whole: the child shares the backend's terminal, so the full error shows in [api]."""
    traceback.print_exc()
    return error_type(code, error_detail(error))


def error_detail(error: Exception) -> str:
    """A child's error as its `WorkerError.detail`, `{type}: {error}`: `jobs.worker_error_message` reads the type."""
    return f"{type(error).__name__}: {error}"


def error_type_of(detail: str) -> str:
    """The exception type's name in an `error_detail`."""
    return detail.split(":", 1)[0]


class Worker(NamedTuple):
    """The child process and its two queues: what the job asks it, what it answers."""

    process: Any
    requests: Any
    replies: Any

    def end(self) -> None:
        """Asks the child to exit on its own once it has answered what it was asked."""
        self.requests.put(None)


def dump_stacks_on_signal() -> None:
    """`kill -USR1 {pid}` prints every thread's stack to stderr, the `[api]` terminal (toon D76):
    what a job that hangs waits on. Windows has no SIGUSR1: `py-spy dump` there."""
    if sys.platform != "win32":
        faulthandler.register(signal.SIGUSR1, all_threads=True)


@contextmanager
def dump_stacks_after(seconds: float) -> Iterator[None]:
    """Every thread's stack to stderr each `seconds` while the block runs (toon D76)."""
    faulthandler.dump_traceback_later(seconds, repeat=True)
    try:
        yield
    finally:
        faulthandler.cancel_dump_traceback_later()
