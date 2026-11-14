"""The sound library of the whole app (sound-library spec, ADR 0037, ADR 0039): `media/sounds/`
holds `sounds.json` and one `{sound_id}.m4a` per sound; the การ์ตูนเล่า and สปอย tabs keep a
`sound_id` and read the sound through here. This module imports no feature.

A sound comes in through a Sound import, one at a time in its own slot (no GPU): a file of
this machine as a raw body in one request (ADR 0028), or a link loaded by a job that reads its
info, checks its length, then downloads its best audio into `.partial/` (spoil's Download
job, ADR 0029). Either way ffmpeg converts it to aac in m4a with no picture, so a render reads
one format (toon D39); those steps are `backend.audio_imports`, shared with the แกะเพลง tab's songs
(ADR 0048). A restart half-way leaves only `.partial/` files, which start-up removes.
Start-up also makes `sounds.json` match the m4a files, which are the sounds themselves: a
library file that won't read never takes the sounds with it (toon D70, D71).

Every read-change-write of the library runs under `lock`. A feature that keeps a `sound_id`
registers a `SoundUser` (ADR 0038): a delete holds each user's lock in `LOCK_ORDER`, then
`lock`, and asks each user's `playing`, so no sound in use goes, and lock order is a feature's
own lock before `lock` everywhere (D7, D11). The link import loads through the คลิป tab's
yt-dlp adapter, which keeps no sound (ADR 0037).
"""

import json
import logging
import os
import re
import secrets
import shutil
import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractContextManager, ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, NamedTuple, get_args

import anyio
from pydantic import BaseModel, ValidationError
from starlette.requests import ClientDisconnect

from backend import audio_imports, checks, disk, ffmpeg, files, gate_rows, paths, uploads
from backend.audio_imports import ImportSlot, Limits, State
from backend.ids import new_id
from backend.errors import ApiError, JobFailed, Row, checked_text, invalid_request, require_rows
from backend.ffmpeg import FfmpegFailed
from backend.jobs import Cancelled
from backend.paths import ProjectPaths
from backend.spoil import links
from backend.spoil.adapter import DownloadCancelled, error_code

log = logging.getLogger(__name__)

VERSION = 1
SOUND_ID = re.compile(r"m_[0-9a-f]{8}")

lock = threading.RLock()

ErrorCode = Literal["login_required", "download_error", "disk_full", "too_long", "unsupported_file", "internal"]
Source = Literal["file", "link"]
Tab = Literal["toon", "spoil"]  # in the order `in_use` lists their users (D7)
# The order a delete takes the users' locks: `gpu.slot.draft_lock` before `toon.store.lock` (D7).
LOCK_ORDER: tuple[Tab, ...] = ("spoil", "toon")

# Every sound's format, and the การ์ตูนเล่า mix's (toon D39).
AUDIO_RATE, AUDIO_BITRATE = audio_imports.M4A_RATE, audio_imports.M4A_BITRATE
UPLOAD_MAX_BYTES = 200 * 1024**2  # toon spec › คลังเสียงพื้น
MAX_SECONDS = 20 * 60
NAME_MAX = audio_imports.NAME_MAX
PROBE_SECONDS = 10  # how long start-up reads the length of an m4a the library lacks (toon D70)

# Where a link's audio lands: the library's `.partial/`, no thumbnail, no mp4 merge (D11).
LINK_OPTIONS = audio_imports.link_options(lambda project: project.sounds_partial_dir)

BUSY = "กำลังเอาเสียงอื่นเข้าคลังอยู่"
IN_USE = "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้"
UNREADABLE = audio_imports.UNREADABLE
TOO_LONG = f"เสียงยาวเกิน {MAX_SECONDS // 60} นาที"
LIMITS = Limits(max_seconds=MAX_SECONDS, too_long=TOO_LONG)
ERROR_MESSAGES: dict[ErrorCode, str] = {
    "login_required": "เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดเสียงเองแล้วเอาไฟล์เข้า",
    "download_error": "โหลดเสียงจากลิงก์นี้ไม่สำเร็จ",
    "too_long": TOO_LONG,
    "unsupported_file": UNREADABLE,
}


