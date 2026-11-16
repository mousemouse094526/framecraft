"""The Render job of a reel cover and its results (drum-cover spec › Render job, D2, D12, D17, D20):
one at a time in its own slot, holding no GPU (no model runs) and running beside a lesson's render
or a Pick job. The song and the cover it plays are copied into `media/songs/.render/` as the job
starts, so a `PUT` while it runs reaches the next render only (video-gen D33). Then the sound
(`audio.reel_wav`), the reel's own text (`captions`) and every frame (`frames`, ADR 0054, sent to
ffmpeg through stdin with video-gen's own command) make `songs/{song_id}/renders/{name}.mp4`, `.srt` and `.json`.
"""

import logging
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend import disk, ffmpeg, gate_rows, paths, renders, subtitles
from backend.checks import now_iso
from backend.drum_cover import audio, captions, cover, frames
from backend.drum_cover import timeline as reel_timeline
from backend.drum_cover.cover import Backing, CoverFields, Drums
from backend.drum_notes import songs
from backend.drum_notes.songs import Song
from backend.errors import ApiError, JobFailed, require_rows
from backend.ffmpeg import FfmpegFailed, PipedRunner
from backend.jobs import Cancelled, JobSlot, short
from backend.paths import ProjectPaths
from backend.subtitles import Timed
from backend.video_gen import captions as lesson_captions
from backend.video_gen import render as drum_render
from backend.video_gen import timeline
from backend.video_gen.captions import TitleFont

log = logging.getLogger(__name__)

State = Literal["rendering", "done", "failed", "cancelled"]
ErrorCode = Literal["ffmpeg_failed", "internal"]
NOT_RUNNING = "ไม่มีงาน render reel ที่ยังไม่จบ"
RENDERS = "renders"


class CoverRenderJob(BaseModel):
    """`GET /api/covers/render`: the latest job."""

    state: State
    song_id: str
    title: str  # the cover's, as the render started: the page names the reel that renders
    percent: int
    result: str | None = None  # the render's name, once `done`
    error: ErrorCode | None = None
    message: str | None = None


class CoverRenderResult(BaseModel):
    """One finished render of a song's reel, as `GET /songs/{id}/cover/renders` lists it: the
    stretch, the pick and the sound it was made from (ADR 0034, D18, D24)."""

    name: str
    song_id: str
    title: str
    length_s: float
    start_s: float
    end_s: float
    picked_at: str
    drums: Drums = Field(default_factory=Drums)
    backing: Backing
    created_at: str
    size_bytes: int


