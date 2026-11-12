import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getJson } from "../../../lib/api";
import { cancelCurrent, isRunning } from "../../../lib/job";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { DRAFT_JOB_PATH, DRAFT_PATH, wholeDraft, type Draft, type DraftJob } from "../lib/draft";
import {
  RENDER_JOB_PATH,
  RENDERS_PATH,
  startJob,
  VOICE_JOB_PATH,
  type RenderJob,
  type RenderResult,
  type SentencesJob,
} from "../lib/render";
import type { StepStatus } from "../lib/steps";

const START: StepStatus = { draft: undefined, renders: undefined, draftJob: null, voiceJob: null, renderJob: null };

type JobKey = "draftJob" | "voiceJob" | "renderJob";

const sentencesOnly = (job: SentencesJob | { kind: string } | null): SentencesJob | null =>
  job?.kind === "sentences" ? (job as SentencesJob) : null;

const readResults = () => Promise.all([getJson<Draft | null>(DRAFT_PATH), getJson<RenderResult[]>(RENDERS_PATH)]);

/**
 * Tells the steps to read everything again. A step calls it once it starts or cancels a
 * job, or changes how many sentences or renders there are; alone (no steps) it does nothing.
 */
export const StepsRefreshContext = createContext<() => void>(() => {});

export const useStepsRefresh = () => useContext(StepsRefreshContext);

/** The latest Draft job as the steps hold it, for the steps that start, follow or show it (spoil-maker D81–D87). */
export type DraftRun = {
  /** False until the steps' first read answered or failed (a failed one leaves `job` null): step 1 starts from its order (D87). */
  loaded: boolean;
  job: DraftJob | null;
  /** A Spoil draft is there: ลองอีกครั้ง asks before replacing it (D86). */
  draftExists: boolean;
  /** The last poll of the running job failed; the steps read again every second until one answers (D87). */
  offline: boolean;
  /** Puts a job a step just started or cancelled in the steps' state, before the hash changes (D87). */
  putJob: (job: DraftJob) => void;
  /** No answer from the backend: offline until a read answers (D87). */
  goOffline: () => void;
};

export const DraftRunContext = createContext<DraftRun>({
  loaded: false,
  job: null,
  draftExists: false,
  offline: false,
  putJob: () => {},
  goOffline: () => {},
});

export const useDraftRun = () => useContext(DraftRunContext);

const RETRY_MS = 1000;

/**
 * `startJob` and `cancelCurrent` for a step's hook: each tells the steps once a job is started
 * or found running (`busy`), or is cancelling, so no caller has to remember to.
 */
export function useJobCalls() {
  const refreshSteps = useStepsRefresh();
  const start = useCallback(
    async <Job>(path: string, body: unknown) => {
      const reply = await startJob<Job>(path, body);
      if (reply.kind === "started" || reply.kind === "busy") refreshSteps();
      return reply;
    },
    [refreshSteps],
  );
  const cancel = useCallback(
    async <Job>(path: string) => {
      const reply = await cancelCurrent<Job>(path);
      if (reply.kind === "cancelling") refreshSteps();
      return reply;
    },
    [refreshSteps],
  );
  return { refreshSteps, startJob: start, cancelCurrent: cancel };
}

/**
 * What the steps of the สปอย tab show (spoil-maker D68, D71): the Spoil draft, the renders and
 * the latest Draft, Voice (`sentences`) and Render job, for whichever step is open. Each
 * job is polled every second while it runs; one that ends reads the draft and the renders
 * again. A failed read keeps the lines as they were: the open step shows offline.
 */
export function useStepStatus() {
  const [status, , setIfMounted] = useMountedState<StepStatus>(START);
  const [draftJobOffline, setDraftJobOffline] = useState(false);
  const [firstReadDone, setFirstReadDone] = useState(false);

  const load = useCallback(async () => {
    try {
      const [[draft, renders], draftJob, voiceJob, renderJob] = await Promise.all([
        readResults(),
        getJson<DraftJob | null>(DRAFT_JOB_PATH),
        getJson<SentencesJob | { kind: string } | null>(VOICE_JOB_PATH),
        getJson<RenderJob | null>(RENDER_JOB_PATH),
      ]);
      setIfMounted({ draft, renders, draftJob, voiceJob: sentencesOnly(voiceJob), renderJob });
      setDraftJobOffline(false);
    } catch {
      // the open step says offline
    }
    setFirstReadDone(true);
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const follow = (key: JobKey) => (job: DraftJob | SentencesJob | RenderJob | null) => {
    setIfMounted((s) => ({ ...s, [key]: key === "voiceJob" ? sentencesOnly(job) : job }));
    if (isRunning(job)) return;
    readResults().then(
      ([draft, renders]) => setIfMounted((s) => ({ ...s, draft, renders })),
      () => {}, // as in load
    );
  };
  // A poll that failed stopped; dropping the job lets the next refresh follow it again.
  const dropJob = (key: JobKey) => () => setIfMounted((s) => ({ ...s, [key]: null }));

  // A failed poll of a whole new draft keeps the job: ตรวจแก้บท says offline, not that the job is gone (D87).
  const draftPollFailed = () => (wholeDraft(status.draftJob) ? setDraftJobOffline(true) : dropJob("draftJob")());
  usePollWhile(isRunning(status.draftJob) && !draftJobOffline, DRAFT_JOB_PATH, follow("draftJob"), draftPollFailed);
  useEffect(() => {
    if (!draftJobOffline) return;
    const timer = setInterval(() => void load(), RETRY_MS);
    return () => clearInterval(timer);
  }, [draftJobOffline, load]);
  usePollWhile(isRunning(status.voiceJob), VOICE_JOB_PATH, follow("voiceJob"), dropJob("voiceJob"));
  usePollWhile(isRunning(status.renderJob), RENDER_JOB_PATH, follow("renderJob"), dropJob("renderJob"));

  const refresh = useCallback(() => void load(), [load]);
  const putJob = useCallback((job: DraftJob) => setIfMounted((s) => ({ ...s, draftJob: job })), [setIfMounted]);
  const goOffline = useCallback(() => setDraftJobOffline(true), []);
  const draftRun: DraftRun = {
    loaded: firstReadDone,
    job: status.draftJob,
    draftExists: Boolean(status.draft),
    offline: draftJobOffline,
    putJob,
    goOffline,
  };

  return { status, refresh, draftRun };
}
