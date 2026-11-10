import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson, type JsonReply } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import { useMountedState } from "../../../lib/useMountedState";
import { castHash, isRunning, itemPath, JOB_PATH, seriesPath, startRefJob, type Item, type Kind, type Series, type ToonJob } from "../lib/series";
import { refusalTextOf } from "../lib/notice";
import { useToonJobPoll } from "./useToonJobPoll";

export type PickState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** The Series is gone, or the item in it. */
  | { kind: "missing" }
  | {
      kind: "ready";
      item: Item;
      /** The latest Toon job if it drew this item; another item's job is no business of this page. */
      job: ToonJob | null;
      choice: number | null;
      sending: boolean;
      error: string | null;
    };

/** เลือกภาพอ้างอิง: follows the item's Ref job, then one of its three pictures becomes the reference image (D31, D32). */
export function usePickRef(sid: string, kind: Kind, id: string) {
  const [state, , setState] = useMountedState<PickState>({ kind: "loading" });

  const update = useCallback(
    (change: (s: Extract<PickState, { kind: "ready" }>) => PickState) =>
      setState((s) => (s.kind === "ready" ? change(s) : s)),
    [setState],
  );

  const load = useCallback(async () => {
    try {
      const [series, job] = await Promise.all([
        // A reply, not getJson: a Series deleted meanwhile is `missing`, not offline.
        sendJson<Series>("GET", seriesPath(sid)),
        getJson<ToonJob | null>(JOB_PATH),
      ]);
      const item = series.status === 200 ? series.body?.[kind].find((i) => i.id === id) : undefined;
      if (!item) return setState({ kind: "missing" });
      const own = job !== null && job.series_id === sid && job.item_id === id ? job : null;
      setState((s) => ({
        kind: "ready",
        item,
        job: own,
        choice: s.kind === "ready" ? s.choice : null,
        sending: false,
        error: null,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [sid, kind, id, setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  useToonJobPoll(
    job,
    (next) => update((s) => ({ ...s, job: next })),
    // The three pictures land all at once when the job is done: read the item again.
    () => void load(),
    () => setState({ kind: "offline" }),
  );

  const send = async (request: () => Promise<JsonReply<unknown>>, ok: number, then: () => void) => {
    update((s) => ({ ...s, sending: true, error: null }));
    try {
      const reply = await request();
      if (reply.status === ok) return then();
      update((s) => ({ ...s, sending: false, error: refusalTextOf(reply.body).text }));
    } catch {
      update((s) => ({ ...s, sending: false, error: OFFLINE_TEXT }));
    }
  };

  const choose = (n: number) => update((s) => ({ ...s, choice: n }));

  const pick = (n: number) =>
    send(() => sendJson("POST", `${itemPath(sid, kind, id)}/ref/pick`, { n }), 200, () => {
      window.location.hash = castHash(sid);
    });

  /** ลองอีกครั้ง: a new Ref job for the same item. */
  const retry = () =>
    send(() => startRefJob(sid, kind, id), 202, () => void load());

  /** ยกเลิก stops a running job; with nothing running it goes back to the lists. */
  const cancel = async () => {
    if (job === null || !isRunning(job)) {
      window.location.hash = castHash(sid);
      return;
    }
    const reply = await cancelCurrent<ToonJob>(JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
    else if (reply.kind === "ended") void load();
    else update((s) => ({ ...s, error: reply.kind === "offline" ? OFFLINE_TEXT : "หยุดงานไม่ได้" }));
  };

  return { state, choose, pick, retry, cancel, reload: load };
}
