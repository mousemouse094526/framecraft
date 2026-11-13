from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import FileResponse, JSONResponse

from backend import body_types, paths
from backend.drum_notes import imports, songs
from backend.drum_notes.imports import SongImport
from backend.drum_notes.songs import KnownSong, Song, SongRow
from backend.uploads import UploadCheck

router = APIRouter(prefix="/songs")


@router.get("")
def list_songs() -> list[SongRow]:
    return songs.list_rows(paths.project())


# The static paths come before `/{song_id}`, so `import` and `check` are never read as an id.


@router.post("/link", response_model=None)
def start_link(body: dict[str, Any]) -> Response:
    """`202` with the job, or `200` with the song's id when a YouTube link is a song already (D3): the module says which."""
    status, content = imports.song_imports.start(body)
    return JSONResponse(status_code=status, content=content)


@router.get("/import")
def get_import() -> SongImport | None:
    """The latest link import, or null when none ran since the backend started."""
    return imports.song_imports.current()


@router.post("/import/cancel")
def cancel_import(body: dict[str, Any]) -> SongImport:
    """The body is `{}` (ADR 0013: every POST takes a JSON object); nothing in it is read."""
    return imports.song_imports.cancel()


@router.post("/check")
def check_file(body: dict[str, Any]) -> UploadCheck | KnownSong:
    return imports.song_imports.check(body)


@router.put("", status_code=201, dependencies=[Depends(body_types.require_octet_stream)])
async def put_file(request: Request, name: str | None = None, size: str | None = None) -> Song:
    """The body is the file itself (ADR 0028); `name` and `size` stay text so the module answers a
    bad one with its own code."""
    return await imports.song_imports.receive(name, size, request.stream(), request.is_disconnected)


@router.get("/{song_id}")
def get_song(song_id: str) -> Song:
    return songs.get(paths.project(), song_id)


@router.delete("/{song_id}", status_code=204)
def delete_song(song_id: str) -> Response:
    songs.delete(paths.project(), song_id)
    return Response(status_code=204)


@router.get("/{song_id}/audio.m4a")
def get_audio(song_id: str) -> FileResponse:
    """`FileResponse` answers `Range` with `206`, so the player can seek."""
    return FileResponse(songs.audio_file(paths.project(), song_id), media_type="audio/mp4")
