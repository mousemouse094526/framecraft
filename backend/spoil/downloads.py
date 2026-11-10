"""The Download job: one at a time, in a daemon thread, state in memory (ADR 0010).

Steps and rules are in docs/features/spoil/spec.md › Download (D6, D11, D14, D15,
D47, D51, D52, D54).
"""

import logging
import math
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, gate_rows, paths, spoil
from backend.paths import ProjectPaths
from backend.spoil import clips, links, mp4check
from backend.spoil.adapter import DownloadCancelled, ErrorCode, error_code
from backend.spoil.mp4check import NotPlayable
from backend.errors import ApiError, JobFailed, Row, require_rows
from backend.jobs import JobSlot

log = logging.getLogger(__name__)

State = Literal["checking", "downloading", "merging", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"checking", "downloading", "merging"})

DISK_MARGIN_BYTES = 2**30
BUSY_MESSAGE = "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่"
UPDATE_COMMAND = "uv lock --upgrade-package yt-dlp"  # then the Setup script installs it

ERROR_MESSAGES: dict[ErrorCode, str] = {
    "live": "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้",
    "unavailable": "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้",
    "login_required": (
        "เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ "
        'โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"'
    ),
    "unsupported": 'เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"',
    "unsupported_format": (
        "เว็บนี้ไม่มีไฟล์ H.264 ไม่เกิน 1080p ให้โหลด โหลดเองแล้วแปลง "
        'จากนั้นกด "เลือกไฟล์ในเครื่อง"'
    ),
    "playlist": "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว",
    "duplicate": "คลิปนี้โหลดไว้แล้ว",
    "download_error": (
        "โหลดไม่สำเร็จ (yt-dlp {version}). ถ้าเป็นทุกคลิป "
        "ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"
    ),
}


class _Duplicate(JobFailed):
    """Another site's link turned out to be a clip already listed (D51)."""

    def __init__(self, clip_id: str):
        super().__init__("duplicate", ERROR_MESSAGES["duplicate"])
        self.clip_id = clip_id


class DownloadJobError(BaseModel):
    code: ErrorCode
    message: str
    yt_dlp_version: str
    fix: str | None = None
    # The clip already listed, on `duplicate` (D51).
    clip_id: str | None = None


class DownloadJob(BaseModel):
    url: str
    # The Temp clip id: a YouTube link's at once, another site's once yt-dlp has read it.
    id: str | None
    state: State
    title: str | None = None
    percent: int | None = None
    cancel_requested: bool = False
    error: DownloadJobError | None = None
    # The Temp clip's id, set once the job is `done`.
    clip_id: str | None = None


@dataclass
class _ProgressCount:
    """What one job's progress hook has seen so far."""

    estimate: int
    format_count: int
    bytes_by_file: dict[str, int] = field(default_factory=dict)
    finished: int = 0


