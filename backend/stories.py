"""Stories of the คลังความรู้ tab and the Story each Temp clip remembers (story-kb, ADR 0023).

Every file lives in `media/stories/`: a Story is `{story_id}.json`, and
`clip-stories.json` maps a clip to the Story it remembers (spec › Data, D12).
Every read and write of that folder takes `_lock`, the innermost lock of the
backend: nothing else is locked while it is held (D16).

Rules are in docs/features/story-kb/spec.md › Data, › API and › Ops. Logs carry a
Story's id only, never its article or character names (spec › Ops).
"""

import json
import logging
import re
import secrets
import threading
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import BaseModel, ValidationError

from backend import files, qwen_tokens
from backend.checks import now_iso
from backend.errors import ApiError, invalid_request
from backend.paths import ProjectPaths

log = logging.getLogger(__name__)

STORY_ID = re.compile(r"st_[0-9a-f]{8}")
# Letters are code points, `len` here and `[...text].length` on the page (D12).
TITLE_MAX = 100
ARTICLE_MAX = 5_000
CHARACTERS_MAX = 30
NAME_MAX = 40
DESCRIPTION_MAX = 200

BLOCK_HEAD = (
    "ข้อมูลพื้นหลังของเรื่อง (ใช้เข้าใจเรื่องและสะกดชื่อเท่านั้น ห้ามเล่าเหตุการณ์จากส่วนนี้ "
    "เหตุการณ์ต้องมาจากบรรทัดของ Transcript):"
)
CHARACTERS_HEAD = "ตัวละคร (เขียนชื่อตามนี้ แม้ Transcript สะกดต่าง):"


class Character(BaseModel):
    name: str
    description: str = ""


class StoryFields(BaseModel):
    """What `POST` and `PUT` take, checked and cleaned (spec › Data)."""

    title: str
    article: str = ""
    characters: list[Character] = []


class Story(StoryFields):
    """One `{story_id}.json`."""

    id: str
    created_at: str
    updated_at: str


class StoryView(Story):
    """A Story as the API answers it."""

    clips: int  # how many clips remember it


class StoryRow(BaseModel):
    """One row of `GET /api/stories`."""

    id: str
    title: str
    characters: int
    clips: int
    tokens: int | None  # the Story block's; None without Qwen's tokenizer (D14)
    updated_at: str


_lock = threading.Lock()


# --- Checking a body ---


def _checked_fields(body: dict[str, Any]) -> StoryFields:
    """The body cleaned: single-line fields have every run of spaces and line breaks made
    one space (D16), the article is trimmed only. A body that isn't an object or a field
    of the wrong type raises `ApiError` 400 `invalid_request`; a value outside the rules,
    400 `invalid_story` with the first failing `field` (spec › Data, D17)."""
    title = _one_line(_text(body, "title"))
    article = _text(body, "article").strip()
    asked = body.get("characters", [])
    if not isinstance(asked, list) or not all(isinstance(character, dict) for character in asked):
        raise invalid_request()
    characters = [
        Character(name=_one_line(_text(character, "name")), description=_one_line(_text(character, "description")))
        for character in asked
    ]

    if not title:
        raise _invalid("title", "ใส่ชื่อเรื่อง")
    if len(title) > TITLE_MAX:
        raise _invalid("title", f"ชื่อเรื่องยาวเกิน {TITLE_MAX} ตัวอักษร")
    if len(article) > ARTICLE_MAX:
        raise _invalid("article", f"บทความยาวเกิน {ARTICLE_MAX:,} ตัวอักษร")
    if len(characters) > CHARACTERS_MAX:
        raise _invalid("characters", f"ตัวละครได้ไม่เกิน {CHARACTERS_MAX} ตัว")
    seen: set[str] = set()
    for index, character in enumerate(characters):
        if not character.name:
            raise _invalid(f"characters.{index}.name", "ใส่ชื่อตัวละคร")
        if len(character.name) > NAME_MAX:
            raise _invalid(f"characters.{index}.name", f"ชื่อตัวละครยาวเกิน {NAME_MAX} ตัวอักษร")
        if character.name.casefold() in seen:
            raise _invalid(f"characters.{index}.name", "ชื่อตัวละครซ้ำ")
        seen.add(character.name.casefold())
        if len(character.description) > DESCRIPTION_MAX:
            raise _invalid(f"characters.{index}.description", f"คำอธิบายยาวเกิน {DESCRIPTION_MAX} ตัวอักษร")
    return StoryFields(title=title, article=article, characters=characters)


def _text(body: dict, key: str) -> str:
    """A text field; left out is empty (spec › API)."""
    value = body.get(key, "")
    if not isinstance(value, str):
        raise invalid_request()
    return value


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(400, "invalid_story", message, field=field)


# --- The API ---


