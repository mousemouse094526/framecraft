from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import paths
from backend.paths import ProjectPaths
from backend.spoil_maker import describe
from backend.spoil_maker.describe import DescribeJob
from backend.spoil_maker.shots import ShotsFile

router = APIRouter(prefix="/spoil-maker")


class DescribeRequest(BaseModel):
    clip_id: str


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
