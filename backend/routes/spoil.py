from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend import paths
from backend.paths import ProjectPaths
from backend.spoil import clips, jobs
from backend.spoil.clips import TempClip
from backend.spoil.errors import SpoilError
from backend.spoil.jobs import DownloadJob

router = APIRouter(prefix="/spoil")


class DownloadRequest(BaseModel):
    url: str


class ClipList(BaseModel):
    clips: list[TempClip]


def _project() -> ProjectPaths:
    # Read per request: tests point `paths.ROOT` at a fake root.
    return ProjectPaths(paths.ROOT)


@router.get("/clips")
def list_clips() -> ClipList:
    return ClipList(clips=clips.list_clips(_project()))


@router.get("/clips/{clip_id}/video")
def get_video(clip_id: str) -> FileResponse:
    """FileResponse answers `Range` with 206, so the player can seek."""
    return FileResponse(clips.video_file(_project(), clip_id), media_type="video/mp4")


@router.get("/clips/{clip_id}/thumbnail")
def get_thumbnail(clip_id: str) -> FileResponse:
    return FileResponse(clips.thumbnail_file(_project(), clip_id))


@router.delete("/clips/{clip_id}", status_code=204)
def delete_clip(clip_id: str) -> Response:
    clips.delete_clip(_project(), clip_id)
    return Response(status_code=204)


@router.post("/downloads", status_code=202)
def start_download(body: DownloadRequest) -> DownloadJob:
    return jobs.downloads.start(body.url)


@router.get("/downloads/current")
def get_current_download() -> DownloadJob | None:
    """The latest job, or null when none ran since the backend started."""
    return jobs.downloads.current()


@router.delete("/downloads/current", status_code=202)
def cancel_download() -> DownloadJob:
    return jobs.downloads.cancel()


def spoil_error_response(request: Request, error: SpoilError) -> JSONResponse:
    """Registered in app.py: every refusal is `{"code", "message"}` plus any extra field."""
    return JSONResponse(
        status_code=error.status,
        content={"code": error.code, "message": error.message, **error.extra},
    )
