"""EPs of a Series: creating one, its plot, its acts, segments and cards, the edits the page
makes, and the state of each card (toon spec › ข้อมูล, › สถานะการ์ด, › API, D8–D10, D13–D15,
D20, D21, D24–D26, D30, D40, spoil-maker D74).

Every edit is refused `ep_locked` while a job locks the EP (a Plot or Cards job) and every
delete `ep_busy` while any job works on it: each job slot of the tab adds a check to `ep_jobs`.
"""

import logging
import shutil
from collections.abc import Callable, Iterator, Mapping, Sized
from contextlib import contextmanager
from typing import Literal, NamedTuple, get_args

from pydantic import BaseModel

from backend import gpu, llm_reply, renders, sounds
from backend.errors import ApiError, checked_text, invalid_request
from backend.ids import new_id
from backend.json_values import is_int, is_number
from backend.paths import EpAddress, ProjectPaths
from backend.spoil_maker import thai, voices
from backend.toon import series as series_module
from backend.toon import store
from backend.toon.kinds import KINDS, ItemKind
from backend.toon.store import Act, Card, Ep, Motion, Plot, PlotItem, Segment, Series, Sound, Stage

log = logging.getLogger(__name__)

IDEA_MAX, TITLE_MAX, SUMMARY_MAX = 500, 60, 1000
TEXT_MAX, CARD_DESCRIPTION_MAX = 200, 500  # D53
CARD_CHARACTERS_MAX = 2  # D30
HOLD_MAX, HOLD_STEP, SILENT_HOLD = 5, 0.5, 2  # D14, D21
EP_NUMBER_MAX = 999  # D40
GAP_S = 0.3  # after the narration, before the next card (D21)
TARGET_S = 90  # what the AI writes toward, inside the page's 60–120 (D14)
MOTIONS = get_args(Motion)
ImageStatus = Literal["no_ref", "no_image", "stale_ref", "ready"]  # spec › สถานะการ์ด
AudioStatus = Literal["silent", "no_audio", "stale_audio", "ready"]
VOLUME_MAX = 100
# Letters per second of a voice the saved voices don't have: an EP's voice can't be deleted (D25),
# so only a broken voices file gets here, and the length is a guess.
UNKNOWN_CHARS_PER_S = 15.0



class EpUse(NamedTuple):
    """The EP an unfinished job works on, as its slot says it in `ep_jobs`."""

    ep_id: str
    # `locks`: edits of the EP are `ep_locked` (a Plot or Cards job); `renders`: a Render job,
    # so starting a Plot or Cards job on the EP is `ep_busy` (D57); `works`: any other job.
    how: Literal["works", "locks", "renders"]


ep_jobs: list[Callable[[], EpUse | None]] = []
"""What each job slot of the tab works on now, or None; each slot's module adds its own as it
loads (`toon.jobs`, `toon.render`). Each reads its job without its slot's
lock (`JobSlot.running`): edits ask under `store.lock`, and a job that locks an EP is set under
it too."""


class ListedEp(BaseModel):
    id: str
    n: int
    title: str
    stage: Stage
    cards: int
    images: int  # cards with a card image
    rendered_at: str | None = None  # the latest render


class CardView(BaseModel):
    """A card as the page shows it: the stored fields but the image prompt, and its state."""

    id: str
    text: str
    character_ids: list[str]
    description: str
    motion: Motion
    flicker: bool
    hold_s: float
    edited: bool
    image_status: ImageStatus
    audio_status: AudioStatus
    duration_s: float
    has_image: bool  # a `no_ref` card may still have one, drawn before (D13)
    has_previous_image: bool


class SegmentView(BaseModel):
    id: str
    background_id: str
    sound: Sound | None
    cards: list[CardView]


class ActView(BaseModel):
    id: str
    name: str
    summary: str
    cards_from: str | None
    segments: list[SegmentView]


class EpView(BaseModel):
    id: str
    series_id: str
    n: int
    idea: str
    title: str
    voice_id: str
    stage: Stage
    plot: Plot
    acts: list[ActView]
    duration_s: float
    locked: bool  # a Plot or Cards job works on it: the page closes its fields


# --- EPs ---


