"""The background sound library of the การ์ตูนเล่า tab (toon spec › คลังเสียงพื้น, D5, D16, D39):
`sounds/sounds.json` and one `sounds/{sound_id}.m4a` per sound, shared by every Series.

A sound comes in through a Sound import, one at a time in its own slot (no GPU): a file of
this machine as a raw body in one request (ADR 0028), or a link loaded by a job that reads its
info, checks its length, then downloads its best audio into `.partial/` (spoil's Download
job, ADR 0029). Either way ffmpeg converts it to aac in m4a with no picture, so a render reads
one format (D39). A restart half-way leaves only `.partial/` files and `.m4a.partial` ones,
which start-up removes.
"""

import logging
import math
import os
import threading
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import anyio
from pydantic import BaseModel
from starlette.requests import ClientDisconnect

from backend import checks, ffmpeg, gate_rows, paths, spoil, uploads
from backend.errors import ApiError, JobFailed, Row, invalid_request, require_rows
from backend.ffmpeg import FfmpegFailed
from backend.jobs import Cancelled, JobSlot
from backend.paths import ProjectPaths
from backend.spoil import links
from backend.spoil.adapter import DownloadCancelled, DownloadOptions, error_code
from backend.toon import series, store
from backend.toon.store import StoredSound

log = logging.getLogger(__name__)

State = Literal["checking", "downloading", "converting", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"checking", "downloading", "converting"})
ErrorCode = Literal["login_required", "download_error", "disk_full", "too_long", "unsupported_file", "internal"]
Source = Literal["file", "link"]

UPLOAD_MAX_BYTES = 200 * 1024**2  # spec › คลังเสียงพื้น
MAX_SECONDS = 20 * 60
NAME_MAX = 60
AUDIO_RATE = 48_000
BITRATE = "192k"

# Where a link's audio lands: `.partial/` of the tab, no thumbnail, no mp4 merge (spec › Modules touched).
LINK_OPTIONS = DownloadOptions(
    format="bestaudio", folder=lambda project: project.toon_partial_dir, thumbnail=False, merge_mp4=False
)

BUSY = "กำลังเอาเสียงอื่นเข้าคลังอยู่"
UNREADABLE = "ไฟล์นี้ไม่มีเสียงที่อ่านได้"
TOO_LONG = f"เสียงยาวเกิน {MAX_SECONDS // 60} นาที"
ERROR_MESSAGES: dict[ErrorCode, str] = {
    "login_required": "เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดเสียงเองแล้วเอาไฟล์เข้า",
    "download_error": "โหลดเสียงจากลิงก์นี้ไม่สำเร็จ",
    "too_long": TOO_LONG,
    "unsupported_file": UNREADABLE,
}


class SoundUser(BaseModel):
    """An EP whose segment plays the sound, as `in_use` names it."""

    series_name: str
    n: int
    title: str


class SoundView(BaseModel):
    id: str
    name: str
    duration_s: float
    source: Source


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


