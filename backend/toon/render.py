"""The Render job of the การ์ตูนเล่า tab and its results (toon spec › Render job, D4, D17, D19,
D22, D23, D32, D37, D38, D45): one at a time in its own slot, so an EP whose narration is all
there renders during an Image job. A card with no narration, or a stale one, is voiced first
(`voicing`, holding the GPU as `toon_render`); then ffmpeg runs without it (`rendering`) and
writes `eps/{ep_id}/renders/{name}.mp4`, `.srt` and `.json`.

The EP is read once as rendering starts, its pictures, narration and sounds copied into
`.render/`: edits after that don't reach this clip (as ADR 0024). A card drawn with an older
reference picture renders with it (D32).
"""

import logging
import os
import shutil
import threading
import wave
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from backend import checks, disk, ffmpeg, gate_rows, gpu, paths, renders, speaking, subtitles
from backend.errors import ApiError, JobFailed, require_rows
from backend.ffmpeg import FfmpegFailed, Runner, probe
from backend.jobs import ModelJobSlot, short
from backend.paths import ProjectPaths
from backend.spoil_maker import tts
from backend.subtitles import Timed
from backend.toon import compose, episodes, series, store, voicing
from backend.toon.compose import Narrated, Placed, SoundRun, Tagged
from backend.toon.store import Ep, Series
from backend.toon.voicing import VoicePlan

log = logging.getLogger(__name__)

State = Literal["voicing", "rendering", "done", "failed", "cancelled"]
UNFINISHED: frozenset[State] = frozenset({"voicing", "rendering"})
ErrorCode = Literal["crashed", "model_failed", "ffmpeg_failed", "internal"]

NOT_READY = ("no_image", "no_ref")  # a card that can't render (spec › Render job step 1)
NEEDS_VOICE = ("no_audio", "stale_audio")
CAPTIONS, NARRATION = "captions.ass", "narration.wav"
SILENT_RATE = 24_000  # the narration's rate when no card speaks: OmniVoice's own

CHANGED = "EP เปลี่ยนระหว่าง render: กด render ใหม่"


class ToonRenderJobError(BaseModel):
    code: ErrorCode
    message: str


class ToonRenderJob(BaseModel):
    kind: Literal["render"] = "render"
    state: State
    series_id: str
    ep_id: str
    percent: int | None = None
    done: int | None = None
    total: int | None = None
    name: str | None = None  # the clip it wrote, once `done`
    error: ToonRenderJobError | None = None
    cancel_requested: bool = False
    started_at: str


class RenderResult(BaseModel):
    """One finished render of an EP, as `GET /eps/{eid}/renders` lists it."""

    name: str
    title: str
    n: int
    duration_s: float
    created_at: str
    size_bytes: int