class Downloads(JobSlot[DownloadJob]):
    """Holds the latest Download job, and whether a File import is receiving a file: one
    of the two at a time (D52). One lock guards every change to either."""

    unfinished = UNFINISHED

    def __init__(self, check_mp4: Callable[[Path], mp4check.Mp4Info] = mp4check.check):
        """`check_mp4` runs ffmpeg on the merged file; a test passes a stand-in (rules › testing)."""
        super().__init__()
        self._check_mp4 = check_mp4
        self._receiving_file = False

    def refuse_if_busy(self) -> None:
        """Raises `ApiError` 409 `busy` while a download or a File import is unfinished."""
        with self._lock:
            self._require_free()

    @contextmanager
    def receiving_file(self) -> Iterator[None]:
        """Holds the slot for a File import while its body comes in and is checked: no
        Download job starts meanwhile, and no other import. The flag goes down however
        the block ends (D55). Raises `ApiError` 409 `busy` when the slot is taken."""
        with self._lock:
            self._require_free()
            self._receiving_file = True
        try:
            yield
        finally:
            with self._lock:
                self._receiving_file = False

    def _require_free(self) -> None:
        """Raises `ApiError` 409 `busy` while a Download job's thread runs or a File import
        is receiving. Call with the lock held."""
        if self._taken() or self._receiving_file:
            raise ApiError(409, "busy", BUSY_MESSAGE)

    def start(self, url: str) -> DownloadJob:
        """Checks in spec order, then starts the job's thread. Raises `ApiError`."""
        require_rows(_needed_rows())
        link = links.parse(url)  # yt-dlp doesn't match a link with spaces around it
        if link is None:
            raise ApiError(400, "invalid_url", "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป")
        project = paths.project()
        with self._lock:
            # Another site's clip is checked once its id is known (D51).
            if link.youtube_id and clips.has_clip(project, link.youtube_id):
                raise ApiError(409, "duplicate", ERROR_MESSAGES["duplicate"], clip_id=link.youtube_id)
            self._require_free()
            self._job = DownloadJob(url=link.url, id=link.youtube_id, state="checking")
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, link.url), daemon=True).start()
        return job

    def cancel(self) -> DownloadJob:
        """Asks the thread to stop; it does after `fetch_info` or at its next progress call (D15)."""
        with self._lock:
            if not self._taken():
                raise ApiError(404, "not_found", "ไม่มีงานโหลดที่ยังไม่จบ")
            if self._job.state == "merging":
                raise ApiError(409, "merging", "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def stop_on_shutdown(self) -> None:
        """Ctrl+C must not wait for a download to finish (D15). Leaves
        `cancel_requested` alone: that field is for the user's own cancel, and
        nobody polls a backend that is stopping."""
        self._cancel.set()

    def _run(self, project: ProjectPaths, url: str) -> None:
        ending: dict = {"state": "failed"}
        try:
            clip_id = self._download(project, url)
            ending = {"state": "done", "clip_id": clip_id}
        except DownloadCancelled:
            ending = {"state": "cancelled"}
        except _Duplicate as failure:
            ending["error"] = _job_error(failure.code, clip_id=failure.clip_id)
        except JobFailed as failure:  # a reason found before yt-dlp raised anything
            ending["error"] = _job_error(failure.code, failure.message)
        except NotPlayable as refused:  # the merged file breaks the rule (D54)
            log.warning("download of %s is not playable here: %s", url, refused.reason)
            ending["error"] = _job_error("unsupported_format")
        except Exception as error:
            code = error_code(error)
            if code == "download_error":
                log.exception("download of %s failed", url)  # the full yt-dlp message, for [api]
            ending["error"] = _job_error(code)
        finally:
            # Whatever happened, the job must end, or every later POST is `busy`.
            # It counts as unfinished until its files are gone (D15).
            with self._lock:
                known_id = self._job.id  # None when yt-dlp never told another site's id
            if ending["state"] != "done" and known_id:
                try:
                    clips.remove_unfinished(project, known_id)
                except Exception:
                    log.exception("could not remove the files of %s", known_id)
            self.update(percent=None, **ending)

    def _download(self, project: ProjectPaths, url: str) -> str:
        """Steps 2–8 of spec › Download; returns the new clip's id."""
        info = spoil.adapter.fetch_info(url)
        if info.get("_type") == "playlist":  # a site that ignores `noplaylist`
            raise JobFailed("playlist", ERROR_MESSAGES["playlist"])
        clip_id = links.clip_id(info["extractor_key"], str(info["id"]))
        if clips.has_clip(project, clip_id):
            # Before the id goes on the job: the clean-up in `_run` goes by that id, and
            # must not touch the clip already listed.
            raise _Duplicate(clip_id)
        self.update(id=clip_id)
        if self._cancel.is_set():
            raise DownloadCancelled()
        if info.get("live_status") in ("is_live", "is_upcoming"):
            raise JobFailed("live", ERROR_MESSAGES["live"])
        estimate = estimate_bytes(info)
        require_disk(project, estimate)
        self.update(state="downloading", title=info.get("title"))
        count = _ProgressCount(estimate, len(_formats(info)))
        mp4 = spoil.adapter.download(info, project, clip_id, lambda event: self._on_progress(count, event))
        # `format` picks by what the site says; this is the file (D54). A format that named
        # no extension isn't merged into mp4 and keeps its own (D56).
        if mp4 != clips.video_path(project, clip_id):
            raise NotPlayable(mp4check.NOT_MP4_CONTAINER)
        shown = self._check_mp4(mp4)
        clips.write_clip(project, _temp_clip(project, info, clip_id, mp4, shown))
        return clip_id

    def _on_progress(self, count: _ProgressCount, event: dict) -> None:
        """yt-dlp's progress hook: percent across every format, then `merging`."""
        with self._lock:
            # Checked under the lock, so a cancel either lands before `merging` or gets 409.
            if self._cancel.is_set():
                raise DownloadCancelled()
            if event["status"] not in ("downloading", "finished"):
                return
            count.bytes_by_file[event["filename"]] = event.get("downloaded_bytes") or 0
            if event["status"] == "finished":
                count.finished += 1
            if count.finished >= count.format_count:
                # Every format is on disk; yt-dlp merges now (a no-op for one format).
                self._job.state, self._job.percent = "merging", None
            elif count.estimate:
                done = sum(count.bytes_by_file.values())
                percent = min(100, math.floor(done / count.estimate * 100))
                # A format that restarts counts its bytes from 0 again.
                self._job.percent = max(percent, self._job.percent or 0)


def require_disk(project: ProjectPaths, needed: int) -> None:
    """Raises `JobFailed` `disk_full` unless media/temp/ has `needed` bytes and 1 GiB more
    free (D11); a File import checks its size the same way (D52)."""
    project.media_temp_dir.mkdir(parents=True, exist_ok=True)
    free = spoil.free_bytes(project.media_temp_dir)
    if free < needed + DISK_MARGIN_BYTES:
        raise JobFailed(
            "disk_full",
            f"ที่ว่างไม่พอ: ต้องการ {(needed + DISK_MARGIN_BYTES) / 1e9:.1f} GB มี {free / 1e9:.1f} GB",
        )


def _formats(info: dict) -> list[dict]:
    """The formats yt-dlp picked: video and audio, or one that has both."""
    return info.get("requested_formats") or [info]


def estimate_bytes(info: dict) -> int:
    """The download's size from metadata; 0 when it can't be told (D11, D17)."""
    total = sum(f.get("filesize") or f.get("filesize_approx") or 0 for f in _formats(info))
    if total:
        return total
    if info.get("tbr") and info.get("duration"):
        return int(info["tbr"] * info["duration"] * 125)  # kbps × s → bytes
    return 0


def _needed_rows() -> dict[str, Row]:
    """The Status check rows a download needs (D9), by id; the frontend's
    `DOWNLOAD_ITEMS` gates on the same rows."""
    return gate_rows.LINK_TOOLS | gate_rows.FFMPEG


def _yt_dlp_version() -> str:
    try:
        return checks.probe_yt_dlp()
    except Exception:  # an error report must not fail because of the version
        return "unknown"


def _job_error(code: ErrorCode, message: str | None = None, clip_id: str | None = None) -> DownloadJobError:
    version = _yt_dlp_version()
    if code == "download_error":
        return DownloadJobError(
            code=code,
            message=ERROR_MESSAGES[code].format(version=version),
            yt_dlp_version=version,
            fix=UPDATE_COMMAND,
        )
    return DownloadJobError(
        code=code, message=message or ERROR_MESSAGES[code], yt_dlp_version=version, clip_id=clip_id
    )


def _temp_clip(
    project: ProjectPaths, info: dict, clip_id: str, mp4: Path, shown: mp4check.Mp4Info
) -> clips.TempClip:
    duration = info.get("duration") or shown.duration_s
    return clips.TempClip(
        id=clip_id,
        title=info.get("title") or clip_id,
        channel=info.get("channel") or info.get("uploader"),
        site=info["extractor_key"],
        source_url=info.get("webpage_url") or info.get("original_url"),
        duration_s=round(duration) if duration else None,
        # As shown, from the file: a phone video's turn is in the file, not the info (D55).
        width=shown.width,
        height=shown.height,
        orientation=shown.orientation,
        file_bytes=mp4.stat().st_size,
        thumbnail=clips.find_thumbnail(project, clip_id),
        downloaded_at=checks.now_iso(),
        yt_dlp_version=_yt_dlp_version(),
    )


downloads = Downloads()
