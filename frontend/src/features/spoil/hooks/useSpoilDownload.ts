import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import type { StatusResponse } from "../../../lib/statusTypes";
import { useMountedState } from "../../../lib/useMountedState";
import { refusalOf, type Refusal } from "./refusal";

// The shape of a Download job (backend.spoil.jobs.DownloadJob, spec › API).
export type JobState = "checking" | "downloading" | "merging" | "done" | "failed" | "cancelled";

export type JobError = {
  code: string;
  message: string;
  yt_dlp_version: string;
  fix: string | null;
};

export type DownloadJob = {
  url: string;
  id: string;
  state: JobState;
  title: string | null;
  percent: number | null;
  cancel_requested: boolean;
  error: JobError | null;
  clip_id: string | null;
};


/** The message after a job or a refusal, kept until the next โหลด (spec › Frontend). */
export type Notice = {
  tone: "success" | "info" | "warning" | "error";
  text: string;
  /** A command to copy, from `error.fix` (D8). */
  fix: string | null;
  /** The list row this message is about, highlighted while it shows (D12). */
  clipId: string | null;
};

export type SpoilState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "notReady"; missing: string[] }
  // `job` is only ever an unfinished job; a finished one becomes the notice.
  | { kind: "ready"; job: DownloadJob | null; notice: Notice | null };

const STATUS_PATH = "/api/setup/status";
const DOWNLOADS_PATH = "/api/spoil/downloads";
const CURRENT_PATH = "/api/spoil/downloads/current";
const POLL_MS = 1000;

// Only these Checklist items decide whether the tab can download (D9).
const NEEDED_ITEMS = ["ffmpeg", "yt_dlp", "deno"];

const UNFINISHED: JobState[] = ["checking", "downloading", "merging"];

function isUnfinished(job: DownloadJob): boolean {
  return UNFINISHED.includes(job.state);
}

function notice(tone: Notice["tone"], text: string, clipId: string | null = null): Notice {
  return { tone, text, fix: null, clipId };
}

function ready(job: DownloadJob | null, shown: Notice | null = null): SpoilState {
  return { kind: "ready", job, notice: shown };
}

const LOST_JOB = notice("warning", "งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง");

/** What a finished job says (spec › Frontend, messages after a job). */
function resultNotice(job: DownloadJob): Notice {
  if (job.state === "done") return notice("success", `โหลดเสร็จ: ${job.title ?? job.id}`, job.clip_id);
  if (job.state === "cancelled") return notice("info", "ยกเลิกแล้ว");
  return { tone: "error", text: job.error?.message ?? "โหลดไม่สำเร็จ", fix: job.error?.fix ?? null, clipId: null };
}

/** A refusal of POST /downloads; the text is the Frontend table's, not the API's. Unknown → undefined. */
function refusalNotice(body: unknown): Notice | undefined {
  const refusal = refusalOf(body);
  switch (refusal?.code) {
    case "invalid_url":
      return notice("error", "ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube");
    case "busy":
      return notice("warning", "กำลังโหลดคลิปอื่นอยู่");
    case "duplicate":
      // Points at the clip already in the list (D12).
      return notice("info", "คลิปนี้โหลดไว้แล้ว", refusal.clip_id ?? null);
  }
  return undefined;
}

function readyState(status: StatusResponse, job: DownloadJob | null): SpoilState {
  const missing = status.items
    .filter((item) => NEEDED_ITEMS.includes(item.id) && item.status !== "ok")
    .map((item) => item.label);
  if (missing.length > 0) return { kind: "notReady", missing };
  if (job === null) return ready(null);
  // Opening the tab on a finished job shows how it ended (D15).
  return isUnfinished(job) ? ready(job) : ready(null, resultNotice(job));
}

/** A poll's answer, applied to the job being followed. */
function afterPoll(state: SpoilState, job: DownloadJob | null): SpoilState {
  if (state.kind !== "ready" || state.job === null) return state;
  if (job === null) return ready(null, LOST_JOB);
  if (isUnfinished(job)) return { ...state, job };
  return ready(null, resultNotice(job));
}

/**
 * The สปอย tab: checks the install and the current job on mount, polls every
 * second only while a job is unfinished (D6), and starts or cancels a job.
 * Any failure (no backend, a status the API never sends, 30 s) is offline.
 * `onJobEnd` (a stable callback) runs once when a followed job ends or is
 * lost, so the list loads again (D6).
 */
export function useSpoilDownload(onJobEnd: () => void) {
  const [state, setState, setIfMounted] = useMountedState<SpoilState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [status, job] = await Promise.all([
        getJson<StatusResponse>(STATUS_PATH),
        getJson<DownloadJob | null>(CURRENT_PATH),
      ]);
      setIfMounted(readyState(status, job));
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const tracking = state.kind === "ready" && state.job !== null;

  useEffect(() => {
    if (!tracking) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const job = await getJson<DownloadJob | null>(CURRENT_PATH);
        if (stopped) return;
        setIfMounted((previous) => afterPoll(previous, job));
        // Polls run only while a job is followed, so any other answer is its end.
        if (job === null || !isUnfinished(job)) onJobEnd();
        // Once the job ends `tracking` flips and the cleanup clears this timer.
        timer = setTimeout(poll, POLL_MS);
      } catch {
        if (!stopped) setIfMounted({ kind: "offline" });
      }
    };
    timer = setTimeout(poll, POLL_MS);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [tracking, setIfMounted, onJobEnd]);

  const start = useCallback(
    async (url: string) => {
      setIfMounted(ready(null));
      try {
        const reply = await sendJson<DownloadJob | Refusal>("POST", DOWNLOADS_PATH, { url });
        if (reply.status === 202) {
          setIfMounted(ready(reply.body as DownloadJob));
          return;
        }
        if (reply.status === 503) {
          // The install broke since the tab opened: show which item is missing.
          await load();
          return;
        }
        const refused = reply.status === 400 || reply.status === 409 ? refusalNotice(reply.body) : undefined;
        setIfMounted(refused ? ready(null, refused) : { kind: "offline" });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [load, setIfMounted],
  );

  const cancel = useCallback(async () => {
    try {
      const reply = await sendJson<DownloadJob | Refusal>("DELETE", CURRENT_PATH);
      if (reply.status === 202) {
        const job = reply.body as DownloadJob;
        setIfMounted((previous) => (previous.kind === "ready" && previous.job ? { ...previous, job } : previous));
      } else if (reply.status === 409 && refusalOf(reply.body)?.code === "merging") {
        setIfMounted((previous) =>
          previous.kind === "ready" ? { ...previous, notice: notice("warning", "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว") } : previous,
        );
      } else if (reply.status !== 404) {
        // 404: the job ended before the cancel arrived; the next poll shows how.
        setIfMounted({ kind: "offline" });
      }
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load]);

  return { state, start, cancel, reload };
}
