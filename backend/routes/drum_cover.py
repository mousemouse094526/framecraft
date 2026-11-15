from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse

from backend import body_types, paths
from backend.drum_cover import audio, backgrounds, cover, render
from backend.drum_cover.cover import CoverView
from backend.drum_cover.render import CoverRenderJob, CoverRenderResult
from backend.uploads import UploadCheck

# No prefix: a cover's routes sit under its song, the job of the whole tab under `/covers` (D12).
router = APIRouter()


@router.get("/songs/{song_id}/cover")
def get_cover(song_id: str) -> CoverView:
    return cover.get(paths.project(), song_id)


# Any JSON: a bad value is `invalid_request` with its field, not a validation error.
@router.put("/songs/{song_id}/cover")
def replace_cover(song_id: str, body: dict[str, Any]) -> CoverView:
    return cover.replace(paths.project(), song_id, body)


@router.post("/songs/{song_id}/cover/background/check")
def check_background(song_id: str, body: dict[str, Any]) -> UploadCheck:
    return backgrounds.check_upload(paths.project(), song_id, body)


@router.put("/songs/{song_id}/cover/background", dependencies=[Depends(body_types.require_octet_stream)])
async def put_background(song_id: str, request: Request, size: str | None = None) -> CoverView:
    """The body is the picture itself (ADR 0028); `size` stays text so the module answers a
    bad one with `invalid_request`."""
    return await backgrounds.receive_upload(paths.project(), song_id, size, request.stream())


@router.delete("/songs/{song_id}/cover/background")
def delete_background(song_id: str) -> CoverView:
    return backgrounds.remove(paths.project(), song_id)


@router.get("/songs/{song_id}/cover/background.jpg")
def get_background(song_id: str) -> FileResponse:
    """The page asks with `?v={updated_at}`, so a new picture is a new URL."""
    return FileResponse(backgrounds.background_file(paths.project(), song_id), media_type="image/jpeg")


@router.post("/songs/{song_id}/cover/listen")
def listen(song_id: str, body: dict[str, Any]) -> Response:
    """The reel's sound from the saved cover, never cached: it may change before the next press (D17)."""
    wav = audio.listen(paths.project(), song_id)
    return Response(wav, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.post("/songs/{song_id}/cover/render", status_code=202)
def start_render(song_id: str, body: dict[str, Any]) -> CoverRenderJob:
    """The body is `{}` (ADR 0013); the cover played is the saved one."""
    return render.render_jobs.start(song_id)


@router.get("/covers/render")
def get_render() -> CoverRenderJob | None:
    """The latest job, or null when none ran since the backend started."""
    return render.render_jobs.current()


@router.post("/covers/render/cancel")
def cancel_render(body: dict[str, Any]) -> CoverRenderJob:
    return render.render_jobs.cancel()


@router.get("/songs/{song_id}/cover/renders")
def list_renders(song_id: str) -> list[CoverRenderResult]:
    """Newest first."""
    return render.list_results(paths.project(), song_id)


@router.get("/songs/{song_id}/cover/renders/{name}.mp4")
def get_render_video(song_id: str, name: str) -> FileResponse:
    """`FileResponse` answers `Range` with `206`, so the player can seek."""
    return FileResponse(render.result_file(paths.project(), song_id, name, ".mp4"), media_type="video/mp4")


@router.get("/songs/{song_id}/cover/renders/{name}.srt")
def get_render_subtitles(song_id: str, name: str) -> FileResponse:
    path = render.result_file(paths.project(), song_id, name, ".srt")
    return FileResponse(path, media_type="application/x-subrip", filename=f"{name}.srt")


@router.delete("/songs/{song_id}/cover/renders/{name}", status_code=204)
def delete_render(song_id: str, name: str) -> Response:
    render.delete_result(paths.project(), song_id, name)
    return Response(status_code=204)
