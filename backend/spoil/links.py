"""Which YouTube links the spoil tab accepts, checked without the network (spoil D14)."""

import re
from urllib.parse import parse_qs, urlsplit

VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
PATH_ID_PREFIXES = ("/shorts/", "/live/")


def video_id(url: str) -> str | None:
    """The 11-character video id of a single-video YouTube link, or None.

    Other query parameters (`list`, `t`, `si`) are ignored.
    """
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        return None
    host = (parts.hostname or "").lower()
    if host == "youtu.be":
        candidate = parts.path.removeprefix("/")
    elif host in YOUTUBE_HOSTS and parts.path == "/watch":
        candidate = parse_qs(parts.query).get("v", [""])[0]
    elif host in YOUTUBE_HOSTS and parts.path.startswith(PATH_ID_PREFIXES):
        candidate = parts.path.split("/")[2]
    else:
        return None
    return candidate if VIDEO_ID.fullmatch(candidate) else None
