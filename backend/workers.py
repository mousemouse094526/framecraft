"""A model's child process as the job that started it holds it (ADR 0012): `spoil_maker.llm`,
`spoil_maker.tts` and `toon.klein` return one, and job slots read its replies (`jobs`). No
import beyond the standard library: a child imports its adapter, and this with it."""

from typing import Any, NamedTuple


class Worker(NamedTuple):
    """The child process and its two queues: what the job asks it, what it answers."""

    process: Any
    requests: Any
    replies: Any

    def end(self) -> None:
        """Asks the child to exit on its own once it has answered what it was asked."""
        self.requests.put(None)
