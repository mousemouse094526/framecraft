import { getJson } from "../../../lib/api";
import type { StatusResponse } from "../../../lib/statusTypes";

/** The fix command of each named row that has one, from the Status check; none when it can't be read. */
export async function fixesOf(rows: string[]): Promise<string[]> {
  try {
    const status = await getJson<StatusResponse>("/api/setup/status");
    // A `hint` is advice, not a command to copy (setup-status D26).
    return status.items.filter((item) => rows.includes(item.id) && item.fix && item.fix_kind === "command").map((item) => item.fix as string);
  } catch {
    return [];
  }
}
