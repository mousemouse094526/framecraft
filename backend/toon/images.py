"""The Image job and card images: which cards it draws, the reference images it draws them
with, its steps and each picture it writes, swapping a card's image with its previous one,
and the files a restart cleans (toon spec › Image job, › คำสั่งภาพ, D13, D27, D29, D30, D32,
D33, D37, D44).

A card's image is `images/{card_id}-{seed}.png`; `image.refs` keeps the `ref_rev` of each
character and background it was drawn with, so a changed reference makes it `stale_ref`.
"""

import logging
import random
import shutil
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel

from backend import disk
from backend.errors import ApiError
from backend.paths import EpAddress, ProjectPaths
from backend.toon import episodes, klein, prompts, series, steps, store
from backend.toon.kinds import CARD_SIZE, ItemKind
from backend.toon.klein import Draw, Drawn
from backend.toon.store import Card, CardImage, Segment, Series

log = logging.getLogger(__name__)

Scope = Literal["missing", "stale_ref"]  # every card with no image, or every `stale_ref` one (D33, D44)


class MissingRef(BaseModel):
    """A character or background with no reference image yet, and how many cards of the job
    it made skip (D13)."""

    item_kind: ItemKind
    id: str
    name: str
    cards: int


class CardDraw(BaseModel):
    """One card of an Image job as it starts: what its prompt and its picture need."""

    card_id: str
    description: str
    names: list[str]  # its characters' names: `character 1`, `character 2` (spec › คำสั่งภาพ)
    refs: dict[str, int]  # the `ref_rev` of each character, then the background, as copied
    ref_paths: list[Path]  # the copies in `.image-job/`, in the same order


class ImagePlan(BaseModel):
    ep_address: EpAddress
    style: str
    size: tuple[int, int]  # a card is drawn as big as its Series' background (D37)
    scope: Scope | None  # the job draws every card the scope takes, not one
    cards: list[CardDraw]
    skipped: int
    missing_refs: list[MissingRef]


def plan(project: ProjectPaths, body: dict) -> ImagePlan:
    """The cards of the job in the EP's order: `card_id` one card, else `scope`'s. Raises
    `not_found`, `invalid_request`, `no_ref` for one card, and `nothing_to_draw` with
    `missing_refs` when every card of the scope is skipped or there is none. Copies no file."""
    card_id, scope = body.get("card_id"), body.get("scope")
    if (card_id is None) == (scope is None) or (scope is not None and scope not in get_args(Scope)):
        raise ApiError(400, "invalid_request", "เลือกการ์ดหนึ่งใบ หรือขอบเขตของภาพที่จะสร้าง")
    with store.lock:
        ep_address, series_now, ep = episodes.look_up(project, body.get("ep_id"))
        refs = series.ref_revs(series_now)
        placed = [(s, c, episodes.image_status(c, s, refs)) for s, c in episodes.placed_cards(ep)]
        if card_id is not None:
            segment, card, status = next(((s, c, st) for s, c, st in placed if c.id == card_id), (None, None, None))
            if card is None:
                raise ApiError(404, "not_found", "ไม่พบการ์ดนี้")
            if status == "no_ref":
                raise ApiError(400, "no_ref", "ตัวละครหรือฉากหลังของการ์ดนี้ยังไม่มีภาพอ้างอิง")
            wanted, skipped = [(segment, card)], []
        else:
            in_scope = [(s, c, st) for s, c, st in placed if _in_scope(scope, st, c)]
            wanted = [(s, c) for s, c, st in in_scope if st != "no_ref"]
            skipped = [(s, c) for s, c, st in in_scope if st == "no_ref"]
        missing = _missing_refs(series_now, skipped)
        if not wanted:
            raise ApiError(
                400, "nothing_to_draw", "ไม่มีการ์ดให้สร้างภาพ", missing_refs=[m.model_dump() for m in missing]
            )
        return ImagePlan(
            ep_address=ep_address,
            style=series_now.style,
            size=CARD_SIZE[series_now.layout],
            scope=scope,
            cards=[_card_draw(project, series_now, segment, card, refs) for segment, card in wanted],
            skipped=len(skipped),
            missing_refs=missing,
        )


