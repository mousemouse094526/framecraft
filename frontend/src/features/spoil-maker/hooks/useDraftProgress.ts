import { useCallback, useEffect, useRef, useState } from "react";
import { askOf, BUSY_TEXT, DRAFT_JOB_PATH, jobFailureText, runningDraft, sendDraft, SETUP_HASH, wholeDraft, type DraftJob, type WholeDraftJob } from "../lib/draft";
import { useDraftRun, useJobCalls } from "./useStepStatus";

/**
 * Refusals of ลองอีกครั้ง that need the setup changed: they offer กลับไปแก้ตั้งค่า only, as
 * sending the same order again can't pass (spec › Frontend, D87, D88; `story_not_found`: story-kb
 * spec › Frontend, step 1 then shows ไม่ใช้). The rest (`busy`,
 * `gpu_busy`, `draft_locked`, no answer) depend on something else: the steps read again and
 * ลองอีกครั้ง stays.
 */
const SETUP_REFUSALS = ["episodes_changed", "clip_not_ready", "voice_not_found", "story_not_found", "ep_empty", "transcript_too_long"] as const;

const needsSetup = (code: string) => (SETUP_REFUSALS as readonly string[]).includes(code);

/** What ตรวจแก้บท shows of a whole new draft, above or instead of the script (D81, D83, D85, D87). */
export type DraftProgressView =
  /** No whole new draft to show: the script as it is. */
  | { kind: "none" }
  /** The progress card; `cancel_requested` is กำลังยกเลิก (D85). */
  | { kind: "running"; job: WholeDraftJob }
  /** A poll or a cancel got no answer: offline until the steps read again (D87). */
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
 * A job is named by its `started_at`: one Draft job starts at a time (ADR-0010).
 */
export function useDraftProgress() {
  const run = useDraftRun();
  const { refreshSteps, cancelCurrent } = useJobCalls();
  const job = wholeDraft(run.job);
  const running = runningDraft(run.job);
  const [cancelledFor, setCancelledFor] = useState<string | null>(null);
  const [lost, setLost] = useState(false);
  const [retryStep, setRetryStep] = useState<RetryStep>("idle");
  const [refused, setRefused] = useState<{ code: string; text: string } | null>(null);
  // The job whose card is showing, and the one this page opened step 1 for after its cancel.
  const cardShownFor = useRef<string | null>(null);
  const openedSetupFor = useRef<string | null>(null);

  useEffect(() => {
    if (running) {
      cardShownFor.current = running.started_at;
      setLost(false);
      setRefused(null);
      return;
    }
    if (run.offline || !run.loaded) return; // nothing known yet: the card's job may still run
    // The card's job is gone with no ending of its own: no job now, or one of another kind (D87).
    if (cardShownFor.current !== null && job?.started_at !== cardShownFor.current) setLost(true);
    cardShownFor.current = null;
  }, [running, job, run.loaded, run.offline]);

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
    if (reply.kind === "cancelling") run.putJob(reply.job);
    else if (reply.kind === "offline") run.goOffline();
    // `ended`: the job stopped first; the steps read it again and this page follows how (D85).
    else refreshSteps();
  }, [job, cancelCurrent, refreshSteps, run]);

  const send = useCallback(async () => {
    if (!job) return;
    setRetryStep("sending");
    const reply = await sendDraft(askOf(job.order), run.draftExists);
    setRetryStep("idle");
    if (reply.kind === "started") {
      run.putJob(reply.job);
      refreshSteps();
      return;
    }
    if (reply.kind === "offline") {
      setRefused({ code: "offline", text: "เชื่อมต่อ backend ไม่ได้" });
      return;
    }
    const code = reply.refusal?.code ?? "";
    setRefused({ code, text: code === "busy" ? BUSY_TEXT : (reply.refusal?.message ?? "ร่างบทไม่สำเร็จ") });
    if (!needsSetup(code)) refreshSteps();
  }, [job, run, refreshSteps]);

  /** ลองอีกครั้ง: with a Spoil draft there it asks first, every time (D86). */
  const retry = useCallback(() => (run.draftExists ? setRetryStep("confirming") : void send()), [run.draftExists, send]);

  let view: DraftProgressView = { kind: "none" };
  if (run.offline) view = { kind: "offline" };
  else if (running) view = { kind: "running", job: running };
  else if (lost) view = { kind: "lost" };
  else if (refused) view = { kind: "failed", text: refused.text, canRetry: !needsSetup(refused.code) };
  else if (job?.state === "failed") view = { kind: "failed", text: jobFailureText(job), canRetry: true };
  else if (job?.state === "done" && cancelledFor === job.started_at) view = { kind: "cancelledTooLate" };

  return {
    view,
    /** A `key` that remounts the script once the job ends, so it is read again (D81). */
    scriptKey: job && !running ? `${job.started_at}:${job.state}` : "",
    retryStep,
    cancel,
    retry,
    /** ร่างทับ in the ask before replacing. */
    replaceDraft: () => void send(),
    /** ยกเลิก in the ask before replacing: the Spoil draft stays. */
    keepDraft: () => setRetryStep("idle"),
  };
}