class StoredSound(BaseModel):
    id: str
    name: str
    duration_s: float = 0
    source: Source = "file"


class SoundView(BaseModel):
    id: str
    name: str
    duration_s: float
    source: Source


class SoundUser(NamedTuple):
    """A feature that keeps a `sound_id` (ADR 0038): its tab, `lock`, which gives the lock it
    writes a `sound_id` under (asked at each delete: spoil's belongs to `gpu.slot`, which a test
    replaces), and `playing`, a label of each of its things that play the sound. `playing` is called
    with `lock` and every user's lock held, takes no other lock and never calls this module."""

    tab: Tab
    lock: Callable[[], AbstractContextManager]
    playing: Callable[[ProjectPaths, str], list[str]]


sound_users: list[SoundUser] = []


class SoundImportError(BaseModel):
    code: ErrorCode
    message: str


class SoundImport(BaseModel):
    """A link's Sound import; a file's is one request and never shows here."""

    url: str
    state: State
    title: str | None = None
    percent: int | None = None
    error: SoundImportError | None = None
    cancel_requested: bool = False
    sound_id: str | None = None  # the new sound, once `done`
    started_at: str


class Legacy(BaseModel):
    """`left_behind`: the old folder while it still holds a sound start-up could not move (D10)."""

    left_behind: str | None


