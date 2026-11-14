"""The Render job of the สอนกลอง tab and its results (video-gen spec › Render job, D14, D21, D22):
one at a time in its own slot, holding no GPU (no model runs). The lesson is read and copied into
`.render/` as the job starts, so a `PUT` while it runs reaches the next render only (as ADR 0024).
Then the drum sound (`mixer`), the text (`captions`) and every frame (`frames`, sent to ffmpeg
through stdin) make `lessons/{lesson_id}/renders/{name}.mp4`, `.srt` and `.json`.
"""

import logging
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import disk, ffmpeg, gate_rows, paths, renders
from backend.checks import now_iso
from backend.errors import ApiError, JobFailed, require_rows
from backend.ffmpeg import FfmpegFailed, PipedRunner
from backend.jobs import Cancelled, JobSlot, short
from backend.paths import ProjectPaths
from backend.video_gen import captions, frames, lessons, mixer, timeline
from backend.video_gen.captions import TitleFont
from backend.video_gen.lessons import Lesson

log = logging.getLogger(__name__)

State = Literal["rendering", "done", "failed", "cancelled"]
ErrorCode = Literal["ffmpeg_failed", "internal"]
BYTES_PER_SECOND = 2 * 1024 * 1024  # what `disk_full` reserves per second of clip (spec › Render job step 5)
AUDIO, TEXT = "audio.wav", "text.ass"
VIDEO_BITRATE = "8M"  # videotoolbox's own default is far too low for 1080×1920
AUDIO_RATE, AUDIO_BITRATE = 48_000, "192k"
NOT_RUNNING = "ไม่มีงาน render บทเรียนกลองที่ยังไม่จบ"


class DrumRenderJob(BaseModel):
    """`GET /api/drums/render`: the latest job."""

    state: State
    lesson_id: str
    title: str  # the lesson's, as the render started: a page names the lesson that renders (D34)
    percent: int
    result: str | None = None  # the render's name, once `done`
    error: ErrorCode | None = None
    message: str | None = None


class RenderResult(BaseModel):
    """One finished render of a lesson, as `GET /lessons/{id}/renders` lists it."""

    name: str
    lesson_id: str
    title: str
    length_s: float
    created_at: str
    size_bytes: int


