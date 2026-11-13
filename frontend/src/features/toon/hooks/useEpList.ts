import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { epPath, seriesEpsPath, type Ep, type ListedEp } from "../lib/episodes";
import { epHash, seriesPath, startToonJob, type Series } from "../lib/series";
import { sendEdit } from "../../../lib/edit";
import type { Notice } from "../../../lib/notice";

export type EpListState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "ready"; series: Series; eps: ListedEp[]; notice: Notice | null };

/** รายการ EP ใน Series: the list, a new EP from an idea that goes straight to a Plot job, and
 * delete after the user confirmed (D12, D26, D40). */
export function useEpList(seriesId: string) {
  const [state, , setState] = useMountedState<EpListState>({ kind: "loading" });

  const load = useCallback(
    async (notice: Notice | null = null) => {
      try {
        const [series, eps] = await Promise.all([getJson<Series>(seriesPath(seriesId)), getJson<ListedEp[]>(seriesEpsPath(seriesId))]);
        setState({ kind: "ready", series, eps, notice });
      } catch {
        setState({ kind: "offline" });
      }
    },
    [seriesId, setState],
  );

  useEffect(() => {
    void load();
  }, [load]);

  /** The EP, then its Plot job; started, the plot page opens and shows the job. A refused
   * job leaves the EP in the list with the reason: its plot page starts it again. */
  const create = async (idea: string): Promise<boolean> => {
    const created = await sendEdit<Ep>("POST", seriesEpsPath(seriesId), { idea }, "สร้าง EP ไม่ได้");
    if (created.kind === "refused") {
      await load(created.notice);
      return false;
    }
    const started = await startToonJob({ kind: "plot", ep_id: created.value.id }, "ยังร่างพล็อตไม่ได้");
    if (started.kind === "ok") {
      window.location.hash = epHash(created.value.id);
      return true;
    }
    // The EP is made either way: whatever stopped its Plot job is a warning.
    await load({ ...started.notice, tone: "warning" });
    return true;
  };

  const remove = async (ep: ListedEp) => {
    const reply = await sendEdit<null>("DELETE", epPath(ep.id), undefined, `ลบ ${ep.title || `EP ${ep.n}`} ไม่ได้`, { ok: [204] });
    // The list is read again either way: a refused delete may mean it changed.
    await load(reply.kind === "ok" ? null : reply.notice);
  };

  return { state, create, remove, reload: () => load() };
}
