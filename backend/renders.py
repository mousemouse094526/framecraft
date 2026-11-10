"""What every render's results folder shares (spoil-maker spec › Render job, toon spec ›
Render job): a finished render is `{YYYYMMDD-HHMMSS}.mp4`, `.srt` and `.json` with no
`.partial` left, the json written last; a delete goes the other way round. spoil_maker's
render and toon's render keep their own folders and read them through this module; the rows
their Render jobs gate on are `gate_rows.render`."""

import json
import logging
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

from backend.errors import ApiError

log = logging.getLogger(__name__)

NAME_FORMAT = "%Y%m%d-%H%M%S"
RESULT_SUFFIXES = (".mp4", ".srt", ".json")

IN_USE = "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง"
NOT_FOUND = "ไม่พบผล render นี้"


def free_name(folder: Path) -> str:
    """`YYYYMMDD-HHMMSS` now, or the next free second (two renders in one second)."""
    moment = datetime.now()
    while any(folder.glob(f"{moment.strftime(NAME_FORMAT)}.*")):
        moment += timedelta(seconds=1)
    return moment.strftime(NAME_FORMAT)


def complete_names(folder: Path) -> list[str]:
    """The complete renders in the folder, newest first: only these names get near the disk."""
    if not folder.is_dir():
        return []
    found = {path.name.split(".")[0] for path in folder.glob("*.json")}
    return sorted((name for name in found if _is_name(name) and _complete(folder, name)), reverse=True)


def results(folder: Path) -> Iterator[tuple[str, dict, int]]:
    """Each complete render's name, its json and its mp4's size, newest first; an
    unreadable one is logged and skipped."""
    for name in complete_names(folder):
        try:
            info = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
            yield name, info, (folder / f"{name}.mp4").stat().st_size
        except (OSError, ValueError):
            log.warning("skipping unreadable render %s", name)


def latest_at(folder: Path) -> str | None:
    """When the folder's newest readable render was made."""
    return next((info["created_at"] for _, info, _ in results(folder) if isinstance(info, dict) and "created_at" in info), None)


def require(folder: Path, name: str) -> None:
    """Only a complete render's name gets near the disk. Raises `ApiError` 404 `not_found`."""
    if not (_is_name(name) and _complete(folder, name)):
        raise ApiError(404, "not_found", NOT_FOUND)


def delete(folder: Path, name: str) -> None:
    """A complete render's files: the mp4 first (a player may hold it open: `409` `in_use`),
    the json last. Raises `ApiError` 404 `not_found`, or 409 `in_use`."""
    require(folder, name)
    try:
        (folder / f"{name}.mp4").unlink(missing_ok=True)
    except PermissionError:
        raise ApiError(409, "in_use", IN_USE) from None
    (folder / f"{name}.srt").unlink(missing_ok=True)
    (folder / f"{name}.json").unlink(missing_ok=True)
    log.info("deleted render %s in %s", name, folder)


def remove_partials(folder: Path) -> None:
    """What a render cut short left: jobs don't survive a restart."""
    if folder.is_dir():
        for leftover in folder.glob("*.partial"):
            leftover.unlink(missing_ok=True)


def _complete(folder: Path, name: str) -> bool:
    return all((folder / f"{name}{suffix}").is_file() for suffix in RESULT_SUFFIXES) and not any(
        folder.glob(f"{name}.*.partial")
    )


def _is_name(name: str) -> bool:
    try:
        return datetime.strptime(name, NAME_FORMAT).strftime(NAME_FORMAT) == name
    except ValueError:
        return False
