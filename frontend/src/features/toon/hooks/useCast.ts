import { useCallback, useEffect, useRef } from "react";
import { getJson, sendFile, sendJson } from "../../../lib/api";
import type { Refusal } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import {
  itemPath,
  JOB_PATH,
  pickHash,
  seriesPath,
  startRefJob,
  type Item,
  type ItemKind,
  type Series,
  type ToonJob,
} from "../lib/series";
import { sendEdit } from "../lib/edit";
import { noticeOf, NOT_NOW, type Notice } from "../lib/notice";
import { cancelToonJob, useToonJobPoll } from "./useToonJobPoll";
import { useReadyState } from "./useReadyState";

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
export function useCast(sid: string) {
  const [state, setState, update] = useReadyState<CastState>({ kind: "loading" });
  const uploading = useRef(false);

  const load = useCallback(async () => {
    try {
      const [series, job] = await Promise.all([getJson<Series>(seriesPath(sid)), getJson<ToonJob | null>(JOB_PATH)]);
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
  }, [sid, setState]);

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

  const notify = (notice: Notice | null) => update((s) => ({ ...s, notice }));
  const refused = (title: string, body: unknown, warnings: readonly string[] = []) =>
    notify(noticeOf(title, body, warnings));

  /** Answers that carry the Series as it is now replace it; others become the notice. */
  const sendItem = async (method: string, path: string, body: unknown, title: string) => {
    const reply = await sendEdit<Series>(method, path, body, title);
    update((s) => (reply.kind === "saved" ? { ...s, series: reply.value, notice: null } : { ...s, notice: reply.notice }));
    return reply.kind === "saved";
  };

  const add = (kind: ItemKind, fields: ItemFields) =>
    sendItem("POST", `${seriesPath(sid)}/${kind}`, fields, `เพิ่ม ${fields.name} ไม่ได้`);

  const remove = (kind: ItemKind, item: Item) =>
    void sendItem("DELETE", itemPath(sid, kind, item.id), undefined, `ลบ ${item.name} ไม่ได้`);

  const startRef = async (kind: ItemKind, item: Item) => {
    const title = "ยังสร้างภาพอ้างอิงไม่ได้";
    try {
      const reply = await startRefJob(sid, kind, item.id);
      if (reply.status === 202) {
        window.location.hash = pickHash(sid, kind, item.id);
        return;
      }
      refused(title, reply.body, NOT_NOW);
    } catch {
      refused(title, null);
    }
  };

  const cancelJob = () => cancelToonJob((job) => update((s) => ({ ...s, job })));

  /** `/ref/upload/check` first, then the file as the raw body (ADR 0028); the answer is the Series. */
  const upload = async (kind: ItemKind, item: Item, file: File) => {
    const title = `เอาไฟล์ ${file.name} เข้าไม่ได้`;
    const path = `${itemPath(sid, kind, item.id)}/ref/upload`;
    try {
      const checked = await sendJson<Refusal>("POST", `${path}/check`, { size: file.size });
      if (checked.status !== 200) return refused(title, checked.body);
    } catch {
      return refused(title, null);
    }
    uploading.current = true;
    update((s) => ({ ...s, notice: null, upload: { id: item.id, percent: 0 } }));
    const sending = sendFile<Series | Refusal>(
      `${path}?size=${file.size}`,
      file,
      (percent) => update((s) => ({ ...s, upload: { id: item.id, percent } })),
      () => {},
    );
    const reply = await sending.reply;
    uploading.current = false;
    update((s) => ({ ...s, upload: null }));
    if (reply.kind === "answer" && reply.status === 200) update((s) => ({ ...s, series: reply.body as Series }));
    else refused(title, reply.kind === "answer" ? reply.body : null);
  };

  return { state, add, remove, startRef, cancelJob, upload, reload: load };
}
