"""Series, their characters and backgrounds, and the reference image of each
(toon spec › Series ตัวละคร ฉากหลัง, › Ref job, D7, D10, D11, D13, D25, D26, D28, D31, D32, D41).

A reference image is `refs/{id}-{rev}.png`, `rev` the item's `ref_rev`; a Ref job's three
pictures wait in `refs/.pending/{id}-{1..3}.png` until one is picked (the job draws them into
`refs/.pending/.new-{id}/` and moves all three in at once, `put_pending`).
"""

import io
import logging
import secrets
import shutil
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import NamedTuple

import anyio
from pydantic import BaseModel

from backend import disk, gpu, paths, uploads
from backend.ids import new_id
from backend.json_values import is_int
from backend.errors import ApiError, checked_text, invalid_request
from backend.jobs import JobSlot
from backend.paths import ProjectPaths
from backend.spoil_maker import voices
from backend.toon import store
from backend.toon.kinds import CARD_SIZE, KINDS, ItemKind
from backend.toon.store import Background, Character, Plot, Series

log = logging.getLogger(__name__)

NAME_MAX, CHANNEL_MAX = 60, 60
ACTS_MAX, ACT_NAME_MAX = 8, 20
ITEM_NAME_MAX, TAG_MAX, DESCRIPTION_MAX = 30, 20, 300
STYLE_MAX, TONE_MAX = 500, 300  # D48
PICTURES = 3  # a Ref job draws three to pick from (D31)
UPLOAD_MAX_BYTES = 20 * 1024**2

# What a new Series starts with, by genre (D10, D11, D28, D41).
DEFAULTS: dict[str, dict] = {
    "horror": {
        "acts": ["เปิด", "ปม", "หักมุม", "จบหลอน"],
        "style": "flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, "
        "dark night scene, only light sources are bright and saturated, deep shadows",
        "tone": 'เล่าเป็น "ฉัน" น้ำเสียงเรียบ ช้า ชวนขนลุก ประโยคสั้น',
    },
    "comedy": {
        "acts": ["ตั้งเรื่อง", "ปั่น", "พลิก", "ตบมุก"],
        "style": "flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, "
        "bright cheerful colors, soft daylight",
        "tone": "เล่ากวนๆ จังหวะเร็ว มีมุกตบท้าย ประโยคสั้น",
    },
}

class ItemRef(NamedTuple):
    """Which character or background of which Series: the address of one item (not its
    reference picture) that each function of one item takes instead of its four parts.
    Whether the item exists is checked by the function, under the store's lock."""

    project: ProjectPaths
    series_id: str
    item_kind: ItemKind
    item_id: str


series_jobs: list[Callable[[], JobSlot]] = []
"""Each job slot of the tab, added by its module as it loads (`toon.jobs`, `toon.render`), looked up as it is asked: the Series of its running job
(`JobSlot.running`, a `series_id`) can't be deleted. Read under `store.lock`, as `episodes.ep_jobs`."""


class CharacterView(Character):
    pending: int  # 0, or the three pictures of a Ref job waiting to be picked


class BackgroundView(Background):
    pending: int


class SeriesView(Series):
    characters: list[CharacterView]
    backgrounds: list[BackgroundView]


class ListedSeries(BaseModel):
    id: str
    name: str
    channel_name: str
    layout: str
    genre: str
    ep_count: int


class EpRef(BaseModel):
    """An EP named in a refusal: its number and title (D25, D26)."""

    n: int
    title: str


# --- Series ---


def list_all(project: ProjectPaths) -> list[ListedSeries]:
    with store.lock:
        return [
            ListedSeries(
                id=s.id,
                name=s.name,
                channel_name=s.channel_name,
                layout=s.layout,
                genre=s.genre,
                ep_count=len(_eps(project, s.id)),
            )
            for s in store.list_series(project)
        ]


