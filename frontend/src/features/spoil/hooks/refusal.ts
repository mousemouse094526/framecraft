/** A refusal from the Spoil API: `{"code", "message"}`, plus `clip_id` on `duplicate`. */
export type Refusal = { code: string; message: string; clip_id?: string };

/** The body as a refusal, or null when it isn't one (no body, no code): the caller reads that as offline. */
export function refusalOf(body: unknown): Refusal | null {
  if (typeof body !== "object" || body === null) return null;
  const refusal = body as Partial<Refusal>;
  return typeof refusal.code === "string" && typeof refusal.message === "string" ? (refusal as Refusal) : null;
}
