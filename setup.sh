#!/bin/sh
# framecraft setup for Mac. Installs uv if needed, syncs the venv, then hands
# everything else (models, checklist) to `python -m backend.setup`.
set -eu
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh
  # The installer adds uv to PATH for new shells only; it picks the first of these.
  export PATH="${XDG_BIN_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/../bin}:$HOME/.local/bin:$PATH"
fi

# npm installs the web UI and npm run dev starts it.
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js 22+ required: https://nodejs.org"
  exit 1
fi

uv sync
# PYTHONUTF8: setup prints Thai. --no-sync: uv sync above already installed everything.
PYTHONUTF8=1 exec uv run --no-sync python -m backend.setup
