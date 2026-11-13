"""Drum lessons of the สอนกลอง tab (video-gen spec › Data, D10, D16, D20, D22).

A lesson is `media/drums/lessons/{lesson_id}/lesson.json`, written with `write_atomic`; its
renders sit in `renders/` beside it. Every read and write of the folder takes `_lock`.
A `lesson_id` is 12 letters `[a-z0-9]`: every function checks it before it builds a path,
so `..` never reaches the disk (D22).
"""

import json
import logging
import re
import secrets
import shutil
import string
import threading
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from backend import files, renders
from backend.checks import now_iso
from backend.errors import ApiError
from backend.json_values import is_int
from backend.paths import ProjectPaths
from backend.video_gen import kit, timeline

log = logging.getLogger(__name__)

VERSION = 1
ID_LENGTH = 12
ID_LETTERS = string.ascii_lowercase + string.digits
LESSON_ID = re.compile(f"[a-z0-9]{{{ID_LENGTH}}}")
# Letters are code points, `len` here and `[...text].length` on the page (story-kb D12).
TITLE_MAX = 40
LINE_MAX = 60  # subtitle, caption, a chapter's text
LABEL_MAX = 16
BPM_RANGE = (40, 240)
BARS_RANGE = (1, 4)
CHAPTERS_RANGE = (1, 6)
REPEATS_RANGE = (1, 8)
SPEED_RANGE = (50, 100)
SPEED_STEP = 5
COPY_SUFFIX = " (สำเนา)"
NEW_LABEL = "ลองเล่นเอง"  # the reference clip's "YOUR TURN." may be its page's trademark (D23)
MAX_LENGTH_S = 90  # listen and render refuse a longer clip; saving doesn't (D16)


class Note(BaseModel):
    piece: str
    step: int
    hand: Literal["R", "L"] | None
    hit: Literal["normal", "accent", "ghost", "flam"]


class Groove(BaseModel):
    bars: int
    notes: list[Note]


class Chapter(BaseModel):
    label: str  # shown in place of the title through the chapter; empty in the first = the title (D12)
    text: str
    focus: list[str]
    repeats: int
    speed: int


class LessonFields(BaseModel):
    """What `PUT` takes, checked (spec › Data)."""

    title: str
    subtitle: str
    caption: str
    bpm: int
    background: Literal["color", "image"]
    groove: Groove
    chapters: list[Chapter]


class Lesson(LessonFields):
    """One `lesson.json`."""

    version: int
    id: str
    updated_at: str


class LessonView(Lesson):
    """A lesson as the API answers it."""

    length_s: float


class LessonRow(BaseModel):
    """One row of `GET /api/drums/lessons`."""

    id: str
    title: str
    length_s: float
    renders: int
    updated_at: str


_lock = threading.Lock()


# --- Checking a body ---


def _checked_fields(body: dict[str, Any], lesson_dir: Path | None) -> LessonFields:
    """A body holding every field of spec › Data. Anything outside the rules raises `ApiError`
    400 `invalid_request` with the first failing `field` (`groove.notes[3]`). `background`
    `"image"` needs the lesson's `background.jpg`; a new lesson (`lesson_dir` None) has none."""
    title = _text(body, "title", 1, TITLE_MAX, "หัวเรื่อง")
    subtitle = _text(body, "subtitle", 0, LINE_MAX, "บรรทัดรอง")
    caption = _text(body, "caption", 0, LINE_MAX, "คำบรรยาย")
    bpm = _int(body, "bpm", BPM_RANGE, "BPM")
    background = body.get("background")
    if background not in ("color", "image"):
        raise _invalid("background", "พื้นหลังต้องเป็นสีหรือภาพ")
    if background == "image" and (lesson_dir is None or not (lesson_dir / "background.jpg").is_file()):
        raise _invalid("background", "ยังไม่มีภาพพื้นหลัง")
    groove = _checked_groove(body.get("groove"))
    chapters = _checked_chapters(body.get("chapters"))
    return LessonFields(
        title=title, subtitle=subtitle, caption=caption, bpm=bpm, background=background, groove=groove, chapters=chapters
    )


