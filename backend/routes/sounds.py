from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse

from backend import body_types, paths, sounds
from backend.sounds import Legacy, SoundImport, SoundView
from backend.uploads import UploadCheck

router = APIRouter(prefix="/sounds")


@router.get("")
def list_sounds() -> list[SoundView]:
    return sounds.list_all(paths.project())


# Before `/{sound_id}` routes: `legacy` is no sound's id, but a `GET /{sound_id}` added later would take it.
@router.get("/legacy")
def get_legacy() -> Legacy:
    """The old library's folder while start-up could not move all of it (spec › ข้อมูล, D10)."""
    return sounds.legacy(paths.project())


@router.patch("/{sound_id}")
def rename_sound(sound_id: str, body: dict[str, Any]) -> SoundView:
    return sounds.rename(paths.project(), sound_id, body)


@router.delete("/{sound_id}", status_code=204)
def delete_sound(sound_id: str) -> Response:
    sounds.delete(paths.project(), sound_id)
    return Response(status_code=204)


@router.get("/{sound_id}/file")
def get_sound_file(sound_id: str) -> FileResponse:
    return FileResponse(sounds.sound_file(paths.project(), sound_id), media_type="audio/mp4")


# A Sound import (toon spec › API): a file is `/imports` (one request), a link `/downloads` (a job);
# `/import/current` is the latest link's, the only one that runs on after its request.
@router.post("/imports/check")
def check_sound_import(body: dict[str, Any]) -> UploadCheck:
    return sounds.sound_imports.check(body)


@router.post("/imports", status_code=201, dependencies=[Depends(body_types.require_octet_stream)])
async def import_sound(request: Request, name: str | None = None, size: str | None = None) -> SoundView:
    """The body is the sound file itself (ADR 0028)."""
    return await sounds.sound_imports.receive(name, size, request.stream(), request.is_disconnected)


@router.post("/downloads", status_code=202)
def download_sound(body: dict[str, Any]) -> SoundImport:
    return sounds.sound_imports.start(body)


@router.get("/import/current")
def get_current_sound_import() -> SoundImport | None:
    """The latest link import, or null when none ran since the backend started."""
    return sounds.sound_imports.current()


@router.delete("/import/current", status_code=202)
def cancel_sound_import() -> SoundImport:
    return sounds.sound_imports.cancel()
