"""The Cards job: Qwen splits each act of an EP's plot into segments and cards (toon spec ›
Cards job, D13, D15, D43, D54). The first split takes every act, later ones those whose
summary changed. Like the Plot job it locks its EP and writes it only at its end.
"""

import logging

from pydantic import BaseModel

from backend import gate_rows
from backend.errors import ApiError, JobFailed, invalid_request
from backend.paths import EpAddress, ProjectPaths
from backend.toon import episodes, plot, series, steps, store, writer
from backend.toon.store import Ep, Series

log = logging.getLogger(__name__)


class LostCards(BaseModel):
    """What re-splitting one act throws away (D15, D43)."""

    id: str
    name: str
    edited: int
    images: int
    audio: int


class CardsPlan(BaseModel):
    """What a Cards job splits, read once under the store's lock as it starts."""

    series: Series
    ep: Ep
    act_ids: list[str]
    chars_per_s: float


def plan(project: ProjectPaths, body: dict) -> CardsPlan:
    """Spec › Cards job step 1 up to the gate: the acts to split, and what they would lose (D15, D43)."""
    confirm_loss = body.get("confirm_loss", False)
    if not isinstance(confirm_loss, bool):
        raise invalid_request()
    found = plot.writable(project, body.get("ep_id"))
    ep = found.ep
    if not ep.plot.backgrounds:
        raise ApiError(400, "invalid_request", "พล็อตต้องมีฉากหลังอย่างน้อยหนึ่ง")
    acts = [act for act in ep.acts if ep.stage == "plot" or act.summary != act.cards_from]
    if not acts:
        raise ApiError(400, "nothing_to_split", "ไม่มีองก์ที่พล็อตเปลี่ยน")
    lost = [_lost(act) for act in acts]
    if not confirm_loss and any(act.edited or act.images or act.audio for act in lost):
        raise ApiError(
            409, "cards_will_be_lost", "การ์ดที่แก้เอง ภาพ หรือเสียงขององก์ที่แตกใหม่จะหาย", acts=[a.model_dump() for a in lost]
        )
    return CardsPlan(series=found.series, ep=ep, act_ids=[act.id for act in acts], chars_per_s=found.chars_per_s)


def run(job: steps.Run, project: ProjectPaths, plan: CardsPlan) -> None:
    """Spec › Cards job steps 2–6: each act to split is asked up to three times; all are written at once at
    the end, with the plot's new characters and backgrounds entering the Series (D13, D15).
    An act with no card after three tries fails the job."""
    series_now, ep = plan.series, plan.ep
    added = series.new_items(series_now, ep.plot)
    cast = series_now.model_copy(
        update={item_kind: [*getattr(series_now, item_kind), *items] for item_kind, items in added.items()}
    )
    known = writer.known(ep.plot, cast)
    characters, backgrounds = known["characters"], known["backgrounds"]
    sounds = store.read_sounds(project)
    chars_per_act = round(episodes.TARGET_S / len(ep.acts) * plan.chars_per_s)
    ids = {i.id for act in ep.acts for segment in act.segments for i in [segment, *segment.cards]}
    qwen = steps.Qwen(job, project)
    written: dict[str, list] = {}
    for done, act_id in enumerate(plan.act_ids, start=1):
        index = next(i for i, act in enumerate(ep.acts) if act.id == act_id)
        prompt = writer.cards_prompt(cast.tone, ep.acts, index, characters, backgrounds, sounds, chars_per_act)
        segments = qwen.answer(
            prompt,
            writer.CARDS_MAX_TOKENS,
            lambda reply: writer.parse_cards(
                reply, [b.id for b in backgrounds], {c.id for c in characters}, {s.id for s in sounds}, ids
            ),
            f"cards of act {index + 1}",
        )
        if segments is None:
            raise JobFailed("write_failed", f"AI แตกการ์ดองก์ {ep.acts[index].name} ไม่สำเร็จ {writer.ATTEMPTS} ครั้ง")
        written[act_id] = segments
        job.update(done=done)
    with store.lock:
        series_now = store.read_series(project, plan.series.id)
        for item_kind, items in added.items():
            getattr(series_now, item_kind).extend(items)
        ep_address = EpAddress(project, plan.series.id, ep.id)
        ep_now = store.read_ep(ep_address)
        in_library = {s.id for s in store.read_sounds(project)}  # a sound deleted while Qwen wrote: none
        gone = []
        for act in ep_now.acts:
            if act.id in written:
                for segment in written[act.id]:
                    if segment.sound is not None and segment.sound.sound_id not in in_library:
                        segment.sound = None
                gone.extend(card for segment in act.segments for card in segment.cards)
                act.segments, act.cards_from = written[act.id], act.summary
        ep_now.plot, ep_now.stage = ep.plot, "cards"
        store.write_series(project, series_now)
        store.write_ep(ep_address, ep_now)
        episodes.remove_card_files(ep_address, gone)


def _lost(act) -> LostCards:
    cards = [card for segment in act.segments for card in segment.cards]
    return LostCards(
        id=act.id,
        name=act.name,
        edited=sum(card.edited for card in cards),
        images=sum(card.image is not None for card in cards),
        audio=sum(card.audio is not None for card in cards),
    )


WORK = steps.Work(
    gpu_kind="toon_write",
    child=steps.WRITER,
    plan=plan,
    rows=gate_rows.qwen_jobs,
    job=lambda plan: {
        "state": "writing",
        "series_id": plan.series.id,
        "ep_id": plan.ep.id,
        "done": 0,
        "total": len(plan.act_ids),
    },
    run=run,
    log_name=lambda plan: f"toon job cards {plan.ep.id}",
)
