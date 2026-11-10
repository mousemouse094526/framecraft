"""EPs of a Series: creating one, its plot, its acts, segments and cards, the edits the page
makes, and the state of each card (toon spec › ข้อมูล, › สถานะการ์ด, › API, D8–D10, D13–D15,
D20, D21, D24–D26, D30, D40, spoil-maker D74).

Every edit is refused `ep_locked` while a job locks the EP (a Plot or Cards job) and every
delete `ep_busy` while any job works on it: each job slot of the tab adds a check to `ep_jobs`.
"""

import logging
import shutil
from collections.abc import Callable
from typing import Literal, NamedTuple, get_args

from pydantic import BaseModel

from backend import gpu, renders
from backend.errors import ApiError, invalid_request
from backend.json_values import is_int, is_number
from backend.paths import ProjectPaths
from backend.spoil_maker import thai, voices
from backend.toon import series as series_module
from backend.toon import store
from backend.toon.kinds import KINDS, ItemKind
from backend.toon.store import Act, Card, Ep, Motion, Plot, PlotItem, Segment, Series, Sound, Stage

log = logging.getLogger(__name__)

IDEA_MAX, TITLE_MAX, SUMMARY_MAX = 500, 60, 1000
TEXT_MAX, CARD_DESCRIPTION_MAX = 200, 500  # D53
PLOT_CHARACTERS_MAX, PLOT_BACKGROUNDS_MAX = 6, 6
CARD_CHARACTERS_MAX = 2  # D30
HOLD_MAX, HOLD_STEP, SILENT_HOLD = 5, 0.5, 2  # D14, D21
EP_NUMBER_MAX = 999  # D40
GAP_S = 0.3  # after the narration, before the next card (D21)
TARGET_S = 90  # what the AI writes toward, inside the page's 60–120 (D14)
MOTIONS = get_args(Motion)
ImageStatus = Literal["no_ref", "no_image", "stale_ref", "ready"]  # spec › สถานะการ์ด
AudioStatus = Literal["silent", "no_audio", "stale_audio", "ready"]
VOLUME_MAX = 100
UNKNOWN_CHARS_PER_S = 15.0  # an EP's voice can't be deleted (D25); this only guesses for a broken file



class EpUse(NamedTuple):
    """The EP an unfinished job works on, as its slot says it in `ep_jobs`."""

    ep_id: str
    # `locks`: edits of the EP are `ep_locked` (a Plot or Cards job); `renders`: a Render job,
    # so starting a Plot or Cards job on the EP is `ep_busy` (D57); `works`: any other job.
    how: Literal["works", "locks", "renders"]