def _checked_groove(value: object) -> Groove:
    if not isinstance(value, dict):
        raise _invalid("groove", "Groove ไม่ถูกต้อง")
    bars = _int(value, "bars", BARS_RANGE, "จำนวนห้อง", field="groove.bars")
    asked = value.get("notes")
    if not isinstance(asked, list):
        raise _invalid("groove.notes", "โน้ตไม่ถูกต้อง")
    notes: list[Note] = []
    for index, item in enumerate(asked):
        field = f"groove.notes[{index}]"
        note = _note(item, field)
        if note.step >= bars * timeline.STEPS_PER_BAR:
            raise _invalid(field, "โน้ตเลยห้องสุดท้าย")
        problem = _clash(note, [other for other in notes if other.step == note.step])
        if problem:
            raise _invalid(field, problem)
        notes.append(note)
    return Groove(bars=bars, notes=notes)


def _note(item: object, field: str) -> Note:
    """One note on its own: a known piece, a step, the hand its piece takes, a hit a flam may be."""
    # Checked before pydantic, which would take `true` or `4.0` as a step.
    if not isinstance(item, dict) or not is_int(item.get("step")) or item["step"] < 0:
        raise _invalid(field, "โน้ตไม่ถูกต้อง")
    try:
        note = Note.model_validate(item)
    except ValidationError:
        raise _invalid(field, "โน้ตไม่ถูกต้อง") from None
    piece = kit.BY_ID.get(note.piece)
    if piece is None:
        raise _invalid(field, "ไม่รู้จักชิ้นกลองนี้")
    if piece.foot and note.hand is not None:
        raise _invalid(field, "ชิ้นของเท้าไม่มีไม้")
    if not piece.foot and note.hand is None:
        raise _invalid(field, "เลือกไม้ R หรือ L")
    if piece.foot and note.hit == "flam":
        raise _invalid(field, "flam ตีด้วยเท้าไม่ได้")
    return note


def _clash(note: Note, same_step: list[Note]) -> str | None:
    """Why `note` can't be played with the notes already in its step (D20), or None."""
    if any(other.piece == note.piece for other in same_step):
        return "ชิ้นนี้มีโน้ตในช่องนี้แล้ว"
    if note.hand is None:
        return None
    hands = [other for other in same_step if other.hand is not None]
    if any(other.hand == note.hand for other in hands):
        return f"ไม้ {note.hand} ตีสองชิ้นในช่องเดียวกันไม่ได้"
    if len(hands) >= 2:
        return "ช่องหนึ่งมีโน้ตมือได้ไม่เกินสองตัว"
    pieces = {note.piece} | {other.piece for other in hands}
    if {"hihat_open", "hihat_closed"} <= pieces:
        return "ไฮแฮทเปิดกับปิดอยู่ช่องเดียวกันไม่ได้"
    if hands and (note.hit == "flam" or any(other.hit == "flam" for other in hands)):
        return "flam ต้องเป็นโน้ตมือตัวเดียวของช่อง"
    return None


def _checked_chapters(value: object) -> list[Chapter]:
    if not isinstance(value, list) or not CHAPTERS_RANGE[0] <= len(value) <= CHAPTERS_RANGE[1]:
        raise _invalid("chapters", f"ท่อนสอนมีได้ {CHAPTERS_RANGE[0]}–{CHAPTERS_RANGE[1]} ท่อน")
    chapters = []
    for index, item in enumerate(value):
        field = f"chapters[{index}]"
        if not isinstance(item, dict):
            raise _invalid(field, "ท่อนสอนไม่ถูกต้อง")
        label = _text(item, "label", 0, LABEL_MAX, "ป้าย", field=f"{field}.label")
        text = _text(item, "text", 0, LINE_MAX, "คำอธิบาย", field=f"{field}.text")
        focus = item.get("focus")
        if (
            not isinstance(focus, list)
            or not all(piece in kit.BY_ID for piece in focus)
            or len(set(focus)) != len(focus)
        ):
            raise _invalid(f"{field}.focus", "ชิ้นที่เน้นไม่ถูกต้อง")
        repeats = _int(item, "repeats", REPEATS_RANGE, "รอบ", field=f"{field}.repeats")
        speed = _int(item, "speed", SPEED_RANGE, "ความเร็ว", field=f"{field}.speed")
        if speed % SPEED_STEP:
            raise _invalid(f"{field}.speed", f"ความเร็วต้องเป็นทีละ {SPEED_STEP}%")
        chapters.append(Chapter(label=label, text=text, focus=focus, repeats=repeats, speed=speed))
    return chapters


