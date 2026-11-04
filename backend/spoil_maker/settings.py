"""What the สปอย tab remembers between drafts: `media/spoil-maker/settings.json`
(spoil-maker spec › ค่าที่จำไว้, D40, D45).

`PATCH /settings` changes `watermarks` and `original_volume`; a draft's volume, a
finished Draft job's voice and the minutes of the latest EP cut are written here too.
"""

import logging
import threading

from typing import Literal

from pydantic import BaseModel, ValidationError

from backend import files
from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.spoil_maker import thai
from backend.spoil_maker.json_values import is_int

log = logging.getLogger(__name__)

VOLUME_STEP = 5  # 0–100 in steps of 5 (spec › ค่าที่จำไว้)
WATERMARKS_MAX = 6  # D41
WATERMARK_TEXT_MAX = 40  # letters that take space

Position = Literal["top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right"]
Size = Literal["small", "medium"]
POSITIONS: tuple[Position, ...] = ("top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right")
SIZES: tuple[Size, ...] = ("small", "medium")


class Watermark(BaseModel):
    text: str
    position: Position
    size: Size
    enabled: bool = True  # off: remembered, not drawn; a file from before D64 has none


class Settings(BaseModel):
    watermarks: list[Watermark] = []  # every render's, not the draft's (spec › ค่าที่จำไว้)
    original_volume: int = 20  # D40
    last_voice_id: str | None = None
    ep_minutes: int = 30  # how long an EP is when a clip is first cut (D69)


# One read-change-write at a time: a draft's `original_volume`, a finished Draft job and an EP cut all write (D71).
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


def change(project: ProjectPaths, body: dict) -> Settings:
    """`PATCH /settings`: `watermarks` and `original_volume`, each optional. Raises
    `ApiError` 400 `invalid_settings` for anything outside the table, writing nothing."""
    unknown = set(body) - {"watermarks", "original_volume"}
    fields: dict[str, object] = {}
    if "watermarks" in body:
        fields["watermarks"] = _watermarks(body["watermarks"])
    if "original_volume" in body:
        if not is_volume(body["original_volume"]):
            raise _invalid("เสียงต้นฉบับต้องเป็น 0–100 ทีละ 5")
        fields["original_volume"] = body["original_volume"]
    if unknown:
        raise _invalid(f"แก้ได้แค่ลายน้ำและเสียงต้นฉบับ ไม่ใช่ {', '.join(sorted(unknown))}")
    return remember(project, **fields)


def _watermarks(value: object) -> list[Watermark]:
    # Switched-off ones count too (D64).
    if not isinstance(value, list) or len(value) > WATERMARKS_MAX:
        raise _invalid(f"ลายน้ำมีได้ไม่เกิน {WATERMARKS_MAX} อัน")
    checked = []
    for mark in value:
        if not isinstance(mark, dict) or mark.get("position") not in POSITIONS or mark.get("size") not in SIZES:
            raise _invalid("ลายน้ำแต่ละอันต้องมีข้อความ ตำแหน่ง และขนาดจากรายการ")
        text = " ".join(mark["text"].split()) if isinstance(mark.get("text"), str) else ""
        if not 1 <= thai.width(text) <= WATERMARK_TEXT_MAX:
            raise _invalid(f"ข้อความลายน้ำต้องยาว 1–{WATERMARK_TEXT_MAX} ตัวอักษร")
        mark_fields = {"text": text, "position": mark["position"], "size": mark["size"]}
        if "enabled" in mark:  # left out: the model's default, as in a file from before D64
            if not isinstance(mark["enabled"], bool):
                raise _invalid("สวิตช์ลายน้ำต้องเป็นเปิดหรือปิด")
            mark_fields["enabled"] = mark["enabled"]
        checked.append(Watermark(**mark_fields))
    return checked


def _invalid(message: str) -> ApiError:
    return ApiError(400, "invalid_settings", message)


def is_volume(value: object) -> bool:
    return is_int(value) and 0 <= value <= 100 and value % VOLUME_STEP == 0