ep_jobs: list[Callable[[], EpUse | None]] = []
"""What each job slot of the tab works on now, or None. Each reads its job without its slot's
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
            rendered_at=renders.latest_at(project.ep_renders_dir(series_id, ep.id)),
        )
        for ep in reversed(eps)
    ]


def create(project: ProjectPaths, series_id: str, body: dict) -> EpView:
    """A new EP numbered past the highest the Series ever had (D40), with the Series' acts
    and voice (D8, D11); its plot comes from a Plot job."""
    idea = series_module.checked_text(body.get("idea"), 1, IDEA_MAX)
    with gpu.slot.draft_lock, store.lock:
        series = _series(project, series_id)
        taken = store.ep_ids(project)
        series.max_ep += 1
        ep = Ep(
            id=store.new_id("e", taken),
            n=series.max_ep,
            idea=idea,
            voice_id=series.voice_id,
            acts=[Act(id=store.new_id("a"), name=name) for name in series.acts],
        )
        store.write_ep(project, series_id, ep)
        store.write_series(project, series)
    log.info("created EP %s in %s", ep.id, series_id)
    return view(project, ep.id)


def view(project: ProjectPaths, ep_id: str) -> EpView:
    with store.lock:
        series, ep = find(project, ep_id)
        chars_per_s = voices.chars_per_s(project, ep.voice_id) or UNKNOWN_CHARS_PER_S
        refs = {item.id: item.ref_rev for item in [*series.characters, *series.backgrounds]}
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


def change(project: ProjectPaths, ep_id: str, body: dict) -> EpView:
    """`title` (D24), `n` (D40), `voice_id` (D8) and `plot` (D13). A `voice_id` is written under
    the draft's lock, so a Saved voice delete can't slip in (D25)."""
    with gpu.slot.draft_lock, store.lock:
        series, ep = editable(project, ep_id)
        if "title" in body:
            ep.title = series_module.checked_text(body["title"], 0, TITLE_MAX)
        if "n" in body:
            ep.n = _ep_number(project, series, ep, body["n"])
            if ep.n > series.max_ep:
                series.max_ep = ep.n
                store.write_series(project, series)
        if "voice_id" in body:
            ep.voice_id = series_module.existing_voice(project, body["voice_id"])
        if "plot" in body:
            ep.plot = _plot(series, body["plot"], ep.stage == "cards")
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def delete(project: ProjectPaths, ep_id: str) -> None:
    """Removes the EP's folder: its plot, cards, images, narration and renders (D26).
    Characters and backgrounds it added stay in the Series."""
    with store.lock:
        series, ep = find(project, ep_id)
        if _jobs_on(ep_id):
            raise ApiError(409, "ep_busy", "EP นี้มีงานที่ยังไม่จบ")
        shutil.rmtree(project.ep_dir(series.id, ep_id))
    log.info("deleted EP %s of %s", ep_id, series.id)


# --- acts ---


def add_act(project: ProjectPaths, ep_id: str, body: dict) -> EpView:
    """An act the user adds: never split, so a Cards job counts it as changed (D10, D15)."""
    name = series_module.checked_text(body.get("name"), 1, series_module.ACT_NAME_MAX)
    summary = series_module.checked_text(body.get("summary", ""), 0, SUMMARY_MAX)
    with store.lock:
        series, ep = editable(project, ep_id)
        act = Act(id=store.new_id("a", {a.id for a in ep.acts}), name=name, summary=summary)
        _insert(ep.acts, act, body)
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def change_act(project: ProjectPaths, ep_id: str, act_id: str, body: dict) -> EpView:
    """The act's `name` and `summary` (D10, D15); a changed summary marks it to split again."""
    with store.lock:
        series, ep = editable(project, ep_id)
        act = _find(ep.acts, act_id)
        if "name" in body:
            act.name = series_module.checked_text(body["name"], 1, series_module.ACT_NAME_MAX)
        if "summary" in body:
            act.summary = series_module.checked_text(body["summary"], 0, SUMMARY_MAX)
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def delete_act(project: ProjectPaths, ep_id: str, act_id: str) -> EpView:
    with store.lock:
        series, ep = editable(project, ep_id)
        act = _find(ep.acts, act_id)
        ep.acts.remove(act)
        store.write_ep(project, series.id, ep)
        remove_card_files(project, series.id, ep.id, [card for segment in act.segments for card in segment.cards])
    return view(project, ep_id)


# --- segments ---


