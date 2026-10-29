"""The Download job: one at a time, in a daemon thread, state in memory (ADR 0010).

Steps and rules are in docs/features/spoil/spec.md › Download (D6, D11, D14, D15).
"""

import logging
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, paths, spoil
from backend.paths import ProjectPaths
from backend.spoil import clips, links
from backend.spoil.adapter import DownloadCancelled, ErrorCode, error_code
from backend.spoil.errors import SpoilError
from backend.spoil.job_slot import JobSlot

log = logging.getLogger(__name__)

State = Literal["checking", "downloading", "merging", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"checking", "downloading", "merging"})

DISK_MARGIN_BYTES = 2**30
UPDATE_COMMAND = "uv lock --upgrade-package yt-dlp"  # then the Setup script installs it

ERROR_MESSAGES: dict[ErrorCode, str] = {
    "live": "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้",
    "unavailable": "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้",
    "login_required": (
        "YouTube ขอให้ login หรือยืนยันว่าไม่ใช่ bot ยังไม่รองรับในรอบนี้ "
        "ลองใหม่ภายหลังหรือใช้คลิปอื่น"
    ),
    "youtube_error": (
        "โหลดไม่สำเร็จ (yt-dlp {version}). ถ้าเป็นทุกคลิป "
        "ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"
    ),
}


class JobError(BaseModel):
    code: ErrorCode
    message: str
    yt_dlp_version: str
    fix: str | None = None


class DownloadJob(BaseModel):
    url: str
    id: str
    state: State
    title: str | None = None
    percent: int | None = None
    cancel_requested: bool = False
    error: JobError | None = None
    clip_id: str | None = None


class _Failed(Exception):
    """Ends a job as `failed` for a reason found before yt-dlp raised anything."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class _ProgressCount:
    """What one job's progress hook has seen so far."""

    estimate: int
    format_count: int
    bytes_by_file: dict[str, int] = field(default_factory=dict)
    finished: int = 0


class Downloads(JobSlot[DownloadJob]):
    """Holds the latest Download job. One lock guards every change to it."""

    unfinished = UNFINISHED

    def start(self, url: str) -> DownloadJob:
        """Checks in spec order, then starts the job's thread. Raises `SpoilError`."""
        missing = _missing_tools()
        if missing:
            raise SpoilError(503, "not_ready", f"ยังติดตั้งไม่ครบ: {', '.join(missing)}")
        url = url.strip()  # yt-dlp doesn't match a link with spaces around it
        video_id = links.video_id(url)
        if video_id is None:
            raise SpoilError(400, "invalid_url", "ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube")
        project = ProjectPaths(paths.ROOT)
        with self._lock:
            if clips.has_clip(project, video_id):
                raise SpoilError(409, "duplicate", "คลิปนี้โหลดไว้แล้ว", clip_id=video_id)
            if self._taken():
                raise SpoilError(409, "busy", "กำลังโหลดคลิปอื่นอยู่")
            self._job = DownloadJob(url=url, id=video_id, state="checking")
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, url, video_id), daemon=True).start()
        return job

    def cancel(self) -> DownloadJob:
        """Asks the thread to stop; it does after `fetch_info` or at its next progress call (D15)."""
        with self._lock:
            if not self._taken():
                raise SpoilError(404, "not_found", "ไม่มีงานโหลดที่ยังไม่จบ")
            if self._job.state == "merging":
                raise SpoilError(409, "merging", "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def stop_on_shutdown(self) -> None:
        """Ctrl+C must not wait for a download to finish (D15). Leaves
        `cancel_requested` alone: that field is for the user's own cancel, and
        nobody polls a backend that is stopping."""
        self._cancel.set()

    def _run(self, project: ProjectPaths, url: str, video_id: str) -> None:
        ending: dict = {"state": "failed"}
        try:
            self._download(project, url, video_id)
            ending = {"state": "done", "clip_id": video_id}
        except DownloadCancelled:
            ending = {"state": "cancelled"}
        except _Failed as failure:
            ending["error"] = _job_error(failure.code, failure.message)
        except Exception as error:
            code = error_code(error)
            if code == "youtube_error":
                log.exception("download of %s failed", url)  # the full yt-dlp message, for [api]
            ending["error"] = _job_error(code)
        finally:
            # Whatever happened, the job must end, or every later POST is `busy`.
            # It counts as unfinished until its files are gone (D15).
            if ending["state"] != "done":
                try:
                    clips.remove_unfinished(project, video_id)
                except Exception:
                    log.exception("could not remove the files of %s", video_id)
            self._update(percent=None, **ending)

    def _download(self, project: ProjectPaths, url: str, video_id: str) -> None:
        info = spoil.adapter.fetch_info(url)
        if self._cancel.is_set():
            raise DownloadCancelled()
        if info.get("live_status") in ("is_live", "is_upcoming"):
            raise _Failed("live", ERROR_MESSAGES["live"])
        estimate = estimate_bytes(info)
        project.media_temp_dir.mkdir(parents=True, exist_ok=True)
        free = spoil.free_bytes(project.media_temp_dir)
        if free < estimate + DISK_MARGIN_BYTES:
            raise _Failed(
                "disk_full",
                f"ที่ว่างไม่พอ: ต้องการ {(estimate + DISK_MARGIN_BYTES) / 1e9:.1f} GB "
                f"มี {free / 1e9:.1f} GB",
            )
        self._update(state="downloading", title=info.get("title"))
        count = _ProgressCount(estimate, len(_formats(info)))
        mp4 = spoil.adapter.download(info, project, lambda event: self._on_progress(count, event))
        clips.write_clip(project, _temp_clip(project, info, mp4))

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


def _missing_tools() -> list[str]:
    """Labels of the Status check rows a download needs that don't pass (D9)."""
    probes = {
        "yt-dlp": checks.probe_yt_dlp,
        "Deno": checks.probe_deno,
        "ffmpeg": checks.probe_ffmpeg,
    }
    missing = []
    for label, probe in probes.items():
        try:
            probe()
        except Exception:
            missing.append(label)
    return missing


def _yt_dlp_version() -> str:
    try:
        return checks.probe_yt_dlp()
    except Exception:  # an error report must not fail because of the version
        return "unknown"


def _job_error(code: ErrorCode, message: str | None = None) -> JobError:
    version = _yt_dlp_version()
    if code == "youtube_error":
        return JobError(
            code=code,
            message=ERROR_MESSAGES[code].format(version=version),
            yt_dlp_version=version,
            fix=UPDATE_COMMAND,
        )
    return JobError(code=code, message=message or ERROR_MESSAGES[code], yt_dlp_version=version)


def _temp_clip(project: ProjectPaths, info: dict, mp4: Path) -> clips.TempClip:
    video = next((f for f in _formats(info) if f.get("vcodec") != "none"), info)
    width, height = video.get("width"), video.get("height")
    duration = info.get("duration")
    return clips.TempClip(
        id=info["id"],
        title=info.get("title") or info["id"],
        channel=info.get("channel") or info.get("uploader"),
        source_url=info.get("webpage_url") or f"https://www.youtube.com/watch?v={info['id']}",
        duration_s=round(duration) if duration else None,
        width=width,
        height=height,
        orientation="portrait" if (width and height and height > width) else "landscape",
        file_bytes=mp4.stat().st_size,
        thumbnail=clips.find_thumbnail(project, info["id"]),
        downloaded_at=checks.now_iso(),
        yt_dlp_version=_yt_dlp_version(),
    )


downloads = Downloads()