def list_for(project: ProjectPaths, series_id: str) -> list[ListedEp]:
    """The Series' EPs, newest number first."""
    with store.lock:
        series_module.view(project, series_id)  # `not_found`
        eps = store.list_eps(project, series_id)
    return [
        ListedEp(
            id=ep.id,
            n=ep.n,
            title=ep.title,
            stage=ep.stage,
            cards=sum(1 for card in ep_cards(ep)),
            images=sum(1 for card in ep_cards(ep) if card.image is not None),
            rendered_at=renders.latest_at(EpAddress(project, series_id, ep.id).renders_dir),
        )
        for ep in reversed(eps)
    ]


def create(project: ProjectPaths, series_id: str, body: dict) -> EpView:
    """A new EP numbered past the highest the Series ever had (D40), with the Series' acts
    and voice (D8, D11); its plot comes from a Plot job."""
    idea = checked_text(body.get("idea"), 1, IDEA_MAX)
    with gpu.slot.draft_lock, store.lock:
        series = series_module.require_series(project, series_id)
        taken = store.ep_ids(project)
        series.max_ep += 1
        acts: list[Act] = []
        for name in series.acts:
            acts.append(Act(id=new_id("a", {act.id for act in acts}), name=name))
        ep = Ep(
            id=new_id("e", taken),
            n=series.max_ep,
            idea=idea,
            voice_id=series.voice_id,
            acts=acts,
        )
        ep_address = EpAddress(project, series_id, ep.id)
        store.write_ep(ep_address, ep)
        store.write_series(project, series)
    log.info("created EP %s in %s", ep.id, series_id)
    return view(ep_address)


def view(ep_address: EpAddress) -> EpView:
    with store.lock:
        series, ep = read(ep_address)
        chars_per_s = voices.chars_per_s(ep_address.project, ep.voice_id) or UNKNOWN_CHARS_PER_S
        refs = series_module.ref_revs(series)
        acts = [
            ActView(
                id=act.id,
                name=act.name,
                summary=act.summary,
                cards_from=act.cards_from,
                segments=[
                    SegmentView(
                        id=segment.id,
                        background_id=segment.background_id,
                        sound=segment.sound,
                        cards=[_card_view(ep, segment, card, refs, chars_per_s) for card in segment.cards],
                    )
                    for segment in act.segments
                ],
            )
            for act in ep.acts
        ]
        return EpView(
            id=ep.id,
            series_id=series.id,
            n=ep.n,
            idea=ep.idea,
            title=ep.title,
            voice_id=ep.voice_id,
            stage=ep.stage,
            plot=ep.plot,
            acts=acts,
            duration_s=round(sum(card.duration_s for act in acts for s in act.segments for card in s.cards), 1),
            locked=_locked(ep.id),
        )


def change(ep_address: EpAddress, body: dict) -> EpView:
    """`title` (D24), `n` (D40), `voice_id` (D8) and `plot` (D13). A `voice_id` is written under
    the draft's lock, so a Saved voice delete can't slip in (D25)."""
    project = ep_address.project
    with gpu.slot.draft_lock, store.lock:
        series, ep = editable(ep_address)
        if "title" in body:
            ep.title = checked_text(body["title"], 0, TITLE_MAX)
        if "n" in body:
            ep.n = _ep_number(ep_address, body["n"])
            if ep.n > series.max_ep:
                series.max_ep = ep.n
                store.write_series(project, series)
        if "voice_id" in body:
            ep.voice_id = series_module.existing_voice(project, body["voice_id"])
        if "plot" in body:
            ep.plot = _plot(series, body["plot"], ep.stage == "cards")
        store.write_ep(ep_address, ep)
    return view(ep_address)


def delete(ep_address: EpAddress) -> None:
    """Removes the EP's folder: its plot, cards, images, narration and renders (D26).
    Characters and backgrounds it added stay in the Series."""
    with store.lock:
        read(ep_address)  # `not_found`
        if _jobs_on(ep_address.ep_id):
            raise ApiError(409, "ep_busy", "EP นี้มีงานที่ยังไม่จบ")
        shutil.rmtree(ep_address.dir)
    log.info("deleted EP %s of %s", ep_address.ep_id, ep_address.series_id)


# --- acts ---


def add_act(ep_address: EpAddress, body: dict) -> EpView:
    """An act the user adds: never split, so a Cards job counts it as changed (D10, D15)."""
    name = checked_text(body.get("name"), 1, series_module.ACT_NAME_MAX)
    summary = checked_text(body.get("summary", ""), 0, SUMMARY_MAX)
    with _editing(ep_address) as (_, ep, _):
        act = Act(id=new_id("a", {a.id for a in ep.acts}), name=name, summary=summary)
        _insert(ep.acts, act, body)
    return view(ep_address)


