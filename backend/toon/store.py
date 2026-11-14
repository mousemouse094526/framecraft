"""The การ์ตูนเล่า tab's files on disk: `series.json` of each Series and `ep.json` of each of
its EPs (toon spec › ข้อมูล). The sound library a segment plays from is `backend.sounds`'.

Every read-change-write of a tab file runs under `lock`, the tab's one RLock. Lock order:
a job slot's lock, then `gpu.slot.draft_lock` (a write of a `voice_id`, D25), then `lock`,
then `sounds.lock` (a write of a `sound_id`, sound-library D7), then the GPU slot's own.
Files are written through `{name}.{uuid}.tmp` and renamed.
"""

import json
import logging
import re
import threading
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import files
from backend.paths import EpAddress, ProjectPaths

log = logging.getLogger(__name__)

VERSION = 1
SERIES_ID = re.compile(r"s_[0-9a-f]{8}")
CHARACTER_ID = re.compile(r"c_[0-9a-f]{8}")
BACKGROUND_ID = re.compile(r"b_[0-9a-f]{8}")
EP_ID = re.compile(r"e_[0-9a-f]{8}")

lock = threading.RLock()

Layout = Literal["frame", "full"]
Genre = Literal["horror", "comedy"]
Stage = Literal["plot", "cards"]  # `plot`: not confirmed yet, no segments
Motion = Literal["still", "zoom_in", "zoom_out", "pan_left", "pan_right"]  # D4


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


class PlotItem(BaseModel):
    """A character or background a plot uses: one of the Series' (`id`), or one the plot
    proposes (`new`, with its `name`, `tag` and `description`, D13)."""

    id: str | None = None
    new: bool = False
    name: str = ""
    tag: str = ""
    description: str = ""


class Plot(BaseModel):
    characters: list[PlotItem] = []
    backgrounds: list[PlotItem] = []


class Sound(BaseModel):
    sound_id: str
    volume: int = 30


class Audio(BaseModel):
    tts_text: str
    voice_id: str
    duration_s: float


class CardImage(BaseModel):
    file: str
    refs: dict[str, int]  # the `ref_rev` of each character and background it was drawn with (D32)
    prompt: str = ""  # for a bug report; the page never gets it (D36)


class Card(BaseModel):
    id: str
    text: str = ""  # empty: a silent card (D14)
    character_ids: list[str] = []
    description: str = ""
    motion: Motion = "still"
    flicker: bool = False
    hold_s: float = 0
    edited: bool = False  # spoil-maker D74
    audio: Audio | None = None
    image: CardImage | None = None
    previous_image: CardImage | None = None


class Segment(BaseModel):
    id: str
    background_id: str
    sound: Sound | None = None
    cards: list[Card]


class Act(BaseModel):
    id: str
    name: str
    summary: str = ""
    cards_from: str | None = None  # `summary` when the act was last split; None: never (D15)
    segments: list[Segment] = []


class Ep(BaseModel):
    version: Literal[1] = VERSION
    id: str
    n: int
    idea: str
    title: str = ""
    voice_id: str
    stage: Stage = "plot"
    plot: Plot = Plot()
    acts: list[Act]


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


def read_ep(ep_address: EpAddress) -> Ep | None:
    """The EP, or None when it is gone, its id is malformed, or its file is unreadable or of
    another `version` (logged)."""
    if not EP_ID.fullmatch(ep_address.ep_id):
        return None
    path = ep_address.dir / "ep.json"
    if not path.is_file():
        return None
    try:
        return Ep.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, ValidationError) as error:
        log.warning("skipped %s: %s", path, str(error).splitlines()[0])
        return None


def list_eps(project: ProjectPaths, series_id: str) -> list[Ep]:
    """Every readable EP of the Series, by number."""
    folder = project.series_dir(series_id) / "eps"
    found = [read_ep(EpAddress(project, series_id, path.name)) for path in folder.iterdir()] if folder.is_dir() else []
    return sorted((ep for ep in found if ep is not None), key=lambda ep: ep.n)


def ep_ids(project: ProjectPaths) -> set[str]:
    """The folder name of every EP of every Series, readable or not: an EP id is unique in
    the whole tab, since `locate_ep` looks it up without its Series."""
    if not project.toon_series_dir.is_dir():
        return set()
    folders = [folder / "eps" for folder in project.toon_series_dir.iterdir()]
    return {path.name for folder in folders if folder.is_dir() for path in folder.iterdir()}


def locate_ep(project: ProjectPaths, ep_id: str) -> EpAddress | None:
    """Which readable Series holds the EP's `ep.json`; whether the file reads is `read_ep`'s."""
    if not EP_ID.fullmatch(ep_id):
        return None
    for series in list_series(project):
        ep_address = EpAddress(project, series.id, ep_id)
        if (ep_address.dir / "ep.json").is_file():
            return ep_address
    return None


def write_ep(ep_address: EpAddress, ep: Ep) -> None:
    """`ep` is the EP at `ep_address`, new or changed."""
    folder = ep_address.dir
    folder.mkdir(parents=True, exist_ok=True)
    files.write_atomic(folder / "ep.json", ep.model_dump_json(indent=2), unique=True)
