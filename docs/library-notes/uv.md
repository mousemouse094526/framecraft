# uv

**Kind:** runtime

**Version:** 0.13.6

**Docs:** https://docs.astral.sh/uv/llms.txt

## Best practices

- Set `project.requires-python`; it limits allowed syntax and the dependency versions uv resolves — [Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/)
- A project with no `[build-system]` is fine for an application: uv installs only its dependencies, not the project — [Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/)
- `[tool.uv] package = false` forces that even when a build system is declared — [Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/)
- Put dev tools in `[dependency-groups] dev`; uv syncs the `dev` group by default, `--no-dev` skips it — [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- Pin a package to a named index with `[tool.uv.sources]`, e.g. `torch = { index = "pytorch-cu130" }` — [Package indexes](https://docs.astral.sh/uv/concepts/indexes/)
- Give a list of sources with `marker = "sys_platform == 'linux'"` and so on to choose an index per platform — [PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/)
- Mark such an index `explicit = true` so only packages pinned to it come from it — [Package indexes](https://docs.astral.sh/uv/concepts/indexes/)
- `uv lock` writes `uv.lock`; `uv sync` installs it and removes packages not in it — [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- `uv run` locks and syncs first; `uv run --no-sync` skips that check — [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- Install on macOS and Linux with `curl -LsSf https://astral.sh/uv/install.sh | sh`; pin a version as `https://astral.sh/uv/0.13.6/install.sh` — [Installation](https://docs.astral.sh/uv/getting-started/installation/)
- Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` — [Installation](https://docs.astral.sh/uv/getting-started/installation/)

## Pattern

```toml
[tool.uv.sources]
torch = [
  { index = "pytorch-cu130", marker = "sys_platform == 'linux' or sys_platform == 'win32'" },
]

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true
```

Follows [PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/).

## Traps

- Where the marker does not match (macOS here), the package falls back to PyPI — [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- An index named in sources must be defined in `pyproject.toml`; CLI, env var and user-config indexes are not seen — [Package indexes](https://docs.astral.sh/uv/concepts/indexes/)
- Sources are read only by uv; pip and other tools ignore them — [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- `--locked` errors when `uv.lock` is stale; `--frozen` uses it without checking — [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- The installer puts `uv` in the first of `$XDG_BIN_HOME`, `$XDG_DATA_HOME/../bin`, `$HOME/.local/bin` — [install.sh 0.13.6](https://astral.sh/uv/0.13.6/install.sh)
- The current shell does not see `uv` until it runs `source $HOME/.local/bin/env` (fish: `env.fish`) or restarts — [install.sh 0.13.6](https://astral.sh/uv/0.13.6/install.sh)
- On Windows it goes to `%USERPROFILE%\.local\bin` unless `XDG_*` is set — [Storage](https://docs.astral.sh/uv/reference/storage/)
- `UV_NO_MODIFY_PATH=1` stops the installer editing shell profiles; `UV_INSTALL_DIR` moves only the binary — [Installer](https://docs.astral.sh/uv/reference/installer/)

## Sources

- [Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/) — `requires-python`, build system, `package = false` (accessed 2026-10-29)
- [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/) — dependency groups, sources, markers (accessed 2026-10-29)
- [Package indexes](https://docs.astral.sh/uv/concepts/indexes/) — `explicit`, index priority (accessed 2026-10-29)
- [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) — `uv lock`, `uv sync`, `--no-sync` (accessed 2026-10-29)
- [Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) — per-platform index example (accessed 2026-10-29)
- [Installation](https://docs.astral.sh/uv/getting-started/installation/) — installer commands, version pinning (accessed 2026-10-29)
- [Installer](https://docs.astral.sh/uv/reference/installer/) — `UV_INSTALL_DIR`, `UV_NO_MODIFY_PATH` (accessed 2026-10-29)
- [Storage](https://docs.astral.sh/uv/reference/storage/) — executable directory (accessed 2026-10-29)
- [install.sh 0.13.6](https://astral.sh/uv/0.13.6/install.sh) — install dir order, env file (accessed 2026-10-29)
