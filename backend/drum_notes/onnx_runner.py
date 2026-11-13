"""The only module that imports onnxruntime (drum-notes D7, D17; ADR 0041): it opens a model file
as a session. The Pick job's runs of ADTOF, Beat This! and Basic Pitch come in their ticket; tests
stand in with a fake at this one edge, and onnxruntime never runs in CI.

onnxruntime is imported inside the function: the backend must start in under a second
(docs/library-notes/onnxruntime.md).
"""

from pathlib import Path

CPU = ["CPUExecutionProvider"]  # the one provider: a CPU job in a thread, no GPU slot (ADR 0040)


def open_session(model_file: Path):
    """An `InferenceSession` of the file on the CPU. Raises for a file onnxruntime can't load
    (missing, truncated, not ONNX): setup's smoke test and a Pick job's `model_broken` both
    read that as the file being broken (D20)."""
    import onnxruntime

    return onnxruntime.InferenceSession(str(model_file), providers=CPU)