class SoundImports(ImportSlot[SoundImport]):
    """The library's import slot: the latest link import, and whether a file is being received,
    one of the two at a time (toon spec › คลังเสียงพื้น)."""

    busy = BUSY

    # --- a file ---

    def check(self, body: dict) -> uploads.UploadCheck:
        """Every check of the file but its body's, before the page sends it (ADR 0028)."""
        project = paths.project()
        size = _file_checks(project, body.get("name"), body.get("size"))
        with self._lock:
            self._require_free()
        return uploads.UploadCheck(size=size)

    async def receive(
        self, name: str | None, size: str | None, body: AsyncIterator[bytes], page_gone: Callable[[], Awaitable[bool]]
    ) -> SoundView:
        """Checks again, writes `body` to `.partial/`, converts it into the library. `page_gone`
        says whether the page went away: ffmpeg stops then and the sound never comes in.
        Raises `ApiError`, or `ClientDisconnect` once its file is gone."""
        project, expected = paths.project(), uploads.whole_number(size)
        await anyio.to_thread.run_sync(_file_checks, project, name, expected)
        with self.receiving():
            sound_id = _new_sound_id(project)
            partial = project.sounds_partial_dir / f"{sound_id}.upload"
            try:
                await uploads.receive(body, partial, expected, self._stall_seconds)
                cancel = threading.Event()
                return await audio_imports.run_unless_gone(
                    page_gone,
                    cancel,
                    lambda: self._take_in(
                        project, sound_id, partial, _file_title(name), "file", cancel, audio_imports.still_wanted(page_gone, cancel)
                    ),
                )
            except (Cancelled, ClientDisconnect):  # `Cancelled`: the page left during ffmpeg
                log.info("the sound import %s stopped: the page went away", sound_id)
                raise ClientDisconnect() from None
            except JobFailed as refused:
                raise ApiError(400, refused.code, refused.message) from None
            finally:
                with anyio.CancelScope(shield=True):
                    await anyio.to_thread.run_sync(lambda: partial.unlink(missing_ok=True))

    # --- a link ---

    def start(self, body: dict) -> SoundImport:
        """The gate, the link (spoil's rules, ADR 0029), `busy`; then the job's thread."""
        require_rows(link_rows())
        url = body.get("url")
        link = links.parse(url) if isinstance(url, str) else None
        if link is None:
            raise ApiError(400, "invalid_url", "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป")
        project = paths.project()
        with self._lock:
            self._require_free()
            self._job = SoundImport(url=link.url, state="checking", started_at=checks.now_iso())
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, link.url), daemon=True).start()
        return job

    def cancel(self) -> SoundImport:
        with self._lock:
            if not self._taken():
                raise ApiError(404, "not_found", "ไม่มีการเอาเสียงเข้าที่ยังไม่จบ")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def _run(self, project: ProjectPaths, url: str) -> None:
        sound_id = _new_sound_id(project)
        ending: dict = {"state": "failed"}
        try:
            sound = self._download(project, url, sound_id)
            ending = {"state": "done", "sound_id": sound.id, "percent": 100}
        except (DownloadCancelled, Cancelled):
            ending = {"state": "cancelled"}
        except JobFailed as failure:
            # The library's error words are fewer than the shared steps' (a playlist is a download error here).
            code = failure.code if failure.code in ERROR_MESSAGES else "download_error"
            ending["error"] = SoundImportError(code=code, message=failure.message)
        except Exception as error:
            code = "login_required" if error_code(error) == "login_required" else "download_error"
            log.exception("sound download of %s failed", url)
            ending["error"] = SoundImportError(code=code, message=ERROR_MESSAGES[code])
        finally:
            audio_imports.remove_leftovers(project.sounds_partial_dir, sound_id)
            self.update(**ending)

    def _download(self, project: ProjectPaths, url: str, sound_id: str) -> SoundView:
        """Spoil's Download job steps: the info, its length before loading, the load with %."""
        info = audio_imports.fetch_info(url, LINK_OPTIONS, LIMITS, self._cancel)
        try:
            disk.require_free(project.root, audio_imports.estimate_bytes(info))
        except ApiError as full:
            raise JobFailed("disk_full", full.message) from None
        title = audio_imports.first_name(info.get("title"), fallback=sound_id)
        self.update(state="downloading", title=title, percent=0)
        loaded = audio_imports.download(project, info, sound_id, LINK_OPTIONS, lambda percent: self.update(percent=percent), self._cancel)
        self.update(state="converting", percent=None)
        return self._take_in(project, sound_id, loaded, title, "link", self._cancel)

    # --- both ---

    def _take_in(
        self,
        project: ProjectPaths,
        sound_id: str,
        source: Path,
        name: str,
        origin: Source,
        cancel: threading.Event,
        still_wanted: Callable[[], bool] | None = None,
    ) -> SoundView:
        """In a thread: `audio_imports.take_in` into the library through its `.partial/` (D11), the
        entry written under `lock`. Raises `JobFailed`, or `Cancelled`."""
        target = path(project, sound_id)
        partial = project.sounds_partial_dir / f"{target.name}.partial"

        def place(seconds: float) -> SoundView:
            sound = StoredSound(id=sound_id, name=name, duration_s=round(seconds, 1), source=origin)
            # Read before the m4a is in place, all under the lock: a library recovered on the read
            # never lists the new sound already, so it is in it once (toon D70).
            with lock:
                sounds = [listed for listed in read_sounds(project) if listed.id != sound_id]
                os.replace(partial, target)
                write_sounds(project, [*sounds, sound])
            log.info("imported sound %s (%s, %.1f s)", sound_id, origin, seconds)
            return _view(sound)

        return audio_imports.take_in(source, target, LIMITS, self._convert, cancel, place, still_wanted, partial=partial)


# --- the library ---


def list_all(project: ProjectPaths) -> list[SoundView]:
    with lock:
        return [_view(sound) for sound in read_sounds(project)]


def exists(project: ProjectPaths, sound_id: object) -> bool:
    """Whether the library lists the sound. A feature asks with its own lock held, so `lock`
    comes after it: the order a delete takes them in (ADR 0038)."""
    return name_of(project, sound_id) is not None


def name_of(project: ProjectPaths, sound_id: object) -> str | None:
    """The sound's name, or None when the library doesn't list it."""
    with lock:
        return next((sound.name for sound in read_sounds(project) if sound.id == sound_id), None)


