# huggingface_hub

**Kind:** library

**Version:** 2.3.0

**Docs:** https://huggingface.co/docs/huggingface_hub/llms.txt

## Best practices

- `snapshot_download()` returns the local snapshot folder path as a `str` — [Downloading files](https://huggingface.co/docs/huggingface_hub/v2.3.0/package_reference/file_download)
- Pin `revision` to a full 40-character commit hash; short hashes are not accepted — [Download guide](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/download)
- Pass `cache_dir` to keep files out of the default `~/.cache/huggingface/hub` — [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache)
- `allow_patterns` and `ignore_patterns` take one pattern or a list, matched with `fnmatch` — [Download guide](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/download)
- Use `dry_run=True` to list what would download and which files are already cached — [Download guide](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/download)
- Catch `HfHubHTTPError` rather than `httpx` or `requests` errors — [Migrating to v1.0](https://huggingface.co/docs/huggingface_hub/v2.3.0/concepts/migration)
- **Avoid:** editing files under `snapshots/`; they point into the shared cache — [Download guide](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/download)

## Pattern

```python
path = snapshot_download(
    repo_id=model.repo_id,
    revision=model.revision,
    cache_dir=MODELS_DIR,
    allow_patterns=["*.json", "*.safetensors"],
)
# path == f"{MODELS_DIR}/models--{owner}--{name}/snapshots/{revision}"
```

Follows [Downloading files](https://huggingface.co/docs/huggingface_hub/v2.3.0/package_reference/file_download).

## Traps

- `resume_download`, `force_filename` and `local_dir_use_symlinks` were removed in 1.0; passing them raises `TypeError` — [Migrating to v1.0](https://huggingface.co/docs/huggingface_hub/v2.3.0/concepts/migration)
- 2.0 swapped `httpx` for `httpx2`; exceptions from the old `httpx` package no longer match — [Migrating to v2.0](https://huggingface.co/docs/huggingface_hub/v2.3.0/concepts/migration_v2)
- Cache layout is `models--{owner}--{name}/` with `blobs/`, `refs/`, `snapshots/{commit}/` and `trees/{commit}.json` — [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache)
- Files in `snapshots/` are symlinks to `blobs/`; without symlink support (Windows without Developer Mode) real files sit in `snapshots/` and a warning is printed — [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache)
- Resume is per run only: a transient network error retries with an HTTP `Range`, but each run writes a fresh `<etag>.<id>.incomplete` file — [file_download.py v2.3.0](https://github.com/huggingface/huggingface_hub/blob/v2.3.0/src/huggingface_hub/file_download.py)
    - A killed run re-downloads the unfinished file from zero; finished files are skipped.
    - Leftover `.incomplete` files stay until `hf cache prune` — [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache)
- Offline or `local_files_only=True` with a partial snapshot raises `IncompleteSnapshotError`, no longer a silent partial folder; files outside `allow_patterns` do not count — [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache)
- `*` also matches `/`, so `*.json` matches files in subfolders too — [fnmatch](https://docs.python.org/3/library/fnmatch.html)
- Matching is case-sensitive (`fnmatchcase`), and a pattern ending in `/` gets `*` appended to match a whole folder — [_paths.py v2.3.0](https://github.com/huggingface/huggingface_hub/blob/v2.3.0/src/huggingface_hub/utils/_paths.py)
- Disk space is checked before each file, which can fail the download early — [file_download.py v2.3.0](https://github.com/huggingface/huggingface_hub/blob/v2.3.0/src/huggingface_hub/file_download.py)

## Sources

- [Downloading files](https://huggingface.co/docs/huggingface_hub/v2.3.0/package_reference/file_download) — `snapshot_download` signature, return, errors (accessed 2026-10-29)
- [Download guide](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/download) — patterns, revision, dry run (accessed 2026-10-29)
- [Understand caching](https://huggingface.co/docs/huggingface_hub/v2.3.0/guides/manage-cache) — cache layout, symlinks, `.incomplete`, `IncompleteSnapshotError` (accessed 2026-10-29)
- [Migrating to v1.0](https://huggingface.co/docs/huggingface_hub/v2.3.0/concepts/migration) — removed parameters, error classes (accessed 2026-10-29)
- [Migrating to v2.0](https://huggingface.co/docs/huggingface_hub/v2.3.0/concepts/migration_v2) — `httpx2` switch, removed APIs (accessed 2026-10-29)
- [file_download.py v2.3.0](https://github.com/huggingface/huggingface_hub/blob/v2.3.0/src/huggingface_hub/file_download.py) — temp-file and resume behaviour (accessed 2026-10-29)
- [_paths.py v2.3.0](https://github.com/huggingface/huggingface_hub/blob/v2.3.0/src/huggingface_hub/utils/_paths.py) — pattern matching (accessed 2026-10-29)
- [fnmatch](https://docs.python.org/3/library/fnmatch.html) — wildcard semantics (accessed 2026-10-29)