class SoundImports(JobSlot[SoundImport]):
    """Holds the latest link import, and whether a file is being received: one of the two at a
    time (spec › คลังเสียงพื้น). `convert` runs ffmpeg; a test passes one that pauses."""

    unfinished = UNFINISHED

    def __init__(self, convert: ffmpeg.Runner = ffmpeg.run, stall_seconds: float = uploads.STALL_SECONDS):
        super().__init__()
        self._convert = convert
        self._stall_seconds = stall_seconds
        self._receiving_file = False

    # --- a file ---

    def check(self, body: dict) -> uploads.UploadCheck:
        """Every check of the file but its body's, before the page sends it (ADR 0028)."""
        project = paths.project()
        size = _file_checks(project, body.get("name"), body.get("size"))
        with self._lock:
            self._require_free()
        return uploads.UploadCheck(size=size)

    async def receive(self, name: str | None, size: str | None, body: AsyncIterator[bytes]) -> SoundView:
        """Checks again, writes `body` to `.partial/`, converts it into the library. Raises
        `ApiError`, or `ClientDisconnect` once its file is gone."""
        project, expected = paths.project(), uploads.whole_number(size)
        await anyio.to_thread.run_sync(_file_checks, project, name, expected)
        with self._receiving():
            sound_id = _new_sound_id(project)
            partial = project.toon_partial_dir / f"{sound_id}.upload"
            try:
                await uploads.receive(body, partial, expected, self._stall_seconds)
                return await anyio.to_thread.run_sync(
                    self._take_in, project, sound_id, partial, _file_title(name), "file", threading.Event()
                )
            except ClientDisconnect:
                log.info("the sound import %s stopped: the page went away", sound_id)
                raise
            except JobFailed as refused:
                raise ApiError(400, refused.code, refused.message) from None
            finally:
                with anyio.CancelScope(shield=True):
                    await anyio.to_thread.run_sync(lambda: partial.unlink(missing_ok=True))

    @contextmanager
    def _receiving(self) -> Iterator[None]:
        with self._lock:
            self._require_free()
            self._receiving_file = True
        try:
            yield
        finally:
            with self._lock:
                self._receiving_file = False

    def _require_free(self) -> None:
        """Call with the lock held."""
        if self._taken() or self._receiving_file:
            raise ApiError(409, "busy", BUSY)

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

    def stop_on_shutdown(self) -> None:
        self._cancel.set()

    def _run(self, project: ProjectPaths, url: str) -> None:
        sound_id = _new_sound_id(project)
        ending: dict = {"state": "failed"}
        try:
            sound = self._download(project, url, sound_id)
            ending = {"state": "done", "sound_id": sound.id, "percent": 100}
        except (DownloadCancelled, Cancelled):
            ending = {"state": "cancelled"}
        except JobFailed as failure:
            ending["error"] = SoundImportError(code=failure.code, message=failure.message)
        except Exception as error:
            code = "login_required" if error_code(error) == "login_required" else "download_error"
            log.exception("sound download of %s failed", url)
            ending["error"] = SoundImportError(code=code, message=ERROR_MESSAGES[code])
        finally:
            for leftover in project.toon_partial_dir.glob(f"{sound_id}.*") if project.toon_partial_dir.is_dir() else ():
                leftover.unlink(missing_ok=True)
            self._update(**ending)

    def _download(self, project: ProjectPaths, url: str, sound_id: str) -> StoredSound:
        """Spoil's Download job steps: the info, its length before loading, the load with %."""
        info = spoil.adapter.fetch_info(url, LINK_OPTIONS)
        if info.get("_type") == "playlist":
            raise JobFailed("download_error", "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว")
        if (info.get("duration") or 0) > MAX_SECONDS:
            raise JobFailed("too_long", TOO_LONG)
        if self._cancel.is_set():
            raise DownloadCancelled()
        estimate = sum(f.get("filesize") or f.get("filesize_approx") or 0 for f in info.get("requested_formats") or [info])
        try:
            series.require_free_disk(project, estimate)
        except ApiError as full:
            raise JobFailed("disk_full", full.message) from None
        title = info.get("title") or sound_id
        self._update(state="downloading", title=title, percent=0)
        project.toon_partial_dir.mkdir(parents=True, exist_ok=True)
        loaded = spoil.adapter.download(
            info, project, sound_id, lambda event: self._on_progress(estimate, event), LINK_OPTIONS
        )
        self._update(state="converting", percent=None)
        return self._take_in(project, sound_id, loaded, title.strip()[:NAME_MAX].strip(), "link", self._cancel)

    def _on_progress(self, estimate: int, event: dict) -> None:
        with self._lock:
            if self._cancel.is_set():
                raise DownloadCancelled()
            total = event.get("total_bytes") or event.get("total_bytes_estimate") or estimate
            if event.get("status") == "downloading" and total:
                percent = min(100, math.floor((event.get("downloaded_bytes") or 0) / total * 100))
                self._job.percent = max(percent, self._job.percent or 0)

    # --- both ---

    def _take_in(
        self, project: ProjectPaths, sound_id: str, source: Path, name: str, origin: Source, cancel: threading.Event
    ) -> StoredSound:
        """In a thread: its length and sound (`unsupported_file`, `too_long`), then aac in m4a
        through `.partial`, then the library's entry. Raises `JobFailed`."""
        try:
            media = ffmpeg.probe(source)
        except FfmpegFailed:
            raise JobFailed("unsupported_file", UNREADABLE) from None
        if not media.has_audio:
            raise JobFailed("unsupported_file", UNREADABLE)
        if media.duration_s > MAX_SECONDS:
            raise JobFailed("too_long", TOO_LONG)
        project.toon_sounds_dir.mkdir(parents=True, exist_ok=True)
        target = project.toon_sounds_dir / f"{sound_id}.m4a"
        partial = target.with_name(target.name + ".partial")
        try:
            self._convert(convert_command(source, partial), project.toon_sounds_dir, cancel)
            seconds = ffmpeg.probe(partial).duration_s
        except FfmpegFailed as failed:
            partial.unlink(missing_ok=True)
            log.warning("could not convert %s: %s", source.name, failed.last_line)
            raise JobFailed("unsupported_file", UNREADABLE) from None
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        os.replace(partial, target)
        sound = StoredSound(id=sound_id, name=name, duration_s=round(seconds, 1), source=origin)
        with store.lock:
            store.write_sounds(project, [*store.read_sounds(project), sound])
        log.info("imported sound %s (%s, %.1f s)", sound_id, origin, seconds)
        return SoundView(**sound.model_dump())


