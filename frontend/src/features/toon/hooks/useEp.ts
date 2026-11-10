import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import { refusalLine, refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { epPath, type Ep, type LostCards } from "../lib/episodes";
import { epHash, isRunning, JOB_PATH, JOBS_PATH, seriesPath, type Series, type ToonJob } from "../lib/series";
import type { Notice } from "./useCast";

export type EpState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      ep: Ep;
      series: Series;
      /** The latest Toon job, whatever it works on: a running one disables every start. */
      job: ToonJob | null;
      notice: Notice | null;
      /** `cards_will_be_lost`: what each act would lose, until the user confirms or cancels (D43). */
      lost: LostCards[] | null;
    };

type Ready = Extract<EpState, { kind: "ready" }>;

/**
 * An EP: its plot (Plot job, edits, confirm), its storyline (acts, segments, cards and their
 * edits), and the Cards job that splits the plot (spec › Plot job, › Cards job). While a Plot
 * or Cards job of this EP runs, the page closes every field; a job that ends reads the EP again.
 */
export function useEp(eid: string) {
  const [state, , setState] = useMountedState<EpState>({ kind: "loading" });

  const update = useCallback(
    (change: (s: Ready) => EpState) => setState((s) => (s.kind === "ready" ? change(s) : s)),
    [setState],
  );

  const load = useCallback(async () => {
    try {
      const [ep, job] = await Promise.all([getJson<Ep>(epPath(eid)), getJson<ToonJob | null>(JOB_PATH)]);
      const series = await getJson<Series>(seriesPath(ep.series_id));
      setState((s) => ({
        kind: "ready",
        ep,
        series,
        job,
        notice: s.kind === "ready" ? s.notice : null,
        lost: s.kind === "ready" ? s.lost : null,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [eid, setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  usePollWhile<ToonJob | null>(
    job !== null && isRunning(job),
    JOB_PATH,
    (next) => {
      if (next !== null && isRunning(next)) return update((s) => ({ ...s, job: next }));
      // A Cards job of this EP that is done opens the storyline (the plot page may be open).
      if (next?.kind === "cards" && next.ep_id === eid && next.state === "done") window.location.hash = epHash(eid);
      void load();
    },
    () => setState({ kind: "offline" }),
  );

  const refused = (title: string, body: unknown, tone: Notice["tone"] = "error") => {
    const refusal = refusalOf(body);
    const line = refusal ? refusalLine(refusal) : { text: OFFLINE_TEXT, setupLink: false };
    update((s) => ({ ...s, notice: { tone, title, text: line.text, setupLink: line.setupLink } }));
  };

  /** An edit: its answer is the EP as it is now; a refusal becomes the notice. */
  const edit = async (method: string, path: string, body: unknown, title = "บันทึกไม่ได้") => {
    try {
      const reply = await sendJson<Ep | Refusal>(method, `${epPath(eid)}${path}`, body);
      if (reply.status === 200 || reply.status === 201) {
        update((s) => ({ ...s, ep: reply.body as Ep, notice: null }));
        return true;
      }
      refused(title, reply.body);
    } catch {
      refused(title, null);
    }
    return false;
  };

  const start = async (body: Record<string, unknown>, title: string) => {
    try {
      const reply = await sendJson<ToonJob | Refusal>("POST", JOBS_PATH, { ep_id: eid, ...body });
      if (reply.status === 202) {
        update((s) => ({ ...s, job: reply.body as ToonJob, notice: null, lost: null }));
        void load(); // the EP reads as locked now
        return;
      }
      const refusal = refusalOf(reply.body) as (Refusal & { acts?: LostCards[] }) | null;
      if (refusal?.code === "cards_will_be_lost") return update((s) => ({ ...s, lost: refusal.acts ?? [] }));
      const busy = ["busy", "gpu_busy", "not_ready", "nothing_to_split"].includes(refusal?.code ?? "");
      refused(title, reply.body, busy ? "warning" : "error");
    } catch {
      refused(title, null);
    }
  };

  /** หยุด: the job shows `cancel_requested` until the poll sees it end. */
  const cancelJob = async () => {
    const reply = await cancelCurrent<ToonJob>(JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
  };

  return {
    state,
    reload: load,
    edit,
    startPlot: () => start({ kind: "plot" }, "ยังร่างพล็อตไม่ได้"),
    /** First without `confirm_loss`: a `cards_will_be_lost` answer opens the confirm (D43). */
    startCards: (confirmLoss = false) => start({ kind: "cards", confirm_loss: confirmLoss }, "ยังแตกการ์ดไม่ได้"),
    closeLost: () => update((s) => ({ ...s, lost: null })),
    cancelJob,
  };
}