def copy_refs(project: ProjectPaths, plan: ImagePlan) -> None:
    """Spec › Image job step 1: the reference images the job uses go into `.image-job/`, so one can change or
    go meanwhile. Call with the store's lock held, as `plan` read their `ref_rev`."""
    folder = project.image_job_dir
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    refs = project.refs_dir(plan.ep_address.series_id)
    for card in plan.cards:
        # `ref_paths` is built from `refs` in its order, one path per item id (`_card_draw`).
        for item_id, path in zip(card.refs, card.ref_paths, strict=True):
            if not path.is_file():
                shutil.copyfile(refs / f"{item_id}-{card.refs[item_id]}.png", path)


def put_image(plan: ImagePlan, card: CardDraw, png: bytes, seed: int, prompt: str) -> bool:
    """Spec › Image job step 4: the new PNG, then under the lock the card's image becomes its previous one and
    the new one its image, then the old previous file goes (D33). False when the card went
    meanwhile (deleted, or its act split again): the picture is dropped."""
    images = plan.ep_address.images_dir
    images.mkdir(parents=True, exist_ok=True)
    picture = images / f"{card.card_id}-{seed}.png"
    picture.write_bytes(png)
    with store.lock:
        ep = store.read_ep(plan.ep_address)
        stored = next((c for _, c in episodes.placed_cards(ep) if c.id == card.card_id), None) if ep else None
        if stored is None:
            picture.unlink(missing_ok=True)
            return False
        dropped = stored.previous_image
        stored.previous_image = stored.image
        stored.image = CardImage(file=picture.name, refs=card.refs, prompt=prompt)
        store.write_ep(plan.ep_address, ep)
        if dropped is not None and dropped.file != picture.name:
            (images / dropped.file).unlink(missing_ok=True)
    return True


def run(job: steps.Run, project: ProjectPaths, plan: ImagePlan) -> None:
    """Spec › Image job steps 2–6: Qwen translates every card's description as it was at the
    start, its child ends (D36), then klein encodes every prompt and draws the cards in order,
    each written as soon as it is (D33). A card klein fails on is counted and the job goes on."""
    asks = [prompts.card_scene_prompt(c.description, c.names) if c.description else None for c in plan.cards]
    scenes = steps.scenes(job, project, asks, counted=True)
    card_prompts = [
        prompts.card_prompt(scene or prompts.fallback_scene(len(c.names), c.description), plan.style, len(c.names))
        for c, scene in zip(plan.cards, scenes, strict=True)
    ]
    job.update(state="drawing", done=0)
    drawer = steps.open_klein(job, project, card_prompts)
    width, height = plan.size
    failed: list[str] = []
    for done, (card, prompt) in enumerate(zip(plan.cards, card_prompts, strict=True), start=1):
        seed = random.randint(0, steps.SEED_MAX)
        request = Draw(index=done - 1, ref_paths=card.ref_paths, width=width, height=height, seed=seed)
        # A `WorkerError` asked for comes back like a `Drawn` instead of failing the job.
        drawn = steps.draw(job, drawer, request, (Drawn, klein.WorkerError))
        if isinstance(drawn, klein.WorkerError):
            log.error("klein failed on card %s (%s): %s", card.card_id, drawn.code, drawn.detail)
            failed.append(card.card_id)
        elif not put_image(plan, card, drawn.png, seed, prompt):
            log.info("the picture of card %s is dropped: the card went", card.card_id)
        job.update(done=done, failed_cards=list(failed))
    drawer.end()


def _ready(project: ProjectPaths, plan: ImagePlan) -> None:
    disk.require_free(project.root)
    copy_refs(project, plan)


