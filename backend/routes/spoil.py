from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.spoil import jobs
from backend.spoil.jobs import DownloadJob, SpoilError

router = APIRouter(prefix="/spoil")


class DownloadRequest(BaseModel):
    url: str


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
