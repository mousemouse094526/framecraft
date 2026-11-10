"""The การ์ตูนเล่า tab's files on disk: `series.json` of each Series, `ep.json` of each of
its EPs, and the background sound library's `sounds.json` (toon spec › ข้อมูล).

Every read-change-write of a tab file runs under `lock`, the tab's one RLock. Lock order:
a job slot's lock, then `gpu.slot.draft_lock` (a write of a `voice_id`, D25), then `lock`,
then the GPU slot's own. Files are written through `{name}.{uuid}.tmp` and renamed.
"""

import json
import logging
import os
import re
import secrets
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import files
from backend.paths import EpAddress, ProjectPaths

log = logging.getLogger(__name__)

VERSION = 1
SERIES_ID = re.compile(r"s_[0-9a-f]{8}")
SOUND_ID = re.compile(r"m_[0-9a-f]{8}")
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


class StoredSound(BaseModel):
    id: str
    name: str
    duration_s: float = 0
    source: Literal["file", "link"] = "file"


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


def read_sounds(project: ProjectPaths) -> list[StoredSound]:
    """The background sound library; empty until a sound is imported. A file changed into one
    that won't read while the app runs is recovered (and rewritten) by `reconcile_sounds`
    from the m4a files, their lengths `0` until the next start reads them (D70). An entry
    whose m4a is gone stays until that start: a read never scans the folder. Holds `lock`."""
    with lock:
        listed = _listed_sounds(project.toon_sounds_file)
        sounds = _good_sounds(listed or [])
        if listed is None or len(sounds) < len(listed):
            return reconcile_sounds(project, lambda m4a: 0.0)
        return sounds


def reconcile_sounds(project: ProjectPaths, length: Callable[[Path], float]) -> list[StoredSound]:
    """`sounds.json` made to match the m4a files beside it, which are the sounds themselves
    (D70): a file that won't read at all is kept aside as `sounds.json.bad-*` and the library
    starts with none; an entry that won't read, repeats an id or has no m4a is dropped; an m4a
    with no entry comes in named by its id, `length` giving its seconds, as it does for an entry
    of length `0` (recovered while the app ran). Written only when something changed; a write
    that fails is logged, and the library is still returned."""
    with lock:
        path, folder = project.toon_sounds_file, project.toon_sounds_dir
        listed = _listed_sounds(path)
        kept_aside = listed is None
        if kept_aside:
            aside = path.with_name(f"{path.name}.bad-{datetime.now(UTC):%Y%m%d-%H%M%S}-{secrets.token_hex(2)}")
            try:
                os.replace(path, aside)
                log.warning("kept the unreadable %s aside as %s", path.name, aside.name)
            except OSError:  # it stays where it is; `write_sounds` won't write over it
                log.exception("could not keep the unreadable %s aside", path)
            listed = []
        on_disk = {sound_id for sound_id in m4a_ids(project) if SOUND_ID.fullmatch(sound_id)}
        sounds = [sound for sound in _good_sounds(listed) if sound.id in on_disk]
        timed = 0
        for sound in sounds:
            if sound.duration_s == 0 and (seconds := round(length(folder / f"{sound.id}.m4a"), 1)):
                sound.duration_s, timed = seconds, timed + 1
        known = {sound.id for sound in sounds}
        added = [
            StoredSound(id=sound_id, name=sound_id, duration_s=round(length(folder / f"{sound_id}.m4a"), 1))
            for sound_id in sorted(on_disk - known)
        ]
        dropped = len(listed) - len(sounds)
        if kept_aside or dropped or added or timed:
            log.warning("the sound library: dropped %d entries, added %d sounds from their m4a, timed %d", dropped, len(added), timed)
            try:
                write_sounds(project, [*sounds, *added])
            except OSError:
                log.exception("could not write the recovered %s", path)
        return [*sounds, *added]


def m4a_ids(project: ProjectPaths) -> set[str]:
    """The name, without `.m4a`, of every m4a in the sound library's folder, listed or not."""
    folder = project.toon_sounds_dir
    return {m4a.stem for m4a in folder.glob("*.m4a")} if folder.is_dir() else set()


def _listed_sounds(path: Path) -> list | None:
    """The entries of `sounds.json`, unchecked: `[]` with no file, None when it won't read
    at all (not JSON, no list of `sounds`, another `version`)."""
    if not path.is_file():
        return []
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log.warning("could not read %s: %s", path, str(error).splitlines()[0])
        return None
    if not isinstance(found, dict) or found.get("version") != VERSION or not isinstance(found.get("sounds"), list):
        log.warning("could not read %s: not a sound library of version %d", path, VERSION)
        return None
    return found["sounds"]


def _good_sounds(listed: list) -> list[StoredSound]:
    """The entries that are sounds, with an id of `SOUND_ID` not taken by one before them."""
    sounds: list[StoredSound] = []
    for entry in listed:
        try:
            sound = StoredSound.model_validate(entry)
        except ValidationError as error:
            log.warning("dropped a sound library entry: %s", str(error).splitlines()[0])
            continue
        if not SOUND_ID.fullmatch(sound.id) or any(sound.id == before.id for before in sounds):
            log.warning("dropped the sound library entry %r: a malformed or repeated id", sound.id)
            continue
        sounds.append(sound)
    return sounds


def write_sounds(project: ProjectPaths, sounds: list[StoredSound]) -> None:
    """Raises `OSError` instead of writing over a `sounds.json` that won't read: one that
    `reconcile_sounds` could not keep aside holds the only copy of the names (D70)."""
    if _listed_sounds(project.toon_sounds_file) is None:
        raise OSError(f"{project.toon_sounds_file} won't read and was not kept aside: not written over")
    project.toon_sounds_dir.mkdir(parents=True, exist_ok=True)
    body = {"version": VERSION, "sounds": [sound.model_dump() for sound in sounds]}
    files.write_atomic(project.toon_sounds_file, json.dumps(body, ensure_ascii=False, indent=2), unique=True)
