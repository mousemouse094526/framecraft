import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { SERIES_PATH, seriesPath, type ListedSeries } from "../lib/series";
import { sendEdit } from "../lib/edit";
import type { Notice } from "../lib/notice";

export type SeriesListState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** `notice`: why the last delete didn't happen (`series_busy`, offline…). */
  | { kind: "result"; series: ListedSeries[]; notice: Notice | null };

/** รายการ Series: the list, and delete after the user confirmed the EP count (D26). */
export function useSeriesList() {
  const [state, , setState] = useMountedState<SeriesListState>({ kind: "loading" });

  const load = useCallback(
    async (notice: Notice | null = null) => {
      try {
        const series = await getJson<ListedSeries[]>(SERIES_PATH);
        setState({ kind: "result", series, notice });
      } catch {
        setState({ kind: "offline" });
      }
    },
    [setState],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const remove = useCallback(
    async (series: ListedSeries) => {
      const reply = await sendEdit<null>("DELETE", seriesPath(series.id), { confirm_eps: series.ep_count }, `ลบ ${series.name} ไม่ได้`, {
        ok: [204],
      });
      // The list is read again either way: a refused delete may mean it changed (a new EP, `confirm_needed`).
      await load(reply.kind === "ok" ? null : reply.notice);
    },
    [load],
  );

  return { state, remove, reload: () => load() };
}
