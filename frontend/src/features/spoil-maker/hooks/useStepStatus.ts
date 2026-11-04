import { createContext, useCallback, useContext, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { isRunning } from "../../../lib/job";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { DRAFT_JOB_PATH, DRAFT_PATH, type Draft, type DraftJob } from "../lib/draft";
import { RENDER_JOB_PATH, RENDERS_PATH, VOICE_JOB_PATH, type RenderJob, type RenderResult, type SentencesJob } from "../lib/render";
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

/**
 * What the steps of the สปอย tab show (spoil-maker D68, D71): the Spoil draft, the renders and
 * the latest Draft, Voice (`sentences`) and Render job, for whichever step is open. Each
 * job is polled every second while it runs; one that ends reads the draft and the renders
 * again. A failed read keeps the lines as they were: the open step shows offline.
 */
export function useStepStatus() {
  const [status, , setIfMounted] = useMountedState<StepStatus>(START);

  const load = useCallback(async () => {
    try {
      const [[draft, renders], draftJob, voiceJob, renderJob] = await Promise.all([
        readResults(),
        getJson<DraftJob | null>(DRAFT_JOB_PATH),
        getJson<SentencesJob | { kind: string } | null>(VOICE_JOB_PATH),
        getJson<RenderJob | null>(RENDER_JOB_PATH),
      ]);
      setIfMounted({ draft, renders, draftJob, voiceJob: sentencesOnly(voiceJob), renderJob });
    } catch {
      // the open step says offline
    }
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
  const lost = (key: JobKey) => () => setIfMounted((s) => ({ ...s, [key]: null }));

  usePollWhile(isRunning(status.draftJob), DRAFT_JOB_PATH, follow("draftJob"), lost("draftJob"));
  usePollWhile(isRunning(status.voiceJob), VOICE_JOB_PATH, follow("voiceJob"), lost("voiceJob"));
  usePollWhile(isRunning(status.renderJob), RENDER_JOB_PATH, follow("renderJob"), lost("renderJob"));

  const refresh = useCallback(() => void load(), [load]);

  return { status, refresh };
}
