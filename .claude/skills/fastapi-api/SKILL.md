---
name: fastapi-api
description: >-
  How framecraft's Python backend code (backend/) is structured and written:
  FastAPI, uv, Python 3.12, pytest. Use whenever writing, moving, or reviewing
  code under backend/ or the setup wrappers (setup.sh, setup.ps1, setup.cmd).
---

# FastAPI backend

The local Python backend that runs every AI and media job (ADR 0001), plus the
setup entry point that installs everything (ADR 0002).

## Folder structure

```
backend/
├── app.py        ← FastAPI app; mounts every router under /api
├── paths.py      ← project root and models/ paths (ADR 0003)
├── models.py     ← the model registry, pinned commits (ADR 0004)
├── checks.py     ← Status check, shared by setup and the API
├── setup.py      ← entry point: python -m backend.setup
├── routes/       ← one router file per feature, e.g. setup_status.py
└── tests/        ← pytest, test_{module}.py
```

No auth and no public/private split: the app binds 127.0.0.1 only.

## Flow

route (routes/{feature}.py) → module function (checks.py, later features/) → libraries

## Where shared code goes

- Code one feature uses lives in that feature's module.
- A second user appears → move it to a top-level module named for its kind, in
  the same change. Never create a shared file ahead of need.
- The second AI feature (TTS, transcribe) decides whether features move into
  `backend/features/{feature}/`; record it here when it does.

## Never break

- Nothing installs or downloads at runtime; only `backend.setup` does (ADR 0002).
- Every Hugging Face call passes `cache_dir` from `backend.paths`; never rely on
  `HF_HOME` or `HF_HUB_CACHE` (ADR 0003).
- Every model comes from `backend.models` with its pinned `revision` (ADR 0004).
- ffmpeg is found with `imageio_ffmpeg.get_ffmpeg_exe()`, never PATH (ADR 0005).
- uvicorn binds 127.0.0.1 only.
- The Status check never imports `omnivoice` or `transformers` and never uses
  the network.
- `setup.ps1` stays ASCII-only; Thai text is printed from Python.

## Rules by layer

| File | Covers |
|---|---|
| [rules/routes.md](rules/routes.md) | FastAPI routers and response shapes |
| [rules/setup.md](rules/setup.md) | backend.setup and the OS wrappers |
| [rules/testing.md](rules/testing.md) | pytest, fakes, what never runs in tests |

A layer with no rules file → stop and ask before writing it.