def list_rows(project: ProjectPaths) -> list[StoryRow]:
    """Every readable Story, latest change first; Stories changed in the same second by
    their files' modification time."""
    with _lock:
        found = _read_all(project)
        remembered = _remembered(project)
    found.sort(key=lambda entry: (entry.story.updated_at, entry.modified_ns), reverse=True)
    return [
        StoryRow(
            id=story.id,
            title=story.title,
            characters=len(story.characters),
            clips=remembered[story.id],
            tokens=_tokens(project, story),
            updated_at=story.updated_at,
        )
        for story, _ in found
    ]


def create(project: ProjectPaths, body: dict[str, Any]) -> StoryView:
    fields = _checked_fields(body)
    with _lock:
        project.stories_dir.mkdir(parents=True, exist_ok=True)
        story_id = _new_id(project)
        at = now_iso()
        story = Story(id=story_id, created_at=at, updated_at=at, **fields.model_dump())
        _write(project, story)
        view = _view(story, _remembered(project))
    log.info("created story %s", story_id)
    return view


def get(project: ProjectPaths, story_id: str) -> StoryView:
    with _lock:
        return _view(_read_known(project, story_id), _remembered(project))


def replace(project: ProjectPaths, story_id: str, body: dict[str, Any]) -> StoryView:
    """`PUT`: the whole Story but its id and `created_at`; the body is checked first."""
    fields = _checked_fields(body)
    with _lock:
        stored = _read_known(project, story_id)
        story = Story(id=story_id, created_at=stored.created_at, updated_at=now_iso(), **fields.model_dump())
        _write(project, story)
        return _view(story, _remembered(project))


def delete(project: ProjectPaths, story_id: str) -> None:
    """The Story's file, then every clip's key that points at it (D10). A crash in between
    leaves keys that start-up removes."""
    with _lock:
        path = _known_path(project, story_id)
        path.unlink()
        _rewrite_clip_stories(project, drop=lambda _clip_id, remembered: remembered == story_id)
    log.info("deleted story %s", story_id)


def clip_stories(project: ProjectPaths) -> dict[str, str]:
    """`{clip_id: story_id}` of every clip that remembers a Story (D3)."""
    with _lock:
        return _clip_stories(project)


def forget_clip(project: ProjectPaths, clip_id: str) -> None:
    """A deleted clip forgets its Story; the Story stays (D7, ADR 0022)."""
    with _lock:
        _rewrite_clip_stories(project, drop=lambda remembering, _story_id: remembering == clip_id)


def clean_on_start(project: ProjectPaths) -> None:
    """Half-written files go, and so does the key of a clip with no json or of a Story with
    no file (spec › Ops). An unreadable `clip-stories.json` is left alone: it reads as
    empty, and the next Story a clip remembers writes it anew (spec › Ops)."""
    files.remove_unfinished(project.stories_dir)
    with _lock:
        _rewrite_clip_stories(
            project,
            drop=lambda clip_id, story_id: not project.clip_json(clip_id).is_file()
            or not _path(project, story_id).is_file(),
        )


# --- The Story block (spec › คำสั่ง LLM) ---


def prompt_block(story: Story) -> str:
    """The Story as the writing and polishing prompts carry it: background and spellings,
    never events (D8). No article, no `บทความ:` line; no characters, no character part."""
    lines = [BLOCK_HEAD, f"ชื่อเรื่อง: {story.title}"]
    if story.article:
        lines += ["บทความ:", story.article]
    if story.characters:
        lines.append(CHARACTERS_HEAD)
        lines += [
            f"- {character.name}: {character.description}" if character.description else f"- {character.name}"
            for character in story.characters
        ]
    return "\n".join(lines)


def names_rule(story: Story | None) -> str:
    """The line that closes the writing prompt's rules: the names as the Story spells
    them (D16); empty without a Story or without characters."""
    if story is None or not story.characters:
        return ""
    return f"เขียนชื่อตัวละครตาม Story: {', '.join(character.name for character in story.characters)}\n"


def block_tokens(project: ProjectPaths, story: Story | None) -> int:
    """The Story block's tokens to Qwen, counted with the EP's against 32,000 (D14); 0 for
    no Story. Raises `ApiError` 503 `not_ready` without Qwen's tokenizer."""
    if story is None:
        return 0
    return qwen_tokens.count(project, prompt_block(story))


def _tokens(project: ProjectPaths, story: Story) -> int | None:
    """`block_tokens` for the list: None when Qwen's tokenizer can't be read (D17),
    whatever transformers raises for broken files: one Story never fails the whole list."""
    try:
        return block_tokens(project, story)
    except ApiError:
        return None  # Qwen isn't installed: nothing to log
    except Exception:
        log.warning("story %s: Qwen's tokenizer can't count", story.id)
        return None


# --- The Story a Draft job uses (D5, D15) ---


def for_draft(project: ProjectPaths, story_id: object) -> Story | None:
    """The Story a `kind: "draft"` asks for, read once as the job starts (D5); None for
    `null`. Raises `ApiError` 400 `story_not_found` for one with no file or one that
    can't be read (spoil-maker spec › Draft job step 1)."""
    if story_id is None:
        return None
    with _lock:
        story = _read_if_stored(project, story_id)
    if story is None:
        raise _story_not_found()
    return story


