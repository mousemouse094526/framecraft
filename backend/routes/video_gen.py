from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from backend import paths
from backend.video_gen import lessons, mixer, render
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
