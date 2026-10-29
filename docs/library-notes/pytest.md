# pytest

**Kind:** library

**Version:** 9.2.0

**Docs:** https://docs.pytest.org/en/stable/

## Best practices

- Since 9.0, use the native `[tool.pytest]` table in `pyproject.toml`; list options are TOML arrays — [Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- `pythonpath` adds directories to the head of `sys.path`; `testpaths` sets where to look when no path is given — [Configuration options](https://docs.pytest.org/en/stable/reference/reference.html#ini-options-ref)
- `strict = true` turns on `strict_config`, `strict_markers`, `strict_parametrization_ids` and `strict_xfail` — [Configuration options](https://docs.pytest.org/en/stable/reference/reference.html#ini-options-ref)
- `tmp_path` gives each test its own `pathlib.Path` directory; use `tmp_path_factory` for session-wide ones — [tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- `monkeypatch` changes (`setattr`, `setenv`, `delenv`, `chdir`) are undone after the test — [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- Patch the name where your module looks it up, not the original object — [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- `capsys.readouterr()` returns `(out, err)` and clears the buffer — [API reference](https://docs.pytest.org/en/stable/reference/reference.html#capsys)
- Put shared fixtures in `conftest.py`; tests in that directory use them without importing — [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- Put teardown after `yield` in a fixture — [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- **Avoid:** importing fixtures into test modules; use `pytest_plugins` in the top `conftest.py` — [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- **Avoid:** patching builtins such as `open`; it can break pytest itself — [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)

## Pattern

```toml
[tool.pytest]
testpaths = ["backend/tests"]
pythonpath = ["."]
strict = true
```

```python
def test_reports_missing_env(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("IMAGEIO_FFMPEG_EXE", raising=False)
    main(root=tmp_path)
    assert "ffmpeg" in capsys.readouterr().out
```

Follows [Configuration](https://docs.pytest.org/en/stable/reference/customize.html) and [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).

## Traps

- Having both `[tool.pytest]` and `[tool.pytest.ini_options]` in one file is an error — [Changelog 9.0](https://docs.pytest.org/en/stable/changelog.html)
- `[tool.pytest.ini_options]` still works but takes INI-style strings (`addopts = "-ra -q"`) — [Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- A `pytest.toml` or `pytest.ini` wins over `pyproject.toml`, even when empty; options from several files never merge — [Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- `rootdir` does not change `sys.path`; imports need `pythonpath` or an installed package — [Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- `monkeypatch.delenv` and `setattr` raise when the target is missing unless `raising=False` — [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- `tmp_path` folders from the last 3 runs are kept; `--basetemp` is wiped at each run — [tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- 9.0 dropped Python 3.9 and turned `PytestRemovedIn9Warning` into errors — [Changelog 9.0](https://docs.pytest.org/en/stable/changelog.html)

## Sources

- [Configuration](https://docs.pytest.org/en/stable/reference/customize.html) — config formats, precedence, rootdir (accessed 2026-10-29)
- [API reference](https://docs.pytest.org/en/stable/reference/reference.html) — `pythonpath`, `testpaths`, `strict`, `capsys`, `monkeypatch` (accessed 2026-10-29)
- [Changelog](https://docs.pytest.org/en/stable/changelog.html) — 9.0 to 9.2 changes (accessed 2026-10-29)
- [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) — `conftest.py`, scope, teardown (accessed 2026-10-29)
- [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) — undo, `raising`, builtins warning (accessed 2026-10-29)
- [tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html) — per-test dirs, retention (accessed 2026-10-29)
