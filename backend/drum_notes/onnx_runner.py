"""The only module that imports onnxruntime (drum-notes D7, D17; ADR 0041): it opens a model file
as a session, and runs the two drum models on it — ADTOF over a whole range in one call, Beat This!
one chunk at a time. Tests stand in with a fake at `open_session` (`PickJobs(open_session=…)`), so
onnxruntime never runs in CI; the Pick job's chunk plan and stitching are `score`'s.

onnxruntime is imported inside the function: the backend must start in under a second
(docs/library-notes/onnxruntime.md).
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import numpy as np

CPU = ["CPUExecutionProvider"]  # the one provider: a CPU job in a thread, no GPU slot (ADR 0040)

# The models' input and output names (their cards; checked on the files in ticket 01's spike).
WAVEFORM = "waveform"
PAD_FRAMES = "pad_frames"
ACTIVATIONS = "activations"
BEAT, DOWNBEAT = "beat", "downbeat"


class Session(Protocol):
    """What `open_session` gives: onnxruntime's `InferenceSession`, or a test's fake."""

    def run(self, output_names: list[str] | None, feeds: dict) -> list: ...


OpenSession = Callable[[Path], Session]


def open_session(model_file: Path) -> Session:
    """An `InferenceSession` of the file on the CPU. Raises for a file onnxruntime can't load
    (missing, truncated, not ONNX): setup's smoke test and a Pick job's `model_broken` both
    read that as the file being broken (D20)."""
    import onnxruntime

    return onnxruntime.InferenceSession(str(model_file), providers=CPU)


def run_adtof(session: Session, pcm: "np.ndarray") -> "np.ndarray":
    """ADTOF over the whole range at once (an RNN, D20): float32 mono at 44.1 kHz in `[1, samples]`
    → `[frames, 5]` sigmoid activations at 100 frames/s."""
    import numpy as np

    [activations] = session.run([ACTIVATIONS], {WAVEFORM: np.asarray(pcm, np.float32)[None, :]})
    return np.asarray(activations, np.float32).reshape(-1, 5)


def run_beat_this(session: Session, pcm: "np.ndarray", pad_before: int, pad_after: int) -> tuple["np.ndarray", "np.ndarray"]:
    """Beat This! over one chunk: float32 mono at 22.05 kHz in `[1, N]` and `pad_frames` `[2]` int64
    → the `beat` and `downbeat` logits, `[T]` each, `T = pad_before + frames + pad_after` at 50 frames/s."""
    import numpy as np

    feeds = {WAVEFORM: np.asarray(pcm, np.float32)[None, :], PAD_FRAMES: np.array([pad_before, pad_after], np.int64)}
    beat, downbeat = session.run([BEAT, DOWNBEAT], feeds)
    return np.asarray(beat, np.float32).reshape(-1), np.asarray(downbeat, np.float32).reshape(-1)
