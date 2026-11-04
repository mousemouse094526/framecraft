import { useCallback, useEffect, useRef, useState } from "react";
import { isRunning } from "../../../lib/job";
import { askOf, BUSY_TEXT, DRAFT_JOB_PATH, jobFailureText, sendDraft, SETUP_HASH, wholeDraft, type DraftJob, type WholeDraftJob } from "../lib/draft";
import { useDraftRun, useJobCalls } from "./useStepStatus";

/**
 * Refusals of ลองอีกครั้ง that need the setup changed: they offer กลับไปแก้ตั้งค่า only, as
 * sending the same order again can't pass (spec › Frontend, D87). The rest (`busy`,
 * `gpu_busy`, `draft_locked`) depend on another job: the steps read again and ลองอีกครั้ง stays.
 */
const SETUP_REFUSALS = ["episodes_changed", "clip_not_ready", "voice_not_found", "ep_empty", "transcript_too_long"];

/** What ตรวจแก้บท shows of a whole new draft, above or instead of the script (D81, D83, D85, D87). */
export type DraftProgressView =
  /** No whole new draft to show: the script as it is. */
  | { kind: "none" }
  /** The progress card; `cancel_requested` is กำลังยกเลิก (D85). */
  | { kind: "running"; job: WholeDraftJob }
  /** A poll failed: offline until the steps read again (D87). */
  | { kind: "offline" }
  /** The draft failed, or ลองอีกครั้ง was refused: the text, and whether ลองอีกครั้ง is offered. */
  | { kind: "failed"; text: string; canRetry: boolean }
  /** The job whose card showed went away without an ending (the backend restarted, ADR-0010). */
  | { kind: "lost" }
  /** ยกเลิก came after the job had written the new draft (D85). */
  | { kind: "cancelledTooLate" };

/** ลองอีกครั้ง: nothing asked, the ask before replacing a draft (D86), or the request on its way. */
export type RetryStep = "idle" | "confirming" | "sending";

/**
 * Step 2's side of a whole new draft (`kind: "draft"`), read from the steps' state: the
 * progress card and its ยกเลิก, which opens step 1 once the job stops; ลองอีกครั้ง with the
 * job's order, asking before replacing a draft (D86); and the job lost on a restart.
 */
export function useDraftProgress() {
  const run = useDraftRun();
  const { refreshSteps, cancelCurrent } = useJobCalls();
  const job = wholeDraft(run.job);
  const running = job !== null && isRunning(job);
  // `started_at` names a job: the one ยกเลิก was pressed for, and the one whose card is showing.
  const [cancelledFor, setCancelledFor] = useState<string | null>(null);
  const [cardShownFor, setCardShownFor] = useState<string | null>(null);
  const [lost, setLost] = useState(false);
  const [retryStep, setRetryStep] = useState<RetryStep>("idle");
  const [refused, setRefused] = useState<{ code: string; text: string } | null>(null);
  const openedSetupFor = useRef<string | null>(null);

  useEffect(() => {
    if (running) {
      setCardShownFor(job.started_at);
      setLost(false);
      setRefused(null);
      return;
    }
    // The card's job is gone with no ending of its own: no job now, or one of another kind (D87).
    if (cardShownFor !== null && run.loaded && !run.offline && (job === null || job.started_at !== cardShownFor)) setLost(true);
    setCardShownFor(null);
  }, [running, job?.started_at, run.loaded, run.offline]);

  // Cancelled from here: step 1 opens with the order still picked (D83).
  useEffect(() => {
    if (job?.state === "cancelled" && cancelledFor === job.started_at && openedSetupFor.current !== job.started_at) {
      openedSetupFor.current = job.started_at;
      window.location.hash = SETUP_HASH;
    }
  }, [job, cancelledFor]);

  const cancel = useCallback(async () => {
    if (!job) return;
    setCancelledFor(job.started_at);
    const reply = await cancelCurrent<DraftJob>(DRAFT_JOB_PATH);
    if (reply.kind === "cancelling") run.show(reply.job);
    // `ended`: the job stopped first; the steps read it again and this page follows how (D85).
    else refreshSteps();
  }, [job, cancelCurrent, refreshSteps, run]);

  const send = useCallback(async () => {
    if (!job) return;
    setRetryStep("sending");
    const reply = await sendDraft(askOf(job.order), run.draftExists);
    setRetryStep("idle");
    if (reply.kind === "started") {
      run.show(reply.job);
      refreshSteps();
      return;
    }
    const code = reply.kind === "refused" ? (reply.refusal?.code ?? "") : "offline";
    const text =
      code === "busy" ? BUSY_TEXT : reply.kind === "refused" ? (reply.refusal?.message ?? "ร่างบทไม่สำเร็จ") : "เชื่อมต่อ backend ไม่ได้";
    setRefused({ code, text });
    if (!SETUP_REFUSALS.includes(code)) refreshSteps();
  }, [job, run, refreshSteps]);

  /** ลองอีกครั้ง: with a Spoil draft there it asks first, every time (D86). */
  const retry = useCallback(() => (run.draftExists ? setRetryStep("confirming") : void send()), [run.draftExists, send]);

  let view: DraftProgressView = { kind: "none" };
  if (run.offline) view = { kind: "offline" };
  else if (running) view = { kind: "running", job };
  else if (lost) view = { kind: "lost" };
  else if (refused) view = { kind: "failed", text: refused.text, canRetry: !SETUP_REFUSALS.includes(refused.code) };
  else if (job?.state === "failed") view = { kind: "failed", text: jobFailureText(job), canRetry: true };
  else if (job?.state === "done" && cancelledFor === job.started_at) view = { kind: "cancelledTooLate" };

  return {
    view,
    /** A `key` for the script: changes once the job ends, so the script is read again (D81). */
    scriptKey: job && !running ? `${job.started_at}:${job.state}` : "",
    retryStep,
    cancel,
    retry,
    /** ร่างทับ in the ask before replacing. */
    replace: () => void send(),
    /** ยกเลิก in the ask before replacing. */
    keep: () => setRetryStep("idle"),
  };
}
