import { OFFLINE_TEXT } from "../../../lib/api";
import { refusalLine, refusalOf } from "../../../lib/refusal";

/** A line above the lists: why an action was refused (Figma toon / 3, states 3–6). */
export type Notice = { tone: "warning" | "error"; title: string; text: string; setupLink: boolean };

/** The line of a refused or failed request: the API's refusal line, or OFFLINE_TEXT when no
 * refusal came back (no backend). */
export function refusalTextOf(body: unknown): { text: string; setupLink: boolean } {
  const refusal = refusalOf(body);
  return refusal ? refusalLine(refusal) : { text: OFFLINE_TEXT, setupLink: false };
}

/** The notice of a refused or failed request: its refusal line; a `warning` for the codes
 * that mean "not now". */
export function noticeOf(title: string, body: unknown, warnings: readonly string[] = []): Notice {
  const refusal = refusalOf(body);
  const tone = refusal && warnings.includes(refusal.code) ? "warning" : "error";
  return { tone, title, ...refusalTextOf(body) };
}

/** "Not now: another job has it, or a model isn't installed." */
export const NOT_NOW = ["gpu_busy", "busy", "not_ready"] as const;
