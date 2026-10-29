# Setup

**Owns:** installing packages, downloading models, writing Model markers,
`npm install` — everything ADR 0002 keeps out of runtime.

**Must not:** start the backend, or be imported by the backend at runtime.

## Shape

```text
setup.sh / setup.cmd -> setup.ps1   (install uv, check node, uv sync)
  -> uv run --no-sync python -m backend.setup   (everything else)
```

## Rules

- Wrappers stay thin: install uv, check node/npm, `uv sync`, call `backend.setup`.
- Every step can be re-run; skip what is already `ok`, resume what is partial.
- A Model marker is written only after its download finished.
- Exit 0 only when no Checklist item is `missing`.
- Messages to the user are Thai and printed from Python with `PYTHONUTF8=1`.

## Good examples

- None yet — the first ticket that touches this layer sets it.