def convert_command(source: Path, out: Path) -> list[str]:
    """The first audio stream as aac 192k 48 kHz stereo in m4a, no picture (D39)."""
    return [
        ffmpeg.exe(), "-nostdin", "-hide_banner", "-v", "error", "-y", "-i", str(source),
        "-map", "0:a:0", "-vn", "-c:a", "aac", "-b:a", BITRATE, "-ar", str(AUDIO_RATE), "-ac", "2",
        "-f", "mp4", str(out),
    ]  # fmt: skip


# --- the library ---


def list_all(project: ProjectPaths) -> list[SoundView]:
    with store.lock:
        return [SoundView(**sound.model_dump()) for sound in store.read_sounds(project)]


def rename(project: ProjectPaths, sound_id: str, body: dict) -> SoundView:
    """Names may repeat (spec › คลังเสียงพื้น)."""
    name = series.checked_text(body.get("name"), 1, NAME_MAX)
    with store.lock:
        sounds = store.read_sounds(project)
        sound = _find(sounds, sound_id)
        sound.name = name
        store.write_sounds(project, sounds)
        return SoundView(**sound.model_dump())


def delete(project: ProjectPaths, sound_id: str) -> None:
    """A sound a segment of any EP plays can't go: `in_use` with those EPs (as D25)."""
    with store.lock:
        sounds = store.read_sounds(project)
        sound = _find(sounds, sound_id)
        users = sound_users(project, sound_id)
        if users:
            raise ApiError(409, "in_use", "ยังมี EP ที่ใช้เสียงนี้อยู่ ลบไม่ได้", eps=[user.model_dump() for user in users])
        sounds.remove(sound)
        store.write_sounds(project, sounds)
        (project.toon_sounds_dir / f"{sound_id}.m4a").unlink(missing_ok=True)
    log.info("deleted sound %s", sound_id)


def sound_users(project: ProjectPaths, sound_id: str) -> list[SoundUser]:
    """Every EP of every Series with a segment that plays the sound. Call with the store's lock."""
    return [
        SoundUser(series_name=found.name, n=ep.n, title=ep.title)
        for found in store.list_series(project)
        for ep in store.list_eps(project, found.id)
        if any(s.sound and s.sound.sound_id == sound_id for act in ep.acts for s in act.segments)
    ]


def sound_file(project: ProjectPaths, sound_id: str) -> Path:
    with store.lock:
        _find(store.read_sounds(project), sound_id)
        path = project.toon_sounds_dir / f"{sound_id}.m4a"
        if not path.is_file():
            raise ApiError(404, "not_found", "ไม่พบไฟล์ของเสียงนี้")
        return path


def clean_on_start(project: ProjectPaths) -> None:
    """A conversion cut short leaves a `.m4a.partial`; `.partial/` itself the Toon job's clean empties."""
    if project.toon_sounds_dir.is_dir():
        for leftover in project.toon_sounds_dir.glob("*.partial"):
            leftover.unlink(missing_ok=True)


def link_rows() -> dict[str, Row]:
    """What a link's Sound import needs (spec › Status check); a file's needs `ffmpeg` alone."""
    tools: dict[str, Row] = {
        "yt_dlp": ("yt-dlp", lambda: checks.check_version(checks.probe_yt_dlp)),
        "deno": ("Deno", lambda: checks.check_version(checks.probe_deno)),
    }
    return gate_rows.FFMPEG | tools


# --- helpers ---


def _file_checks(project: ProjectPaths, name: object, size: object) -> int:
    require_rows(gate_rows.FFMPEG)
    if not isinstance(name, str) or not _file_title(name):
        raise invalid_request()
    size = uploads.require_size(size, UPLOAD_MAX_BYTES, f"ไฟล์เสียงใหญ่เกิน {UPLOAD_MAX_BYTES // 1024**2} MB")
    series.require_free_disk(project, size)
    return size


def _file_title(name: str | None) -> str:
    """A sound's first name: the file's without its extension, cut to 60 letters (a link's is its
    clip's title, cut the same way)."""
    return os.path.splitext((name or "").strip())[0].strip()[:NAME_MAX].strip()


def _new_sound_id(project: ProjectPaths) -> str:
    with store.lock:
        return store.new_id("m", {sound.id for sound in store.read_sounds(project)})


def _find(sounds: list[StoredSound], sound_id: str) -> StoredSound:
    found = next((sound for sound in sounds if sound.id == sound_id), None)
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบเสียงนี้ในคลังเสียงพื้น")
    return found


sound_imports = SoundImports()