def path(project: ProjectPaths, sound_id: str) -> Path:
    """Where the sound's m4a is, for a render to copy; whether it is there is the caller's to check."""
    return project.sounds_dir / f"{sound_id}.m4a"


def rename(project: ProjectPaths, sound_id: str, body: dict) -> SoundView:
    """Names may repeat (toon spec › คลังเสียงพื้น)."""
    name = checked_text(body.get("name"), 1, NAME_MAX)
    with lock:
        sounds = read_sounds(project)
        sound = _find(sounds, sound_id)
        sound.name = name
        write_sounds(project, sounds)
        return _view(sound)


def delete(project: ProjectPaths, sound_id: str) -> None:
    """A sound any user's check names can't go: `in_use` with each of them, toon's before
    spoil's (D7). Its m4a goes before its entry: a crash in between leaves an entry the next
    start drops (toon D70)."""
    with ExitStack() as held:
        for user in sorted(sound_users, key=lambda user: LOCK_ORDER.index(user.tab)):
            held.enter_context(user.lock())
        held.enter_context(lock)
        sounds = read_sounds(project)
        sound = _find(sounds, sound_id)
        users = [
            {"tab": user.tab, "label": label}
            for user in sorted(sound_users, key=lambda user: get_args(Tab).index(user.tab))
            for label in user.playing(project, sound_id)
        ]
        if users:
            raise ApiError(409, "in_use", IN_USE, users=users)
        path(project, sound_id).unlink(missing_ok=True)
        sounds.remove(sound)
        write_sounds(project, sounds)
    log.info("deleted sound %s", sound_id)


def sound_file(project: ProjectPaths, sound_id: str) -> Path:
    with lock:
        _find(read_sounds(project), sound_id)
        found = path(project, sound_id)
        if not found.is_file():
            raise ApiError(404, "not_found", "ไม่พบไฟล์ของเสียงนี้")
        return found


def legacy(project: ProjectPaths) -> Legacy:
    """An m4a not named by a sound id was never a sound (`reconcile_sounds` skips it): it stays
    in the old folder but is not left behind (D14)."""
    folder = project.legacy_sounds_dir
    left = folder.is_dir() and any(SOUND_ID.fullmatch(m4a.stem) for m4a in folder.glob("*.m4a"))
    return Legacy(left_behind=_shown(project, folder) if left else None)


def link_rows() -> dict[str, Row]:
    """What a link's Sound import needs (toon spec › Status check); a file's needs `ffmpeg` alone."""
    return gate_rows.FFMPEG | gate_rows.LINK_TOOLS


# --- start-up ---


def move_legacy(project: ProjectPaths) -> None:
    """The library of an app before sound-library, `media/toon/sounds/`, into `media/sounds/`
    (spec › ข้อมูล › ย้ายจากที่เดิม, D10): the whole folder when the new one has no sound yet,
    else each m4a of an id the new one lacks, with its entry, one at a time. An `OSError`
    stops it with what moved in its new place and the rest in the old; the next start goes on.
    Runs before `clean_on_start`, which empties a `.partial/` that came along."""
    old, new = project.legacy_sounds_dir, project.sounds_dir
    if not old.is_dir():
        return
    try:
        if not (new / "sounds.json").is_file() and not any(new.glob("*.m4a")):
            if new.exists():
                shutil.rmtree(new)
            os.replace(old, new)
            log.info("moved sound library to media/sounds")
            return
        _merge_legacy(project)
    except OSError:
        log.exception("could not move the sound library from %s: the next start goes on", _shown(project, old))


