import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { busyText } from "../../../lib/gpu";
import { cancelCurrent, isUnfinishedIn, onlyWhen } from "../../../lib/job";
import { refusalLine, refusalOf, type Refusal, type RefusalLine } from "../../../lib/refusal";
import { usePollWhile } from "../../../lib/usePollWhile";

// The shape of a Describe job (backend.spoil_maker.describe.DescribeJob, spoil-maker spec › API).
export type DescribeJobState = "cutting" | "describing" | "done" | "failed" | "cancelled";

export type DescribeJob = {
  kind: "describe";
  state: DescribeJobState;
  clip_id: string;
  /** `cutting` only. */
  percent: number | null;
  /** Shots described so far, and of how many: `describing` only. */
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
};

export type DescribeState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      /** Only ever an unfinished job; a failed one becomes its row's error. */
      job: DescribeJob | null;
      /** Why a row's last try didn't describe it (a refusal or a failed job), by clip id. */
      errors: Record<string, RefusalLine>;
    };

type Loaded = Extract<DescribeState, { kind: "loaded" }>;

const DESCRIBES_PATH = "/api/spoil-maker/describes";
const CURRENT_PATH = "/api/spoil-maker/describes/current";

const isUnfinished = isUnfinishedIn<DescribeJobState>(["cutting", "describing"]);

/** A model or a child that stopped says the same thing (spoil-maker spec › Frontend); the rest say the API's message. */
function failureText(job: DescribeJob): string {
  const code = job.error?.code;
  if (code === "crashed" || code === "model_failed") return "งานหยุดกลางทาง";
  return job.error?.message ?? "บรรยายฉากไม่สำเร็จ";
}

const whenLoaded = (change: (state: Loaded) => DescribeState) => onlyWhen<DescribeState, "loaded">("loaded", change);

const withError = (clipId: string, error: RefusalLine | null) =>
  whenLoaded((s) => {
    const errors = { ...s.errors };
    if (error === null) delete errors[clipId];
    else errors[clipId] = error;
    return { ...s, errors };
  });

/**
 * The one Describe job of the clip list (spoil-maker D16): checks the current
 * job on mount, polls every second while one is unfinished, apart from the
 * other jobs' polls. Any failure (no backend, a status the API never sends,
 * 30 s) is offline. `onClipsChanged` (stable) loads the list again when a job
 * ends (บรรยายฉากแล้ว may change) or a clip is gone; `onNotReady` (stable) runs on
 * a `503`, so the status is checked again.
 */
export function useDescribe(onClipsChanged: () => void, onNotReady: () => void) {
  const [state, setState, setIfMounted] = useMountedState<DescribeState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const job = await getJson<DescribeJob | null>(CURRENT_PATH);
      setIfMounted({ kind: "loaded", job: job !== null && isUnfinished(job) ? job : null, errors: {} });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  usePollWhile<DescribeJob | null>(
    state.kind === "loaded" && state.job !== null,
    CURRENT_PATH,
    (job) => {
      if (job !== null && isUnfinished(job)) {
        setIfMounted(whenLoaded((s) => ({ ...s, job })));
        return;
      }
      // Polls run only while a job is followed, so any other answer is its end.
      setIfMounted(whenLoaded((s) => ({ ...s, job: null })));
      if (job?.state === "failed") setIfMounted(withError(job.clip_id, { text: failureText(job), setupLink: false }));
      onClipsChanged();
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /**
   * Posts the job; a refusal the user should read stays under the clip's row.
   * `confirmDraftLoss` once the user went on past the Spoil draft warning (spoil-maker D49).
   */
  const start = useCallback(
    async (clipId: string, confirmDraftLoss = false) => {
      setIfMounted(withError(clipId, null));
      try {
        const body = confirmDraftLoss ? { clip_id: clipId, confirm_draft_loss: true } : { clip_id: clipId };
        const reply = await sendJson<DescribeJob | Refusal>("POST", DESCRIBES_PATH, body);
        if (reply.status === 202) {
          const job = reply.body as DescribeJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        const refusal = refusalOf(reply.body);
        if (reply.status === 409 && refusal?.code === "busy") {
          const job = await getJson<DescribeJob | null>(CURRENT_PATH);
          if (job !== null && isUnfinished(job)) setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        if (reply.status === 409 && refusal && busyText(refusal)) {
          setIfMounted(withError(clipId, refusalLine(refusal)));
          return;
        }
        if (reply.status === 404 && refusal?.code === "not_found") {
          onClipsChanged();
          return;
        }
        if (reply.status === 409 && refusal?.code === "in_draft") {
          // A draft made since the list loaded: the new list marks the clip, so the next try warns.
          setIfMounted(withError(clipId, refusalLine(refusal)));
          onClipsChanged();
          return;
        }
        if (reply.status === 503 && refusal?.code === "not_ready") {
          // "ยังติดตั้งไม่ครบ: {rows}" with a link to ติดตั้ง (spec › Frontend), and the status is checked again.
          setIfMounted(withError(clipId, refusalLine(refusal)));
          onNotReady();
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [onClipsChanged, onNotReady, setIfMounted],
  );

  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<DescribeJob>(CURRENT_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenLoaded((s) => (s.job ? { ...s, job: reply.job } : s)));
    } else if (reply.kind !== "ended") {
      // The API never refuses this cancel with 409, so that too is an answer it never sends.
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, start, cancel, reload };
}