class RenderJobs(ModelJobSlot[ToonRenderJob]):
    """Holds the latest Render job; its `voicing` speaks through its `speaker`.
    `run_ffmpeg` runs each ffmpeg command; a test passes one that pauses (`fastapi-api` › testing)."""

    unfinished = UNFINISHED
    gpu_kind = "toon_render"
    error_type = ToonRenderJobError
    nothing_to_cancel = "ไม่มีงาน render การ์ตูนเล่าที่ยังไม่จบ"
    worker_error = tts.WorkerError
    child_name = "ตัวสร้างเสียง"
    failure = "render ไม่สำเร็จ"

    def __init__(self, run_ffmpeg: Runner = ffmpeg.run):
        super().__init__()
        self.speaker = speaking.Speaker(self)
        self._run_ffmpeg = run_ffmpeg

    def ep_use(self) -> episodes.EpUse | None:
        """The EP an unfinished render works on; it never locks it (`episodes.ep_jobs`)."""
        job = self.running()
        return episodes.EpUse(job.ep_id, "renders") if job else None

    def start(self, body: dict) -> ToonRenderJob:
        """Spec › Render job step 1, in order: the EP and its cards, `ep_locked`, `disk_full`, the gate,
        `busy`, and `gpu_busy` when cards need their narration. The draft's lock and the
        store's cover the checks and the start, so no edit or voice delete slips between."""
        project, ep_id = paths.project(), body.get("ep_id")
        with self._lock, gpu.slot.draft_lock, store.lock:
            series_now, ep = episodes.find(project, ep_id)
            to_voice = _cards_to_voice(project, series_now, ep)
            require_rows(gate_rows.render(project, voices_first=bool(to_voice)))
            if self._taken():
                raise ApiError(409, "busy", "กำลัง render การ์ตูนเล่าอยู่")
            plans = []
            if to_voice:
                voice = voicing.ep_voice(project, ep)
                plans = [voicing.plan_card(series_now.id, ep, card, voice) for card in to_voice]
                gpu.slot.take("toon_render")
                self._job = ToonRenderJob(
                    state="voicing", series_id=series_now.id, ep_id=ep.id, done=0, total=len(plans), started_at=checks.now_iso()
                )
            else:
                self._job = ToonRenderJob(
                    state="rendering", series_id=series_now.id, ep_id=ep.id, percent=0, started_at=checks.now_iso()
                )
            self._cancel.clear()
            job = self._job.model_copy(deep=True)
        threading.Thread(target=self._run, args=(project, series_now.id, ep.id, plans), daemon=True).start()
        return job

    def _run(self, project: ProjectPaths, series_id: str, ep_id: str, plans: list[VoicePlan]) -> None:
        """A cancel keeps the narration already made in the EP."""

        def clean_up(state: str) -> None:  # however it ended
            shutil.rmtree(project.toon_render_dir, ignore_errors=True)
            renders.remove_partials(project.ep_renders_dir(series_id, ep_id))

        what = f"toon render {ep_id}"
        self._run_job(what, lambda: self._voice_and_render(project, series_id, ep_id, plans), clean_up)

    def _voice_and_render(self, project: ProjectPaths, series_id: str, ep_id: str, plans: list[VoicePlan]) -> dict:
        if plans:
            spoken_all = self.speaker.speak(project, [plan.tts_text for plan in plans], plans[0].voice)
            # The speaker first: `zip` asks it once more after the last text, so it ends its child.
            for done, (spoken, plan) in enumerate(zip(spoken_all, plans), start=1):
                if not voicing.put_audio(project, plan, spoken):
                    log.info("the narration of card %s is dropped: the card went", plan.card_id)
                self.update(done=done)
            self.free_gpu()  # voicing is over: the GPU is free while ffmpeg runs
        self.update(state="rendering", percent=0, done=None, total=None)
        try:
            name = self._render(project, series_id, ep_id)
        except FfmpegFailed as error:
            raise JobFailed("ffmpeg_failed", f"render ไม่สำเร็จ: {short(error)}") from None
        log.info("render of %s wrote %s", ep_id, name)
        return {"percent": 100, "name": name}

    def _render(self, project: ProjectPaths, series_id: str, ep_id: str) -> str:
        """Spec › Render job step 3: the EP read and copied once, each card's piece, then the whole clip."""
        work = project.toon_render_dir
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        with store.lock:
            series_now = store.read_series(project, series_id)
            ep = store.read_ep(project, series_id, ep_id)
            if series_now is None or ep is None:
                raise JobFailed("internal", "อ่าน EP นี้ไม่ได้แล้ว")
            placed, runs = _copy_in(project, series_now, ep, work)
        total_frames = placed[-1].start_frame + placed[-1].frames
        total = total_frames / compose.FPS
        narrated = [
            Narrated(text=card.text, start=p.start_frame / compose.FPS, end=p.start_frame / compose.FPS + p.narration_s)
            for p, card in zip(placed, episodes.ep_cards(ep), strict=True)
            if p.narration is not None
        ]
        (work / CAPTIONS).write_text(
            compose.ass_file(
                project, series_now.layout, ep.title, ep.n, series_now.channel_name, narrated,
                _tags(series_now, ep, placed), total,
            ),
            encoding="utf-8",
        )  # fmt: skip
        _write_narration(work, placed)
        pieces = []
        fade_frames = compose.frames_of(compose.FADE_S)
        for index, card in enumerate(placed):
            frames = card.frames + (fade_frames if index < len(placed) - 1 else 0)
            piece = f"{index}.mkv"
            self._run_ffmpeg(compose.piece_command(card, series_now.layout, frames, piece), work, self._cancel)
            pieces.append(piece)
            self.update(percent=renders.pieces_percent(index + 1, len(placed)))
        folder = project.ep_renders_dir(series_id, ep_id)
        folder.mkdir(parents=True, exist_ok=True)
        render = renders.next_free(folder)
        mp4_partial = render.file(".mp4.partial")
        command = compose.final_command(
            pieces, placed, NARRATION, runs, CAPTIONS, os.path.relpath(project.kanit_dir, work), total_frames, str(mp4_partial)
        )
        self._run_ffmpeg(command, work, self._cancel, renders.encode_progress(self.update, total))
        info = {
            "title": ep.title,
            "n": ep.n,
            "duration_s": round(probe(mp4_partial).duration_s, 2),
            "created_at": checks.now_iso(),
        }
        render.finish(subtitles.srt_file([Timed(*n) for n in narrated]), info)
        return render.name


