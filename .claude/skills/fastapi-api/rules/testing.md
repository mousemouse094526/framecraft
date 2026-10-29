# Testing

**Owns:** proving backend behaviour with pytest.

**Must not:** download models, load models, call the network, or depend on the
machine's GPU.

## Shape

```python
def test_missing_marker(tmp_path):
    root = make_fake_root(tmp_path, models={"whisper": "ok"})
    result = run_checks(root, fake_probes(device=lambda: "cpu"))
    assert item(result, "model_omnivoice").status == "missing"
```

## Rules

- Runner: `uv run pytest`. Tests live in `backend/tests/test_{module}.py`;
  `test_wrappers.py` checks the text of `setup.cmd` and `setup.ps1`, which can't run on a Mac.
- API tests use FastAPI `TestClient(app, base_url="http://127.0.0.1")`;
  the default `testserver` host fails `TrustedHostMiddleware` (ADR 0011).
- Fake the project root in `tmp_path`; inject probes instead of monkeypatching
  globals where the code takes them as arguments.
- Each case asserts one exact count or status, never "8 or 9".
- No browser e2e tool yet; UI is tested in the frontend with Vitest.
- Background jobs are tested without sleeps on a timer: the fake pauses at a
  named point (`pause_at`, `wait_until`, `release`) and the test polls the API
  until the job's state is final. Swap the job holder for a fresh one per test
  (`monkeypatch.setattr(jobs, "downloads", jobs.Downloads())`).
- A lifespan only runs inside `with TestClient(app, ...)`.
- The Whisper child process is never started in tests; the real `worker` is
  checked by hand with the model (spoil seam 3). Its pure helpers
  (`plan_segments`, `to_lines`) have unit tests, and one test runs a plain
  `python -c` to prove importing the adapter loads neither torch nor
  transformers.

## Good examples

- [backend/tests/conftest.py](../../../../backend/tests/conftest.py) — the `fake_root` fixture only.
- [backend/tests/fakes.py](../../../../backend/tests/fakes.py) — plain helpers tests import: `write_snapshot`, `write_marker`, fake probes.
- [backend/tests/test_setup.py](../../../../backend/tests/test_setup.py) — `FakeDownload` stands in for `snapshot_download`.
- [backend/tests/test_app.py](../../../../backend/tests/test_app.py) — API tests monkeypatch `backend.paths.ROOT` and the default probes in `backend.checks`.
- [backend/tests/test_spoil_api.py](../../../../backend/tests/test_spoil_api.py) — `FakeAdapter` from `fakes.py` stands in for yt-dlp; `wait_for_end` polls the job.
- [backend/tests/test_spoil_transcribe_api.py](../../../../backend/tests/test_spoil_transcribe_api.py) — `FakeWorker` stands in for the Whisper child process: a thread feeds the queue and pauses at a message index.
