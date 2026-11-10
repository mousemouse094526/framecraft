"""The Plot job: Qwen writes an EP's title, its acts' summaries and the plot's cast from its
idea (toon spec › Plot job, D13, D53, D57). It locks its EP: edits are `ep_locked` until it
ends, and the EP changes only at its end, so a cancelled, failed or crashed job leaves it as
it was.
"""

import logging

from pydantic import BaseModel

from backend import gate_rows
from backend.errors import ApiError, JobFailed
from backend.paths import EpAddress, ProjectPaths
from backend.spoil_maker import voices
from backend.toon import episodes, steps, store, writer
from backend.toon.store import Ep, Series

log = logging.getLogger(__name__)


class WritePlan(BaseModel):
    """What a Plot or a Cards job writes: an EP Qwen may write, read under the store's lock as
    the job starts."""

    series: Series
    ep: Ep
    chars_per_s: float  # the EP's voice's speed


def plan(project: ProjectPaths, body: dict) -> WritePlan:
    """Spec › Plot job step 1 up to the gate: the EP, its idea, its voice, its stage."""
    found = writable(project, body.get("ep_id"))
    if found.ep.stage == "cards":
        raise ApiError(409, "plot_confirmed", "ยืนยันพล็อตแล้ว: แก้พล็อตแล้วแตกการ์ดใหม่แทน")
    return found


def writable(project: ProjectPaths, ep_id: object) -> WritePlan:
    """The EP with its Series, and its voice's speed. Raises `not_found`, `ep_busy` while a
    render works on the EP (a Plot or Cards job would lock it, D57), `invalid_request` for an
    idea out of 1–500, `voice_not_found`."""
    _, series_now, ep = episodes.look_up(project, ep_id)
    if episodes.rendering(ep.id):
        raise ApiError(409, "ep_busy", "กำลัง render EP นี้: เขียนใหม่ได้เมื่อ render จบ")
    if not 1 <= len(ep.idea) <= episodes.IDEA_MAX:
        raise ApiError(400, "invalid_request", f"ไอเดียต้องยาว 1–{episodes.IDEA_MAX} ตัวอักษร")
    chars_per_s = voices.chars_per_s(project, ep.voice_id)
    if chars_per_s is None:
        raise ApiError(400, "voice_not_found", "ไม่พบเสียงเล่าของ EP นี้: เลือกเสียงที่บันทึกไว้")
    return WritePlan(series=series_now, ep=ep, chars_per_s=chars_per_s)


def run(job: steps.Run, project: ProjectPaths, found: WritePlan) -> None:
    """Spec › Plot job steps 2–5: up to three tries, then the title, the summaries and the plot's cast are
    written; new characters and backgrounds stay in the plot (D13)."""
    ep_address = EpAddress(project, found.series.id, found.ep.id)
    with store.lock:
        series_now, ep = store.read_series(project, ep_address.series_id), store.read_ep(ep_address)
    prompt = writer.plot_prompt(
        series_now, ep.idea, [act.name for act in ep.acts], round(episodes.TARGET_S * found.chars_per_s)
    )
    written = steps.Qwen(job, project).answer(
        prompt, writer.PLOT_MAX_TOKENS, lambda reply: writer.parse_plot(reply, series_now, len(ep.acts)), "plot"
    )
    if written is None:
        raise JobFailed("write_failed", f"AI ร่างพล็อตไม่สำเร็จ {writer.ATTEMPTS} ครั้ง")
    with store.lock:
        ep = store.read_ep(ep_address)
        if ep is None:
            raise JobFailed("internal", "อ่าน EP นี้ไม่ได้แล้ว")
        ep.title = written.title
        for act, summary in zip(ep.acts, written.summaries, strict=True):
            act.summary = summary
        ep.plot = written.plot
        store.write_ep(ep_address, ep)


WORK = steps.Work(
    gpu_kind="toon_write",
    child=steps.WRITER,
    plan=plan,
    rows=gate_rows.qwen_jobs,
    job=lambda found: {"state": "writing", "series_id": found.series.id, "ep_id": found.ep.id},
    run=run,
    log_name=lambda found: f"toon job plot {found.ep.id}",
)