def _merge_legacy(project: ProjectPaths) -> None:
    """Every m4a of the old folder whose id has no m4a in the new library, one at a time, then
    `sounds.json` with it: its new entry when the new library lists it already, else its old
    one (none: named by its id, timed by `clean_on_start`); the new one's copy of an id in both
    stays. The old folder goes once each of its m4a has a copy in the new one; any other m4a
    keeps it there, never deleted (D14)."""
    old = project.legacy_sounds_dir
    entries = {sound.id: sound for sound in _good_sounds(_listed_sounds(old / "sounds.json") or [])}
    moved = 0
    with lock:
        sounds = read_sounds(project)
        for m4a in sorted(old.glob("*.m4a")):
            sound_id = m4a.stem
            if not SOUND_ID.fullmatch(sound_id) or sound_id in m4a_ids(project):
                continue
            os.replace(m4a, path(project, sound_id))
            if all(sound.id != sound_id for sound in sounds):
                sounds.append(entries.get(sound_id) or StoredSound(id=sound_id, name=sound_id))
            write_sounds(project, sounds)
            moved += 1
        left = sorted(m4a.name for m4a in old.glob("*.m4a") if m4a.stem not in m4a_ids(project))
    if moved:
        log.warning("merged %d sounds of %s into %s", moved, _shown(project, old), _shown(project, project.sounds_dir))
    if left:
        log.warning("left in %s: %s", _shown(project, old), ", ".join(left))
    else:
        shutil.rmtree(old)


def clean_on_start(project: ProjectPaths) -> None:
    """A Sound import cut short leaves files in `.partial/`, emptied whole (D11), and an app
    before sound-library left a `.m4a.partial` beside the m4a files. Then the library is made
    to match its m4a files (`reconcile_sounds`, toon D70)."""
    shutil.rmtree(project.sounds_partial_dir, ignore_errors=True)
    if project.sounds_dir.is_dir():
        for leftover in project.sounds_dir.glob("*.partial"):
            leftover.unlink(missing_ok=True)
    reconcile_sounds(project, _length)


# --- `sounds.json` ---


def read_sounds(project: ProjectPaths) -> list[StoredSound]:
    """The library; empty until a sound is imported. A file changed into one that won't read
    while the app runs is recovered (and rewritten) by `reconcile_sounds` from the m4a files,
    their lengths `0` until the next start reads them (toon D70). A good file is returned as
    it is, so an entry whose m4a is gone stays until that start. Holds `lock`."""
    with lock:
        listed = _listed_sounds(project.sounds_file)
        sounds = _good_sounds(listed or [])
        if listed is None or len(sounds) < len(listed):
            return reconcile_sounds(project, lambda m4a: 0.0)
        return sounds


def reconcile_sounds(project: ProjectPaths, length: Callable[[Path], float]) -> list[StoredSound]:
    """`sounds.json` made to match the m4a files beside it, which are the sounds themselves
    (toon D70): a file that won't read at all is kept aside as `sounds.json.bad-*` and the
    library starts with none; an entry that won't read, repeats an id or has no m4a is dropped;
    an m4a with no entry comes in named by its id, `length` giving its seconds, as it does for
    an entry of length `0` (recovered while the app ran). Written only when something changed;
    a write that fails is logged, and the library is still returned."""
    with lock:
        file = project.sounds_file
        listed = _listed_sounds(file)
        kept_aside = listed is None
        if kept_aside:
            aside = file.with_name(f"{file.name}.bad-{datetime.now(UTC):%Y%m%d-%H%M%S}-{secrets.token_hex(2)}")
            try:
                os.replace(file, aside)
                log.warning("kept the unreadable %s aside as %s", file.name, aside.name)
            except OSError:  # it stays where it is; `write_sounds` won't write over it
                log.exception("could not keep the unreadable %s aside", file)
            listed = []
        on_disk = {sound_id for sound_id in m4a_ids(project) if SOUND_ID.fullmatch(sound_id)}
        sounds = [sound for sound in _good_sounds(listed) if sound.id in on_disk]
        timed = 0
        for sound in sounds:
            if sound.duration_s == 0 and (seconds := round(length(path(project, sound.id)), 1)):
                sound.duration_s, timed = seconds, timed + 1
        known = {sound.id for sound in sounds}
        added = [
            StoredSound(id=sound_id, name=sound_id, duration_s=round(length(path(project, sound_id)), 1))
            for sound_id in sorted(on_disk - known)
        ]
        dropped = len(listed) - len(sounds)
        if kept_aside or dropped or added or timed:
            log.warning("the sound library: dropped %d entries, added %d sounds from their m4a, timed %d", dropped, len(added), timed)
            try:
                write_sounds(project, [*sounds, *added])
            except OSError:
                log.exception("could not write the recovered %s", file)
        return [*sounds, *added]


