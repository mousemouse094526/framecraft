# yt-dlp

**Kind:** library

**Version:** 2026.10.26, extras `default` (yt-dlp-ejs 0.8.0) and `deno` (deno 2.9.8)

**Docs:** https://github.com/yt-dlp/yt-dlp (the `YoutubeDL` class docstring is the API reference)

## Best practices

- Embed through `YoutubeDL(params)` as a context manager; every option is a key in `params`, documented in the class docstring — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- `extract_info(url, download=False)` returns the info dict without downloading; `process_ie_result(info, download=True)` downloads from that same dict without asking the site again — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- `format_sort: ["res:1080", ...]` sorts by the smaller side of the picture and prefers the largest format not above 1080 — [README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats)
- `progress_hooks` get a dict; check `status` first (`downloading`, `finished`, `error`) and ignore unknown values. `total_bytes` and `total_bytes_estimate` may be `None` — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- Raising `yt_dlp.utils.DownloadCancelled` inside a progress hook stops the download — [utils/_utils.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/utils/_utils.py)
- YouTube needs a JavaScript runtime; `js_runtimes: {"deno": {"path": ...}}` points at a Deno that is not on `PATH`. Without the key only `deno` on `PATH` is tried — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py), [EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS)
- `ffmpeg_location` takes the binary itself or its folder — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- `paths: {"home": ..., "temp": ...}` keeps files being written apart from finished ones — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- **Avoid:** `remote_components`; it fetches JavaScript from npm or GitHub at runtime. The `default` extra ships the matching `yt-dlp-ejs` instead — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)

## Pattern

```python
def fetch_then_download(url: str, params: dict, on_progress) -> Path:
    with YoutubeDL(params) as ydl:
        info = ydl.extract_info(url, download=False)
    with YoutubeDL({**params, "progress_hooks": [on_progress]}) as ydl:
        result = ydl.process_ie_result(info, download=True)
    return Path(result["requested_downloads"][0]["filepath"])
```

Follows [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py).

## Traps

Checked against YouTube on 2026-10-29 with this version (spoil ticket 01):

- Errors from `extract_info` and `process_ie_result` are `DownloadError`; the original exception is `error.exc_info[1]` (an `ExtractorError` with `expected=True` for site messages) — [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py)
- `DownloadCancelled` raised in a hook comes out of `process_ie_result` as itself, not wrapped in `DownloadError`. The `.part` file and the thumbnail stay in the `temp` path.
- A not-yet-started live event raises at `extract_info` with "This live event will begin in …"; there is no info dict, so no `live_status`.
- An age-gated video raises "Sign in to confirm your age. …"; the bot check is "Sign in to confirm you're not a bot".
- A private or removed video raises "Video unavailable …" or "This video is unavailable".
- `result["filepath"]` is `None` after a merge; the mp4 path is in `result["requested_downloads"][0]["filepath"]`.
- `requested_formats` is missing when one combined format was picked (small old videos); size is then only on the info dict itself (`filesize`, `filesize_approx`, `tbr`).
- `thumbnails[i]["filepath"]` names the file under the `temp` path, but the file ends up in `home` after the download.
- Merging into mp4 works with imageio-ffmpeg's ffmpeg and no ffprobe: 1080p h264 + aac came out 1920×1080 with sound.
- Warnings ("Unknown codec …") still print with `quiet: True`; `no_warnings: True` hides them.

## Sources

- [YoutubeDL.py at 2026.10.26](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/YoutubeDL.py) — params, progress hooks, `js_runtimes` (accessed 2026-10-29, read from the installed package)
- [utils/_utils.py at 2026.10.26](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/yt_dlp/utils/_utils.py) — `DownloadError`, `DownloadCancelled`, `GeoRestrictedError` (accessed 2026-10-29)
- [README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) — `res` meaning (accessed 2026-10-29)
- [EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS) — JavaScript runtime requirement (accessed 2026-10-29)
