"""What the สปอย tab remembers between drafts: `media/spoil-maker/settings.json`
(spoil-maker spec › ค่าที่จำไว้, D40, D45).

This ticket reads it and writes `original_volume` and `last_voice_id`; watermarks
and `PATCH /settings` come with the Render job.
"""

import logging
import threading

from pydantic import BaseModel, ValidationError

from backend import files
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

VOLUME_STEP = 5  # 0–100 in steps of 5 (spec › ค่าที่จำไว้)


class Settings(BaseModel):
    watermarks: list[dict] = []  # `{text, position, size}`, checked when the Render job sets them
    original_volume: int = 20  # D40
    last_voice_id: str | None = None


# One read-change-write at a time: a draft's `original_volume` and a finished Draft job both write.
_lock = threading.Lock()


def read(project: ProjectPaths) -> Settings:
    """The remembered values; a missing or unreadable file gives the defaults."""
    path = project.settings_file
    if not path.is_file():
        return Settings()
    try:
        return Settings.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        log.warning("using default settings: %s can't be read", path.name)
        return Settings()


def remember(project: ProjectPaths, **fields: object) -> Settings:
    """Writes the given fields, keeping the rest."""
    with _lock:
        settings = read(project).model_copy(update=fields)
        project.spoil_maker_dir.mkdir(parents=True, exist_ok=True)
        files.write_atomic(project.settings_file, settings.model_dump_json(indent=2))
        return settings


def is_volume(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100 and value % VOLUME_STEP == 0
