# python

**Kind:** language

**Version:** 3.12, no type checker or linter configured

**Docs:** https://docs.python.org/3.12/

## Best practices

- Pass the distribution name to `importlib.metadata.version()`, not the import name; map them with `packages_distributions()` — [importlib.metadata](https://docs.python.org/3.12/library/importlib.metadata.html)
- Catch `PackageNotFoundError` (a `ModuleNotFoundError` subclass) for "not installed" — [importlib.metadata](https://docs.python.org/3.12/library/importlib.metadata.html)
- Pass `encoding="utf-8"` to `Path.read_text()` and `write_text()`; they follow `open()`, whose default is the locale encoding — [pathlib](https://docs.python.org/3.12/library/pathlib.html)
- Use `Path.mkdir(parents=True, exist_ok=True)` for `mkdir -p` behaviour — [pathlib](https://docs.python.org/3.12/library/pathlib.html)
- Pass `subprocess.run()` a list of args, not a shell string; a full executable path avoids Windows lookup differences — [subprocess](https://docs.python.org/3.12/library/subprocess.html)
- With `timeout=`, the child is killed and waited for, then `TimeoutExpired` is raised — [subprocess](https://docs.python.org/3.12/library/subprocess.html)
- Prepare for `OSError` from `subprocess.run()` when the executable does not exist — [subprocess](https://docs.python.org/3.12/library/subprocess.html)
- `shutil.disk_usage(path)` returns `total`, `used`, `free` in bytes; `path` may be a file or a directory — [shutil](https://docs.python.org/3.12/library/shutil.html)
- `datetime.now().astimezone()` gives an aware local time, so `isoformat()` ends with the UTC offset (`+07:00`) — [datetime](https://docs.python.org/3.12/library/datetime.html)
- Pass `timeout=` to `socket.create_connection()` and use it as a context manager so the socket closes — [socket](https://docs.python.org/3.12/library/socket.html)
- **Avoid:** `datetime.utcnow()`; deprecated in 3.12, use `datetime.now(UTC)` — [datetime](https://docs.python.org/3.12/library/datetime.html)

## Pattern

```python
def probe_version(exe: str) -> str | None:
    try:
        done = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.splitlines()[0] if done.returncode == 0 else None
```

Follows [subprocess](https://docs.python.org/3.12/library/subprocess.html).

## Traps

- `os.kill(pid, 0)` is a liveness check on Unix only; on Windows any signal other than `CTRL_C_EVENT` or `CTRL_BREAK_EVENT` kills the process via `TerminateProcess` — [os.kill](https://docs.python.org/3.12/library/os.html#os.kill)
- `json.dumps()` escapes non-ASCII by default; pass `ensure_ascii=False` to keep Thai text readable — [json](https://docs.python.org/3.12/library/json.html)
- JSON keys always come back as `str`, so `loads(dumps(x)) != x` when `x` has int keys — [json](https://docs.python.org/3.12/library/json.html)
- `json.loads()` raises `JSONDecodeError`, a `ValueError` subclass, on bad input — [json](https://docs.python.org/3.12/library/json.html)
- `Path.exists()` and `is_file()` follow symlinks, so a broken symlink reports `False` — [pathlib](https://docs.python.org/3.12/library/pathlib.html)
- `socket.create_connection()` with no `timeout` uses the global default, which may block forever — [socket](https://docs.python.org/3.12/library/socket.html)
- On timeout, sockets raise `TimeoutError` (`socket.timeout` is an alias), an `OSError` subclass — [socket](https://docs.python.org/3.12/library/socket.html)

## Sources

- [importlib.metadata](https://docs.python.org/3.12/library/importlib.metadata.html) — `version()`, `PackageNotFoundError` (accessed 2026-10-29)
- [pathlib](https://docs.python.org/3.12/library/pathlib.html) — encoding, `mkdir`, symlink behaviour (accessed 2026-10-29)
- [subprocess](https://docs.python.org/3.12/library/subprocess.html) — `run`, `timeout`, `OSError` (accessed 2026-10-29)
- [os](https://docs.python.org/3.12/library/os.html#os.kill) — `os.kill` Windows behaviour (accessed 2026-10-29)
- [shutil](https://docs.python.org/3.12/library/shutil.html) — `disk_usage` (accessed 2026-10-29)
- [json](https://docs.python.org/3.12/library/json.html) — `ensure_ascii`, keys, `JSONDecodeError` (accessed 2026-10-29)
- [datetime](https://docs.python.org/3.12/library/datetime.html) — `astimezone`, `isoformat`, `utcnow` (accessed 2026-10-29)
- [socket](https://docs.python.org/3.12/library/socket.html) — `create_connection`, timeouts (accessed 2026-10-29)
