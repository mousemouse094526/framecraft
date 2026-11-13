from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse

from backend import body_types, paths
from backend.uploads import UploadCheck
from backend.video_gen import backgrounds, lessons, mixer, render
from backend.video_gen.lessons import LessonRow, LessonView
from backend.video_gen.render import DrumRenderJob, RenderResult

router = APIRouter(prefix="/drums")


@router.get("/lessons")
def list_lessons() -> list[LessonRow]:
    return lessons.list_rows(paths.project())


# Any JSON: a bad value is `invalid_request` with its field, not a validation error.
@router.post("/lessons", status_code=201)
def create_lesson(body: dict[str, Any]) -> LessonView:
    return lessons.create(paths.project(), body)


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str) -> LessonView:
    return lessons.get(paths.project(), lesson_id)


@router.put("/lessons/{lesson_id}")
def replace_lesson(lesson_id: str, body: dict[str, Any]) -> LessonView:
    return lessons.replace(paths.project(), lesson_id, body)


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: str) -> Response:
    lessons.delete(paths.project(), lesson_id)
    return Response(status_code=204)


@router.post("/lessons/{lesson_id}/copy", status_code=201)
def copy_lesson(lesson_id: str) -> LessonView:
    return lessons.copy(paths.project(), lesson_id)


@router.post("/lessons/{lesson_id}/background/check")
def check_background(lesson_id: str, body: dict[str, Any]) -> UploadCheck:
    return backgrounds.check_upload(paths.project(), lesson_id, body)


@router.put("/lessons/{lesson_id}/background", dependencies=[Depends(body_types.require_octet_stream)])
async def put_background(lesson_id: str, request: Request, size: str | None = None) -> LessonView:
    """The body is the picture itself (ADR 0028); `size` stays text so the module answers a
    bad one with `invalid_request`."""
    return await backgrounds.receive_upload(paths.project(), lesson_id, size, request.stream())


@router.delete("/lessons/{lesson_id}/background")
def delete_background(lesson_id: str) -> LessonView:
    return backgrounds.remove(paths.project(), lesson_id)


@router.get("/lessons/{lesson_id}/background.jpg")
def get_background(lesson_id: str) -> FileResponse:
    """The page asks with `?v={updated_at}`, so a new picture is a new URL."""
    return FileResponse(lessons.background_file(paths.project(), lesson_id), media_type="image/jpeg")


@router.post("/lessons/{lesson_id}/listen")
def listen(lesson_id: str) -> Response:
    """The clip's drum sound, never cached: the lesson may change before the next press (D8)."""
    wav = mixer.listen(paths.project(), lesson_id)
    return Response(wav, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.post("/render", status_code=202)
def start_render(body: dict[str, Any]) -> DrumRenderJob:
    return render.render_jobs.start(body)


@router.get("/render")
def get_render() -> DrumRenderJob | None:
    """The latest job, or null when none ran since the backend started."""
    return render.render_jobs.current()


@router.post("/render/cancel")
def cancel_render(body: dict[str, Any]) -> DrumRenderJob:
    return render.render_jobs.cancel()


@router.get("/lessons/{lesson_id}/renders")
def list_renders(lesson_id: str) -> list[RenderResult]:
    """Newest first."""
    return render.list_results(paths.project(), lesson_id)


@router.get("/lessons/{lesson_id}/renders/{name}.mp4")
def get_render_video(lesson_id: str, name: str) -> FileResponse:
    """`FileResponse` answers `Range` with `206`, so the player can seek."""
    return FileResponse(render.result_file(paths.project(), lesson_id, name, ".mp4"), media_type="video/mp4")


@router.get("/lessons/{lesson_id}/renders/{name}.srt")
def get_render_subtitles(lesson_id: str, name: str) -> FileResponse:
    path = render.result_file(paths.project(), lesson_id, name, ".srt")
    return FileResponse(path, media_type="application/x-subrip", filename=f"{name}.srt")


@router.delete("/lessons/{lesson_id}/renders/{name}", status_code=204)
def delete_render(lesson_id: str, name: str) -> Response:
    render.delete_result(paths.project(), lesson_id, name)
    return Response(status_code=204)
