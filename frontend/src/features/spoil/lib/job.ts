import { sendJson } from "../../../lib/api";
import { refusalOf, type Refusal } from "./refusal";

/** A test for "still running" over a job's `state`, from the states that keep it polling. */
export function isUnfinishedIn<S extends string>(unfinished: readonly S[]) {
  return (job: { state: S }): boolean => unfinished.includes(job.state);
}

/** A state updater that applies `change` only while the state is of `kind`. */
export function onlyWhen<S extends { kind: string }, K extends S["kind"]>(
  kind: K,
  change: (state: Extract<S, { kind: K }>) => S,
) {
  return (previous: S): S => (previous.kind === kind ? change(previous as Extract<S, { kind: K }>) : previous);
}

export type CancelReply<Job> =
  | { kind: "cancelling"; job: Job }
  /** The job ended before the cancel arrived; the next poll shows how. */
  | { kind: "ended" }
  | { kind: "refused"; code: string }
  | { kind: "offline" };

/** `DELETE {path}` for a job's `…/current`, as the answer a hook acts on. */
export async function cancelCurrent<Job>(path: string): Promise<CancelReply<Job>> {
  try {
    const reply = await sendJson<Job | Refusal>("DELETE", path);
    if (reply.status === 202) return { kind: "cancelling", job: reply.body as Job };
    if (reply.status === 404) return { kind: "ended" };
    const code = refusalOf(reply.body)?.code;
    if (reply.status === 409 && code) return { kind: "refused", code };
  } catch {
    // no backend or no answer in 30 s
  }
  return { kind: "offline" };
}