class DrumRenderJobs(JobSlot[DrumRenderJob]):
    """Holds the latest Render job. `run_piped` runs ffmpeg and `title_font` measures the title; a
    test passes ones that pause or stand in (`fastapi-api` › testing)."""

    unfinished = frozenset({"rendering"})
    nothing_to_cancel = NOT_RUNNING
    cancel_refusal = (409, "not_running")  # spec › API: `cancel` kills ffmpeg before the next frame

    def __init__(self, run_piped: PipedRunner = ffmpeg.run_piped, title_font: TitleFont = captions.kanit_bold):
        super().__init__()
        self._run_piped = run_piped
        self._title_font = title_font

    def lesson_use(self) -> str | None:
        """The lesson an unfinished render works on (`lessons.lesson_jobs`)."""
        job = self.running()
        return job.lesson_id if job else None

    def start(self, body: dict) -> DrumRenderJob:
        """Spec › Render job steps 1–6, in order. The lesson is copied before the answer (D33), under
        `lessons.lock`, so neither a delete nor a `PUT` slips between the read and the job."""
        lesson_id = body.get("lesson_id")
        if not isinstance(lesson_id, str):
            raise ApiError(400, "invalid_request", "ต้องมี lesson_id")
        project = paths.project()
        require_rows(gate_rows.drums(project))
        with self._lock:
            running = self.running()
            if running is not None:
                raise ApiError(409, "busy", f"กำลัง render {running.title} อยู่", lesson_id=running.lesson_id)
            with lessons.lock:
                lesson = lessons.read_under_lock(project, lesson_id)
                length_s = lessons.require_short(lesson)
                disk.require_free(project.root, round(length_s * BYTES_PER_SECOND))
                _copy_in(project, lesson_id)
                self._job = DrumRenderJob(state="rendering", lesson_id=lesson_id, title=lesson.title, percent=0)
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, lesson_id), daemon=True).start()
        return job


    def _run(self, project: ProjectPaths, lesson_id: str) -> None:
        started = time.monotonic()
        ending: dict = {"state": "failed", "error": "internal", "message": "render ไม่สำเร็จ"}
        try:
            name = self._render(project, lesson_id)
            ending = {"state": "done", "percent": 100, "result": name}
        except Cancelled:
            ending = {"state": "cancelled"}
        except FfmpegFailed as error:
            ending = {"state": "failed", "error": "ffmpeg_failed", "message": f"render ไม่สำเร็จ: {error.last_line}"}
        except JobFailed as failed:
            ending = {"state": "failed", "error": failed.code, "message": failed.message}
        except Exception as error:
            log.exception("drum render of %s failed", lesson_id)
            ending = {"state": "failed", "error": "internal", "message": f"render ไม่สำเร็จ: {short(error)}"}
        finally:
            try:
                shutil.rmtree(project.drums_render_dir, ignore_errors=True)
                renders.remove_partials(_renders_dir(project, lesson_id))
            except Exception:  # the job must still end, or every later render is busy
                log.exception("drum render of %s: clean-up failed", lesson_id)
            self.update(**ending)
            log.info("drum render of %s ended %s after %.1f s", lesson_id, ending["state"], time.monotonic() - started)

    def _render(self, project: ProjectPaths, lesson_id: str) -> str:
        """Spec › Render job steps 7–9, from the copies in `.render/`."""
        work = project.drums_render_dir
        lesson = Lesson.model_validate_json((work / lessons.LESSON_FILE).read_bytes())
        timing = timeline.build(lesson)
        (work / AUDIO).write_bytes(mixer.mix(project, timing))
        (work / TEXT).write_text(captions.ass_file(project, lesson, timing, self._title_font), encoding="utf-8")
        background = work / lessons.BACKGROUND if lesson.background == "image" else None
        if background is not None and not background.is_file():
            background = None  # a lesson saved as `image` whose picture went: the app's colours
        scene = frames.Scene(lesson, timing, background)
        total = scene.frames()
        folder = _renders_dir(project, lesson_id)
        folder.mkdir(parents=True, exist_ok=True)
        render = renders.next_free(folder)
        command = _command(os.path.relpath(project.kanit_dir, work), str(render.file(".mp4.partial")))
        drawn = (frames.frame_at(scene, n / frames.FPS) for n in range(total))
        self._run_piped(command, work, self._cancel, drawn, lambda sent: self.update(percent=min(99, sent * 100 // total)))
        info = {"lesson_id": lesson_id, "title": lesson.title, "length_s": round(timing.length_s, 2), "created_at": now_iso()}
        render.finish(captions.srt_file(lesson, timing), info)
        log.info("drum render of %s wrote %s (%d frames)", lesson_id, render.name, total)
        return render.name


def _command(fonts_dir: str, out: str) -> list[str]:
    """Raw RGB frames from stdin and the wav, the text drawn over (spec › Render job step 8)."""
    return [
        ffmpeg.exe(), "-hide_banner", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{frames.WIDTH}x{frames.HEIGHT}", "-r", str(frames.FPS), "-i", "-",
        "-i", AUDIO,
        "-vf", f"ass={TEXT}:fontsdir={fonts_dir}",
        *ffmpeg.h264_args(), "-b:v", VIDEO_BITRATE, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", str(AUDIO_RATE), "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart", "-f", "mp4", out,
    ]  # fmt: skip


def _copy_in(project: ProjectPaths, lesson_id: str) -> None:
    """The lesson and its picture into a fresh `.render/`. Call with `lessons.lock` held."""
    work = project.drums_render_dir
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    folder = lessons.lesson_dir(project, lesson_id)
    shutil.copyfile(folder / lessons.LESSON_FILE, work / lessons.LESSON_FILE)
    if (folder / lessons.BACKGROUND).is_file():
        shutil.copyfile(folder / lessons.BACKGROUND, work / lessons.BACKGROUND)


def _renders_dir(project: ProjectPaths, lesson_id: str) -> Path:
    return lessons.lesson_dir(project, lesson_id) / "renders"


# --- the results ---


def list_results(project: ProjectPaths, lesson_id: str) -> list[RenderResult]:
    """Every complete render of the lesson, newest first. Raises `ApiError` 404 `not_found`."""
    lessons.stored(project, lesson_id)
    return renders.listed(_renders_dir(project, lesson_id), RenderResult)


def result_file(project: ProjectPaths, lesson_id: str, name: str, suffix: str) -> Path:
    """The `.mp4` or `.srt` of a complete render. Raises `ApiError` 404 `not_found`."""
    lessons.stored(project, lesson_id)
    render = renders.Render(_renders_dir(project, lesson_id), name)
    render.require()
    return render.file(suffix)


def delete_result(project: ProjectPaths, lesson_id: str, name: str) -> None:
    """`404` `not_found`, or `409` `in_use` while a player holds the mp4 open."""
    lessons.stored(project, lesson_id)
    renders.Render(_renders_dir(project, lesson_id), name).delete()


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart: the work folder goes, and every half-written result."""
    shutil.rmtree(project.drums_render_dir, ignore_errors=True)
    if project.lessons_dir.is_dir():
        for folder in project.lessons_dir.glob("*/renders"):
            renders.remove_partials(folder)


render_jobs = DrumRenderJobs()
lessons.lesson_jobs.append(lambda: render_jobs.lesson_use())