def change_act(ep_address: EpAddress, act_id: str, body: dict) -> EpView:
    """The act's `name` and `summary` (D10, D15); a changed summary marks it to split again."""
    with _editing(ep_address) as (_, ep, _):
        act = _find(ep.acts, act_id)
        if "name" in body:
            act.name = checked_text(body["name"], 1, series_module.ACT_NAME_MAX)
        if "summary" in body:
            act.summary = checked_text(body["summary"], 0, SUMMARY_MAX)
    return view(ep_address)


def delete_act(ep_address: EpAddress, act_id: str) -> EpView:
    with _editing(ep_address) as (_, ep, removed):
        act = _find(ep.acts, act_id)
        ep.acts.remove(act)
        removed.extend(card for segment in act.segments for card in segment.cards)
    return view(ep_address)


# --- segments ---


def add_segment(ep_address: EpAddress, body: dict) -> EpView:
    """A segment needs a background of the Series and one card: a silent card the user
    fills, counted as written by them (spec › API, spoil-maker D74)."""
    with _editing(ep_address) as (series, ep, _):
        act = _find(ep.acts, body.get("act_id"))
        background_id = _require_background(series, body.get("background_id"))
        taken = _ids(ep)
        card = Card(id=new_id("k", taken), hold_s=SILENT_HOLD, edited=True)
        segment = Segment(id=new_id("g", taken), background_id=background_id, cards=[card])
        _insert(act.segments, segment, body)
    return view(ep_address)


def change_segment(ep_address: EpAddress, segment_id: str, body: dict) -> EpView:
    """The segment's background (cards drawn on the old one go `stale_ref`, D32) and its
    background sound: off (`null`), another from the library, or its volume (D5)."""
    with _editing(ep_address) as (series, ep, _):
        segment = _segment(ep, segment_id)
        if "background_id" in body:
            segment.background_id = _require_background(series, body["background_id"])
        if "sound" in body:
            segment.sound = _sound(ep_address.project, body["sound"], segment.sound)
    return view(ep_address)


def delete_segment(ep_address: EpAddress, segment_id: str) -> EpView:
    with _editing(ep_address) as (_, ep, removed):
        segment = _segment(ep, segment_id)
        next(act for act, placed in _placed_segments(ep) if placed is segment).segments.remove(segment)
        removed.extend(segment.cards)
    return view(ep_address)


# --- cards ---


def add_card(ep_address: EpAddress, body: dict) -> EpView:
    """A card the user inserts is `edited` (spoil-maker D74); a silent one holds 2 s (D21)."""
    with _editing(ep_address) as (series, ep, _):
        segment = _segment(ep, body.get("segment_id"))
        card = Card(id=new_id("k", _ids(ep)), edited=True)
        _apply_card(series, card, body)
        if "hold_s" not in body and not card.text:
            card.hold_s = SILENT_HOLD
        _check_card(card)
        _insert(segment.cards, card, body)
    return view(ep_address)


def change_card(ep_address: EpAddress, card_id: str, body: dict) -> EpView:
    """A changed `text` or `description` makes the card `edited` (spoil-maker D74)."""
    with _editing(ep_address) as (series, ep, _):
        card = card_of(ep, card_id)
        before = (card.text, card.description)
        _apply_card(series, card, body)
        _check_card(card)
        if (card.text, card.description) != before:
            card.edited = True
    return view(ep_address)


def delete_card(ep_address: EpAddress, card_id: str) -> EpView:
    """The last card of a segment takes the segment with it (spec › API)."""
    with _editing(ep_address) as (_, ep, removed):
        card = card_of(ep, card_id)
        act, segment = next((act, segment) for act, segment in _placed_segments(ep) if card in segment.cards)
        segment.cards.remove(card)
        if not segment.cards:
            act.segments.remove(segment)
        removed.append(card)
    return view(ep_address)


def remove_card_files(ep_address: EpAddress, cards: list[Card]) -> None:
    """The images and narration of cards that are gone (D15)."""
    images, audio = ep_address.images_dir, ep_address.audio_dir
    for card in cards:
        for path in images.glob(f"{card.id}-*.png") if images.is_dir() else ():
            path.unlink(missing_ok=True)
        (audio / f"{card.id}.wav").unlink(missing_ok=True)


# --- the state of a card ---


