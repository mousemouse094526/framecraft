import { sendJson } from "./api";
import { refusalOf, type Refusal } from "./refusal";
import { noticeOf, type Notice } from "./notice";

/**
 * How a request ended: `ok` with the answer's body (what it changed as it is now, the job
 * started; `null` for a `204`), or `refused` with the notice and the refusal itself, for the
 * caller to check its `code` (`null` when no refusal came back: no backend).
 */
export type EditReply<T, R extends Refusal = Refusal> =
  | { kind: "ok"; value: T }
  | { kind: "refused"; notice: Notice; refusal: R | null };

export type EditOptions = {
  /** The statuses that mean it happened; 200 and 201 by default (a job start is 202, a delete 204). */
  ok?: readonly number[];
  /** The refusal codes whose notice is a `warning` (`NOT_NOW`); none by default. */
  warnings?: readonly string[];
};

/**
 * Every request of a page that changes something (an add, change or delete, a job start): an
 * `ok` status is `ok`; a refusal, or no backend, is `refused` with the notice titled `title`.
 * `R` is the refusal with the fields its codes carry (`card_ids`, `eps`…).
 */
export async function sendEdit<T, R extends Refusal = Refusal>(
  method: string,
  path: string,
  body: unknown,
  title: string,
  { ok = [200, 201], warnings = [] }: EditOptions = {},
): Promise<EditReply<T, R>> {
  try {
    const reply = await sendJson<T | R>(method, path, body);
    if (ok.includes(reply.status)) return { kind: "ok", value: reply.body as T };
    return { kind: "refused", notice: noticeOf(title, reply.body, warnings), refusal: refusalOf(reply.body) as R | null };
  } catch {
    return { kind: "refused", notice: noticeOf(title, null), refusal: null };
  }
}

/** How a หยุด ended: `cancelling` with the job, `ended` when it ended before the cancel came
 * (`404` `not_found`), or `refused` with the notice (a refusal, or no backend). */
export type StopReply<Job> = { kind: "cancelling"; job: Job } | { kind: "ended" } | { kind: "refused"; notice: Notice };

/** หยุด of a job of การ์ตูนเล่า or คลังเสียง: `DELETE {path}` of the job's `…/current`. */
export async function stopJob<Job>(path: string): Promise<StopReply<Job>> {
  const reply = await sendEdit<Job>("DELETE", path, undefined, "หยุดงานไม่ได้", { ok: [202] });
  if (reply.kind === "ok") return { kind: "cancelling", job: reply.value };
  return reply.refusal?.code === "not_found" ? { kind: "ended" } : { kind: "refused", notice: reply.notice };
}
