import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { SERIES_PATH, seriesPath, type ListedSeries } from "../lib/series";
import { refusalTextOf } from "../lib/notice";

/** A delete that didn't happen: which Series, and why (`series_busy`, offline…). */
export type DeleteRefusal = { name: string; text: string };

export type SeriesListState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "result"; series: ListedSeries[]; refusal: DeleteRefusal | null };

/** รายการ Series: the list, and delete after the user confirmed the EP count (D26). */
export function useSeriesList() {
  const [state, , setState] = useMountedState<SeriesListState>({ kind: "loading" });

  const load = useCallback(
    async (refusal: DeleteRefusal | null = null) => {
      try {
        const series = await getJson<ListedSeries[]>(SERIES_PATH);
        setState({ kind: "result", series, refusal });
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
      let text = OFFLINE_TEXT;
      try {
        const reply = await sendJson("DELETE", seriesPath(series.id), { confirm_eps: series.ep_count });
        if (reply.status === 204) return load();
        text = refusalTextOf(reply.body).text;
      } catch {
        // no answer: the line says so
      }
      // The list is read again: a refused delete may mean it changed (a new EP, `confirm_needed`).
      await load({ name: series.name, text });
    },
    [load],
  );

  return { state, remove, reload: () => load() };
}
