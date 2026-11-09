"""The การ์ตูนเล่า tab's files on disk: `series.json` of each Series (toon spec › ข้อมูล).

Every read-change-write of a tab file runs under `lock`, the tab's one RLock. Lock order:
a job slot's lock, then `gpu.slot.draft_lock` (a write of a `voice_id`, D25), then `lock`,
then the GPU slot's own. Files are written through `{name}.{uuid}.tmp` and renamed.
"""

import json
import logging
import re
import secrets
import threading
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import files
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

VERSION = 1
SERIES_ID = re.compile(r"s_[0-9a-f]{8}")
CHARACTER_ID = re.compile(r"c_[0-9a-f]{8}")
BACKGROUND_ID = re.compile(r"b_[0-9a-f]{8}")

lock = threading.RLock()

Layout = Literal["frame", "full"]
Genre = Literal["horror", "comedy"]


class Character(BaseModel):
    id: str
    name: str
    tag: str = ""  # the short word after the name on a name tag (D23)
    description: str = ""
    ref_rev: int = 0  # 0: no reference image yet (D13)


class Background(BaseModel):
    id: str
    name: str
    description: str = ""
    ref_rev: int = 0


class Series(BaseModel):
    version: Literal[1] = VERSION
    id: str
    name: str
    channel_name: str = ""
    layout: Layout
    genre: Genre
    style: str
    tone: str
    acts: list[str]
    voice_id: str
    name_tags: bool = True
    max_ep: int = 0  # the highest EP number the Series ever had (D40)
    characters: list[Character] = []
    backgrounds: list[Background] = []


def new_id(prefix: str, taken: set[str] = frozenset()) -> str:
    """`{prefix}_` and 8 hex digits, not in `taken`."""
    while (found := f"{prefix}_{secrets.token_hex(4)}") in taken:
        pass
    return found


def read_series(project: ProjectPaths, series_id: str) -> Series | None:
    """The Series, or None when it is gone, its id is malformed, or its file is unreadable
    or of another `version` (logged)."""
    if not SERIES_ID.fullmatch(series_id):
        return None
    path = project.series_dir(series_id) / "series.json"
    if not path.is_file():
        return None
    try:
        return Series.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, ValidationError) as error:
        log.warning("skipped %s: %s", path, str(error).splitlines()[0])
        return None


def list_series(project: ProjectPaths) -> list[Series]:
    """Every readable Series, by name."""
    found = []
    if project.toon_series_dir.is_dir():
        for folder in project.toon_series_dir.iterdir():
            series = read_series(project, folder.name) if folder.is_dir() else None
            if series is not None:
                found.append(series)
    return sorted(found, key=lambda series: (series.name, series.id))


def write_series(project: ProjectPaths, series: Series) -> None:
    folder = project.series_dir(series.id)
    folder.mkdir(parents=True, exist_ok=True)
    files.write_atomic(folder / "series.json", series.model_dump_json(indent=2), unique=True)