def create(project: ProjectPaths, body: dict) -> SeriesView:
    """A new Series with its genre's acts, style and tone (spec › Series ตัวละคร ฉากหลัง), or the
    ones the body sends: the form shows the defaults and the user may change them first (D52)."""
    name = checked_text(body.get("name"), 1, NAME_MAX)
    channel_name = checked_text(body.get("channel_name", ""), 0, CHANNEL_MAX)
    layout, genre = body.get("layout"), body.get("genre")
    if layout not in CARD_SIZE or genre not in DEFAULTS:
        raise invalid_request()
    name_tags = body.get("name_tags", True)
    if not isinstance(name_tags, bool):
        raise invalid_request()
    overrides = _style_tone_acts(body)  # what the form changed from the genre's defaults (D52)
    # A `voice_id` is written under the draft's lock, so a voice delete can't slip in (D25).
    with gpu.slot.draft_lock, store.lock:
        voice_id = existing_voice(project, body.get("voice_id"))
        taken = {s.id for s in store.list_series(project)}
        series = Series(
            id=new_id("s", taken),
            name=name,
            channel_name=channel_name,
            layout=layout,
            genre=genre,
            voice_id=voice_id,
            name_tags=name_tags,
            **(DEFAULTS[genre] | overrides),
        )
        store.write_series(project, series)
    log.info("created series %s", series.id)
    return view(project, series.id)


def _style_tone_acts(body: dict) -> dict:
    """The `style`, `tone` and `acts` the body sends, each checked; a field it leaves out is not in the answer."""
    fields: dict = {}
    if "style" in body:
        fields["style"] = checked_text(body["style"], 1, STYLE_MAX)
    if "tone" in body:
        fields["tone"] = checked_text(body["tone"], 0, TONE_MAX)
    if "acts" in body:
        acts = body["acts"]
        if not isinstance(acts, list) or not 1 <= len(acts) <= ACTS_MAX:
            raise ApiError(400, "invalid_request", f"โครงองก์มีได้ 1–{ACTS_MAX} องก์")
        fields["acts"] = [checked_text(act, 1, ACT_NAME_MAX) for act in acts]
    return fields


def view(project: ProjectPaths, series_id: str) -> SeriesView:
    with store.lock:
        series = require_series(project, series_id)
        pending = _pending_counts(project, series)
        return SeriesView(
            **series.model_dump(exclude={"characters", "backgrounds"}),
            characters=[CharacterView(**c.model_dump(), pending=pending.get(c.id, 0)) for c in series.characters],
            backgrounds=[BackgroundView(**b.model_dump(), pending=pending.get(b.id, 0)) for b in series.backgrounds],
        )


def change(project: ProjectPaths, series_id: str, body: dict) -> SeriesView:
    """Every field but `layout`, `genre` and `max_ep`, which stay as they are (D7, D10, D40);
    new `acts` count for new EPs only (D11)."""
    changes: dict = _style_tone_acts(body)
    if "name" in body:
        changes["name"] = checked_text(body["name"], 1, NAME_MAX)
    if "channel_name" in body:
        changes["channel_name"] = checked_text(body["channel_name"], 0, CHANNEL_MAX)
    if "name_tags" in body:
        if not isinstance(body["name_tags"], bool):
            raise invalid_request()
        changes["name_tags"] = body["name_tags"]
    with gpu.slot.draft_lock, store.lock:
        series = require_series(project, series_id)
        if "voice_id" in body:
            changes["voice_id"] = existing_voice(project, body["voice_id"])
        store.write_series(project, series.model_copy(update=changes))
    return view(project, series_id)


def delete(project: ProjectPaths, series_id: str, body: dict | None) -> None:
    """Removes the Series' folder with every EP once `confirm_eps` is their count (D26);
    Saved voices and background sounds stay. `series_busy` while a job works on it: every job
    starts under the store's lock, so it finds the Series either whole or gone (`not_found`)."""
    with store.lock:
        require_series(project, series_id)
        eps = _eps(project, series_id)
        confirm = (body or {}).get("confirm_eps")
        if not is_int(confirm) or confirm != len(eps):
            raise ApiError(409, "confirm_needed", f"ยืนยันการลบ Series พร้อม {len(eps)} EP", eps=[e.model_dump() for e in eps])
        if any((job := slot().running()) is not None and job.series_id == series_id for slot in series_jobs):
            raise ApiError(409, "series_busy", "Series นี้มีงานที่ยังไม่จบ")
        shutil.rmtree(project.series_dir(series_id))
    log.info("deleted series %s with %d EP", series_id, len(eps))


def uses_voice(voice_id: str) -> bool:
    """Whether a Series or an EP narrates with the Saved voice, which then can't be deleted (D25)."""
    project = paths.project()
    with store.lock:
        return any(
            series.voice_id == voice_id or any(ep.voice_id == voice_id for ep in store.list_eps(project, series.id))
            for series in store.list_series(project)
        )


