"""What the Download job and the Transcribe job share: one job at a time, held in
memory behind one lock, with a cancel flag its thread checks (ADR 0010)."""

import threading
from typing import Generic, TypeVar

from pydantic import BaseModel

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
