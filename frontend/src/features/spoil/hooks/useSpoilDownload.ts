import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import type { StatusResponse } from "../../../lib/statusTypes";
import { useMountedState } from "../../../lib/useMountedState";
import { DOWNLOAD_ITEMS, missingLabels } from "../lib/gate";
import { cancelCurrent, isUnfinishedIn, onlyWhen } from "../lib/job";
import { notice, type Notice } from "../lib/notice";
import { refusalOf, type Refusal } from "../lib/refusal";
import { usePollWhile } from "./usePollWhile";

// The shape of a Download job (backend.spoil.downloads.DownloadJob, spec › API).
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

// The notice after a download is kept until the next โหลด (spec › Frontend).
export type SpoilState =
  | { kind: "loading" }
  | { kind: "offline" }
  // `status` is kept for the transcript panel, which gates on other items (D27).
  | { kind: "notReady"; status: StatusResponse; missing: string[] }
  // `job` is only ever an unfinished job; a finished one becomes the notice.
  | { kind: "ready"; status: StatusResponse; job: DownloadJob | null; notice: Notice | null };

const STATUS_PATH = "/api/setup/status";
const DOWNLOADS_PATH = "/api/spoil/downloads";
const CURRENT_PATH = "/api/spoil/downloads/current";

const isUnfinished = isUnfinishedIn<JobState>(["checking", "downloading", "merging"]);

function ready(status: StatusResponse, job: DownloadJob | null, shown: Notice | null = null): SpoilState {
  return { kind: "ready", status, job, notice: shown };
}

type Ready = Extract<SpoilState, { kind: "ready" }>;

/** Applies `change` only while the tab is ready. */
const whenReady = (change: (state: Ready) => SpoilState) => onlyWhen<SpoilState, "ready">("ready", change);

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
  const missing = missingLabels(status, DOWNLOAD_ITEMS);
  if (missing.length > 0) return { kind: "notReady", status, missing };
  if (job === null) return ready(status, null);
  // Opening the tab on a finished job shows how it ended (D15).
  return isUnfinished(job) ? ready(status, job) : ready(status, null, resultNotice(job));
}

/** A poll's answer, applied to the job being followed. */
function afterPoll(state: SpoilState, job: DownloadJob | null): SpoilState {
  if (state.kind !== "ready" || state.job === null) return state;
  if (job === null) return ready(state.status, null, LOST_JOB);
  if (isUnfinished(job)) return { ...state, job };
  return ready(state.status, null, resultNotice(job));
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

  usePollWhile<DownloadJob | null>(
    tracking,
    CURRENT_PATH,
    (job) => {
      setIfMounted((previous) => afterPoll(previous, job));
      // Polls run only while a job is followed, so any other answer is its end.
      if (job === null || !isUnfinished(job)) onJobEnd();
    },
    () => setIfMounted({ kind: "offline" }),
  );

  const start = useCallback(
    async (url: string) => {
      setIfMounted(whenReady((s) => ({ ...s, notice: null })));
      try {
        const reply = await sendJson<DownloadJob | Refusal>("POST", DOWNLOADS_PATH, { url });
        if (reply.status === 202) {
          const job = reply.body as DownloadJob;
          setIfMounted(whenReady((s) => ({ ...s, job })));
          return;
        }
        if (reply.status === 503) {
          // The install broke since the tab opened: show which item is missing.
          await load();
          return;
        }
        const refused = reply.status === 400 || reply.status === 409 ? refusalNotice(reply.body) : undefined;
        if (!refused) {
          setIfMounted({ kind: "offline" });
          return;
        }
        setIfMounted(whenReady((s) => ({ ...s, notice: refused })));
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [load, setIfMounted],
  );

  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<DownloadJob>(CURRENT_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenReady((s) => (s.job ? { ...s, job: reply.job } : s)));
    } else if (reply.kind === "refused" && reply.code === "merging") {
      setIfMounted(whenReady((s) => ({ ...s, notice: notice("warning", "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว") })));
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load]);

  /**
   * Asks for the status again, keeping the job and its message: the transcript
   * panel got a `503` and gates on the same status (D27, D34). A download still
   * running stays followed even if an item it needs went missing, so its
   * progress and its end are still shown.
   */
  const recheckStatus = useCallback(async () => {
    try {
      const status = await getJson<StatusResponse>(STATUS_PATH);
      setIfMounted((previous) => {
        if (previous.kind !== "ready" && previous.kind !== "notReady") return previous;
        if (previous.kind === "ready" && previous.job !== null) return { ...previous, status };
        const next = readyState(status, previous.kind === "ready" ? previous.job : null);
        return next.kind === "ready" && previous.kind === "ready" ? { ...next, notice: previous.notice } : next;
      });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  return { state, start, cancel, reload, recheckStatus };
}