# --- characters and backgrounds ---


def add_item(project: ProjectPaths, series_id: str, item_kind: ItemKind, body: dict) -> SeriesView:
    with store.lock:
        series = require_series(project, series_id)
        row = KINDS[item_kind]
        fields = _item_fields(body, item_kind, partial=False)
        getattr(series, item_kind).append(row.model(id=new_id(row.id_prefix, _taken_ids(series)), **fields))
        store.write_series(project, series)
    return view(project, series_id)


def new_items(series: Series, plot: Plot) -> dict[ItemKind, list[Character | Background]]:
    """The plot's new characters and backgrounds as items of the Series, by kind (D13): each
    gets its id in the plot too, and is no longer `new` there. The Series isn't changed."""
    taken = _taken_ids(series)
    added: dict[ItemKind, list[Character | Background]] = {item_kind: [] for item_kind in KINDS}
    for item_kind, row in KINDS.items():
        for item in getattr(plot, item_kind):
            if item.new:
                item.id, item.new = new_id(row.id_prefix, taken), False
                taken.add(item.id)
                added[item_kind].append(row.model(**item.model_dump(include=set(row.model.model_fields))))
    return added


def _taken_ids(series: Series) -> set[str]:
    return {item.id for item in [*series.characters, *series.backgrounds]}


def change_item(item_ref: ItemRef, body: dict) -> SeriesView:
    fields = _item_fields(body, item_ref.item_kind, partial=True)
    with store.lock:
        series, item = _require_item(item_ref)
        for name, value in fields.items():
            setattr(item, name, value)
        store.write_series(item_ref.project, series)
    return view(item_ref.project, item_ref.series_id)


def delete_item(item_ref: ItemRef) -> SeriesView:
    """An item a card, a segment or a plot of an EP uses can't go: `in_use` with those EPs (D25)."""
    project, series_id = item_ref.project, item_ref.series_id
    with store.lock:
        series, item = _require_item(item_ref)
        users = [EpRef(n=ep.n, title=ep.title) for ep in store.list_eps(project, series_id) if item.id in _used_items(ep)]
        if users:
            raise ApiError(409, "in_use", "ยังมี EP ที่ใช้อยู่ ลบไม่ได้", eps=[ep.model_dump() for ep in users])
        getattr(series, item_ref.item_kind).remove(item)
        store.write_series(project, series)
        _remove_ref_files(item_ref)
    return view(project, series_id)


def find_item(series: Series, item_kind: ItemKind, item_id: str) -> Character | Background | None:
    return next((item for item in getattr(series, item_kind) if item.id == item_id), None)


def ref_revs(series: Series) -> dict[str, int]:
    """The `ref_rev` of each character and background, by id: what a card's image status
    compares its image's `refs` with (`episodes.image_status`)."""
    return {item.id: item.ref_rev for item in [*series.characters, *series.backgrounds]}


class RefPlan(BaseModel):
    """What a Ref job draws, read once when it starts (spec › Ref job)."""

    item_ref: ItemRef
    name: str
    description: str
    style: str
    size: tuple[int, int]


def ref_plan(item_ref: ItemRef) -> RefPlan:
    """Raises `ApiError` 404 `not_found` when the Series or the item isn't there."""
    with store.lock:
        series = store.read_series(item_ref.project, item_ref.series_id)
        item = _item_or_none(series, item_ref) if series else None
        if item is None:
            raise ApiError(404, "not_found", "ไม่พบตัวละครหรือฉากหลังนี้")
        return RefPlan(
            item_ref=item_ref,
            name=item.name,
            description=item.description,
            style=series.style,
            size=picture_size(series, item_ref.item_kind),
        )


def picture_size(series: Series, item_kind: ItemKind) -> tuple[int, int]:
    """(width, height) of a reference picture of this kind in this Series."""
    return KINDS[item_kind].sizes[series.layout]


# --- reference images ---


def ref_image(item_ref: ItemRef) -> Path:
    with store.lock:
        _, item = _require_item(item_ref)
        path = item_ref.project.refs_dir(item_ref.series_id) / f"{item.id}-{item.ref_rev}.png"
        if item.ref_rev == 0 or not path.is_file():
            raise ApiError(404, "not_found", "ยังไม่มีภาพอ้างอิง")
        return path