def _text(body: dict, key: str, low: int, high: int, name: str, field: str | None = None) -> str:
    """A one-line text: every run of spaces and line breaks made one space (story-kb D16)."""
    value = body.get(key)
    if not isinstance(value, str):
        raise _invalid(field or key, f"{name}ไม่ถูกต้อง")
    text = " ".join(value.split())
    if len(text) < low:
        raise _invalid(field or key, f"ใส่{name}")
    if len(text) > high:
        raise _invalid(field or key, f"{name}ยาวเกิน {high} ตัวอักษร")
    return text


def _int(body: dict, key: str, bounds: tuple[int, int], name: str, field: str | None = None) -> int:
    value = body.get(key)
    if not is_int(value) or not bounds[0] <= value <= bounds[1]:
        raise _invalid(field or key, f"{name}ต้องเป็นจำนวนเต็ม {bounds[0]}–{bounds[1]}")
    return value


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "invalid_request", message, field=field)


# --- The API ---


def list_rows(project: ProjectPaths) -> list[LessonRow]:
    """Every readable lesson, latest change first; a `lesson.json` that can't be read is
    logged and left out, and can still be deleted (D22)."""
    rows = []
    with _lock:
        folders = sorted(project.lessons_dir.iterdir()) if project.lessons_dir.is_dir() else []
        for folder in folders:
            if not LESSON_ID.fullmatch(folder.name):
                continue
            lesson = _read_folder(folder)
            if lesson is None:
                continue
            rows.append(
                LessonRow(
                    id=lesson.id,
                    title=lesson.title,
                    length_s=length_s(lesson),
                    renders=len(renders.complete_names(folder / "renders")),
                    updated_at=lesson.updated_at,
                )
            )
    rows.sort(key=lambda row: row.updated_at, reverse=True)
    return rows


def create(project: ProjectPaths, body: dict[str, Any]) -> LessonView:
    """`POST`: a lesson with the given title and the defaults of spec › Data (D22, D23)."""
    title = _text(body, "title", 1, TITLE_MAX, "หัวเรื่อง")
    fields = _new_fields(title)
    with _lock:
        lesson = _write_new(project, fields)
    log.info("created lesson %s", lesson.id)
    return _view(lesson)


def copy(project: ProjectPaths, lesson_id: str) -> LessonView:
    """`POST …/copy`: the lesson under a new id, its title ending " (สำเนา)" cut at 40; its
    background picture comes along, its renders don't (spec › API)."""
    with _lock:
        source = _read_known(project, lesson_id)
        title = (source.title + COPY_SUFFIX)[:TITLE_MAX]
        fields = LessonFields.model_validate(source.model_dump() | {"title": title})
        lesson = _write_new(project, fields, background=_folder(project, lesson_id) / "background.jpg")
    log.info("copied lesson %s to %s", lesson_id, lesson.id)
    return _view(lesson)


def get(project: ProjectPaths, lesson_id: str) -> LessonView:
    with _lock:
        return _view(_read_known(project, lesson_id))


def stored(project: ProjectPaths, lesson_id: str) -> Lesson:
    """The lesson as stored, without `length_s` (`get` is the API's view), for listen and render. Raises `ApiError` 404 `not_found`."""
    with _lock:
        return _read_known(project, lesson_id)


def replace(project: ProjectPaths, lesson_id: str, body: dict[str, Any]) -> LessonView:
    """`PUT`: every field but `id`, `version` and `updated_at`. A lesson over 90 s is saved
    (D16); a value outside the rules changes nothing."""
    with _lock:
        _read_known(project, lesson_id)
        fields = _checked_fields(body, _folder(project, lesson_id))
        lesson = Lesson(version=VERSION, id=lesson_id, updated_at=now_iso(), **fields.model_dump())
        _write(project, lesson)
    return _view(lesson)


