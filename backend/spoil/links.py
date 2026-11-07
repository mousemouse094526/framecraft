"""Which links the คลิป tab accepts, checked without the network, and the Temp clip id
each source gets (spoil D14, D47, D51, D52, D55; ADR 0029).

A YouTube link in the table gives its id at once. Any other `http(s)` link with a public
host is taken as another site's; its id is known only once yt-dlp has read it.
"""

import hashlib
import ipaddress
import re
from typing import NamedTuple
from urllib.parse import parse_qs, urlsplit

CLIP_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
"""Every Temp clip id: safe as a file name and in an API path, with no dot (D51)."""

YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
PATH_ID_PREFIXES = ("/shorts/", "/live/")
YOUTUBE_KEY = "Youtube"  # yt-dlp's `extractor_key` for a YouTube video

MAX_ID = 64
HASH_LENGTH = 8
UNSAFE = re.compile(r"[^A-Za-z0-9_-]")
# Parts in decimal or `0x` hex that are not a plain four-part IPv4: `127.1`, `2130706433`
# and `0x7f000001` still reach 127.0.0.1 (D52).
NUMERIC_HOST = re.compile(r"(?:0x[0-9a-f]*|\d+)(?:\.(?:0x[0-9a-f]*|\d+))*\.?")


class Link(NamedTuple):
    url: str
    # The video id of a YouTube link in the table; None for another site's link.
    youtube_id: str | None


def parse(url: str) -> Link | None:
    """The link to load, or None when it is not one (`invalid_url`). Spaces around it go.

    YouTube's own hosts must match the table (a playlist link does not); any other site
    needs an `http(s)` link to a host that is not this machine or the local network. That
    host check does no DNS lookup and stops no redirect: it is only the first layer, and
    turning off yt-dlp's generic extractor is the main one (D55, ADR 0029).
    """
    url = url.strip()
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return None
    host = (parts.hostname or "").rstrip(".").lower()
    if not host:
        return None
    if host == "youtu.be" or host in YOUTUBE_HOSTS:
        found = _youtube_id(host, parts.path, parts.query)
        return Link(url, found) if found else None
    return Link(url, None) if _public(host) else None


def _youtube_id(host: str, path: str, query: str) -> str | None:
    if host == "youtu.be":
        candidate = path.removeprefix("/")
    elif path == "/watch":
        candidate = parse_qs(query).get("v", [""])[0]  # `list`, `t`, `si` don't matter
    elif path.startswith(PATH_ID_PREFIXES):
        candidate = path.split("/")[2]
    else:
        return None
    return candidate if YOUTUBE_ID.fullmatch(candidate) else None


def _public(host: str) -> bool:
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # A name, or digits ipaddress won't read but a resolver would.
        return NUMERIC_HOST.fullmatch(host) is None
    return not (address.is_loopback or address.is_private or address.is_link_local or address.is_unspecified)


def clip_id(extractor_key: str, video_id: str) -> str:
    """The Temp clip id of a video yt-dlp read (D51, D55).

    YouTube keeps its 11-character id, so clips from before other sites stay where they
    are. Another site's is `{site}-{id}` with the id's case kept; a character outside
    `A-Za-z0-9_-` becomes `_` and an id that is too long is cut, and either way a hash of
    the original is added so two ids never end the same.
    """
    if extractor_key == YOUTUBE_KEY and YOUTUBE_ID.fullmatch(video_id):
        return video_id
    digest = hashlib.sha1(f"{extractor_key}:{video_id}".encode()).hexdigest()[:HASH_LENGTH]
    safe = f"{UNSAFE.sub('_', extractor_key.lower())}-{UNSAFE.sub('_', video_id)}"
    if safe != f"{extractor_key.lower()}-{video_id}":
        safe = f"{safe}-{digest}"
    if len(safe) > MAX_ID:
        safe = f"{safe[: MAX_ID - HASH_LENGTH - 1]}-{digest}"
    return safe
