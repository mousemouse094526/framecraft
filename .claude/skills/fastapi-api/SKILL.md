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
├── spoil/        ← a feature with several modules gets a package (spoil D14)
├── routes/       ← one router file per feature, e.g. setup_status.py
└── tests/        ← pytest, test_{module}.py
```

No auth and no public/private split: the app binds 127.0.0.1 only.

## Flow

route (routes/{feature}.py) → module function (checks.py, spoil/) → libraries

Long jobs run as a daemon thread in the backend process; their state lives in
memory and the web page polls it (ADR 0010).

## Where shared code goes

- Code one feature uses lives in that feature's module.
- A second user appears → move it to a top-level module named for its kind, in
  the same change. Never create a shared file ahead of need.
- The second AI feature (TTS, transcribe) decides whether features move into
  `backend/features/{feature}/`; record it here when it does.

## Never break

- Nothing installs packages or downloads models at runtime; only `backend.setup`
  does. Media from a link the user typed may be fetched at runtime (ADR 0008).
- Only one module per library that talks to the outside world (the yt-dlp
  adapter in `backend.spoil`); tests replace it with a fake.
- `TrustedHostMiddleware` allows only `127.0.0.1`, `localhost`, `[::1]`
  (ADR 0011).
- Every Hugging Face call passes `cache_dir` from `backend.paths`; never rely on
  `HF_HOME` or `HF_HUB_CACHE` (ADR 0003).
- Every model comes from `backend.models` with its pinned `revision` (ADR 0004).
- ffmpeg is found with `imageio_ffmpeg.get_ffmpeg_exe()`, never PATH (ADR 0005).
- uvicorn binds 127.0.0.1 only. `npm run dev` starts it with the venv's Python
  (`scripts/dev-api.mjs`), never `uv run`: right after setup the terminal may
  not see uv on PATH (D24).
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
