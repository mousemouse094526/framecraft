from typing import Any

from fastapi import APIRouter, Response

from backend import paths
from backend.video_gen import lessons, mixer
from backend.video_gen.lessons import LessonRow, LessonView

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