def image_status(card: Card, segment: Segment, refs: dict[str, int]) -> ImageStatus:
    """`no_ref`, `no_image`, `stale_ref` or `ready` (spec › สถานะการ์ด, D13, D32)."""
    used = [*card.character_ids, segment.background_id]
    if any(refs.get(item_id, 0) == 0 for item_id in used):
        return "no_ref"
    if card.image is None:
        return "no_image"
    if set(card.image.refs) != set(used) or any(refs.get(i) != rev for i, rev in card.image.refs.items()):
        return "stale_ref"
    return "ready"


def audio_status(card: Card, ep: Ep) -> AudioStatus:
    """`silent`, `no_audio`, `stale_audio` or `ready` (spec › สถานะการ์ด, D8)."""
    if not card.text:
        return "silent"
    if card.audio is None:
        return "no_audio"
    if card.audio.tts_text != thai.spoken(card.text) or card.audio.voice_id != ep.voice_id:
        return "stale_audio"
    return "ready"


def card_seconds(card: Card, status: AudioStatus, chars_per_s: float) -> float:
    """The narration (heard, or guessed from the voice's speed), the gap, and the hold (D14, D21)."""
    if status == "silent":
        return card.hold_s
    if status == "ready":
        return card.audio.duration_s + GAP_S + card.hold_s
    return thai.letters(thai.spoken(card.text)) / chars_per_s + GAP_S + card.hold_s


# --- helpers ---


def _card_view(ep: Ep, segment: Segment, card: Card, refs: dict[str, int], chars_per_s: float) -> CardView:
    audio = audio_status(card, ep)
    return CardView(
        **card.model_dump(include={"id", "text", "character_ids", "description", "motion", "flicker", "hold_s", "edited"}),
        image_status=image_status(card, segment, refs),
        audio_status=audio,
        duration_s=round(card_seconds(card, audio, chars_per_s), 1),
        has_image=card.image is not None,
        has_previous_image=card.previous_image is not None,
    )


def _apply_card(series: Series, card: Card, body: dict) -> None:
    if "text" in body:
        card.text = checked_text(body["text"], 0, TEXT_MAX)
    if "description" in body:
        card.description = checked_text(body["description"], 0, CARD_DESCRIPTION_MAX)
    if "character_ids" in body:
        ids = body["character_ids"]
        if (
            not isinstance(ids, list)
            or len(ids) > CARD_CHARACTERS_MAX
            or len(set(map(str, ids))) != len(ids)
            or any(series_module.find_item(series, "characters", i) is None for i in ids)
        ):
            raise ApiError(400, "invalid_card", f"เลือกตัวละครใน Series ได้ 0–{CARD_CHARACTERS_MAX} ตัว")
        card.character_ids = list(ids)
    if "motion" in body:
        if body["motion"] not in MOTIONS:
            raise ApiError(400, "invalid_card", "เลือกการขยับจากรายการ")
        card.motion = body["motion"]
    if "flicker" in body:
        if not isinstance(body["flicker"], bool):
            raise invalid_request()
        card.flicker = body["flicker"]
    if "hold_s" in body:
        hold = body["hold_s"]
        if not is_number(hold) or not 0 <= hold <= HOLD_MAX or (hold / HOLD_STEP) % 1:
            raise ApiError(400, "invalid_card", f"ค้างเพิ่มได้ 0–{HOLD_MAX} วินาที ทีละ {HOLD_STEP}")
        card.hold_s = float(hold)


def _check_card(card: Card) -> None:
    if not card.text and card.hold_s < HOLD_STEP:
        raise ApiError(400, "invalid_card", f"การ์ดเงียบต้องค้างอย่างน้อย {HOLD_STEP} วินาที")


def _plot(series: Series, value: object, confirmed: bool) -> Plot:
    """The plot's characters and backgrounds: the Series' by `id`, or new ones by `name`
    (D13); at least one background (spec › Plot job). New ones only before the plot is
    confirmed: only the first Cards job takes them into the Series (spec › Cards job, D54)."""
    if not isinstance(value, dict):
        raise invalid_request()
    by_kind = {item_kind: value.get(item_kind, []) for item_kind in KINDS}
    if not all(isinstance(items, list) for items in by_kind.values()) or over_max(by_kind):
        raise invalid_request()
    plot = plot_of(series, by_kind)
    if not plot.backgrounds:
        raise ApiError(400, "invalid_request", "พล็อตต้องมีฉากหลังอย่างน้อยหนึ่ง")
    if confirmed and any(item.new for item in [*plot.characters, *plot.backgrounds]):
        raise ApiError(400, "invalid_request", "ยืนยันพล็อตแล้ว: เพิ่มตัวละครหรือฉากหลังใหม่ที่หน้าตัวละครของชุด")
    return plot


