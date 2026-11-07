import { useCallback, useEffect, useRef } from "react";
import { sendFile, sendJson, type JsonReply } from "../../../lib/api";
import type { TempClip } from "../../../lib/clips";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { notice, type Notice } from "../lib/notice";

const CHECK_PATH = "/api/spoil/imports/check";
const IMPORTS_PATH = "/api/spoil/imports";

/**
 * A file on its way in: `sending` from the pick until the whole body is out (0% while the
 * `/imports/check` request runs), then `checking` while the backend reads the file with ffmpeg.
 */
export type Upload = { name: string; phase: "sending"; percent: number } | { name: string; phase: "checking" };

export type ImportState =
  | { kind: "offline" }
  // `notice` stays until the next import or โหลด (spec › Frontend, เอาไฟล์เข้า).
  | { kind: "ready"; upload: Upload | null; notice: Notice | null };

const IDLE: ImportState = { kind: "ready", upload: null, notice: null };

const NOT_MP4 = notice("error", "รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน");
const ONE_AT_A_TIME = notice("warning", "เอาเข้าได้ทีละไฟล์");
const CANCELLED = notice("info", "ยกเลิกแล้ว");
// The upload got no answer. Not offline: the backend answers early (and the browser then sees
// only a network error) when it refuses a file mid-body, so trying again is the way out (D55).
const UPLOAD_FAILED = notice("error", "เอาไฟล์เข้าไม่สำเร็จ ลองอีกครั้ง");

/** The statuses either request refuses with `{code, message}` (spec › API). */
const REFUSAL_STATUSES = [400, 408, 409];

/** A refusal of either request as a message; anything else → undefined (offline). */
function refusalNotice(reply: JsonReply<unknown>): Notice | undefined {
  if (!REFUSAL_STATUSES.includes(reply.status)) return undefined;
  const refusal = refusalOf(reply.body);
  if (!refusal) return undefined;
  // Points at the clip already in the list (D51).
  if (refusal.code === "duplicate") return notice("info", "ไฟล์นี้เอาเข้าไว้แล้ว", refusal.clip_id ?? null);
  return notice(refusal.code === "busy" ? "warning" : "error", refusal.message);
}

/** The import under way: `stop` ends its upload (or flags a check still out), `stopped` says it was. */
type Running = { stop: () => void; stopped: boolean };

type Callbacks = {
  /** A clip came in: the list loads again (D6). */
  onImported: () => void;
  /** `503 not_ready`: the install changed, the tab asks for the status again. */
  onNotReady: () => void;
};

/**
 * Imports an mp4 from this computer (D49–D52): `POST /imports/check` first, then the file as a
 * raw body over `XMLHttpRequest` with its % (ADR-0028). ยกเลิก and leaving the tab stop the
 * upload; the backend drops the half-written file.
 */
export function useFileImport({ onImported, onNotReady }: Callbacks) {
  const [state, , setIfMounted] = useMountedState<ImportState>(IDLE);
  const running = useRef<Running | null>(null);

  useEffect(
    () => () => {
      running.current?.stop();
    },
    [],
  );

  const start = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file || running.current) return;
      // Several files dropped: the first goes in, the message says why the rest don't (spec › Frontend).
      const warning = files.length > 1 ? ONE_AT_A_TIME : null;

      const job: Running = {
        stop: () => {
          job.stopped = true;
        },
        stopped: false,
      };
      /** Shows this job's state, unless `reset` (Refresh, offline) has dropped the job. */
      const show = (upload: Upload | null, shown: Notice | null) => {
        if (running.current !== job) return;
        if (upload === null) running.current = null;
        setIfMounted({ kind: "ready", upload, notice: shown });
      };
      const goOffline = () => {
        if (running.current !== job) return;
        running.current = null;
        setIfMounted({ kind: "offline" });
      };
      /** Ends on a reply that isn't the one hoped for: `503`, a refusal, or (anything else) offline. */
      const endOnReply = (reply: JsonReply<unknown>) => {
        if (reply.status === 503) {
          show(null, null);
          onNotReady();
          return;
        }
        const refused = refusalNotice(reply);
        if (refused) show(null, refused);
        else goOffline();
      };

      running.current = job;
      // `accept` is only a hint to the file dialog, and a drop has none (docs/library-notes/web-platform.md).
      if (!/\.mp4$/i.test(file.name)) {
        show(null, NOT_MP4);
        return;
      }
      show({ name: file.name, phase: "sending", percent: 0 }, warning);

      let checked: JsonReply<{ clip_id: string } | Refusal>;
      try {
        // A refusal sent while the browser is still sending the body reaches it as a network
        // error, so the cheap checks go first as JSON (spec › File import, step 0).
        checked = await sendJson("POST", CHECK_PATH, { name: file.name, size: file.size });
      } catch {
        if (job.stopped) show(null, CANCELLED);
        else goOffline();
        return;
      }
      if (job.stopped) show(null, CANCELLED);
      else if (checked.status !== 200) endOnReply(checked);
      else {
        const upload = sendFile<TempClip | Refusal>(
          `${IMPORTS_PATH}?name=${encodeURIComponent(file.name)}&size=${file.size}`,
          file,
          (percent) => show({ name: file.name, phase: "sending", percent }, warning),
          () => show({ name: file.name, phase: "checking" }, warning),
        );
        job.stop = upload.abort;
        const reply = await upload.reply;
        if (reply.kind === "aborted") show(null, CANCELLED);
        else if (reply.kind === "failed") show(null, UPLOAD_FAILED);
        else if (reply.status === 201 && reply.body !== null) {
          const clip = reply.body as TempClip;
          show(null, notice("success", `เอาไฟล์เข้าเสร็จ: ${clip.title}`, clip.id));
          onImported();
        } else endOnReply(reply);
      }
    },
    [onImported, onNotReady, setIfMounted],
  );

  /** ยกเลิก: the upload stops at once; a check still out is dropped when it answers. */
  const cancel = useCallback(() => running.current?.stop(), []);

  /** The next โหลด takes the place of the last import's message. */
  const clearNotice = useCallback(
    () => setIfMounted((s) => (s.kind === "ready" ? { ...s, notice: null } : s)),
    [setIfMounted],
  );

  /**
   * Refresh, or the tab going offline for another reason: stops an import under way without a
   * word (no cancel button behind the offline panel) and starts again idle.
   */
  const reset = useCallback(() => {
    const job = running.current;
    running.current = null;
    job?.stop();
    setIfMounted(IDLE);
  }, [setIfMounted]);

  return { state, start, cancel, clearNotice, reset };
}
