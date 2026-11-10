import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, sendFile, sendJson } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import { refusalLine, refusalOf, type Refusal } from "../../../lib/refusal";
import { useLeaveGuard } from "../../../lib/useHash";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import {
  itemPath,
  JOB_PATH,
  pickHash,
  seriesPath,
  isRunning,
  startRefJob,
  type Item,
  type Kind,
  type Series,
  type ToonJob,
} from "../lib/series";

/** A line above the lists: why an action was refused (Figma toon / 3, states 3–6). */
export type Notice = { tone: "warning" | "error"; title: string; text: string; setupLink: boolean };

/** The notice of a refused or failed request: the API's refusal line (none: no backend); a
 * `warning` for the codes that mean "not now". */
export function noticeOf(title: string, body: unknown, warnings: readonly string[] = []): Notice {
  const refusal = refusalOf(body);
  const line = refusal ? refusalLine(refusal) : { text: OFFLINE_TEXT, setupLink: false };
  const tone = refusal && warnings.includes(refusal.code) ? "warning" : "error";
  return { tone, title, text: line.text, setupLink: line.setupLink };
}

/** "Not now: another job has it, or a model isn't installed." */
export const NOT_NOW = ["gpu_busy", "busy", "not_ready"] as const;

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
  const [state, , setState] = useMountedState<CastState>({ kind: "loading" });
  const uploading = useRef(false);

  const update = useCallback(
    (change: (s: Extract<CastState, { kind: "ready" }>) => CastState) =>
      setState((s) => (s.kind === "ready" ? change(s) : s)),
    [setState],
  );

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
  usePollWhile<ToonJob | null>(
    job !== null && isRunning(job),
    JOB_PATH,
    (next) => {
      // A job that ends leaves three pictures waiting (or none): read the Series again.
      if (next === null || !isRunning(next)) void load();
      else update((s) => ({ ...s, job: next }));
    },
    () => setState({ kind: "offline" }),
  );

  useLeaveGuard(useCallback(() => uploading.current, []));

  const notify = (notice: Notice | null) => update((s) => ({ ...s, notice }));
  const refused = (title: string, body: unknown, warnings: readonly string[] = []) =>
    notify(noticeOf(title, body, warnings));

  /** Answers that carry the Series as it is now replace it; others become the notice. */
  const sendItem = async (method: string, path: string, body: unknown, title: string) => {
    try {
      const reply = await sendJson<Series | Refusal>(method, path, body);
      if (reply.status === 200 || reply.status === 201) {
        update((s) => ({ ...s, series: reply.body as Series, notice: null }));
        return true;
      }
      refused(title, reply.body);
    } catch {
      refused(title, null);
    }
    return false;
  };

  const add = (kind: Kind, fields: ItemFields) =>
    sendItem("POST", `${seriesPath(sid)}/${kind}`, fields, `เพิ่ม ${fields.name} ไม่ได้`);

  const remove = (kind: Kind, item: Item) =>
    void sendItem("DELETE", itemPath(sid, kind, item.id), undefined, `ลบ ${item.name} ไม่ได้`);

  const startRef = async (kind: Kind, item: Item) => {
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

  /** หยุด: the job shows `cancel_requested` until the poll sees it end. */
  const cancelJob = async () => {
    const reply = await cancelCurrent<ToonJob>(JOB_PATH);
    if (reply.kind === "cancelling") update((s) => ({ ...s, job: reply.job }));
  };

  /** `/ref/upload/check` first, then the file as the raw body (ADR 0028); the answer is the Series. */
  const upload = async (kind: Kind, item: Item, file: File) => {
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