def plot_of(series: Series, by_kind: dict[ItemKind, list], from_qwen: bool = False) -> Plot:
    """The plot of each kind's items as sent (`by_kind`), each list read by `plot_items`."""
    return Plot(**{item_kind: plot_items(series, item_kind, by_kind[item_kind], from_qwen) for item_kind in KINDS})


def over_max(by_kind: Mapping[ItemKind, Sized]) -> bool:
    """Whether any kind has more items, as sent or as read, than a plot may use (`KINDS`' `plot_max`)."""
    return any(len(by_kind[item_kind]) > KINDS[item_kind].plot_max for item_kind in KINDS)


def plot_items(series: Series, item_kind: ItemKind, value: list, from_qwen: bool = False) -> list[PlotItem]:
    """A plot's characters or backgrounds (`item_kind`): the Series' by `id`, each once, or new
    ones by `name` (D13). From the user, anything else raises `invalid_request`. From Qwen
    (`from_qwen`, spec › Plot job step 4) it is dropped instead, and a new one's text is cleaned
    of CJK letters and cut to length. How many there may be is the caller's to check."""

    def text(item: dict, field: str, least: int, most: int) -> str:
        found = item.get(field, "")
        if from_qwen:
            return llm_reply.clean(found)[:most] if isinstance(found, str) else ""
        return checked_text(found, least, most)

    def drop() -> None:
        """An item that isn't one: Qwen's is dropped, the user's refused."""
        if not from_qwen:
            raise invalid_request()

    items: list[PlotItem] = []
    for item in value:
        if not isinstance(item, dict):
            drop()
            continue
        item_id = item.get("id")
        # Qwen names an `id` only for the Series' own (spec › Plot job step 3); the page sends `null` with a new one.
        names_own = "id" in item if from_qwen else item_id is not None
        if names_own:
            if series_module.find_item(series, item_kind, item_id) is None or any(i.id == item_id for i in items):
                drop()
            else:
                items.append(PlotItem(id=item_id))
            continue
        name = text(item, "name", 1, series_module.ITEM_NAME_MAX)  # `checked_text` raises at an empty one
        if not name:
            continue  # Qwen's: no name, nothing to make
        new = PlotItem(new=True, name=name, description=text(item, "description", 0, series_module.DESCRIPTION_MAX))
        if KINDS[item_kind].tagged:
            new.tag = text(item, "tag", 0, series_module.TAG_MAX)
        items.append(new)
    return items


def _sound(project: ProjectPaths, value: object, now: Sound | None) -> Sound | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise invalid_request()
    sound_id = value.get("sound_id", now.sound_id if now else None)
    volume = value.get("volume", now.volume if now else Sound.model_fields["volume"].default)
    if not sounds.exists(project, sound_id):  # with the store's lock held (ADR 0038)
        raise ApiError(400, "invalid_request", "ไม่พบเสียงนี้ในคลังเสียง")
    if not is_int(volume) or not 0 <= volume <= VOLUME_MAX:
        raise ApiError(400, "invalid_request", f"ความดังต้องเป็น 0–{VOLUME_MAX}")
    return Sound(sound_id=sound_id, volume=volume)


def _ep_number(ep_address: EpAddress, value: object) -> int:
    others = store.list_eps(ep_address.project, ep_address.series_id)
    taken = {other.n for other in others if other.id != ep_address.ep_id}
    if not is_int(value) or not 1 <= value <= EP_NUMBER_MAX or value in taken:
        raise ApiError(400, "invalid_ep_number", f"เลข EP ต้องเป็น 1–{EP_NUMBER_MAX} และไม่ซ้ำกับ EP อื่นในชุด")
    return value


def _jobs_on(ep_id: str) -> list[EpUse]:
    """One entry per unfinished job working on the EP."""
    return [use for current in ep_jobs if (use := current()) is not None and use.ep_id == ep_id]


def _locked(ep_id: str) -> bool:
    return any(use.how == "locks" for use in _jobs_on(ep_id))


def rendering(ep_id: str) -> bool:
    """Whether a Render job works on the EP."""
    return any(use.how == "renders" for use in _jobs_on(ep_id))