def read_clip_story(project: ProjectPaths, clip_id: str) -> Story | None:
    """The Story the clip remembers, read as it is now (D5, ADR 0024). Never raises, unlike
    `for_draft`: None when the clip remembers none, or its Story was deleted or can't be read."""
    with _lock:
        return _read_if_stored(project, _clip_stories(project).get(clip_id))


def set_clip_story(project: ProjectPaths, clip_id: str, story_id: str | None) -> None:
    """The clip remembers the Story of its latest draft, or forgets its Story for `None` (D15). The Story
    may have been deleted since `for_draft`: then `story_not_found`, and nothing changes."""
    with _lock:
        if story_id is not None and not _is_stored(project, story_id):
            raise _story_not_found()
        _rewrite_clip_stories(
            project,
            drop=lambda remembering, _story_id: remembering == clip_id,
            add={clip_id: story_id} if story_id is not None else None,
        )


def _story_not_found() -> ApiError:
    return ApiError(400, "story_not_found", "ไม่พบเรื่องนี้ในคลังความรู้แล้ว")


# --- Files; call with `_lock` held ---


def _path(project: ProjectPaths, story_id: str) -> Path:
    return project.stories_dir / f"{story_id}.json"


def _is_stored(project: ProjectPaths, story_id: object) -> bool:
    """Whether the id is a Story's and its file is there."""
    return isinstance(story_id, str) and STORY_ID.fullmatch(story_id) is not None and _path(project, story_id).is_file()


def _read_if_stored(project: ProjectPaths, story_id: object) -> Story | None:
    """The Story of an id with a file there, if it can be read."""
    return _read(_path(project, story_id), story_id) if _is_stored(project, story_id) else None


def _known_path(project: ProjectPaths, story_id: str) -> Path:
    """Raises `ApiError` 404 `not_found` for an id that isn't a Story's or has no file."""
    if not _is_stored(project, story_id):
        raise _not_found()
    return _path(project, story_id)


def _read_known(project: ProjectPaths, story_id: str) -> Story:
    """An unreadable Story is `not_found` too, the same as in the list."""
    story = _read(_known_path(project, story_id), story_id)
    if story is None:
        raise _not_found()
    return story


def _read(path: Path, story_id: str) -> Story | None:
    try:
        story = Story.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        story = None
    if story is None or story.id != story_id:
        # The id only: the file holds the article and character names (spec › Ops).
        log.warning("leaving out story %s: its file can't be read", story_id)
        return None
    return story


class StoredStory(NamedTuple):
    story: Story
    modified_ns: int  # its file's `st_mtime_ns`, which orders Stories changed in the same second


def _read_all(project: ProjectPaths) -> list[StoredStory]:
    """Every readable Story."""
    found = []
    if project.stories_dir.is_dir():
        for path in project.stories_dir.glob("st_*.json"):
            if STORY_ID.fullmatch(path.stem) and (story := _read(path, path.stem)) is not None:
                found.append(StoredStory(story, path.stat().st_mtime_ns))
    return found


def _write(project: ProjectPaths, story: Story) -> None:
    files.write_atomic(_path(project, story.id), story.model_dump_json(indent=2))


def _new_id(project: ProjectPaths) -> str:
    while True:
        story_id = f"st_{secrets.token_hex(4)}"
        if not _path(project, story_id).exists():
            return story_id


def _rewrite_clip_stories(
    project: ProjectPaths, drop: Callable[[str, str], bool], add: dict[str, str] | None = None
) -> None:
    """Removes every `(clip_id, story_id)` that `drop` picks, then adds `add`, writing
    only when something changed."""
    stored = _clip_stories(project)
    kept = {clip_id: story_id for clip_id, story_id in stored.items() if not drop(clip_id, story_id)} | (add or {})
    if kept != stored:
        _write_clip_stories(project, kept)


def _clip_stories(project: ProjectPaths) -> dict[str, str]:
    """`clip-stories.json`; missing, unreadable or of the wrong shape reads as empty (spec › Ops)."""
    path = project.clip_stories_file
    if not path.is_file():
        return {}
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log.warning("reading clip-stories.json as empty: %s", error)
        return {}
    if not isinstance(stored, dict) or not all(
        isinstance(clip_id, str) and isinstance(story_id, str) and STORY_ID.fullmatch(story_id)
        for clip_id, story_id in stored.items()
    ):
        log.warning("reading clip-stories.json as empty: it isn't {clip_id: story_id}")
        return {}
    return stored


def _write_clip_stories(project: ProjectPaths, clip_stories: dict[str, str]) -> None:
    project.stories_dir.mkdir(parents=True, exist_ok=True)
    files.write_atomic(project.clip_stories_file, json.dumps(clip_stories, ensure_ascii=False, indent=2))


def _remembered(project: ProjectPaths) -> Counter[str]:
    """How many clips remember each Story, by its id."""
    return Counter(_clip_stories(project).values())


def _view(story: Story, remembered: Counter[str]) -> StoryView:
    return StoryView(**story.model_dump(), clips=remembered[story.id])


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "ไม่พบเรื่องนี้")