WORK = steps.Work(
    gpu_kind="toon_image",
    child=steps.DRAWER,
    plan=plan,
    rows=steps.image_rows,
    # Under the store's lock with the job set, as the cards are read again: each copy of a
    # reference image is the `ref_rev` its card records.
    job=lambda plan: {
        "state": "translating",
        "series_id": plan.ep_address.series_id,
        "ep_id": plan.ep_address.ep_id,
        "card_ids": [card.card_id for card in plan.cards],
        "scope": plan.scope,
        "done": 0,
        "total": len(plan.cards),
        "skipped": plan.skipped,
        "missing_refs": plan.missing_refs,
        "failed_cards": [],
    },
    run=run,
    log_name=lambda plan: f"toon job image {plan.ep_address.ep_id} ({len(plan.cards)} cards)",
    ready=_ready,
    clean_up=lambda project, plan: shutil.rmtree(project.image_job_dir, ignore_errors=True),
)


def swap(ep_address: EpAddress, card_id: str) -> episodes.EpView:
    """The card's image and its previous one change places (D33)."""
    with store.lock:
        _, ep = episodes.editable(ep_address)
        card = episodes.card_of(ep, card_id)
        if card.previous_image is None:
            raise ApiError(404, "not_found", "การ์ดนี้ไม่มีภาพก่อนหน้า")
        card.image, card.previous_image = card.previous_image, card.image
        store.write_ep(ep_address, ep)
    return episodes.view(ep_address)


def image_file(ep_address: EpAddress, card_id: str, previous: bool = False) -> Path:
    with store.lock:
        _, ep = episodes.read(ep_address)
        card = episodes.card_of(ep, card_id)
        image = card.previous_image if previous else card.image
        path = ep_address.images_dir / image.file if image else None
        if path is None or not path.is_file():
            raise ApiError(404, "not_found", "การ์ดนี้ยังไม่มีภาพ")
        return path


def clean_on_start(project: ProjectPaths) -> None:
    """The copies of a job that didn't end, and every card picture no `ep.json` names: jobs
    don't survive a restart (spec › Image job)."""
    shutil.rmtree(project.image_job_dir, ignore_errors=True)
    with store.lock:
        for series_now in store.list_series(project):
            for ep in store.list_eps(project, series_now.id):
                folder = EpAddress(project, series_now.id, ep.id).images_dir
                if not folder.is_dir():
                    continue
                named = {i.file for _, c in episodes.placed_cards(ep) for i in (c.image, c.previous_image) if i is not None}
                for path in folder.iterdir():
                    if path.name not in named:
                        path.unlink(missing_ok=True)


# --- helpers ---


def _in_scope(scope: Scope, status: str, card: Card) -> bool:
    """Whether the scope draws the card, its reference images aside: `missing` the cards with
    no image, `stale_ref` the ones drawn with an older reference (D32, D44). A card of either
    whose character or background has no reference image is skipped (D13): `stale_ref` takes in
    the `no_ref` cards that have an image too, only for the job to count them as skipped."""
    if scope == "missing":
        return card.image is None
    return status == "stale_ref" or (status == "no_ref" and card.image is not None)


def _card_draw(project: ProjectPaths, series_now: Series, segment: Segment, card: Card, refs: dict[str, int]) -> CardDraw:
    used = [*card.character_ids, segment.background_id]
    return CardDraw(
        card_id=card.id,
        description=card.description,
        names=[series.find_item(series_now, "characters", i).name for i in card.character_ids],
        refs={item_id: refs[item_id] for item_id in used},
        ref_paths=[project.image_job_dir / f"{item_id}-{refs[item_id]}.png" for item_id in used],
    )


def _missing_refs(series_now: Series, skipped: list[tuple[Segment, Card]]) -> list[MissingRef]:
    """Each item with `ref_rev` 0 that a skipped card uses, by first use, with its card count."""
    found: dict[str, MissingRef] = {}
    for segment, card in skipped:
        for item_kind, item_id in [*(("characters", i) for i in card.character_ids), ("backgrounds", segment.background_id)]:
            item = series.find_item(series_now, item_kind, item_id)
            if item is not None and item.ref_rev == 0:
                found.setdefault(item_id, MissingRef(item_kind=item_kind, id=item_id, name=item.name, cards=0)).cards += 1
    return list(found.values())
