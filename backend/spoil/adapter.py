"""The only module that talks to yt-dlp (spoil D14). Tests replace `YtDlpAdapter`
with a fake; `error_code` and `select_formats` stay real.

Behaviour this relies on was checked against YouTube on 2026-10-29 and 2026-11-07; see
docs/library-notes/yt-dlp.md › Traps.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Literal, NamedTuple

import yt_dlp
from yt_dlp.utils import DownloadCancelled, GeoRestrictedError

from backend.paths import ProjectPaths
from backend.spoil.mp4check import MAX_SHORT_SIDE

__all__ = ["DownloadCancelled", "DownloadOptions", "ErrorCode", "YtDlpAdapter", "error_code", "select_formats"]

ErrorCode = Literal[
    "live",
    "disk_full",
    "unavailable",
    "login_required",
    "unsupported",
    "unsupported_format",
    "playlist",
    "duplicate",
    "download_error",
]

# Substrings of yt-dlp's error message, checked in this order (spoil D15, D16, D52, D56).
LIVE_MESSAGES = ("This live event will begin", "Premieres in")
# Not a bare "login": the message often quotes the link, which may have it in its path.
LOGIN_MESSAGES = ("Sign in to confirm", "not a bot", "logged-in", "registered users", "login required")
UNAVAILABLE_MESSAGES = ("Private video", "unavailable", "removed")
# "Unsupported URL" is the generic extractor's; with it off, yt-dlp finds no extractor (D55).
UNSUPPORTED_MESSAGES = ("Unsupported URL", "No suitable extractor found")
NO_FORMAT_MESSAGES = ("Requested format is not available",)

H264 = ("avc1", "h264")
AAC = ("mp4a", "aac")
SOCKET_TIMEOUT_S = 30


class DownloadOptions(NamedTuple):
    """What a download asks yt-dlp for and where it lands; the defaults are a Temp clip's
    (an h264/aac mp4 in media/temp/ with its thumbnail). toon's background sounds take the
    best audio alone into their own folder, with no thumbnail and no merge (toon spec ›
    Modules touched)."""

    format: str | None = None  # None: `select_formats`
    # Where it lands, written there too; None: media/temp/, written in media/temp/.partial/.
    folder: Callable[[ProjectPaths], Path] | None = None
    name: str = "{id}.%(ext)s"  # yt-dlp's `outtmpl`; `{id}` is `download`'s `clip_id` (a sound's id for toon)
    thumbnail: bool = True
    merge_mp4: bool = True


class YtDlpAdapter:
    def fetch_info(self, url: str, options: DownloadOptions = DownloadOptions()) -> dict:
        """The video's metadata and the formats `options` picks, without downloading."""
        with yt_dlp.YoutubeDL(self._params(None, None, options)) as ydl:
            return ydl.extract_info(url, download=False)

    def download(
        self,
        info: dict,
        project: ProjectPaths,
        clip_id: str,
        on_progress: Callable[[dict], None],
        options: DownloadOptions = DownloadOptions(),
    ) -> Path:
        """Downloads from `info` without asking the site again, into `options.name` (by
        default `{clip_id}.mp4`).

        `on_progress` gets yt-dlp's progress hook dicts and may raise
        `DownloadCancelled` to stop.
        """
        params = self._params(project, clip_id, options) | {"progress_hooks": [on_progress]}
        with yt_dlp.YoutubeDL(params) as ydl:
            result = ydl.process_ie_result(info, download=True)
        # `result["filepath"]` is None after a merge.
        return Path(result["requested_downloads"][0]["filepath"])

    def _params(self, project: ProjectPaths | None, clip_id: str | None, options: DownloadOptions) -> dict:
        import deno
        import imageio_ffmpeg

        params = {
            "format": options.format or select_formats,
            # Only sites with their own extractor: no generic page scraping (D55, ADR 0029).
            "allowed_extractors": ["default", "-generic"],
            "socket_timeout": SOCKET_TIMEOUT_S,
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "js_runtimes": {"deno": {"path": deno.find_deno_bin()}},
            "writethumbnail": options.thumbnail,
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
        }
        if options.merge_mp4:
            params["merge_output_format"] = "mp4"
        if project and clip_id:
            if options.folder is None:
                params["paths"] = {"home": str(project.media_temp_dir), "temp": str(project.partial_dir)}
            else:
                params["paths"] = {"home": str(options.folder(project)), "temp": str(options.folder(project))}
            params["outtmpl"] = options.name.format(id=clip_id)
        return params


def select_formats(ctx: dict) -> Iterator[dict]:
    """yt-dlp's `format` as a function: the largest h264 `yuv420p` picture with its short
    side ≤ 1080 and aac sound, as one combined format or a video and an audio one to merge.
    Yields nothing when there is none, which yt-dlp reports as "Requested format is not
    available" (D54). `format_sort` alone would fall back to HEVC or AV1. When no format
    is known to fit, one that names no codec is tried (D56).

    The ctx and the merged dict follow the README's "Use a custom format selector".
    """
    formats = ctx["formats"]
    pictures = [f for f in formats if _good_picture(f) and f.get("acodec") == "none"]
    sounds = [f for f in formats if _codec(f, "acodec").startswith(AAC) and f.get("vcodec") == "none"]
    choices = [f for f in formats if _good_picture(f) and _codec(f, "acodec").startswith(AAC)]
    if pictures and sounds:
        picture = max(pictures, key=_rank)
        sound = max(sounds, key=lambda f: f.get("tbr") or 0)
        choices.append(
            {
                "format_id": f"{picture['format_id']}+{sound['format_id']}",
                "ext": "mp4",
                "requested_formats": [picture, sound],
                "protocol": f"{picture.get('protocol')}+{sound.get('protocol')}",
                "width": picture.get("width"),
                "height": picture.get("height"),
                "vcodec": picture.get("vcodec"),
                "acodec": sound.get("acodec"),
                "tbr": (picture.get("tbr") or 0) + (sound.get("tbr") or 0),
            }
        )
    if choices:
        yield max(choices, key=_rank)
        return
    # A format that names no codec (Facebook's progressive `hd`/`sd`) may well be h264/aac:
    # take the best of those, and the Download job's file check decides (D56). yt-dlp
    # hands `formats` sorted worst first.
    unnamed = [f for f in formats if f.get("vcodec") is None and f.get("acodec") is None]
    if unnamed:
        yield unnamed[-1]


def _codec(info: dict, key: str) -> str:
    return info.get(key) or ""


def _short_side(info: dict) -> int:
    sides = [side for side in (info.get("width"), info.get("height")) if side]
    return min(sides) if sides else 0


def _good_picture(info: dict) -> bool:
    return (
        _codec(info, "vcodec").startswith(H264)
        and info.get("pix_fmt") in (None, "yuv420p")
        and _short_side(info) <= MAX_SHORT_SIDE
    )


def _rank(info: dict) -> tuple[int, float]:
    """Sort key: the larger short side, then the higher bitrate."""
    return _short_side(info), info.get("tbr") or 0


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
    if any(text in message for text in UNSUPPORTED_MESSAGES):
        return "unsupported"
    if any(text in message for text in NO_FORMAT_MESSAGES):
        return "unsupported_format"
    return "download_error"
