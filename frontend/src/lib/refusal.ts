import { busyText } from "./gpu";

/**
 * A refusal from the API: `{"code", "message"}`, plus `clip_id` on `duplicate`, `running` on
 * `gpu_busy`, `field` on `invalid_story` and `invalid_request`, and `rows` on `not_ready`.
 */
export type Refusal = { code: string; message: string; clip_id?: string; running?: string; field?: string; rows?: string[] };

/** The body as a refusal, or null when it isn't one (no body, no code): the caller reads that as offline. */
export function refusalOf(body: unknown): Refusal | null {
  if (typeof body !== "object" || body === null) return null;
  const refusal = body as Partial<Refusal>;
  return typeof refusal.code === "string" && typeof refusal.message === "string" ? (refusal as Refusal) : null;
}

/** A refusal to show as a line: `setupLink` when the install misses a row the job needs (`not_ready`, spoil-maker spec › Frontend). */
export type RefusalLine = { text: string; setupLink: boolean };

/** The line for a refusal: `gpu_busy` names the running job, anything else says the API's message. */
export function refusalLine(refusal: Refusal): RefusalLine {
  return { text: busyText(refusal) ?? refusal.message, setupLink: refusal.code === "not_ready" };
}
