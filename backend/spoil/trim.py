"""The Trim job: cut ranges out of a Temp clip by encoding `{id}.mp4` again without
them and putting the new file in place of the old one (D36, D37, D41, D42). The clip's
Transcript, Shots, EP cuts and Spoil draft were made from the old file, so they go
once the new one is in place (ADR-0021).

ffmpeg runs as a subprocess in the job's thread: no model, no GPU slot (ADR-0015),
but `gpu.slot.begin_trim` marks the clip so every other job refuses it meanwhile.
"""

import logging
import math
import os
import sys
import threading
import time
from pathlib import Path
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from backend import checks, disk, ffmpeg, files, gate_rows, gpu, paths
from backend.errors import ApiError, require_rows
from backend.ffmpeg import FfmpegFailed, Media, Runner
from backend.jobs import Cancelled, JobSlot, short
from backend.paths import ProjectPaths
from backend.spoil import clips, transcribe
from backend.spoil.clips import Range, TempClip
from backend.spoil_maker import draft_file

log = logging.getLogger(__name__)

MAX_RANGES = 20
MIN_RANGE_S = 0.5
MIN_KEPT_S = 10.0
AUDIO_BPS = 192_000
MIN_VIDEO_BPS = 1_000_000
GIB = 1024**3
LENGTH_SLACK_S = 1.0  # how far the new file's length may be from `kept_s` (D42)
REPLACE_TRIES = 20  # `os.replace` every 0.5 s for 10 s while Windows holds the mp4 (D42)
REPLACE_WAIT_S = 0.5

State = Literal["trimming", "replacing", "done", "failed", "cancelled"]
UNFINISHED = frozenset({"trimming", "replacing"})
Derived = Literal["transcript", "shots", "episodes", "draft"]
DERIVED_NAMES: dict[Derived, str] = {"transcript": "Transcript", "shots": "Shot", "episodes": "การตัด EP", "draft": "Spoil draft"}


class TrimJobError(BaseModel):
    code: Literal["disk_full", "ffmpeg_failed", "in_use", "internal"]
    message: str


class TrimJob(BaseModel):
    clip_id: str
    state: State
    percent: int | None = None  # `trimming` only
    kept_s: float
    cancel_requested: bool = False
    error: TrimJobError | None = None