class CoverRenderJobs(JobSlot[CoverRenderJob]):
    """Holds the latest Render job. `run_piped` runs ffmpeg and `title_font` measures the title; a
    test passes ones that pause or stand in (`fastapi-api` › testing)."""

    unfinished = frozenset({"rendering"})
    nothing_to_cancel = NOT_RUNNING
    cancel_refusal = (409, "not_running")

    def __init__(self, run_piped: PipedRunner = ffmpeg.run_piped, title_font: TitleFont = lesson_captions.kanit_bold):
        super().__init__()
        self._run_piped = run_piped
        self._title_font = title_font

    def song_use(self) -> str | None:
        """The song an unfinished render works on (`songs.song_jobs`): it can't be deleted meanwhile."""
        job = self.running()
        return job.song_id if job else None

    def start(self, song_id: str) -> CoverRenderJob:
        """Spec › Render job steps 1–6, in order. The song and cover are copied before the answer,
        under `songs.lock`, so neither a delete nor a `PUT` slips between the read and the job."""
        project = paths.project()
        with songs.lock:
            cover.require_analysis(songs.read_under_lock(project, song_id))
        require_rows(gate_rows.drums(project))
        with self._lock:
            running = self.running()
            if running is not None:
                raise ApiError(409, "busy", f"กำลัง render {running.title} อยู่", song_id=running.song_id)
            with songs.lock:
                song = songs.read_under_lock(project, song_id)
                fields = cover.used(project, song)
                length_s = fields.end_s - fields.start_s + timeline.TAIL_S
                disk.require_free(project.root, round(length_s * drum_render.BYTES_PER_SECOND))
                _copy_in(project, song, fields)
                self._job = CoverRenderJob(state="rendering", song_id=song_id, title=fields.title, percent=0)
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, song_id), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, song_id: str) -> None:
        started = time.monotonic()
        ending: dict = {"state": "failed", "error": "internal", "message": "render ไม่สำเร็จ"}
        try:
            name = self._render(project, song_id)
            ending = {"state": "done", "percent": 100, "result": name}
        except Cancelled:
            ending = {"state": "cancelled"}
        except FfmpegFailed as error:
            ending = {"state": "failed", "error": "ffmpeg_failed", "message": f"render ไม่สำเร็จ: {error.last_line}"}
        except JobFailed as failed:
            ending = {"state": "failed", "error": failed.code, "message": failed.message}
        except Exception as error:
            log.exception("reel render of %s failed", song_id)
            ending = {"state": "failed", "error": "internal", "message": f"render ไม่สำเร็จ: {short(error)}"}
        finally:
            try:
                shutil.rmtree(project.songs_render_dir, ignore_errors=True)
                renders.remove_partials(_renders_dir(project, song_id))
            except Exception:  # the job must still end, or every later render is busy
                log.exception("reel render of %s: clean-up failed", song_id)
            self.update(**ending)
            log.info("reel render of %s ended %s after %.1f s", song_id, ending["state"], time.monotonic() - started)

    def _render(self, project: ProjectPaths, song_id: str) -> str:
        """Spec › Render job steps 7–9, from the copies in `.render/`."""
        work = project.songs_render_dir
        song = Song.model_validate_json((work / songs.SONG_FILE).read_bytes())
        fields = CoverFields.model_validate_json((work / cover.COVER_FILE).read_bytes())
        analysis = cover.require_analysis(song)
        timing = reel_timeline.build(analysis, fields)
        song_audio = songs.checked_dir(project, song_id) / songs.AUDIO_FILE  # `song_busy` keeps it there
        (work / drum_render.AUDIO).write_bytes(audio.reel_wav(project, song_audio, fields, timing, self._cancel))
        lesson = reel_timeline.lesson(analysis, fields)
        (work / drum_render.TEXT).write_text(captions.ass_file(project, lesson, timing, self._title_font), encoding="utf-8")
        background = work / cover.BACKGROUND if fields.background == "image" else None
        if background is not None and not background.is_file():
            background = None  # a cover saved as `image` whose picture went: the app's colours
        scene = frames.Scene(lesson, timing, background)
        total = scene.frames()
        folder = _renders_dir(project, song_id)
        folder.mkdir(parents=True, exist_ok=True)
        render = renders.next_free(folder)
        # video-gen's own command, unchanged (D17): the backing is already in `audio.wav`.
        command = drum_render._command(os.path.relpath(project.kanit_dir, work), str(render.file(".mp4.partial")))
        drawn = (frames.frame_at(scene, n / frames.FPS) for n in range(total))
        self._run_piped(command, work, self._cancel, drawn, lambda sent: self.update(percent=min(99, sent * 100 // total)))
        info = {
            "song_id": song_id,
            "title": fields.title,
            "length_s": round(timing.length_s, 2),
            "start_s": fields.start_s,
            "end_s": fields.end_s,
            "picked_at": analysis.picked_at,
            "drums": fields.drums.model_dump(),
            "backing": fields.backing.model_dump(),
            "created_at": now_iso(),
        }
        render.finish(srt_file(fields, timing.length_s), info)
        log.info("reel render of %s wrote %s (%d frames)", song_id, render.name, total)
        return render.name


def srt_file(fields: CoverFields, length_s: float) -> str:
    """One cue over the whole clip: the title, the line under it and the caption (D12)."""
    text = "\n".join(line for line in (fields.title, fields.subtitle, fields.caption) if line)
    return subtitles.srt_file([Timed(text, 0.0, length_s)])


def _copy_in(project: ProjectPaths, song: Song, fields: CoverFields) -> None:
    """The song, the cover as it will play, and its picture into a fresh `.render/`. Call with
    `songs.lock` held."""
    work = project.songs_render_dir
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    folder = songs.checked_dir(project, song.id)
    shutil.copyfile(folder / songs.SONG_FILE, work / songs.SONG_FILE)
    (work / cover.COVER_FILE).write_text(fields.model_dump_json(), encoding="utf-8")
    if fields.background == "image" and (folder / cover.BACKGROUND).is_file():
        shutil.copyfile(folder / cover.BACKGROUND, work / cover.BACKGROUND)


def _renders_dir(project: ProjectPaths, song_id: str) -> Path:
    return songs.checked_dir(project, song_id) / RENDERS


# --- the results ---


def list_results(project: ProjectPaths, song_id: str) -> list[CoverRenderResult]:
    """Every complete render of the song's reel, newest first. Raises `ApiError` 404 `not_found`."""
    _require_song(project, song_id)
    return renders.listed(_renders_dir(project, song_id), CoverRenderResult)


def result_file(project: ProjectPaths, song_id: str, name: str, suffix: str) -> Path:
    """The `.mp4` or `.srt` of a complete render. Raises `ApiError` 404 `not_found`."""
    _require_song(project, song_id)
    render = renders.Render(_renders_dir(project, song_id), name)
    render.require()
    return render.file(suffix)


def delete_result(project: ProjectPaths, song_id: str, name: str) -> None:
    """`404` `not_found`, or `409` `in_use` while a player holds the mp4 open."""
    _require_song(project, song_id)
    renders.Render(_renders_dir(project, song_id), name).delete()


def _require_song(project: ProjectPaths, song_id: str) -> None:
    with songs.lock:
        songs.read_under_lock(project, song_id)


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart: the work folder goes, and every half-written result."""
    shutil.rmtree(project.songs_render_dir, ignore_errors=True)
    if project.songs_dir.is_dir():
        for folder in project.songs_dir.glob(f"*/{RENDERS}"):
            renders.remove_partials(folder)


render_jobs = CoverRenderJobs()
songs.song_jobs.append(lambda: render_jobs.song_use())
