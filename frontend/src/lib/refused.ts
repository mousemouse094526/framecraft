import { OFFLINE_TEXT } from "./api";
import { refusalOf } from "./refusal";
import { fixesFor } from "./setupFixes";

/**
 * A request the API refused, as a page shows it (drum-notes D30): the line, its tone (`warning` for
 * a code that means "not now", else `error`), the fix commands of the Status check rows a `not_ready`
 * or `model_broken` names (setup-status D26), and the field an `invalid_request` names, which a page
 * shows at that field instead. No backend is a refusal too: OFFLINE_TEXT, nothing else.
 */
export type Refused = { tone: "error" | "warning"; text: string; fixes: string[]; field: string | null };

export const OFFLINE: Refused = { tone: "error", text: OFFLINE_TEXT, fixes: [], field: null };

/** The codes that mean "not now", not "wrong" (toon D72). */
export const NOT_NOW: readonly string[] = ["busy", "not_ready"];

/** The `Refused` of an answer's body; `warnings` are the codes shown as a `warning`. */
export async function refusedOf(body: unknown, warnings: readonly string[] = []): Promise<Refused> {
  const refusal = refusalOf(body);
  if (!refusal) return OFFLINE;
  return { tone: warnings.includes(refusal.code) ? "warning" : "error", text: refusal.message, fixes: await fixesFor(refusal), field: refusal.field ?? null };
}

/** A refusal with no backend call for its fixes: a job's own failure line, a message the page already has. */
export const refusedLine = (text: string, fixes: string[] = []): Refused => ({ tone: "error", text, fixes, field: null });
