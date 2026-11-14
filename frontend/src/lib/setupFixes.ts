import { getJson } from "./api";
import type { StatusResponse } from "./statusTypes";

/** The fix command of each named row that has one, from the Status check; none when it can't be read. */
/** The fix commands of a refusal: those of the rows a `not_ready` names, none for any other code. */
export async function fixesFor(refusal: { code: string; rows?: string[] }): Promise<string[]> {
  return refusal.code === "not_ready" ? fixesOf(refusal.rows ?? []) : [];
}

export async function fixesOf(rows: string[]): Promise<string[]> {
  try {
    const status = await getJson<StatusResponse>("/api/setup/status");
    // A `hint` is advice, not a command to copy (setup-status D26).
    return status.items.filter((item) => rows.includes(item.id) && item.fix && item.fix_kind === "command").map((item) => item.fix as string);
  } catch {
    return [];
  }
}
