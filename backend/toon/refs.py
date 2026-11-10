"""The Ref job: three reference pictures of a character or a background to pick from (toon
spec › Ref job, D31, D48). Qwen writes the scene, its child ends, then klein draws them with
different seeds; they become the item's waiting set only once all three are in.
"""

import logging
import random
import shutil
from pathlib import Path
from typing import get_args

from backend.errors import ApiError
from backend.paths import ProjectPaths
from backend.toon import prompts, series, steps
from backend.toon.kinds import Kind
from backend.toon.klein import Draw, Drawn, Encode, Encoded

log = logging.getLogger(__name__)


def plan(project: ProjectPaths, body: dict) -> series.RefPlan:
    """Step 1 up to the gate: the item. Raises `invalid_request`, `not_found`."""
    series_id, kind, item_id = body.get("series_id"), body.get("item_kind"), body.get("item_id")
    if not all(isinstance(value, str) for value in (series_id, kind, item_id)) or kind not in get_args(Kind):
        raise ApiError(400, "invalid_request", "เลือกตัวละครหรือฉากหลังที่จะสร้างภาพ")
    return series.ref_plan(project, series_id, kind, item_id)


def _pictures_dir(project: ProjectPaths, plan: series.RefPlan) -> Path:
    """Where the job's pictures wait until all three are in."""
    return project.pending_refs_dir(plan.series_id) / f".new-{plan.item_id}"


def run(job: steps.Run, project: ProjectPaths, plan: series.RefPlan) -> None:
    """Steps 2–3."""
    [scene] = steps.scenes(job, project, [prompts.ref_scene_prompt(plan.kind, plan.name, plan.description)])
    if scene is None:
        scene = plan.description or plan.name  # D48: the description as it was written
    prompt = prompts.ref_prompt(plan.kind, scene, plan.style)
    job.update(state="drawing", done=0, total=series.PICTURES)
    process, requests, replies = steps.start_klein(job, project)
    requests.put(Encode([prompt]))
    steps.klein_reply(job, process, replies, Encoded)
    work = _pictures_dir(project, plan)
    work.mkdir(parents=True, exist_ok=True)
    pictures = []
    width, height = plan.size
    for n in range(1, series.PICTURES + 1):
        requests.put(Draw(index=0, ref_paths=[], width=width, height=height, seed=random.randint(0, steps.SEED_MAX)))
        drawn = steps.klein_reply(job, process, replies, Drawn)
        picture = work / f"{n}.png"
        picture.write_bytes(drawn.png)
        pictures.append(picture)
        job.update(done=n)
    requests.put(None)
    if not series.put_pending(project, plan.series_id, plan.kind, plan.item_id, pictures):
        log.info("the reference pictures of %s are dropped: it was deleted", plan.item_id)


WORK = steps.Work(
    gpu_kind="toon_image",
    child=steps.DRAWER,
    plan=plan,
    rows=steps.image_rows,
    job=lambda plan: {"state": "translating", "series_id": plan.series_id, "item_id": plan.item_id},
    run=run,
    log_name=lambda plan: f"toon job ref {plan.item_id}",
    ready=lambda project, plan: series.require_free_disk(project),
    clean_up=lambda project, plan: shutil.rmtree(_pictures_dir(project, plan), ignore_errors=True),
)