def _cards_to_voice(project: ProjectPaths, series_now: Series, ep: Ep) -> list[store.Card]:
    """Spec › Render job step 1 up to the gate; returns the cards to voice first (D38). Call under the store's lock."""
    # An EP still at its plot has no cards to render either (spec › Render job step 1).
    if ep.stage != "cards" or not any(True for _ in episodes.placed_cards(ep)):
        raise ApiError(400, "cards_not_ready", "EP นี้ยังไม่มีการ์ด", card_ids=[])
    episodes.editable(project, ep.id)  # `ep_locked`
    refs = series.ref_revs(series_now)
    missing = [card.id for segment, card in episodes.placed_cards(ep) if episodes.image_status(card, segment, refs) in NOT_READY]
    if missing:
        raise ApiError(400, "cards_not_ready", "ทุกการ์ดต้องมีภาพก่อน render", card_ids=missing)
    disk.require_free(project.root)
    return [card for card in episodes.ep_cards(ep) if episodes.audio_status(card, ep) in NEEDS_VOICE]


def _copy_in(project: ProjectPaths, series_now: Series, ep: Ep, work: Path) -> tuple[list[Placed], list[SoundRun]]:
    """Every card's picture and narration, and every sound played, into the work folder; the
    cards on the timeline (each card's length on whole frames, D14) and the sound runs (D17).
    Call under the store's lock."""
    images = project.card_images_dir(series_now.id, ep.id)
    audio = project.card_audio_dir(series_now.id, ep.id)
    placed: list[Placed] = []
    runs: list[SoundRun] = []
    frame = 0
    for act in ep.acts:
        for segment in act.segments:
            segment_start = frame
            for card in segment.cards:
                status = episodes.audio_status(card, ep)
                picture = images / card.image.file if card.image else None
                if picture is None or not picture.is_file() or status not in ("ready", "silent"):
                    raise JobFailed("internal", CHANGED)
                index = len(placed)
                shutil.copyfile(picture, work / f"{index}.png")
                narration = None
                if status == "ready":
                    narration = f"{index}.wav"
                    shutil.copyfile(audio / f"{card.id}.wav", work / narration)
                # A card heard or silent has its length; the voice's speed only guesses the others.
                frames = compose.frames_of(episodes.card_seconds(card, status, chars_per_s=0.0))
                placed.append(
                    Placed(
                        card_id=card.id,
                        picture=f"{index}.png",
                        narration=narration,
                        narration_s=card.audio.duration_s if narration else 0.0,
                        start_frame=frame,
                        frames=frames,
                        motion=card.motion,
                        flicker=card.flicker,
                    )
                )
                frame += frames
            seconds = (frame - segment_start) / compose.FPS
            sound = None
            if segment.sound is not None:
                sound = f"{segment.sound.sound_id}.m4a"
                if not (work / sound).is_file():
                    source = project.toon_sounds_dir / sound
                    if not source.is_file():
                        raise JobFailed("internal", CHANGED)
                    shutil.copyfile(source, work / sound)
            if runs and runs[-1].sound == sound:
                runs[-1] = runs[-1]._replace(seconds=runs[-1].seconds + seconds)
            else:
                volume = segment.sound.volume if segment.sound else 0
                runs.append(SoundRun(sound=sound, volume=volume, seconds=seconds))
    if not placed:
        raise JobFailed("internal", CHANGED)
    return placed, runs


