import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalLine, refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { epPath, seriesEpsPath, type Ep, type ListedEp } from "../lib/episodes";
import { epHash, JOBS_PATH, seriesPath, type Series, type ToonJob } from "../lib/series";
import type { Notice } from "./useCast";

export type EpListState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "ready"; series: Series; eps: ListedEp[]; notice: Notice | null };

/** รายการ EP ใน Series: the list, a new EP from an idea that goes straight to a Plot job, and
 * delete after the user confirmed (D12, D26, D40). */
export function useEpList(sid: string) {
  const [state, , setState] = useMountedState<EpListState>({ kind: "loading" });

  const load = useCallback(
    async (notice: Notice | null = null) => {
      try {
        const [series, eps] = await Promise.all([getJson<Series>(seriesPath(sid)), getJson<ListedEp[]>(seriesEpsPath(sid))]);
        setState({ kind: "ready", series, eps, notice });
      } catch {
        setState({ kind: "offline" });
      }
    },
    [sid, setState],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const notice = (title: string, body: unknown): Notice => {
    const refusal = refusalOf(body);
    const line = refusal ? refusalLine(refusal) : { text: OFFLINE_TEXT, setupLink: false };
    return { tone: "error", title, text: line.text, setupLink: line.setupLink };
  };

  /** The EP, then its Plot job; started, the plot page opens and shows the job. A refused
   * job leaves the EP in the list with the reason: its plot page starts it again. */
  const create = async (idea: string): Promise<boolean> => {
    const title = "สร้าง EP ไม่ได้";
    try {
      const created = await sendJson<Ep | Refusal>("POST", seriesEpsPath(sid), { idea });
      if (created.status !== 201) {
        await load(notice(title, created.body));
        return false;
      }
      const ep = created.body as Ep;
      const started = await sendJson<ToonJob | Refusal>("POST", JOBS_PATH, { kind: "plot", ep_id: ep.id });
      if (started.status === 202) {
        window.location.hash = epHash(ep.id);
        return true;
      }
      await load({ ...notice("ยังร่างพล็อตไม่ได้", started.body), tone: "warning" });
      return true;
    } catch {
      await load(notice(title, null));
      return false;
    }
  };

  const remove = async (ep: ListedEp) => {
    try {
      const reply = await sendJson("DELETE", epPath(ep.id));
      // The list is read again either way: a refused delete may mean it changed.
      await load(reply.status === 204 ? null : notice(`ลบ ${ep.title || `EP ${ep.n}`} ไม่ได้`, reply.body));
    } catch {
      await load(notice(`ลบ ${ep.title || `EP ${ep.n}`} ไม่ได้`, null));
    }
  };

  return { state, create, remove, reload: () => load() };
}
