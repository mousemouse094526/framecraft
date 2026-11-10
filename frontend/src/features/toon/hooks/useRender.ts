import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";
import { usePollWhile } from "../../../lib/usePollWhile";
import { readEpAndSeries, type Ep } from "../lib/episodes";
import {
  isRendering,
  renderFilePath,
  RENDER_JOB_PATH,
  RENDER_PATH,
  rendersPath,
  type RenderJob,
  type RenderResult,
} from "../lib/render";
import type { Series } from "../lib/series";
import { sendEdit } from "../lib/edit";
import { NOT_NOW, type Notice } from "../lib/notice";
import { useReadyState } from "./useReadyState";

export type RenderState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      ep: Ep;
      series: Series;
      /** The latest Render job, of any EP: only one runs at a time. */
      job: RenderJob | null;
      renders: RenderResult[];
      notice: Notice | null;
      /** `cards_not_ready`'s cards, until the next render starts. */
      notReady: string[] | null;
    };

/** render และผล: the EP's summary, its Render job polled while it runs, and its clips. */
export function useRender(epId: string) {
  const [state, setState, update] = useReadyState<RenderState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [{ ep, series }, job, renders] = await Promise.all([
        readEpAndSeries(epId),
        getJson<RenderJob | null>(RENDER_JOB_PATH),
        getJson<RenderResult[]>(rendersPath(epId)),
      ]);
      setState((s) => ({
        kind: "ready",
        ep,
        series,
        job,
        renders,
        notice: s.kind === "ready" ? s.notice : null,
        notReady: s.kind === "ready" ? s.notReady : null,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [epId, setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  usePollWhile<RenderJob | null>(
    job !== null && isRendering(job),
    RENDER_JOB_PATH,
    (next) => {
      update((s) => ({ ...s, job: next }));
      // Voicing writes narration into the EP; an ended job may leave a new clip.
      if (next === null || !isRendering(next) || next.state !== job?.state) void load();
    },
    () => setState({ kind: "offline" }),
  );

  const start = async () => {
    const reply = await sendEdit<RenderJob, Refusal & { card_ids?: string[] }>("POST", RENDER_PATH, { ep_id: epId }, "ยัง render ไม่ได้", {
      ok: [202],
      warnings: NOT_NOW,
    });
    if (reply.kind === "ok") return update((s) => ({ ...s, job: reply.value, notice: null, notReady: null }));
    const cardIds = reply.refusal?.code === "cards_not_ready" ? reply.refusal.card_ids : undefined;
    if (cardIds?.length) return update((s) => ({ ...s, notice: null, notReady: cardIds }));
    update((s) => ({ ...s, notice: reply.notice }));
  };

  const cancel = async () => {
    const reply = await cancelCurrent<RenderJob>(RENDER_JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
  };

  const remove = async (result: RenderResult) => {
    const reply = await sendEdit<null>("DELETE", renderFilePath(epId, result.name), undefined, `ลบคลิป ${result.name} ไม่ได้`, {
      ok: [204],
      warnings: NOT_NOW,
    });
    update((s) =>
      reply.kind === "ok"
        ? { ...s, notice: null, renders: s.renders.filter((r) => r.name !== result.name) }
        : { ...s, notice: reply.notice },
    );
  };

  return { state, reload: load, start, cancel, remove };
}
