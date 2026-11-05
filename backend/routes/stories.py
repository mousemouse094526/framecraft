from typing import Any

from fastapi import APIRouter, Response

from backend import paths, stories
from backend.stories import StoryRow, StoryView

router = APIRouter(prefix="/stories")
# Its own prefix, so no `{story_id}` path meets it (story-kb spec › API).
clips_router = APIRouter(prefix="/story-clips")


@router.get("")
def list_stories() -> list[StoryRow]:
    return stories.list_rows(paths.project())


# Any JSON: a bad value is `invalid_story` with its field, not a validation error.
@router.post("", status_code=201)
def create_story(body: dict[str, Any]) -> StoryView:
    return stories.create(paths.project(), body)


@router.get("/{story_id}")
def get_story(story_id: str) -> StoryView:
    return stories.get(paths.project(), story_id)


@router.put("/{story_id}")
def replace_story(story_id: str, body: dict[str, Any]) -> StoryView:
    return stories.replace(paths.project(), story_id, body)


@router.delete("/{story_id}", status_code=204)
def delete_story(story_id: str) -> Response:
    stories.delete(paths.project(), story_id)
    return Response(status_code=204)


@clips_router.get("")
def get_clip_stories() -> dict[str, str]:
    """`{clip_id: story_id}`: the Story each clip remembers."""
    return stories.clip_stories(paths.project())
