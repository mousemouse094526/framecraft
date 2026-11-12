"""The rule every Temp clip's mp4 meets, wherever it came from (ADR 0027): the picture is
h264 `yuv420p` with its short side ≤ 1080, every sound track is aac (or there is none),
and its length can be read (spoil spec › File import step 4, D54, D55).

A download checks its merged file with it, and a File import checks the file it got.
It reads `ffmpeg -i` (no ffprobe, ADR 0005; docs/library-notes/ffmpeg.md).
"""

import re
from pathlib import Path
from typing import Literal, NamedTuple

from backend import ffmpeg

MAX_SHORT_SIDE = 1080
UNREADABLE = "อ่านไฟล์ไม่ได้"
NOT_MP4_CONTAINER = "ไฟล์ไม่ใช่ mp4"

# "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'a.mp4':" — ffmpeg names an mp4 by this family.
CONTAINER = re.compile(r"^Input #0, (.+), from ", re.MULTILINE)
STREAM = re.compile(r"^\s*Stream #\S+: (Video|Audio|Subtitle|Data|Attachment): (.*)$")
# "h264 (High) (avc1 / 0x31637661), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], …"
PICTURE = re.compile(r"^(\w+)[^,]*, (\w+)(?:\([^)]*\))?, (\d+)x(\d+)")
# ffmpeg 7 prints the turn as side data; older muxers left a `rotate` tag.
ROTATION = re.compile(r"displaymatrix: rotation of (-?\d+(?:\.\d+)?) degrees|^\s*rotate\s*:\s*(-?\d+)")


class Mp4Info(NamedTuple):
    duration_s: float
    # As the file is shown: a quarter turn swaps the stored width and height.
    width: int
    height: int

    @property
    def orientation(self) -> Literal["portrait", "landscape"]:
        return "portrait" if self.height > self.width else "landscape"


class NotPlayable(Exception):
    """The file breaks the rule; `reason` says which part, in the words the page shows."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class _Stream(NamedTuple):
    kind: str
    description: str
    details: list[str]


def check(path: Path) -> Mp4Info:
    """Runs `ffmpeg -i` on the file and reads it. Raises `NotPlayable`."""
    return read_streams(ffmpeg.input_info(path))


def read_streams(stderr: str) -> Mp4Info:
    """The file's length, shown size and sound from `ffmpeg -i`'s output. Raises `NotPlayable`."""
    container = CONTAINER.search(stderr)
    if container and "mp4" not in container.group(1).split(","):
        raise NotPlayable(NOT_MP4_CONTAINER)
    duration = ffmpeg.DURATION.search(stderr)
    streams = _streams(stderr)
    # A cover image is a video stream too; it is not the picture (D55).
    picture = next((s for s in streams if s.kind == "Video" and "(attached pic)" not in s.description), None)
    if duration is None or picture is None:
        raise NotPlayable(UNREADABLE)
    found = PICTURE.match(picture.description)
    if found is None:
        raise NotPlayable(UNREADABLE)
    codec, pixels, width, height = found.group(1), found.group(2), int(found.group(3)), int(found.group(4))
    if codec != "h264":
        raise NotPlayable(f"ภาพเป็น {codec}")
    if pixels != "yuv420p":
        raise NotPlayable(f"ภาพเป็น h264 แบบ {pixels}")
    if _quarter_turned(picture):
        width, height = height, width
    if min(width, height) > MAX_SHORT_SIDE:
        raise NotPlayable(f"ภาพ {width}×{height} ด้านสั้นเกิน {MAX_SHORT_SIDE}")
    for sound in (s for s in streams if s.kind == "Audio"):  # no sound at all is fine
        sound_codec = sound.description.split(maxsplit=1)[0].rstrip(",")
        if sound_codec != "aac":
            raise NotPlayable(f"เสียงเป็น {sound_codec}")
    return Mp4Info(duration_s=ffmpeg.seconds_of(duration), width=width, height=height)


def _streams(stderr: str) -> list[_Stream]:
    """Each `Stream #…` line with the indented lines under it (its metadata and side data)."""
    streams: list[_Stream] = []
    for line in stderr.splitlines():
        found = STREAM.match(line)
        if found:
            streams.append(_Stream(found.group(1), found.group(2), []))
        elif streams and line.startswith("    "):
            streams[-1].details.append(line)
        elif streams:
            break  # "At least one output file…": the stream list is over
    return streams


def _quarter_turned(stream: _Stream) -> bool:
    for line in stream.details:
        found = ROTATION.search(line)
        if found:
            angle = float(found.group(1) or found.group(2))
            return round(abs(angle)) % 180 == 90
    return False
