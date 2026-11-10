"""The prompts of the Plot job and the Cards job, and the reading of Qwen's answers (toon spec
› Plot job, › Cards job, D5, D9, D12, D13, D21, D24, D30, D41).

A reply is read the way the spoil-maker Draft job reads one: the JSON object in it, its text
cleaned (`llm_reply.clean`). A reply that can't be used is None, and the job asks again.
"""

from pydantic import BaseModel

from backend import llm_reply
from backend.toon import episodes, series, store
from backend.toon.kinds import KINDS, ItemKind
from backend.toon.store import Act, Card, PlotItem, Segment, Series, StoredSound

ATTEMPTS = 3
TEMPERATURE = 0.3  # spoil-maker D61
PLOT_MAX_TOKENS, CARDS_MAX_TOKENS = 2048, 4096  # D53


class WrittenPlot(BaseModel):
    title: str
    summaries: list[str]
    characters: list[PlotItem]
    backgrounds: list[PlotItem]


class Known(BaseModel):
    """A character or background the prompt names, by the id the answer cites."""

    id: str
    name: str
    description: str


def plot_prompt(cast: Series, idea: str, act_names: list[str], target_letters: int) -> str:
    """Spec › Plot job step 2: the idea, the EP's acts, the Series' tone and its cast."""
    acts = "\n".join(f"{n}. {name}" for n, name in enumerate(act_names, start=1))
    return (
        "เขียนพล็อตของคลิปการ์ตูนเล่าเรื่องแนวตั้งหนึ่งตอน เป็นภาษาไทย\n"
        f"ไอเดีย: {idea}\n"
        f"น้ำเสียงเล่า: {cast.tone}\n"
        f"องก์ของตอนนี้ ({len(act_names)} องก์ ตามลำดับ):\n{acts}\n"
        f"ทั้งตอนเล่าราว {target_letters} ตัวอักษร\n"
        f"ตัวละครที่มีอยู่แล้ว:\n{_lines(cast.characters)}\n"
        f"ฉากหลังที่มีอยู่แล้ว:\n{_lines(cast.backgrounds)}\n"
        "ใช้ตัวละครและฉากหลังที่มีอยู่แล้วด้วย id เมื่อเข้ากับเรื่อง; ต้องการของใหม่ให้ตั้งชื่อและบรรยายหน้าตาหรือสถานที่\n"
        f"ตัวละครไม่เกิน 6, ฉากหลัง 1–6, สรุปองก์ละ 1–3 ประโยค เท่ากับจำนวนองก์\n"
        "ตอบเป็น JSON อย่างเดียว:\n"
        '{"title": "ชื่อตอน", "acts": [{"summary": "..."}], '
        '"characters": [{"id": "c_..."} | {"name": "...", "tag": "คำสั้น", "description": "..."}], '
        '"backgrounds": [{"id": "b_..."} | {"name": "...", "description": "..."}]}'
    )


def parse_plot(reply: str, cast: Series, act_count: int) -> WrittenPlot | None:
    """Spec › Plot job step 4: an answer with a title, one summary per act, at most 6 characters and 1–6
    backgrounds once ids the Series lacks are dropped; None when it isn't one."""
    found = llm_reply.json_object(reply)
    if found is None:
        return None
    title = _cleaned(found.get("title"))[: episodes.TITLE_MAX]
    acts = found.get("acts")
    if not title or not isinstance(acts, list) or len(acts) != act_count:
        return None
    summaries = [_cleaned(act.get("summary") if isinstance(act, dict) else None) for act in acts]
    if not all(summaries):
        return None
    characters = _plot_items(found.get("characters"), cast, "characters")
    backgrounds = _plot_items(found.get("backgrounds"), cast, "backgrounds")
    if (
        characters is None
        or backgrounds is None
        or len(characters) > episodes.PLOT_CHARACTERS_MAX
        or not 1 <= len(backgrounds) <= episodes.PLOT_BACKGROUNDS_MAX
    ):
        return None
    return WrittenPlot(title=title, summaries=summaries, characters=characters, backgrounds=backgrounds)


