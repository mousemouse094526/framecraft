"""The prompts of the Plot job and the Cards job, and the reading of Qwen's answers (toon spec
› Plot job, › Cards job, D5, D9, D12, D13, D21, D24, D30, D41).

A reply is read the way the spoil-maker Draft job reads one: the JSON object in it, its text
cleaned (`llm_reply.clean`). A reply that can't be used is None, and the job asks again.
"""

from collections.abc import Collection

from pydantic import BaseModel

from backend import llm_reply
from backend.toon import episodes, store
from backend.toon.kinds import KINDS, ItemKind
from backend.toon.store import Act, Card, Plot, Segment, Series, StoredSound

ATTEMPTS = 3
TEMPERATURE = 0.3  # spoil-maker D61
PLOT_MAX_TOKENS, CARDS_MAX_TOKENS = 2048, 4096  # D53


class WrittenPlot(BaseModel):
    title: str
    summaries: list[str]
    plot: Plot


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
    by_kind = {item_kind: found.get(item_kind) for item_kind in KINDS}
    if not all(value is None or isinstance(value, list) for value in by_kind.values()):
        return None
    plot = episodes.plot_of(cast, {item_kind: value or [] for item_kind, value in by_kind.items()}, from_qwen=True)
    if not plot.backgrounds or episodes.over_max({item_kind: getattr(plot, item_kind) for item_kind in KINDS}):
        return None
    return WrittenPlot(title=title, summaries=summaries, plot=plot)


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
            background_id=background if _one_of(background, background_ids) else background_ids[0],
            sound=store.Sound(sound_id=sound) if _one_of(sound, sound_ids) else None,
            cards=cards,
        )
        segments.append(segment)
    return segments or None


def known(plot: Plot, cast: Series) -> dict[ItemKind, list[Known]]:
    """The plot's items of each kind as the Cards job's prompt names them, all by an id of the Series."""

    def known_of(item_kind: ItemKind) -> list[Known]:
        by_id = {item.id: item for item in getattr(cast, item_kind)}
        items = getattr(plot, item_kind)
        return [Known(id=item.id, name=by_id[item.id].name, description=by_id[item.id].description) for item in items]

    return {item_kind: known_of(item_kind) for item_kind in KINDS}


# --- helpers ---


def _card(value: object, character_ids: set[str], taken: set[str]) -> Card | None:
    if not isinstance(value, dict):
        return None
    text = _cleaned(value.get("text"))[: episodes.TEXT_MAX]
    named = [c for c in _list(value.get("characters")) if _one_of(c, character_ids)]
    characters = list(dict.fromkeys(named))[: episodes.CARD_CHARACTERS_MAX]
    motion = value.get("motion")
    return Card(
        id=_new_id("k", taken),
        text=text,
        character_ids=characters,
        description=_cleaned(value.get("description"))[: episodes.CARD_DESCRIPTION_MAX],
        motion=motion if _one_of(motion, episodes.MOTIONS) else "still",
        flicker=value.get("flicker") is True,
        hold_s=0 if text else episodes.SILENT_HOLD,
    )


def _cleaned(value: object) -> str:
    return llm_reply.clean(value) if isinstance(value, str) else ""


def _one_of(value: object, ids: Collection[str]) -> bool:
    """Whether Qwen's value is one of these; a list or an object where a name belongs is not."""
    return isinstance(value, str) and value in ids


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _lines(items) -> str:
    """One line per character or background: its id, name and description."""
    return "\n".join(f"- {item.id}: {item.name} — {item.description}" for item in items) or "(ไม่มี)"


def _new_id(prefix: str, taken: set[str]) -> str:
    found = store.new_id(prefix, taken)
    taken.add(found)
    return found

