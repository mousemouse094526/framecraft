import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";
import { usePollWhile } from "../../../lib/usePollWhile";
import { epPath, type Ep } from "../lib/episodes";
import {
  isRendering,
  renderFilePath,
  RENDER_JOB_PATH,
  RENDER_PATH,
  rendersPath,
  type RenderJob,
  type RenderResult,
} from "../lib/render";
import { seriesPath, type Series } from "../lib/series";
import { noticeOf, NOT_NOW, type Notice } from "../lib/notice";
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
export function useRender(eid: string) {
  const [state, setState, update] = useReadyState<RenderState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [ep, job, renders] = await Promise.all([
        getJson<Ep>(epPath(eid)),
        getJson<RenderJob | null>(RENDER_JOB_PATH),
        getJson<RenderResult[]>(rendersPath(eid)),
      ]);
      const series = await getJson<Series>(seriesPath(ep.series_id));
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
  }, [eid, setState]);

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

  const refused = (title: string, body: unknown) => update((s) => ({ ...s, notice: noticeOf(title, body, NOT_NOW) }));

  const start = async () => {
    const title = "ยัง render ไม่ได้";
    try {
      const reply = await sendJson<RenderJob | (Refusal & { card_ids?: string[] })>("POST", RENDER_PATH, { ep_id: eid });
      if (reply.status === 202) {
        update((s) => ({ ...s, job: reply.body as RenderJob, notice: null, notReady: null }));
        return;
      }
      const body = reply.body as Refusal & { card_ids?: string[] };
      if (body?.code === "cards_not_ready" && body.card_ids?.length) {
        update((s) => ({ ...s, notice: null, notReady: body.card_ids ?? [] }));
        return;
      }
      refused(title, reply.body);
    } catch {
      refused(title, null);
    }
  };

  const cancel = async () => {
    const reply = await cancelCurrent<RenderJob>(RENDER_JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
  };

  const remove = async (result: RenderResult) => {
    const title = `ลบคลิป ${result.name} ไม่ได้`;
    try {
      const reply = await sendJson<Refusal>("DELETE", renderFilePath(eid, result.name));
      if (reply.status === 204) {
        update((s) => ({ ...s, notice: null, renders: s.renders.filter((r) => r.name !== result.name) }));
        return;
      }
      refused(title, reply.body);
    } catch {
      refused(title, null);
    }
  };

  return { state, reload: load, start, cancel, remove };
}
