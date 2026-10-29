"""The only module that talks to yt-dlp (spoil D14). Tests replace `YtDlpAdapter`
with a fake; `error_code` stays real so the fake's exceptions are sorted the
same way.

Behaviour this relies on was checked against YouTube on 2026-10-29; see
docs/library-notes/yt-dlp.md › Traps.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Literal

import yt_dlp
from yt_dlp.utils import DownloadCancelled, GeoRestrictedError

from backend.paths import ProjectPaths

__all__ = ["DownloadCancelled", "ErrorCode", "YtDlpAdapter", "error_code"]

ErrorCode = Literal["live", "disk_full", "unavailable", "login_required", "youtube_error"]

# Substrings of yt-dlp's error message, checked in this order (spoil D15, D16).
LIVE_MESSAGES = ("This live event will begin", "Premieres in")
LOGIN_MESSAGES = ("Sign in to confirm", "not a bot")
UNAVAILABLE_MESSAGES = ("Private video", "unavailable", "removed")


class YtDlpAdapter:
    def fetch_info(self, url: str) -> dict:
        """The video's metadata, without downloading."""
        with yt_dlp.YoutubeDL(self._params(None)) as ydl:
            return ydl.extract_info(url, download=False)

    def download(
        self, info: dict, project: ProjectPaths, on_progress: Callable[[dict], None]
    ) -> Path:
        """Downloads from `info` without asking YouTube again; returns the mp4.

        `on_progress` gets yt-dlp's progress hook dicts and may raise
        `DownloadCancelled` to stop.
        """
        params = self._params(project) | {"progress_hooks": [on_progress]}
        with yt_dlp.YoutubeDL(params) as ydl:
            result = ydl.process_ie_result(info, download=True)
        # `result["filepath"]` is None after a merge.
        return Path(result["requested_downloads"][0]["filepath"])

    def _params(self, project: ProjectPaths | None) -> dict:
        import deno
        import imageio_ffmpeg

        params = {
            "format_sort": ["res:1080", "vcodec:h264", "acodec:aac"],
            "merge_output_format": "mp4",
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "js_runtimes": {"deno": {"path": deno.find_deno_bin()}},
            "outtmpl": "%(id)s.%(ext)s",
            "writethumbnail": True,
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
        }
        if project:
            params["paths"] = {"home": str(project.media_temp_dir), "temp": str(project.partial_dir)}
        return params


def error_code(error: Exception) -> ErrorCode:
    """Sorts an exception from `fetch_info` or `download` into a job error code.

    Mostly by message; only geo restriction has its own exception class, which
    yt-dlp wraps in `DownloadError.exc_info`.
    """
    cause = getattr(error, "exc_info", None)
    cause = cause[1] if cause and cause[1] is not None else error
    message = str(error)
    if any(text in message for text in LIVE_MESSAGES):
        return "live"
    if any(text in message for text in LOGIN_MESSAGES):
        return "login_required"
    if isinstance(cause, GeoRestrictedError) or any(text in message for text in UNAVAILABLE_MESSAGES):
        return "unavailable"
    return "youtube_error"
