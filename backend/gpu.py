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

Kind = Literal["transcribe", "describe", "draft", "voice", "render"]

# How `gpu_busy` names the running job (spoil-maker spec › Frontend).
RUNNING_NAMES: dict[Kind, str] = {
    "transcribe": "ถอดบทพูด",
    "describe": "บรรยายฉาก",
    "draft": "ร่างบท",
    "voice": "สร้างเสียง",
    "render": "render",
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
        self._trimming_clip: str | None = None
        self._rendering_clip: str | None = None  # a Render job's clip, GPU or not (spoil D42)
        self.draft_lock = threading.RLock()
        """Every read-change-write of `draft.json`, from the API or a job, and the
        `draft_locked` check with the start of a job that changes the draft (D51).
        Lock order: a job slot's lock, then this one, then the slot's own lock."""

    def take(self, kind: Kind, clip_ids: Iterable[str] = (), locks_draft: bool = False) -> None:
        """Raises `ApiError` 409 `gpu_busy` with `running` when another job holds it.
        `locks_draft`: the job changes the Spoil draft (a Draft, sentence Voice or Render job),
        so edits are `draft_locked` until it ends. A Render job holds the slot while it voices
        sentences only (spoil-maker spec › ช่อง GPU)."""
        clip_ids = frozenset(clip_ids)
        with self._lock:
            if self._trimming_clip in clip_ids:
                raise _clip_busy()
            if self._kind is not None:
                running = self._kind
                raise ApiError(409, "gpu_busy", f"รอให้งาน{RUNNING_NAMES[running]}เสร็จก่อน", running=running)
            self._kind, self._clip_ids, self._holds_draft = kind, clip_ids, locks_draft

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
    def clip_untouched(self, clip_id: str, by: Iterable[Kind] | None = None) -> Iterator[None]:
        """Runs the block (deleting or changing the clip's files) under the slot's lock:
        refuses with `ApiError` 409 `clip_busy` while the holder reads the clip — only a
        holder of a kind in `by`, when given — or while a Trim job cuts it, whatever `by`
        (spoil D42); and no job can take the slot until the block ends."""
        with self._lock:
            self._refuse_readers(clip_id, by)
            if clip_id == self._trimming_clip:
                raise _clip_busy()
            yield

    @contextmanager
    def trimmed_clip_swap(self, clip_id: str) -> Iterator[None]:
        """`clip_untouched` for the Trim job that cuts the clip, putting its new mp4 in
        place: the clip's trim mark is its own, so only a holder that reads the clip refuses."""
        with self._lock:
            self._refuse_readers(clip_id)
            yield

    def _refuse_readers(self, clip_id: str, by: Iterable[Kind] | None = None) -> None:
        """Call with the lock held."""
        if clip_id in self._clip_ids and (by is None or self._kind in by):
            raise _clip_busy()

    def begin_render(self, clip_id: str) -> None:
        """Marks the clip a Render job reads, from its start to `end_render` on every ending:
        a render whose sentences all have their voice never takes the slot, and one that
        voices frees it before ffmpeg, yet both read the clip till the end. Raises `ApiError`
        409 `clip_busy` while a Trim job cuts it; `begin_trim` refuses the marked clip (D42)."""
        with self._lock:
            if clip_id == self._trimming_clip:
                raise _clip_busy()
            self._rendering_clip = clip_id

    def end_render(self) -> None:
        with self._lock:
            self._rendering_clip = None

    @contextmanager
    def begin_trim(self, clip_id: str) -> Iterator[None]:
        """Runs the block (the Trim job's start checks) like `clip_untouched`; when it ends
        without raising, the Trim job cuts the clip, and every job that reads it is refused
        until `end_trim`. It holds no GPU (spoil D41, D42), so the slot's holder is left as it is.

        The mark outlives this `with`: it is set as the block ends, still under the lock, and
        stays set until the job's thread calls `end_trim` on every ending."""
        with self.clip_untouched(clip_id):
            if clip_id == self._rendering_clip:
                raise _clip_busy()
            yield
            self._trimming_clip = clip_id

    def end_trim(self) -> None:
        with self._lock:
            self._trimming_clip = None

    def is_trimming(self, clip_id: str) -> bool:
        with self._lock:
            return self._trimming_clip == clip_id

    @contextmanager
    def clip_files_lock(self) -> Iterator[None]:
        """Runs the block under the slot's lock, refusing nothing. A clip's EP cuts are read
        and written under it: the cuts sit on the clip's Shot edges, and a Describe job swaps
        in new Shots and removes the cuts under this same lock, so neither sees half of the
        other (spoil-maker spec › EP, D71)."""
        with self._lock:
            yield


def _clip_busy() -> ApiError:
    return ApiError(409, "clip_busy", "คลิปนี้กำลังถูกใช้ในงานอื่น")


slot = GpuSlot()