def delete(project: ProjectPaths, lesson_id: str) -> None:
    """Each render (stopping at the first `in_use`; one deleted stays deleted), then
    `background.jpg`, then `lesson.json` last, then the folder. A `lesson.json` that can't be
    read is deleted all the same (D22)."""
    with _lock:
        folder = _folder(project, lesson_id)
        if not (folder / "lesson.json").is_file():
            raise _not_found()
        for name in renders.complete_names(folder / "renders"):
            renders.Render(folder / "renders", name).delete()
        (folder / "background.jpg").unlink(missing_ok=True)
        (folder / "lesson.json").unlink()
        shutil.rmtree(folder, ignore_errors=True)
    log.info("deleted lesson %s", lesson_id)


# --- Files; call with `_lock` held ---


def _new_fields(title: str) -> LessonFields:
    """A basic rock beat of one bar: closed hi-hat on every 8th with R, snare on 2 and 4 with
    L, kick on 1 and 3; two chapters, the first showing the title (spec › Data)."""
    hihats = [Note(piece="hihat_closed", step=step, hand="R", hit="normal") for step in range(0, 16, 2)]
    snares = [Note(piece="snare", step=step, hand="L", hit="normal") for step in (4, 12)]
    kicks = [Note(piece="kick", step=step, hand=None, hit="normal") for step in (0, 8)]
    return LessonFields(
        title=title,
        subtitle="",
        caption="",
        bpm=100,
        background="color",
        groove=Groove(bars=1, notes=kicks + hihats + snares),
        chapters=[
            Chapter(label="", text="", focus=[], repeats=2, speed=100),
            Chapter(label=NEW_LABEL, text="", focus=[], repeats=2, speed=100),
        ],
    )


def _write_new(project: ProjectPaths, fields: LessonFields, background: Path | None = None) -> Lesson:
    project.lessons_dir.mkdir(parents=True, exist_ok=True)
    while True:
        lesson_id = "".join(secrets.choice(ID_LETTERS) for _ in range(ID_LENGTH))
        try:
            _folder(project, lesson_id).mkdir()
            break
        except FileExistsError:
            continue
    if background is not None and background.is_file():
        shutil.copyfile(background, _folder(project, lesson_id) / "background.jpg")
    lesson = Lesson(version=VERSION, id=lesson_id, updated_at=now_iso(), **fields.model_dump())
    _write(project, lesson)
    return lesson


def _write(project: ProjectPaths, lesson: Lesson) -> None:
    text = json.dumps(lesson.model_dump(), ensure_ascii=False, indent=2)
    files.write_atomic(_folder(project, lesson.id) / "lesson.json", text)


def _folder(project: ProjectPaths, lesson_id: str) -> Path:
    require_id(lesson_id)
    return project.lessons_dir / lesson_id


def _read_known(project: ProjectPaths, lesson_id: str) -> Lesson:
    lesson = _read_folder(_folder(project, lesson_id))
    if lesson is None:
        raise _not_found()
    return lesson


def _read_folder(folder: Path) -> Lesson | None:
    """The folder's lesson; None with no file, and a log line for one that can't be read."""
    path = folder / "lesson.json"
    try:
        return Lesson.model_validate_json(path.read_bytes())
    except FileNotFoundError:
        return None
    except (OSError, ValidationError) as error:
        log.warning("lesson %s can't be read: %s", folder.name, type(error).__name__)
        return None


def _view(lesson: Lesson) -> LessonView:
    return LessonView(**lesson.model_dump(), length_s=length_s(lesson))


def require_id(lesson_id: str) -> None:
    """Raises `ApiError` 404 `not_found` for an id that isn't ID_LENGTH of `[a-z0-9]` (D22)."""
    if not LESSON_ID.fullmatch(lesson_id):
        raise _not_found()


def length_s(lesson: Lesson) -> float:
    return timeline.length_s(lesson.bpm, lesson.groove.bars, lesson.chapters)


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "ไม่พบบทเรียนนี้")
