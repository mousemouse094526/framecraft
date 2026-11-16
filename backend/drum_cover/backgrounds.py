"""A reel cover's background picture (drum-cover D8, D21; video-gen D6, D36, D37; ADR 0028): the
page checks the size, then sends the PNG or JPEG as the raw body; `backend.pictures` crops it to
1080×1920 and it is kept as the song's `cover-background.jpg`, the cover's `background` then
`image`. Neither changes while the song's reel renders or its notes are picked (`song_busy`).
A render blurs and darkens it, as a lesson's.
"""

import logging
import os
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import anyio

from backend import disk, pictures, uploads
from backend.checks import now_iso
from backend.drum_cover import cover, render
from backend.drum_cover.cover import Cover, CoverView
from backend.drum_notes import songs
from backend.errors import ApiError
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

SONG_BUSY = "กำลัง render reel ของเพลงนี้อยู่"


def check_upload(project: ProjectPaths, song_id: str, body: dict) -> uploads.UploadCheck:
    """The upload's checks before the page sends the body (ADR 0028)."""
    return uploads.UploadCheck(size=_upload_checks(project, song_id, body.get("size")))


async def receive_upload(project: ProjectPaths, song_id: str, size: str | None, body: AsyncIterator[bytes]) -> CoverView:
    """The checks again, then the picture through `pictures.receive` and into the song's folder."""
    expected = uploads.whole_number(size)
    await anyio.to_thread.run_sync(_upload_checks, project, song_id, expected)
    # Not `{song_id}.…`: a Song import's leftovers go by that name in the same `.partial/` (D21).
    partial = project.songs_partial_dir / f"cover-background.{secrets.token_hex(4)}.tmp"
    view = await pictures.receive(body, partial, expected, lambda picture: set_background(project, song_id, picture))
    log.info("took a background picture for the reel cover of song %s", song_id)
    return view


def remove(project: ProjectPaths, song_id: str) -> CoverView:
    """`DELETE …/background`: back to the app's colours; no picture is no error."""
    view = set_background(project, song_id, None)
    log.info("removed the reel cover background of song %s", song_id)
    return view


def background_file(project: ProjectPaths, song_id: str) -> Path:
    """The cropped picture. Raises `ApiError` 404 for no song or no picture."""
    with songs.lock:
        songs.read_under_lock(project, song_id)
        path = songs.checked_dir(project, song_id) / cover.BACKGROUND
        if not path.is_file():
            raise ApiError(404, "not_found", cover.NO_PICTURE)
    return path


def set_background(project: ProjectPaths, song_id: str, picture: Path | None) -> CoverView:
    """`picture` (a finished jpg on the songs' disk, so this is a rename) becomes `cover-background.jpg`
    and the cover's `background` `image`; None removes it and makes it `color`. A cover never saved
    is saved with its defaults then. Raises `ApiError` 404, 409 `no_analysis`, or 409 `song_busy`,
    and then `picture` stays for the caller."""
    with songs.lock:
        song = songs.read_under_lock(project, song_id)
        _require_idle(song)
        folder = songs.checked_dir(project, song_id)
        fields = cover.used(project, song, check_sound=False)
        saved = Cover(version=cover.VERSION, updated_at=now_iso(), **(fields.model_dump() | {"background": "color" if picture is None else "image"}))
        # The json first: a cover saying `image` with no picture reads as `color` (`cover.view`), never the other way.
        cover.write(project, song_id, saved)
        if picture is None:
            (folder / cover.BACKGROUND).unlink(missing_ok=True)
        else:
            os.replace(picture, folder / cover.BACKGROUND)
        return cover.view(project, song, saved)


def _upload_checks(project: ProjectPaths, song_id: str, size: object) -> int:
    size = pictures.checked_size(size)
    with songs.lock:
        _require_idle(songs.read_under_lock(project, song_id))
    disk.require_free(project.root, size)
    return size


def _require_idle(song: songs.Song) -> None:
    """The song is picked, and neither its reel renders (this message) nor its notes are picked (drum-notes'). Call with `songs.lock` held."""
    cover.require_analysis(song)
    if render.render_jobs.song_use() == song.id:
        raise ApiError(409, "song_busy", SONG_BUSY)
    songs.require_idle(song.id)
