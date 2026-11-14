import { useCallback, useEffect } from "react";
import { getJson, getReply } from "../../../lib/api";
import { castHash, isRunning, itemPath, JOB_PATH, seriesPath, startRefJob, type Item, type ItemRef, type Series, type ToonJob } from "../lib/series";
import { sendEdit, stopJob, type EditReply } from "../../../lib/edit";
import type { Notice } from "../../../lib/notice";
import { useToonJobPoll } from "./useToonJobPoll";
import { useReadyState } from "../../../lib/useReadyState";

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
      /** Why the last pick, retry or stop didn't happen; the page shows its text only, untitled. */
      notice: Notice | null;
    };

/** เลือกภาพอ้างอิง: follows the item's Ref job, then one of its three pictures becomes the reference image (D31, D32). */
export function usePickRef(itemRef: ItemRef) {
  const { seriesId, itemKind, itemId } = itemRef;
  const [state, setState, update] = useReadyState<PickState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [series, job] = await Promise.all([
        // A reply, not getJson: a Series deleted meanwhile is `missing`, not offline.
        getReply<Series>(seriesPath(seriesId)),
        getJson<ToonJob | null>(JOB_PATH),
      ]);
      const item = series.status === 200 ? series.body?.[itemKind].find((i) => i.id === itemId) : undefined;
      if (!item) return setState({ kind: "missing" });
      const own = job !== null && job.series_id === seriesId && job.item_id === itemId ? job : null;
      setState((s) => ({
        kind: "ready",
        item,
        job: own,
        choice: s.kind === "ready" ? s.choice : null,
        sending: false,
        notice: null,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [seriesId, itemKind, itemId, setState]);

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

  const send = async (request: () => Promise<EditReply<unknown>>, then: () => void) => {
    update((s) => ({ ...s, sending: true, notice: null }));
    const reply = await request();
    if (reply.kind === "ok") return then();
    update((s) => ({ ...s, sending: false, notice: reply.notice }));
  };

  /** Marks picture `n` on the page only; nothing is sent until `pick`. */
  const choose = (n: number) => update((s) => ({ ...s, choice: n }));

  /** ใช้ภาพนี้: picture `n` becomes the item's reference image, then back to the lists. */
  const pick = (n: number) =>
    send(() => sendEdit("POST", `${itemPath(itemRef)}/ref/pick`, { n }, "ใช้ภาพนี้ไม่ได้"), () => {
      window.location.hash = castHash(seriesId);
    });

  /** ลองอีกครั้ง: a new Ref job for the same item. */
  const retry = () =>
    send(() => startRefJob(itemRef), () => void load());

  /** ยกเลิก stops a running job; with nothing running it goes back to the lists. */
  const cancel = async () => {
    if (job === null || !isRunning(job)) {
      window.location.hash = castHash(seriesId);
      return;
    }
    const reply = await stopJob<ToonJob>(JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
    else if (reply.kind === "ended") void load();
    else update((s) => ({ ...s, notice: reply.notice }));
  };

  return { state, choose, pick, retry, cancel, reload: load };
}