def pending_image(item_ref: ItemRef, n: int) -> Path:
    with store.lock:
        _require_item(item_ref)
        if not 1 <= n <= PICTURES or not _pending_complete(item_ref):
            raise ApiError(404, "no_pending", "ไม่มีภาพที่รอเลือก")
        return pending_path(item_ref, n)


def pending_path(item_ref: ItemRef, n: int) -> Path:
    return item_ref.project.pending_refs_dir(item_ref.series_id) / f"{item_ref.item_id}-{n}.png"


def put_pending(item_ref: ItemRef, pictures: list[Path]) -> bool:
    """Moves a finished Ref job's pictures in as the item's one waiting set, replacing an
    older one. False when the item went meanwhile: the pictures are dropped."""
    with store.lock:
        series = store.read_series(item_ref.project, item_ref.series_id)
        if series is None or _item_or_none(series, item_ref) is None:
            return False
        item_ref.project.pending_refs_dir(item_ref.series_id).mkdir(parents=True, exist_ok=True)
        for n, picture in enumerate(pictures, start=1):
            picture.replace(pending_path(item_ref, n))
        return True


def pick(item_ref: ItemRef, body: dict) -> SeriesView:
    """The picked picture becomes the reference image, `ref_rev` + 1; the old one and the
    rest of the set go (D31, D32)."""
    n = body.get("n")
    if not is_int(n) or not 1 <= n <= PICTURES:
        raise ApiError(400, "invalid_request", f"เลือกภาพที่ 1–{PICTURES}")
    with store.lock:
        series, _ = _require_item(item_ref)
        if not _pending_complete(item_ref):
            raise ApiError(404, "no_pending", "ไม่มีภาพที่รอเลือก")
        _set_ref(item_ref, series, pending_path(item_ref, n))
    return view(item_ref.project, item_ref.series_id)


def check_upload(item_ref: ItemRef, body: dict) -> uploads.UploadCheck:
    """The upload's checks before the page sends the body (ADR 0028)."""
    return uploads.UploadCheck(size=_upload_checks(item_ref, body.get("size")))


async def receive_upload(item_ref: ItemRef, size: str | None, body: AsyncIterator[bytes]) -> SeriesView:
    """A PNG or JPEG of the user's becomes the reference image like a picked one (D31): a
    background cropped to its layout and sized as a card, a character's long side ≤ 1536."""
    expected = uploads.whole_number(size)
    await anyio.to_thread.run_sync(_upload_checks, item_ref, expected)
    partial = item_ref.project.toon_partial_dir / f"{item_ref.item_id}.{secrets.token_hex(4)}.upload"  # one per request
    try:
        await uploads.receive(body, partial, expected)
        return await anyio.to_thread.run_sync(_take_upload, item_ref, partial)
    finally:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(lambda: partial.unlink(missing_ok=True))


def clean_on_start(project: ProjectPaths) -> None:
    """Pictures never picked go, and uploads never received in full: jobs and requests
    don't survive a restart (spec › Ref job)."""
    if project.toon_series_dir.is_dir():
        for folder in project.toon_series_dir.iterdir():
            shutil.rmtree(project.pending_refs_dir(folder.name), ignore_errors=True)
    shutil.rmtree(project.toon_partial_dir, ignore_errors=True)


# --- helpers ---


def _upload_checks(item_ref: ItemRef, size: object) -> int:
    size = uploads.require_size(size, UPLOAD_MAX_BYTES, "ไฟล์ภาพใหญ่เกิน 20 MB")
    with store.lock:
        _require_item(item_ref)
    disk.require_free(item_ref.project.root, size)
    return size