def m4a_ids(project: ProjectPaths) -> set[str]:
    """The name, without `.m4a`, of every m4a in the library's folder, listed or not."""
    folder = project.sounds_dir
    return {m4a.stem for m4a in folder.glob("*.m4a")} if folder.is_dir() else set()


def write_sounds(project: ProjectPaths, sounds: list[StoredSound]) -> None:
    """Raises `OSError` instead of writing over a `sounds.json` that won't read: one that
    `reconcile_sounds` could not keep aside holds the only copy of the names (toon D70)."""
    if _listed_sounds(project.sounds_file) is None:
        raise OSError(f"{project.sounds_file} won't read and was not kept aside: not written over")
    project.sounds_dir.mkdir(parents=True, exist_ok=True)
    body = {"version": VERSION, "sounds": [sound.model_dump() for sound in sounds]}
    files.write_atomic(project.sounds_file, json.dumps(body, ensure_ascii=False, indent=2), unique=True)


def _listed_sounds(file: Path) -> list | None:
    """The entries of a `sounds.json`, unchecked: `[]` with no file, None when it won't read
    at all (not JSON, no list of `sounds`, another `version`)."""
    if not file.is_file():
        return []
    try:
        found = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log.warning("could not read %s: %s", file, str(error).splitlines()[0])
        return None
    if not isinstance(found, dict) or found.get("version") != VERSION or not isinstance(found.get("sounds"), list):
        log.warning("could not read %s: not a sound library of version %d", file, VERSION)
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


# --- helpers ---


def _file_checks(project: ProjectPaths, name: object, size: object) -> int:
    require_rows(gate_rows.FFMPEG)
    if not isinstance(name, str) or not _file_title(name):
        raise invalid_request()
    size = uploads.require_size(size, UPLOAD_MAX_BYTES, f"ไฟล์เสียงใหญ่เกิน {UPLOAD_MAX_BYTES // 1024**2} MB")
    disk.require_free(project.root, size)
    return size


def _file_title(name: str | None) -> str:
    """A file's sound's first name: the file's without its extension, cut to 60; empty for no name."""
    return audio_imports.file_title(name)


def _length(m4a: Path) -> float:
    """An m4a's seconds as ffmpeg reads them in `PROBE_SECONDS`; `0` when it can't."""
    try:
        return ffmpeg.probe(m4a, timeout=PROBE_SECONDS).duration_s
    except FfmpegFailed as failed:
        log.warning("no length for %s: %s", m4a.name, failed.last_line)
    except OSError:  # ffmpeg didn't run at all
        log.exception("no length for %s", m4a.name)
    return 0.0


def _new_sound_id(project: ProjectPaths) -> str:
    """Not one of the library's, nor of an m4a it lacks (the next start would add that one)."""
    with lock:
        return new_id("m", {sound.id for sound in read_sounds(project)} | m4a_ids(project))


def _view(sound: StoredSound) -> SoundView:
    return SoundView(**sound.model_dump())


def _shown(project: ProjectPaths, folder: Path) -> str:
    """A folder as the page and the log name it: from the project's root, `media/toon/sounds`."""
    return folder.relative_to(project.root).as_posix()


def _find(sounds: list[StoredSound], sound_id: str) -> StoredSound:
    found = next((sound for sound in sounds if sound.id == sound_id), None)
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบเสียงนี้ในคลังเสียง")
    return found


sound_imports = SoundImports()