def _tags(series_now: Series, ep: Ep, placed: list[Placed]) -> list[Tagged]:
    """Each character's name tag over the first card it is in, when the Series shows them (D19, D23)."""
    if not series_now.name_tags:
        return []
    names = {c.id: f"{c.name} / {c.tag}" if c.tag else c.name for c in series_now.characters}
    seen: set[str] = set()
    tagged = []
    for card, at in zip(episodes.ep_cards(ep), placed, strict=True):
        new = [i for i in card.character_ids if i not in seen and i in names]
        seen.update(card.character_ids)
        if new:
            start = at.start_frame / compose.FPS
            tagged.append(Tagged(tags=[names[i] for i in new], start=start, end=start + at.frames / compose.FPS))
    return tagged


def _write_narration(work: Path, placed: list[Placed]) -> None:
    """Every card's wav, then silence to the card's end, as one wav: the gap and the hold
    (D14, D21); a silent card is silence. OmniVoice speaks every card at one rate."""
    params = None
    for card in placed:
        if card.narration:
            with wave.open(str(work / card.narration), "rb") as part:
                found = (part.getframerate(), part.getnchannels(), part.getsampwidth())
                if params is not None and found != params:
                    raise JobFailed("internal", "เสียงเล่าของการ์ดไม่เข้ากัน: สร้างเสียงเล่าใหม่")
                params = found
    rate, channels, width = params or (SILENT_RATE, 1, 2)
    with wave.open(str(work / NARRATION), "wb") as out:
        out.setframerate(rate)
        out.setnchannels(channels)
        out.setsampwidth(width)
        for card in placed:
            samples = round(card.frames / compose.FPS * rate)
            audio = b""  # the card's narration, cut to the card's length; silence fills the rest
            if card.narration:
                with wave.open(str(work / card.narration), "rb") as part:
                    audio = part.readframes(min(part.getnframes(), samples))
            out.writeframes(audio + b"\0" * (samples * channels * width - len(audio)))


# --- the results ---


def list_results(project: ProjectPaths, ep_id: str) -> list[RenderResult]:
    """Every complete render of the EP, newest first."""
    return renders.listed(_renders_dir(project, ep_id), RenderResult)


def result_file(project: ProjectPaths, ep_id: str, name: str) -> Path:
    """The mp4 of a complete render of the EP. Raises `ApiError` 404 `not_found`."""
    render = renders.Render(_renders_dir(project, ep_id), name)
    render.require()
    return render.file(".mp4")


def delete_result(project: ProjectPaths, ep_id: str, name: str) -> None:
    """`404` `not_found`, or `409` `in_use` while a player holds the mp4 open."""
    renders.Render(_renders_dir(project, ep_id), name).delete()


def clean_on_start(project: ProjectPaths) -> None:
    """Jobs don't survive a restart: the work folder goes, and every half-written result."""
    shutil.rmtree(project.toon_render_dir, ignore_errors=True)
    if project.toon_series_dir.is_dir():
        for folder in project.toon_series_dir.glob("*/eps/*/renders"):
            renders.remove_partials(folder)


def _renders_dir(project: ProjectPaths, ep_id: str) -> Path:
    with store.lock:
        series_now, ep = episodes.find(project, ep_id)
        return project.ep_renders_dir(series_now.id, ep.id)


render_jobs = RenderJobs()
episodes.ep_jobs.append(lambda: render_jobs.ep_use())
series.series_jobs.append(lambda: render_jobs)
