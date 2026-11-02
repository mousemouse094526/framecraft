from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import paths
from backend.paths import ProjectPaths
from backend.spoil_maker import describe, voices
from backend.spoil_maker.describe import DescribeJob
from backend.spoil_maker.shots import ShotsFile
from backend.spoil_maker.voices import Voice, VoiceJob

router = APIRouter(prefix="/spoil-maker")


class DescribeRequest(BaseModel):
    clip_id: str


class VoiceName(BaseModel):
    # Any JSON: a missing or non-text name is `invalid_voice`, not a validation error.
    name: Any = None


def _project() -> ProjectPaths:
    # Read per request: tests point `paths.ROOT` at a fake root.
    return ProjectPaths(paths.ROOT)


@router.get("/clips/{clip_id}/shots")
def get_shots(clip_id: str) -> ShotsFile:
    return describe.clip_shots(_project(), clip_id)


@router.get("/clips/{clip_id}/shots/{name}")
def get_shot_image(clip_id: str, name: str) -> FileResponse:
    return FileResponse(describe.shot_image(_project(), clip_id, name), media_type="image/jpeg")


@router.post("/describes", status_code=202)
def start_describe(body: DescribeRequest) -> DescribeJob:
    return describe.describes.start(body.clip_id)


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
    return voices.list_voices(_project())


@router.post("/voices", status_code=201)
def save_voice(body: VoiceName) -> Voice:
    return voices.save_preview(_project(), body.name)


@router.patch("/voices/{voice_id}")
def rename_voice(voice_id: str, body: VoiceName) -> Voice:
    return voices.rename(_project(), voice_id, body.name)


@router.delete("/voices/{voice_id}", status_code=204)
def delete_voice(voice_id: str) -> Response:
    voices.delete(_project(), voice_id)
    return Response(status_code=204)


@router.get("/voices/{voice_id}/sample.wav")
def get_voice_sample(voice_id: str) -> FileResponse:
    return FileResponse(voices.sample_audio(_project(), voice_id), media_type="audio/wav")


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
    return FileResponse(voices.preview_audio(_project()), media_type="audio/wav")
