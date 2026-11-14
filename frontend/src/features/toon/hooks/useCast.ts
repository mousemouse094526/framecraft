import { useCallback, useEffect, useRef } from "react";
import { getJson } from "../../../lib/api";
import { useLeaveGuard } from "../../../lib/useHash";
import {
  itemPath,
  JOB_PATH,
  pickHash,
  seriesPath,
  startRefJob,
  type Item,
  type ItemKind,
  type ItemRef,
  type Series,
  type ToonJob,
} from "../lib/series";
import { sendEdit } from "../../../lib/edit";
import { sendChecked } from "../../../lib/upload";
import type { Notice } from "../../../lib/notice";
import { cancelToonJob, useToonJobPoll } from "./useToonJobPoll";
import { useReadyState } from "../../../lib/useReadyState";

export type ItemFields = { name: string; tag?: string; description: string };

export type CastState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "ready";
      series: Series;
      /** The latest Toon job, whatever it works on: a running one disables every start. */
      job: ToonJob | null;
      notice: Notice | null;
      /** The reference image being sent: which item, and the percent out. */
      upload: { id: string; percent: number } | null;
    };

/**
 * ตัวละครและฉากหลัง: a Series' two lists, add and delete, a Ref job (its banner while it runs;
 * started, the pick page opens), and a reference image from a file (spec › Ref job, D31).
 */
export function useCast(seriesId: string) {
  const [state, setState, update] = useReadyState<CastState>({ kind: "loading" });
  const uploading = useRef(false);

  const load = useCallback(async () => {
    try {
      const [series, job] = await Promise.all([getJson<Series>(seriesPath(seriesId)), getJson<ToonJob | null>(JOB_PATH)]);
      setState((s) => ({
        kind: "ready",
        series,
        job,
        notice: s.kind === "ready" ? s.notice : null,
        upload: s.kind === "ready" ? s.upload : null,
      }));
    } catch {
      setState({ kind: "offline" });
    }
  }, [seriesId, setState]);

  useEffect(() => {
    void load();
  }, [load]);

  const job = state.kind === "ready" ? state.job : null;
  useToonJobPoll(
    job,
    (next) => update((s) => ({ ...s, job: next })),
    // A job that ends leaves three pictures waiting (or none): read the Series again.
    () => void load(),
    () => setState({ kind: "offline" }),
  );

  useLeaveGuard(useCallback(() => uploading.current, []));

  /** Answers that carry the Series as it is now replace it; others become the notice. */
  const sendItem = async (method: string, path: string, body: unknown, title: string) => {
    const reply = await sendEdit<Series>(method, path, body, title);
    update((s) => (reply.kind === "ok" ? { ...s, series: reply.value, notice: null } : { ...s, notice: reply.notice }));
    return reply.kind === "ok";
  };

  const refOf = (kind: ItemKind, item: Item): ItemRef => ({ seriesId, itemKind: kind, itemId: item.id });

  const add = (kind: ItemKind, fields: ItemFields) =>
    sendItem("POST", `${seriesPath(seriesId)}/${kind}`, fields, `เพิ่ม ${fields.name} ไม่ได้`);

  const remove = (kind: ItemKind, item: Item) =>
    void sendItem("DELETE", itemPath(refOf(kind, item)), undefined, `ลบ ${item.name} ไม่ได้`);

  const startRef = async (kind: ItemKind, item: Item) => {
    const ref = refOf(kind, item);
    const reply = await startRefJob(ref);
    if (reply.kind === "ok") window.location.hash = pickHash(ref);
    else update((s) => ({ ...s, notice: reply.notice }));
  };

  const cancelJob = () =>
    cancelToonJob(
      (job) => update((s) => ({ ...s, job })),
      (notice) => update((s) => ({ ...s, notice })),
    );

  /** `/ref/upload/check` first, then the file as the raw body (ADR 0028); the answer is the Series. */
  const upload = async (kind: ItemKind, item: Item, file: File) => {
    const path = `${itemPath(refOf(kind, item))}/ref/upload`;
    const title = `เอาไฟล์ ${file.name} เข้าไม่ได้`;
    const reply = await sendChecked<Series>({ path, checkBody: { size: file.size }, query: `size=${file.size}`, file, title }, {
      started: () => {
        uploading.current = true;
        update((s) => ({ ...s, notice: null, upload: { id: item.id, percent: 0 } }));
      },
      progress: (percent) => update((s) => ({ ...s, upload: { id: item.id, percent } })),
    });
    uploading.current = false;
    update((s) => {
      const done = { ...s, upload: null };
      if (reply.kind === "ok") return { ...done, series: reply.value };
      return reply.kind === "refused" ? { ...done, notice: reply.notice } : done;
    });
  };

  return { state, add, remove, startRef, cancelJob, upload, reload: load };
}