def add_segment(project: ProjectPaths, ep_id: str, body: dict) -> EpView:
    """A segment needs a background of the Series and one card: a silent card the user
    fills, counted as written by them (spec › API, spoil-maker D74)."""
    with store.lock:
        series, ep = editable(project, ep_id)
        act = _find(ep.acts, body.get("act_id"))
        background_id = body.get("background_id")
        if series_module.find_item(series, "backgrounds", background_id) is None:
            raise ApiError(400, "invalid_request", "เลือกฉากหลังของช่วง")
        taken = _ids(ep)
        card = Card(id=store.new_id("k", taken), hold_s=SILENT_HOLD, edited=True)
        segment = Segment(id=store.new_id("g", taken), background_id=background_id, cards=[card])
        _insert(act.segments, segment, body)
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def change_segment(project: ProjectPaths, ep_id: str, segment_id: str, body: dict) -> EpView:
    """The segment's background (cards drawn on the old one go `stale_ref`, D32) and its
    background sound: off (`null`), another from the library, or its volume (D5)."""
    with store.lock:
        series, ep = editable(project, ep_id)
        segment = _segment(ep, segment_id)
        if "background_id" in body:
            if series_module.find_item(series, "backgrounds", body["background_id"]) is None:
                raise ApiError(400, "invalid_request", "เลือกฉากหลังของช่วง")
            segment.background_id = body["background_id"]
        if "sound" in body:
            segment.sound = _sound(project, body["sound"], segment.sound)
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def delete_segment(project: ProjectPaths, ep_id: str, segment_id: str) -> EpView:
    with store.lock:
        series, ep = editable(project, ep_id)
        segment = _segment(ep, segment_id)
        next(act for act in ep.acts if segment in act.segments).segments.remove(segment)
        store.write_ep(project, series.id, ep)
        remove_card_files(project, series.id, ep.id, segment.cards)
    return view(project, ep_id)


# --- cards ---


def add_card(project: ProjectPaths, ep_id: str, body: dict) -> EpView:
    """A card the user inserts is `edited` (spoil-maker D74); a silent one holds 2 s (D21)."""
    with store.lock:
        series, ep = editable(project, ep_id)
        segment = _segment(ep, body.get("segment_id"))
        card = Card(id=store.new_id("k", _ids(ep)), edited=True)
        _apply_card(series, card, body)
        if "hold_s" not in body and not card.text:
            card.hold_s = SILENT_HOLD
        _check_card(card)
        _insert(segment.cards, card, body)
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def change_card(project: ProjectPaths, ep_id: str, card_id: str, body: dict) -> EpView:
    """A changed `text` or `description` makes the card `edited` (spoil-maker D74)."""
    with store.lock:
        series, ep = editable(project, ep_id)
        card = card_of(ep, card_id)
        before = (card.text, card.description)
        _apply_card(series, card, body)
        _check_card(card)
        if (card.text, card.description) != before:
            card.edited = True
        store.write_ep(project, series.id, ep)
    return view(project, ep_id)


def delete_card(project: ProjectPaths, ep_id: str, card_id: str) -> EpView:
    """The last card of a segment takes the segment with it (spec › API)."""
    with store.lock:
        series, ep = editable(project, ep_id)
        card = card_of(ep, card_id)
        for act in ep.acts:
            for segment in act.segments:
                if card in segment.cards:
                    segment.cards.remove(card)
                    if not segment.cards:
                        act.segments.remove(segment)
                    break
        store.write_ep(project, series.id, ep)
        remove_card_files(project, series.id, ep.id, [card])
    return view(project, ep_id)


def remove_card_files(project: ProjectPaths, series_id: str, ep_id: str, cards: list[Card]) -> None:
    """The images and narration of cards that are gone (D15)."""
    images, audio = project.card_images_dir(series_id, ep_id), project.card_audio_dir(series_id, ep_id)
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


def card_seconds(card: Card, status: str, chars_per_s: float) -> float:
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
        card.text = series_module.checked_text(body["text"], 0, TEXT_MAX)
    if "description" in body:
        card.description = series_module.checked_text(body["description"], 0, CARD_DESCRIPTION_MAX)
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
    plot = Plot(
        characters=_plot_items(series, "characters", value.get("characters", []), PLOT_CHARACTERS_MAX),
        backgrounds=_plot_items(series, "backgrounds", value.get("backgrounds"), PLOT_BACKGROUNDS_MAX),
    )
    if not plot.backgrounds:
        raise ApiError(400, "invalid_request", "พล็อตต้องมีฉากหลังอย่างน้อยหนึ่ง")
    if confirmed and any(item.new for item in [*plot.characters, *plot.backgrounds]):
        raise ApiError(400, "invalid_request", "ยืนยันพล็อตแล้ว: เพิ่มตัวละครหรือฉากหลังใหม่ที่หน้าตัวละครของชุด")
    return plot


