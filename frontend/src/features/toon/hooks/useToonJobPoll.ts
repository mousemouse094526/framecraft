import { cancelCurrent } from "../../../lib/job";
import { usePollWhile } from "../../../lib/usePollWhile";
import { isRunning, JOB_PATH, type ToonJob } from "../lib/series";

/**
 * Polls the Toon job while `job` runs (spec › Frontend): a running answer goes to `onRunning`,
 * the job's end (or no job at all) to `onEnd`, a failed poll to `onFail`.
 */
export function useToonJobPoll(
  job: ToonJob | null,
  onRunning: (next: ToonJob) => void,
  onEnd: (next: ToonJob | null) => void,
  onFail: () => void,
) {
  usePollWhile<ToonJob | null>(
    job !== null && isRunning(job),
    JOB_PATH,
    (next) => (next !== null && isRunning(next) ? onRunning(next) : onEnd(next)),
    onFail,
  );
}

/** หยุด: the job, now `cancel_requested`, goes to `onCancelling` until the poll sees it end. */
export async function cancelToonJob(onCancelling: (job: ToonJob) => void) {
  const reply = await cancelCurrent<ToonJob>(JOB_PATH);
  if (reply.kind === "cancelling") onCancelling(reply.job);
}