def _take_upload(item_ref: ItemRef, partial: Path) -> SeriesView:
    """In a thread: read the file with Pillow, size it, then set it as the reference."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        with Image.open(partial, formats=["PNG", "JPEG"]) as opened:
            opened.load()
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ApiError(400, "unsupported_file", "รับเฉพาะไฟล์ภาพ PNG หรือ JPEG") from None
    with store.lock:
        series, _ = _require_item(item_ref)
        side = KINDS[item_ref.item_kind].upload_side
        if side is None:
            image = ImageOps.fit(image, picture_size(series, item_ref.item_kind), Image.Resampling.LANCZOS)
        else:
            image.thumbnail((side, side), Image.Resampling.LANCZOS)
        png = partial.with_suffix(".png")
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        png.write_bytes(buffer.getvalue())
        _set_ref(item_ref, series, png)
    log.info("uploaded the reference image of %s in %s", item_ref.item_id, item_ref.series_id)
    return view(item_ref.project, item_ref.series_id)


def _set_ref(item_ref: ItemRef, series: Series, picture: Path) -> None:
    """`picture` becomes `{id}-{rev + 1}.png`; the old reference and any waiting set go.
    Call with the store's lock held."""
    item = _item_or_none(series, item_ref)
    refs = item_ref.project.refs_dir(series.id)
    refs.mkdir(parents=True, exist_ok=True)
    old = refs / f"{item.id}-{item.ref_rev}.png"
    item.ref_rev += 1
    picture.replace(refs / f"{item.id}-{item.ref_rev}.png")
    store.write_series(item_ref.project, series)
    old.unlink(missing_ok=True)
    for n in range(1, PICTURES + 1):
        pending_path(item_ref, n).unlink(missing_ok=True)


def _remove_ref_files(item_ref: ItemRef) -> None:
    project, series_id = item_ref.project, item_ref.series_id
    for folder in (project.refs_dir(series_id), project.pending_refs_dir(series_id)):
        if folder.is_dir():
            for path in folder.glob(f"{item_ref.item_id}-*.png"):
                path.unlink(missing_ok=True)


def _pending_complete(item_ref: ItemRef) -> bool:
    return all(pending_path(item_ref, n).is_file() for n in range(1, PICTURES + 1))


def _pending_counts(project: ProjectPaths, series: Series) -> dict[str, int]:
    return {
        item.id: PICTURES
        for item_kind in KINDS
        for item in getattr(series, item_kind)
        if _pending_complete(ItemRef(project, series.id, item_kind, item.id))
    }


def _eps(project: ProjectPaths, series_id: str) -> list[EpRef]:
    """The Series' EPs by number, as a refusal names them."""
    return [EpRef(n=ep.n, title=ep.title) for ep in store.list_eps(project, series_id)]


def _used_items(ep: store.Ep) -> set[str]:
    """Every character and background the EP's plot, segments and cards use."""
    used = {item.id for item in [*ep.plot.characters, *ep.plot.backgrounds] if item.id}
    for act in ep.acts:
        for segment in act.segments:
            used.add(segment.background_id)
            for card in segment.cards:
                used.update(card.character_ids)
    return used


def require_series(project: ProjectPaths, series_id: str) -> Series:
    """The stored Series, or `ApiError` 404 `not_found`."""
    series = store.read_series(project, series_id)
    if series is None:
        raise ApiError(404, "not_found", "ไม่พบ Series นี้")
    return series


def _item_or_none(series: Series, item_ref: ItemRef) -> Character | Background | None:
    return find_item(series, item_ref.item_kind, item_ref.item_id)


def _require_item(item_ref: ItemRef) -> tuple[Series, Character | Background]:
    """The stored Series and the item in it, or `ApiError` 404 `not_found` naming which
    isn't there. Call with the store's lock held."""
    series = require_series(item_ref.project, item_ref.series_id)
    item = _item_or_none(series, item_ref)
    if item is None:
        raise ApiError(404, "not_found", "ไม่พบตัวละครหรือฉากหลังนี้")
    return series, item


def _item_fields(body: dict, item_kind: ItemKind, partial: bool) -> dict:
    fields = {}
    if "name" in body or not partial:
        fields["name"] = checked_text(body.get("name"), 1, ITEM_NAME_MAX)
    if "description" in body:
        fields["description"] = checked_text(body["description"], 0, DESCRIPTION_MAX)
    if "tag" in body and KINDS[item_kind].tagged:
        fields["tag"] = checked_text(body["tag"], 0, TAG_MAX)
    return fields


def existing_voice(project: ProjectPaths, voice_id: object) -> str:
    """A Saved voice that exists. Raises `ApiError` 400 `voice_not_found`."""
    if not isinstance(voice_id, str) or voices.chars_per_s(project, voice_id) is None:
        raise ApiError(400, "voice_not_found", "ไม่พบเสียงนี้: เลือกเสียงที่บันทึกไว้")
    return voice_id


voices.voice_users.append(uses_voice)
