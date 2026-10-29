# imageio-ffmpeg

**Kind:** library

**Version:** 0.7.0

**Docs:** https://github.com/imageio/imageio-ffmpeg

## Best practices

- Call `get_ffmpeg_exe()` to get the ffmpeg path; it searches in this order — [README](https://github.com/imageio/imageio-ffmpeg)
    1. `IMAGEIO_FFMPEG_EXE` environment variable.
    2. The binary bundled in the wheel (`imageio_ffmpeg/binaries/`).
    3. A conda ffmpeg under `sys.prefix`.
    4. `ffmpeg` on the system `PATH`.
- PyPI wheels bundle ffmpeg for Windows, Linux and macOS; installs with `--no-binary` or conda `--no-deps` must supply their own — [README](https://github.com/imageio/imageio-ffmpeg)
- `get_ffmpeg_version()` returns the version string of the executable in use — [README](https://github.com/imageio/imageio-ffmpeg)
- `get_ffmpeg_exe()` raises `RuntimeError` when no valid ffmpeg is found — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)

## Pattern

```python
def find_ffmpeg() -> tuple[str | None, str]:
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except RuntimeError:
        return None, "missing"
    if os.environ.get("IMAGEIO_FFMPEG_EXE"):
        return exe, "env"
    return exe, "system" if exe == "ffmpeg" else "bundled"
```

Follows [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py).

## Traps

- There is no API that says which source was used; infer it from the returned value — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)
    - System ffmpeg comes back as the bare string `"ffmpeg"`, not a full path.
    - Bundled and conda binaries come back as absolute paths.
- `IMAGEIO_FFMPEG_EXE` is returned as-is without running it, so a wrong value is not caught here — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)
- The auto-detect result is cached for the process (`lru_cache`); a test that changes the files will not see a new result — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)
- Each candidate is checked by running `ffmpeg -version`, so the first call starts subprocesses — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)
- `RuntimeError` message: "No ffmpeg exe could be found." It names the env var as the fix — [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py)

## Sources

- [imageio-ffmpeg README](https://github.com/imageio/imageio-ffmpeg) — API, lookup order, platform wheels (accessed 2026-10-29)
- [_utils.py v0.7.0](https://github.com/imageio/imageio-ffmpeg/blob/v0.7.0/imageio_ffmpeg/_utils.py) — lookup code, error, caching (accessed 2026-10-29)
