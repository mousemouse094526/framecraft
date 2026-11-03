from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import paths
from backend.spoil_maker import describe, draft, render, settings, voices
from backend.spoil_maker.describe import DescribeJob
from backend.spoil_maker.draft import DraftJob, DraftView, TokenCount
from backend.spoil_maker.render import RenderJob, RenderResult
from backend.spoil_maker.settings import Settings
from backend.spoil_maker.shots import ShotsFile
from backend.spoil_maker.voices import Voice, VoiceJob

router = APIRouter(prefix="/spoil-maker")


class DescribeRequest(BaseModel):
    clip_id: str
    confirm_draft_loss: bool = False


class VoiceName(BaseModel):
    # Any JSON: a missing or non-text name is `invalid_voice`, not a validation error.
    name: Any = None


@router.get("/clips/{clip_id}/shots")
def get_shots(clip_id: str) -> ShotsFile:
    return describe.clip_shots(paths.project(), clip_id)


@router.get("/clips/{clip_id}/shots/{name}")
def get_shot_image(clip_id: str, name: str) -> FileResponse:
    return FileResponse(describe.shot_image(paths.project(), clip_id, name), media_type="image/jpeg")


@router.post("/describes", status_code=202)
def start_describe(body: DescribeRequest) -> DescribeJob:
    return describe.describes.start(body.clip_id, body.confirm_draft_loss)


@router.get("/describes/current")
def get_current_describe() -> DescribeJob | None:
    """The latest job, or null when none ran since the backend started."""
    return describe.describes.current()


@router.delete("/describes/current", status_code=202)
def cancel_describe() -> DescribeJob:
    return describe.describes.cancel()


@router.get("/voices")
def list_voices() -> list[Voice]:
    """Newest first."""
    return voices.list_voices(paths.project())


@router.post("/voices", status_code=201)
def save_voice(body: VoiceName) -> Voice:
    return voices.save_preview(paths.project(), body.name)


@router.patch("/voices/{voice_id}")
def rename_voice(voice_id: str, body: VoiceName) -> Voice:
    return voices.rename(paths.project(), voice_id, body.name)


@router.delete("/voices/{voice_id}", status_code=204)
def delete_voice(voice_id: str) -> Response:
    voices.delete(paths.project(), voice_id)
    return Response(status_code=204)


@router.get("/voices/{voice_id}/sample.wav")
def get_voice_sample(voice_id: str) -> FileResponse:
    return FileResponse(voices.sample_audio(paths.project(), voice_id), media_type="audio/wav")


@router.post("/voice-jobs", status_code=202)
def start_voice_job(body: dict[str, Any]) -> VoiceJob:
    """The body depends on `kind` (spec › Voice job), so the module checks it."""
    return voices.voice_jobs.start(body)


@router.get("/voice-jobs/current")
def get_current_voice_job() -> VoiceJob | None:
    """The latest job, or null when none ran since the backend started."""
    return voices.voice_jobs.current()


@router.delete("/voice-jobs/current", status_code=202)
def cancel_voice_job() -> VoiceJob:
    return voices.voice_jobs.cancel()


@router.api_route("/voice-jobs/preview.wav", methods=["GET", "HEAD"])
def get_voice_preview() -> FileResponse:
    """`HEAD` tells the page whether a preview is there without downloading it."""
    return FileResponse(voices.preview_audio(paths.project()), media_type="audio/wav")


@router.get("/tokens")
def get_tokens(clip_ids: str = "") -> TokenCount:
    """`clip_ids=a,b` in the order the user put them."""
    return draft.tokens(paths.project(), clip_ids)


@router.get("/draft")
def get_draft() -> DraftView | None:
    """The Spoil draft, or null when there is none."""
    return draft.view(paths.project())


@router.patch("/draft")
def change_draft(body: dict[str, Any]) -> DraftView:
    """Each field is optional and checked by the module (spec › API)."""
    return draft.change_draft(paths.project(), body)


@router.post("/draft/sentences", status_code=201)
def insert_sentence(body: dict[str, Any]) -> DraftView:
    return draft.insert_sentence(paths.project(), body)


@router.patch("/draft/sentences/{sentence_id}")
def change_sentence(sentence_id: str, body: dict[str, Any]) -> DraftView:
    return draft.change_sentence(paths.project(), sentence_id, body)


@router.delete("/draft/sentences/{sentence_id}")
def delete_sentence(sentence_id: str) -> DraftView:
    return draft.delete_sentence(paths.project(), sentence_id)


@router.get("/draft/sentences/{sentence_id}/audio.wav")
def get_sentence_audio(sentence_id: str) -> FileResponse:
    # A new voice of the same length gets the same `?v=`, so the browser must never reuse an old copy.
    return FileResponse(
        draft.sentence_audio(paths.project(), sentence_id), media_type="audio/wav", headers={"Cache-Control": "no-store"}
    )


@router.post("/draft-jobs", status_code=202)
def start_draft_job(body: dict[str, Any]) -> DraftJob:
    """The body depends on `kind` (spec › API), so the module checks it."""
    return draft.draft_jobs.start(body)


@router.get("/draft-jobs/current")
def get_current_draft_job() -> DraftJob | None:
    """The latest job, or null when none ran since the backend started."""
    return draft.draft_jobs.current()


@router.delete("/draft-jobs/current", status_code=202)
def cancel_draft_job() -> DraftJob:
    return draft.draft_jobs.cancel()


@router.get("/settings")
def get_settings() -> Settings:
    return settings.read(paths.project())


@router.patch("/settings")
def change_settings(body: dict[str, Any]) -> Settings:
    """Each field is optional and checked by the module (spec › ค่าที่จำไว้)."""
    return settings.change(paths.project(), body)


@router.post("/renders", status_code=202)
def start_render() -> RenderJob:
    """The body is `{}` (JSON, ADR 0013): a render takes the Spoil draft as it is."""
    return render.render_jobs.start()


@router.get("/renders/current")
def get_current_render() -> RenderJob | None:
    """The latest job, or null when none ran since the backend started."""
    return render.render_jobs.current()


@router.delete("/renders/current", status_code=202)
def cancel_render() -> RenderJob:
    return render.render_jobs.cancel()


@router.get("/renders")
def list_renders() -> list[RenderResult]:
    """Newest first."""
    return render.list_results(paths.project())


@router.get("/renders/{name}.mp4")
def get_render_video(name: str) -> FileResponse:
    """`FileResponse` answers `Range` with `206`, so the player can seek."""
    return FileResponse(render.result_file(paths.project(), name, ".mp4"), media_type="video/mp4")


@router.get("/renders/{name}.srt")
def get_render_subtitles(name: str) -> FileResponse:
    return FileResponse(
        render.result_file(paths.project(), name, ".srt"), media_type="application/x-subrip", filename=f"{name}.srt"
    )


@router.delete("/renders/{name}", status_code=204)
def delete_render(name: str) -> Response:
    render.delete_result(paths.project(), name)
    return Response(status_code=204)