class TrimFailed(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


# --- Pure parts: the ranges, the bitrate and the ffmpeg command (spec › Seams 1) ---


def checked_ranges(value: object) -> list[Range]:
    """`ranges` as the body sends it: 1–20 objects of finite numbers (no booleans).
    Anything else → `400` `invalid_request` (spec › Trim step 1.2)."""
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_RANGES:
        raise ApiError(400, "invalid_request", f"ranges ต้องมี 1–{MAX_RANGES} ช่วง")
    found = []
    for item in value:
        start, end = (item.get("start_s"), item.get("end_s")) if isinstance(item, dict) else (None, None)
        if not (_is_finite(start) and _is_finite(end)):
            raise ApiError(400, "invalid_request", "แต่ละช่วงต้องมี start_s และ end_s เป็นตัวเลข")
        found.append(Range(start_s=float(start), end_s=float(end)))
    return found


def _is_finite(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def merged(ranges: list[Range], duration_s: float) -> list[Range]:
    """Sorted, overlapping or touching ranges joined, after D41's checks against the
    file's real length; one that fails → `400` `invalid_ranges` with the reason."""
    for one in ranges:
        if not 0 <= one.start_s < one.end_s <= duration_s:
            raise _invalid(f"ช่วงต้องอยู่ใน 0–{duration_s:.1f} วินาทีและเริ่มก่อนจบ")
        if one.end_s - one.start_s < MIN_RANGE_S:
            raise _invalid(f"แต่ละช่วงต้องยาวอย่างน้อย {MIN_RANGE_S} วินาที")
    joined: list[Range] = []
    for one in sorted(ranges, key=lambda r: r.start_s):
        if joined and one.start_s <= joined[-1].end_s:
            joined[-1] = Range(start_s=joined[-1].start_s, end_s=max(joined[-1].end_s, one.end_s))
        else:
            joined.append(one)
    if kept_seconds(kept_spans(joined, duration_s)) < MIN_KEPT_S:
        raise _invalid(f"ต้องเหลือคลิปอย่างน้อย {MIN_KEPT_S:.0f} วินาที")
    return joined


def _invalid(reason: str) -> ApiError:
    return ApiError(400, "invalid_ranges", f"ช่วงที่ตัดไม่ถูกต้อง: {reason}")


def kept_spans(cut: list[Range], duration_s: float) -> list[Range]:
    """What is left of [0, duration_s) once the merged `cut` ranges go."""
    spans, start = [], 0.0
    for one in cut:
        if one.start_s > start:
            spans.append(Range(start_s=start, end_s=one.start_s))
        start = one.end_s
    if start < duration_s:
        spans.append(Range(start_s=start, end_s=duration_s))
    return spans


def kept_seconds(spans: list[Range]) -> float:
    return sum(span.end_s - span.start_s for span in spans)


def video_bps(file_bytes: int, duration_s: float) -> int:
    """The old file's average bitrate less the audio's, at least 1 Mbps (D41)."""
    return max(MIN_VIDEO_BPS, round(file_bytes * 8 / duration_s) - AUDIO_BPS)


def command(source: Path, out: Path, spans: list[Range], has_audio: bool, bps: int, platform: str = sys.platform) -> list[str]:
    """The ffmpeg argv: each kept span trimmed, then joined with `concat` (spec ›
    Library assumptions); videotoolbox on a Mac, libx264 elsewhere (D36)."""
    graph, inputs = [], []
    for n, span in enumerate(spans):
        cut = f"{_seconds(span.start_s)}:{_seconds(span.end_s)}"
        graph.append(f"[0:v]trim={cut},setpts=PTS-STARTPTS[v{n}]")
        inputs.append(f"[v{n}]")
        if has_audio:
            graph.append(f"[0:a]atrim={cut},asetpts=PTS-STARTPTS[a{n}]")
            inputs.append(f"[a{n}]")
    outputs = "[v][a]" if has_audio else "[v]"
    graph.append(f"{''.join(inputs)}concat=n={len(spans)}:v=1:a={1 if has_audio else 0}{outputs}")
    encoder = ["-c:v", "h264_videotoolbox"] if platform == "darwin" else ["-c:v", "libx264", "-preset", "veryfast"]
    audio = ["-map", "[a]", "-c:a", "aac", "-b:a", str(AUDIO_BPS)] if has_audio else []
    return [
        ffmpeg.exe(), "-nostdin", "-hide_banner", "-y", "-progress", "pipe:1", "-nostats",
        "-i", str(source), "-filter_complex", ";".join(graph),
        "-map", "[v]", *encoder, "-b:v", str(bps), *audio,
        "-movflags", "+faststart", str(out),
    ]  # fmt: skip


def _seconds(value: float) -> str:
    """Seconds as ffmpeg's filter options take them: no exponent, no trailing zeros."""
    return f"{value:.3f}".rstrip("0").rstrip(".")


# --- Files ---


def trimmed_partial(project: ProjectPaths, clip_id: str) -> Path:
    return project.partial_dir / f"{clip_id}.trim.mp4"


def marker_path(project: ProjectPaths, clip_id: str) -> Path:
    """The new json of a clip whose mp4 is being put in place (D41)."""
    return project.media_temp_dir / f"{clip_id}{clips.TRIMMING_SUFFIX}"


def derived_of(project: ProjectPaths, clip_id: str) -> list[Derived]:
    """What the clip has that was made from its mp4 (D37), in the spec's order."""
    found: list[Derived] = []
    if clips.transcript_path(project, clip_id).is_file():
        found.append("transcript")
    if project.clip_shots_dir(clip_id).is_dir():
        found.append("shots")
    if project.episodes_file(clip_id).is_file():
        found.append("episodes")
    if draft_file.made_from_clip(project, clip_id):
        found.append("draft")
    return found


def recover_on_start(project: ProjectPaths) -> None:
    """Before `.partial/` is cleaned (D15): a marker with its file still in `.partial/`
    means the mp4 wasn't replaced — the marker goes; without it, the mp4 was replaced —
    the derived data goes and the marker becomes the json (spec › Trim)."""
    for marker in project.media_temp_dir.glob(f"*{clips.TRIMMING_SUFFIX}"):
        clip_id = marker.name.removesuffix(clips.TRIMMING_SUFFIX)
        try:
            TempClip.model_validate_json(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            log.exception("unreadable trim marker %s; removed", marker.name)
            marker.unlink(missing_ok=True)
            continue
        if not clips.has_clip(project, clip_id):
            marker.unlink(missing_ok=True)
        elif trimmed_partial(project, clip_id).is_file():
            marker.unlink(missing_ok=True)
        else:
            clips.delete_derived(project, clip_id)
            draft_file.drop_if_uses(project, clip_id)
            os.replace(marker, clips.json_path(project, clip_id))
            log.info("finished replacing %s after a restart", clip_id)


# --- The job ---


class Trims(JobSlot[TrimJob]):
    """Holds the latest Trim job: one at a time in the whole app (D41).

    Tests pass fakes for ffmpeg (`run_ffmpeg` writes the output, reports progress and
    can wait for a signal), `probe`, `free_bytes`, `sleep` and `replace_mp4`, which
    Windows refuses while the old mp4 is open (D42, D43)."""

    unfinished = UNFINISHED

    def __init__(
        self,
        run_ffmpeg: Runner = ffmpeg.run,
        probe: Callable[[Path], Media] = ffmpeg.probe,
        free_bytes: Callable[[Path], int] = disk.free_bytes,
        sleep: Callable[[float], None] = time.sleep,
        replace_mp4: Callable[[Path, Path], None] = os.replace,
    ):
        super().__init__()
        self._run_ffmpeg, self._probe, self._free_bytes = run_ffmpeg, probe, free_bytes
        self._sleep, self._replace_mp4 = sleep, replace_mp4
        self._thread: threading.Thread | None = None

    def start(self, body: dict) -> TrimJob:
        """Checks in spec order (Trim step 1), then starts the thread. Raises `ApiError`."""
        project = paths.project()
        require_rows(gate_rows.FFMPEG)
        clip_id, confirm = body.get("clip_id"), body.get("confirm_derived_loss", False)
        if not isinstance(clip_id, str) or not isinstance(confirm, bool):
            raise ApiError(400, "invalid_request", "ส่ง clip_id เป็นข้อความ และ confirm_derived_loss เป็น true หรือ false")
        asked = checked_ranges(body.get("ranges"))
        with self._lock, transcribe.transcriptions.clips_lock():
            mp4 = clips.video_file(project, clip_id)  # 404 unless both json and mp4 are there
            clip = clips.read_clip(project, clip_id)
            try:
                media = self._probe(mp4)
            except FfmpegFailed as error:
                raise ApiError(500, "internal", f"อ่านความยาวคลิปไม่ได้: {short(error)}") from error
            cut = merged(asked, media.duration_s)
            if transcribe.transcriptions.transcribing(clip_id):
                raise ApiError(409, "transcribing", "กำลังถอดคลิปนี้อยู่ รอให้ถอดเสร็จก่อนแล้วตัด")
            if self._taken():
                raise ApiError(409, "busy", "กำลังตัดคลิปอื่นอยู่")
            with gpu.slot.begin_trim(clip_id):
                derived = derived_of(project, clip_id)
                if derived and not confirm:
                    names = ", ".join(DERIVED_NAMES[one] for one in derived)
                    raise ApiError(409, "has_derived", f"ตัดคลิปจะลบ {names} ของคลิปนี้", derived=derived)
                spans = kept_spans(cut, media.duration_s)
                self._job = TrimJob(clip_id=clip_id, state="trimming", percent=0, kept_s=round(kept_seconds(spans), 3))
                self._cancel.clear()
            job = self._job.model_copy(deep=True)
            self._thread = threading.Thread(target=self._run, args=(project, clip, mp4, media, cut, spans), daemon=True)
            self._thread.start()
        return job

    def cancel(self) -> TrimJob:
        with self._lock:
            if not self._taken():
                raise ApiError(404, "not_found", "ไม่มีงานตัดที่ยังไม่จบ")
            if self._job.state == "replacing":
                raise ApiError(409, "replacing", "กำลังแทนไฟล์ ยกเลิกไม่ได้แล้ว")
            self._job.cancel_requested = True
            self._cancel.set()
            return self._job.model_copy(deep=True)

    def stop_on_shutdown(self) -> None:
        """Kills a running ffmpeg; a `replacing` job finishes first (spec › Trim step 9),
        so the restart finds the clip whole. A job still trimming checks the cancel at
        its next ffmpeg read and never starts replacing."""
        with self._lock:
            self._cancel.set()
            replacing = self._job is not None and self._job.state == "replacing"
            thread = self._thread
        if replacing and thread is not None:
            thread.join()

    def _run(self, project: ProjectPaths, clip: TempClip, mp4: Path, media: Media, cut: list[Range], spans: list[Range]) -> None:
        ending: dict = {"state": "failed"}
        try:
            self._trim(project, clip, mp4, media, cut, spans)
            ending = {"state": "done"}
        except Cancelled:
            ending = {"state": "cancelled"}
        except TrimFailed as failed:
            ending["error"] = TrimJobError(code=failed.code, message=failed.message)
        except Exception as error:
            log.exception("Trim job of %s failed", clip.id)
            ending["error"] = TrimJobError(code="internal", message=f"ตัดคลิปไม่สำเร็จ: {short(error)}")
        finally:
            # A restart reads the partial's absence as "the mp4 was replaced" (recover_on_start),
            # so it goes only here, after the replace is over either way.
            trimmed_partial(project, clip.id).unlink(missing_ok=True)
            # Before the state reads as finished: a client that sees it may use the clip at once.
            gpu.slot.end_trim()
        self._update(percent=None, **ending)

    def _trim(self, project: ProjectPaths, clip: TempClip, mp4: Path, media: Media, cut: list[Range], spans: list[Range]) -> None:
        """Steps 2–6: encode the kept spans into `.partial/`, check the result, then put it in place."""
        kept = kept_seconds(spans)
        file_bytes = mp4.stat().st_size
        needed = file_bytes * kept / media.duration_s + GIB
        free = self._free_bytes(project.media_temp_dir)
        if free < needed:
            raise TrimFailed("disk_full", f"ที่ว่างไม่พอ: ต้องการ {needed / 1e9:.1f} GB มี {free / 1e9:.1f} GB")
        project.partial_dir.mkdir(parents=True, exist_ok=True)
        out = trimmed_partial(project, clip.id)
        argv = command(mp4, out, spans, media.has_audio, video_bps(file_bytes, media.duration_s))

        def on_progress(seconds: float) -> None:
            self._update(percent=min(99, math.floor(seconds / kept * 100)))

        try:
            self._run_ffmpeg(argv, project.partial_dir, self._cancel, on_progress)
        except FfmpegFailed as error:
            raise TrimFailed("ffmpeg_failed", f"ตัดคลิปไม่สำเร็จ: {short(error)}") from error
        made = self._probe(out)
        if abs(made.duration_s - kept) > LENGTH_SLACK_S or (media.has_audio and not made.has_audio):
            raise TrimFailed("ffmpeg_failed", "ตัดคลิปไม่สำเร็จ: ไฟล์ที่ตัดได้ไม่ครบ")
        with self._lock:
            if self._cancel.is_set():
                raise Cancelled()
            self._job.state, self._job.percent = "replacing", None
        self._replace(project, clip, out, made, cut)

    def _replace(self, project: ProjectPaths, clip: TempClip, out: Path, made: Media, cut: list[Range]) -> None:
        """Step 6, in `Transcriptions.delete_clip`'s lock order (D42)."""
        marker = marker_path(project, clip.id)
        new = clip.model_copy(
            update={
                "duration_s": round(made.duration_s),
                "file_bytes": out.stat().st_size,
                "trimmed": [*clip.trimmed, *cut],
                "trimmed_at": checks.now_iso(),
            }
        )
        files.write_atomic(marker, new.model_dump_json(indent=2))
        for attempt in range(REPLACE_TRIES):
            if self._put_in_place(project, clip.id, out):
                break
            if attempt < REPLACE_TRIES - 1:
                self._sleep(REPLACE_WAIT_S)  # without the locks, so other jobs and polls go on
        else:
            marker.unlink(missing_ok=True)
            raise TrimFailed("in_use", "แทนไฟล์ไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง")
        # After the slot's lock: the draft's lock comes before it (spoil-maker D49).
        draft_file.drop_if_uses(project, clip.id)
        os.replace(marker, clips.json_path(project, clip.id))

    def _put_in_place(self, project: ProjectPaths, clip_id: str, out: Path) -> bool:
        """One try of the new mp4 over the old, and the derived files with it; False while
        Windows still holds the old file (D42)."""
        with transcribe.transcriptions.clips_lock(), gpu.slot.clip_untouched(clip_id, trimming=True):
            try:
                self._replace_mp4(out, clips.video_path(project, clip_id))
            except PermissionError:
                return False
            clips.delete_derived(project, clip_id)
            return True


trims = Trims()
