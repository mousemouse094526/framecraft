"""The one GPU slot of the backend: every job that loads a model takes it before it
starts, and a job that can't is refused at once, naming the one that runs (ADR 0015).
It also holds the Spoil draft's lock and knows whether the holder works on the draft
(spoil-maker spec › Spoil draft, D51).

`slot` is looked up at call time, so tests swap it for a fresh one.
"""

import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from typing import Literal

from backend.errors import ApiError

# Render comes in a later ticket (spoil-maker spec › ช่อง GPU).
Kind = Literal["transcribe", "describe", "draft", "voice"]

# How `gpu_busy` names the running job (spoil-maker spec › Frontend).
RUNNING_NAMES: dict[Kind, str] = {
    "transcribe": "ถอดบทพูด",
    "describe": "บรรยายฉาก",
    "draft": "ร่างบท",
    "voice": "สร้างเสียง",
}

# Ends the message of a job whose model failed or stopped: another app may hold the GPU.
ADVICE = "ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง"


class GpuSlot:
    """Who holds the GPU, and which Temp clips that job reads (spoil-maker D49).

    Its lock is always the innermost: a job slot's lock and `draft_lock` may be held
    while taking it, never the other way round, so they can't deadlock.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._kind: Kind | None = None
        self._clip_ids: frozenset[str] = frozenset()
        self._holds_draft = False
        self.draft_lock = threading.RLock()
        """Every read-change-write of `draft.json`, from the API or a job, and the
        `draft_locked` check with the start of a job that changes the draft (D51).
        Lock order: a job slot's lock, then this one, then the slot's own lock."""

    def take(self, kind: Kind, clip_ids: Iterable[str] = (), draft: bool = False) -> None:
        """Raises `ApiError` 409 `gpu_busy` with `running` when another job holds it.
        `draft`: the job changes the Spoil draft, so edits are `draft_locked` until it ends."""
        with self._lock:
            if self._kind is not None:
                running = self._kind
                raise ApiError(409, "gpu_busy", f"รอให้งาน{RUNNING_NAMES[running]}เสร็จก่อน", running=running)
            self._kind, self._clip_ids, self._holds_draft = kind, frozenset(clip_ids), draft

    def release(self, kind: Kind) -> None:
        """Frees the slot if `kind` holds it; every ending of a job calls it (done, failed, cancelled)."""
        with self._lock:
            if self._kind == kind:
                self._kind, self._clip_ids, self._holds_draft = None, frozenset(), False

    def holds_draft(self) -> bool:
        """Whether the holder changes the Spoil draft: edits are `draft_locked` (D51)."""
        with self._lock:
            return self._holds_draft

    def reads_clip(self, kind: Kind, clip_id: str) -> bool:
        """Whether a job of `kind` holds the slot and reads that clip."""
        with self._lock:
            return self._kind == kind and clip_id in self._clip_ids

    @contextmanager
    def clip_untouched(self, clip_id: str) -> Iterator[None]:
        """Runs the block (deleting the clip's files) under the slot's lock: refuses with
        `ApiError` 409 `clip_busy` while the holder reads the clip, and no job can take
        the slot until the block ends."""
        with self._lock:
            if clip_id in self._clip_ids:
                raise ApiError(409, "clip_busy", "คลิปนี้กำลังถูกใช้ในงานอื่น")
            yield


slot = GpuSlot()