def cards_prompt(
    tone: str,
    acts: list[Act],
    index: int,
    characters: list[Known],
    backgrounds: list[Known],
    sounds: list[StoredSound],
    target_letters: int,
) -> str:
    """Spec › Cards job step 3, for the act at `index`: its summary with the ones around it."""
    act = acts[index]
    before = acts[index - 1].summary if index > 0 else "(องก์แรก)"
    after = acts[index + 1].summary if index + 1 < len(acts) else "(องก์สุดท้าย)"
    sound_lines = "\n".join(f"- {sound.id}: {sound.name}" for sound in sounds) or "(ไม่มี: ใส่ null)"
    return (
        "แตกองก์หนึ่งของคลิปการ์ตูนเล่าเรื่องเป็นช่วงและการ์ด เป็นภาษาไทย\n"
        f"น้ำเสียงเล่า: {tone}\n"
        f"องก์ก่อนหน้า: {before}\n"
        f"องก์นี้ ({act.name}): {act.summary}\n"
        f"องก์ถัดไป: {after}\n"
        f"องก์นี้เล่าราว {target_letters} ตัวอักษรรวมทุกการ์ด\n"
        f"ตัวละคร:\n{_lines(characters)}\n"
        f"ฉากหลัง:\n{_lines(backgrounds)}\n"
        f"เสียงพื้น:\n{sound_lines}\n"
        "ช่วงคือการ์ดที่ติดกันในฉากหลังเดียว; เปลี่ยนฉากหลังคือช่วงใหม่\n"
        "การ์ดหนึ่งใบคือหนึ่งประโยคเล่า (ว่างได้ = การ์ดเงียบ) กับภาพหนึ่งภาพ: "
        "ตัวละครในภาพ 0–2 ตัว, คำบรรยายภาพบอกท่าทาง สีหน้า มุมกล้อง และแสง, "
        f"การขยับหนึ่งใน {', '.join(episodes.MOTIONS)}, ไฟกะพริบ true หรือ false\n"
        "ตอบเป็น JSON อย่างเดียว:\n"
        '{"segments": [{"background": "b_...", "sound": "m_..." | null, "cards": '
        '[{"text": "...", "characters": ["c_..."], "description": "...", "motion": "still", "flicker": false}]}]}'
    )


def parse_cards(
    reply: str, background_ids: list[str], character_ids: set[str], sound_ids: set[str], taken: set[str]
) -> list[Segment] | None:
    """Spec › Cards job step 5: the act's segments, each kept to what the plot and the library have; None
    when the reply isn't the JSON asked for or holds no card. New ids avoid `taken`."""
    found = llm_reply.json_object(reply)
    segments_found = found.get("segments") if found else None
    if not isinstance(segments_found, list):
        return None
    segments: list[Segment] = []
    for item in segments_found:
        if not isinstance(item, dict):
            continue
        cards = [card for card in map(lambda c: _card(c, character_ids, taken), _list(item.get("cards"))) if card]
        if not cards:
            continue
        background = item.get("background")
        sound = item.get("sound")
        segment = Segment(
            id=_new_id("g", taken),
            background_id=background if background in background_ids else background_ids[0],
            sound=store.Sound(sound_id=sound) if sound in sound_ids else None,
            cards=cards,
        )
        segments.append(segment)
    return segments or None


def known(items: list[PlotItem], cast: Series, item_kind: ItemKind) -> list[Known]:
    """The plot's items as the Cards job's prompt names them, all by an id of the Series."""
    by_id = {item.id: item for item in getattr(cast, item_kind)}
    return [Known(id=item.id, name=by_id[item.id].name, description=by_id[item.id].description) for item in items]


# --- helpers ---


def _card(value: object, character_ids: set[str], taken: set[str]) -> Card | None:
    if not isinstance(value, dict):
        return None
    text = _cleaned(value.get("text"))[: episodes.TEXT_MAX]
    characters = [c for c in dict.fromkeys(_list(value.get("characters"))) if c in character_ids][: episodes.CARD_CHARACTERS_MAX]
    motion = value.get("motion")
    return Card(
        id=_new_id("k", taken),
        text=text,
        character_ids=characters,
        description=_cleaned(value.get("description"))[: episodes.CARD_DESCRIPTION_MAX],
        motion=motion if motion in episodes.MOTIONS else "still",
        flicker=value.get("flicker") is True,
        hold_s=0 if text else episodes.SILENT_HOLD,
    )


def _plot_items(value: object, cast: Series, item_kind: ItemKind) -> list[PlotItem] | None:
    ids = {item.id for item in getattr(cast, item_kind)}
    if value is None:
        return []
    if not isinstance(value, list):
        return None
    items: list[PlotItem] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        if "id" in item:
            if item["id"] in ids and all(found.id != item["id"] for found in items):
                items.append(PlotItem(id=item["id"]))
            continue
        name = _cleaned(item.get("name"))[: series.ITEM_NAME_MAX]
        if name:
            tag = _cleaned(item.get("tag"))[: series.TAG_MAX] if KINDS[item_kind].tagged else ""
            items.append(PlotItem(new=True, name=name, tag=tag, description=_cleaned(item.get("description"))[: series.DESCRIPTION_MAX]))
    return items


def _cleaned(value: object) -> str:
    return llm_reply.clean(value) if isinstance(value, str) else ""


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _lines(items) -> str:
    """One line per character or background: its id, name and description."""
    return "\n".join(f"- {item.id}: {item.name} — {item.description}" for item in items) or "(ไม่มี)"


def _new_id(prefix: str, taken: set[str]) -> str:
    found = store.new_id(prefix, taken)
    taken.add(found)
    return found

