# onnxruntime

**Kind:** library

**Version:** 1.32.0 (CPU wheel; `cp312` for `macosx_14_0_arm64` and `win_amd64`, MIT)

**Docs:** https://onnxruntime.ai/docs/api/python/api_summary.html

## Best practices

- Create one `InferenceSession(path, providers=["CPUExecutionProvider"])` per model file and reuse it; the docs say the provider list must be given explicitly since 1.10, and CPU is the one case the API lets it be left out — [Python API](https://onnxruntime.ai/docs/api/python/api_summary.html)
- Read the names and shapes from `session.get_inputs()` / `get_outputs()` (`NodeArg.name`, `.shape`, `.type` such as `tensor(float)`); a free dimension shows as a string (`'samples'`) — [Python API](https://onnxruntime.ai/docs/api/python/api_summary.html)
- `session.run(None, {name: array})` runs every output and returns a list of numpy arrays in `get_outputs()` order; feed arrays of the exact dtype the input names (`float32`, `int64`) — [Get started with Python](https://onnxruntime.ai/docs/get-started/with-python.html)
- `SessionOptions.intra_op_num_threads` (default 0: the runtime picks) and `log_severity_level` (default 2, warnings) are the knobs that matter on CPU — [Python API](https://onnxruntime.ai/docs/api/python/api_summary.html)
- A session's `run` is a blocking call; a cancel can only land between calls, so long audio goes in chunks (Beat This!), never one call of several minutes
- **Avoid:** importing `onnxruntime` at module import: it loads the native library (tens of ms, and its thread pool); import it inside the function that makes the session, as the project does with torch and numpy

## Pattern

```python
def open_session(model_file: Path):
    """The one place onnxruntime is imported; raises for a file it can't load."""
    import onnxruntime

    return onnxruntime.InferenceSession(str(model_file), providers=["CPUExecutionProvider"])

activations = session.run(None, {"waveform": pcm[None, :].astype(np.float32)})[0]
```

Follows [Get started with Python](https://onnxruntime.ai/docs/get-started/with-python.html).

## Traps

- A missing, truncated or non-ONNX file raises at `InferenceSession(...)`, not at `run`: the exceptions are `onnxruntime.capi.onnxruntime_pybind11_state.NoSuchFile`, `InvalidProtobuf` (junk bytes) and `InvalidArgument` (an empty file), all plain `Exception` subclasses of a private module (checked on 1.32.0, 2026-11-14); catch `Exception` around the constructor
- The ADTOF file names its free dims `samples` / `frames`; the Beat This! file takes a second input `pad_frames` `[2]` `int64`; the Basic Pitch file keeps TensorFlow's names (`serving_default_input_2:0`, `StatefulPartitionedCall:0..2`; which is onset is in [basic-pitch.md](basic-pitch.md)), so `get_inputs()` is the source of truth, not the model card — spike of drum-notes ticket 01 (progress.md › Log)
- Timings on a Mac Apple Silicon CPU (spike): ADTOF 30 s of audio in 0.25 s, Beat This! 30 s (two chunks of 1,500 frames) in 2.4 s, each session created in under 0.2 s

## Sources

- [onnxruntime Python API](https://onnxruntime.ai/docs/api/python/api_summary.html) — `InferenceSession`, `SessionOptions`, `get_inputs`, `run` (accessed 2026-11-14)
- [Get started with Python](https://onnxruntime.ai/docs/get-started/with-python.html) — the `providers` and `run` examples (accessed 2026-11-14)
- [onnxruntime on PyPI](https://pypi.org/project/onnxruntime/) — 1.32.0 wheels, `requires_python >= 3.11`, MIT (accessed 2026-11-14)
