# deno (PyPI)

**Kind:** runtime

**Version:** 2.9.8 (the `deno` wheel on PyPI, pulled in by `yt-dlp[deno]`)

**Docs:** https://pypi.org/project/deno/

## Best practices

- `deno.find_deno_bin()` returns the path of the binary the wheel installed; look it up there instead of relying on `PATH` — [deno on PyPI](https://pypi.org/project/deno/)
- `{deno} --version` prints `deno 2.9.8 (...)` on its first line — [deno CLI](https://docs.deno.com/runtime/reference/cli/)

## Traps

- `find_deno_bin()` raises `FileNotFoundError` when no binary is found; it does not return `None` — [_find_deno.py](https://pypi.org/project/deno/) (read from the installed package)
- It looks in the interpreter's `scripts` folder first, then the user scheme, then `bin/` beside the package, so a user-wide install can be found when the venv has none.

## Sources

- [deno on PyPI](https://pypi.org/project/deno/) — wheels, `find_deno_bin` (accessed 2026-10-29)
- [deno CLI reference](https://docs.deno.com/runtime/reference/cli/) — `--version` (accessed 2026-10-29)
