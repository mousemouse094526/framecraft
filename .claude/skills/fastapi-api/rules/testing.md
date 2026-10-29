# Testing

**Owns:** proving backend behaviour with pytest.

**Must not:** download models, load models, call the network, or depend on the
machine's GPU.

## Shape

```python
def test_missing_marker(tmp_path):
    root = make_fake_root(tmp_path, models={"whisper": "ok"})
    result = run_checks(root, device_probe=lambda: "cuda", ffmpeg_probe=ok_ffmpeg)
    assert item(result, "model_omnivoice").status == "missing"
```

## Rules

- Runner: `uv run pytest`. Tests live in `backend/tests/test_{module}.py`.
- API tests use FastAPI `TestClient`.
- Fake the project root in `tmp_path`; inject probes instead of monkeypatching
  globals where the code takes them as arguments.
- Each case asserts one exact count or status, never "8 or 9".
- No browser e2e tool yet; UI is tested in the frontend with Vitest.

## Good examples

- None yet — the first ticket that touches this layer sets it.
