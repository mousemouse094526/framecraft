# framecraft

Local video generator: a React UI calling a FastAPI backend that runs
OmniVoice, Whisper, and ffmpeg on your machine. Personal, non-commercial use
only — see [NOTICE.md](NOTICE.md).

Supported: Mac with Apple Silicon. Windows with an NVIDIA card comes next.

## Setup

Install [Node.js 22+](https://nodejs.org) first, then run once:

```sh
./setup.sh
```

It installs [uv](https://docs.astral.sh/uv/) if missing, Python 3.12, every
package, ffmpeg, both models, and the web UI's npm packages (about 5 GB; the whole folder ends up near
10 GB) into this folder, then prints a checklist. Running it again is safe:
what is installed is skipped and a broken download resumes. Keep at least
15 GB free while models download.

## Run

```sh
npm run dev
```

Then open http://localhost:5173 for the Setup status page. This starts the
backend on `127.0.0.1:8000` (lines prefixed `[api]`) and the web UI (lines
prefixed `[web]`); it installs nothing. `GET /api/setup/status` returns the
same checklist as JSON.

## Tests

```sh
uv run pytest
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Moving to another machine

Copy the whole folder to another machine with the same OS and run
`./setup.sh` again. The models in `models/` are reused; `.venv` is rebuilt,
which needs internet.

## Uninstall

1. Delete the project folder — `.venv/`, `models/`, and `node_modules/` are
   all inside it.
2. Remove uv's cache and Python: `uv cache clean` and `uv python uninstall 3.12`.
3. Remove uv itself: follow
   [uv's uninstall guide](https://docs.astral.sh/uv/getting-started/installation/#uninstallation).