@contextmanager
def _editing(ep_address: EpAddress) -> Iterator[tuple[Series, Ep, list[Card]]]:
    """An edit of the EP under the store's lock: the Series, the EP to change, and a list for
    the cards it takes out. The EP is written when the block ends, then those cards' files go."""
    with store.lock:
        series, ep = editable(ep_address)
        removed: list[Card] = []
        yield series, ep, removed
        store.write_ep(ep_address, ep)
        remove_card_files(ep_address, removed)


def _require_background(series: Series, background_id: object) -> str:
    """A segment's background is one of the Series'; raises `ApiError` 400 `invalid_request`."""
    if series_module.find_item(series, "backgrounds", background_id) is None:
        raise ApiError(400, "invalid_request", "เลือกฉากหลังของช่วง")
    return background_id


def editable(ep_address: EpAddress) -> tuple[Series, Ep]:
    """The EP to change; `ep_locked` while a Plot or Cards job works on it. Call with the
    store's lock held."""
    found = read(ep_address)
    if _locked(ep_address.ep_id):
        raise ApiError(409, "ep_locked", "AI กำลังเขียน EP นี้: แก้ได้อีกครั้งเมื่องานจบ")
    return found


def address_of(project: ProjectPaths, ep_id: object) -> EpAddress:
    """Where the EP an id names lives, whichever Series holds it: a route's `{ep_id}`, a job's
    `ep_id`. It never refuses: an id no Series holds gets an empty `series_id`, so `read` answers
    `404` at the point each function always checked it, after the body's own checks."""
    with store.lock:
        found = store.locate_ep(project, ep_id) if isinstance(ep_id, str) else None
    return found or EpAddress(project, "", ep_id if isinstance(ep_id, str) else "")


def read(ep_address: EpAddress) -> tuple[Series, Ep]:
    """The EP with its Series, read now. Raises `ApiError` 404 `not_found`."""
    series = store.read_series(ep_address.project, ep_address.series_id)
    ep = store.read_ep(ep_address) if series is not None else None
    if ep is None:
        raise ApiError(404, "not_found", "ไม่พบ EP นี้")
    return series, ep


def look_up(project: ProjectPaths, ep_id: object) -> tuple[EpAddress, Series, Ep]:
    """A job's `ep_id`: the EP's address, its Series and the EP. Raises `ApiError` 404 `not_found`."""
    ep_address = address_of(project, ep_id)
    return ep_address, *read(ep_address)


def ep_cards(ep: Ep):
    """Every card of the EP in order."""
    return (card for _, card in placed_cards(ep))


def placed_cards(ep: Ep):
    """Every card of the EP in order, with the segment it is in (its background)."""
    return ((segment, card) for _, segment in _placed_segments(ep) for card in segment.cards)


def _placed_segments(ep: Ep) -> Iterator[tuple[Act, Segment]]:
    """Every segment of the EP in order, with the act it is in."""
    return ((act, segment) for act in ep.acts for segment in act.segments)


def _ids(ep: Ep) -> set[str]:
    return {item.id for _, segment in _placed_segments(ep) for item in [segment, *segment.cards]}


def _find(items: list, item_id: object):
    found = next((item for item in items if item.id == item_id), None)
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบส่วนนี้ของ EP")
    return found


def _segment(ep: Ep, segment_id: object) -> Segment:
    return _find([segment for _, segment in _placed_segments(ep)], segment_id)


def card_of(ep: Ep, card_id: object) -> Card:
    """Raises `ApiError` 404 `not_found` when the EP has no such card."""
    return _find(list(ep_cards(ep)), card_id)


def _insert(items: list, item, body: dict) -> None:
    """At the end when the body has no `after`; first when `after` is null; else after that id."""
    if "after" not in body:
        items.append(item)
    elif body["after"] is None:
        items.insert(0, item)
    else:
        items.insert(items.index(_find(items, body["after"])) + 1, item)


def eps_playing(project: ProjectPaths, sound_id: str) -> list[str]:
    """`{Series} · EP {n} {title}` of each EP with a segment that plays the sound, by Series
    name then EP number. `sounds.delete` calls it with the store's lock held (D25, sound-library D7)."""
    return [
        f"{found.name} · EP {ep.n} {ep.title}".rstrip()
        for found in store.list_series(project)
        for ep in store.list_eps(project, found.id)
        if any(segment.sound and segment.sound.sound_id == sound_id for _, segment in _placed_segments(ep))
    ]


sounds.sound_users.append(sounds.SoundUser(tab="toon", lock=lambda: store.lock, playing=eps_playing))