def _plot_items(series: Series, item_kind: ItemKind, value: object, most: int) -> list[PlotItem]:
    if not isinstance(value, list) or len(value) > most or not all(isinstance(item, dict) for item in value):
        raise invalid_request()
    items: list[PlotItem] = []
    for item in value:
        if item.get("id") is not None:
            if series_module.find_item(series, item_kind, item["id"]) is None or any(i.id == item["id"] for i in items):
                raise invalid_request()
            items.append(PlotItem(id=item["id"]))
        else:
            new = PlotItem(
                new=True,
                name=series_module.checked_text(item.get("name"), 1, series_module.ITEM_NAME_MAX),
                description=series_module.checked_text(item.get("description", ""), 0, series_module.DESCRIPTION_MAX),
            )
            if KINDS[item_kind].tagged:
                new.tag = series_module.checked_text(item.get("tag", ""), 0, series_module.TAG_MAX)
            items.append(new)
    return items


def _sound(project: ProjectPaths, value: object, now: Sound | None) -> Sound | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise invalid_request()
    sound_id = value.get("sound_id", now.sound_id if now else None)
    volume = value.get("volume", now.volume if now else Sound.model_fields["volume"].default)
    if sound_id not in {sound.id for sound in store.read_sounds(project)}:
        raise ApiError(400, "invalid_request", "ไม่พบเสียงนี้ในคลังเสียงพื้น")
    if not is_int(volume) or not 0 <= volume <= VOLUME_MAX:
        raise ApiError(400, "invalid_request", f"ความดังต้องเป็น 0–{VOLUME_MAX}")
    return Sound(sound_id=sound_id, volume=volume)


def _ep_number(project: ProjectPaths, series: Series, ep: Ep, value: object) -> int:
    taken = {other.n for other in store.list_eps(project, series.id) if other.id != ep.id}
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


def editable(project: ProjectPaths, ep_id: str) -> tuple[Series, Ep]:
    """The EP to change; `ep_locked` while a Plot or Cards job works on it. Call with the
    store's lock held."""
    found = find(project, ep_id)
    if _locked(ep_id):
        raise ApiError(409, "ep_locked", "AI กำลังเขียน EP นี้: แก้ได้อีกครั้งเมื่องานจบ")
    return found


def find(project: ProjectPaths, ep_id: object) -> tuple[Series, Ep]:
    """The EP with its Series. Raises `ApiError` 404 `not_found`."""
    found = store.find_ep(project, ep_id) if isinstance(ep_id, str) else None
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบ EP นี้")
    return found


def _series(project: ProjectPaths, series_id: str) -> Series:
    series = store.read_series(project, series_id)
    if series is None:
        raise ApiError(404, "not_found", "ไม่พบ Series นี้")
    return series


def ep_cards(ep: Ep):
    """Every card of the EP in order."""
    return (card for _, card in placed_cards(ep))


def placed_cards(ep: Ep):
    """Every card of the EP in order, with the segment it is in (its background)."""
    return ((segment, card) for act in ep.acts for segment in act.segments for card in segment.cards)


def _ids(ep: Ep) -> set[str]:
    return {item.id for act in ep.acts for segment in act.segments for item in [segment, *segment.cards]}


def _find(items: list, item_id: object):
    found = next((item for item in items if item.id == item_id), None)
    if found is None:
        raise ApiError(404, "not_found", "ไม่พบส่วนนี้ของ EP")
    return found


def _segment(ep: Ep, segment_id: object) -> Segment:
    return _find([segment for act in ep.acts for segment in act.segments], segment_id)


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
