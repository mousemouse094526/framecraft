import { OFFLINE_TEXT } from "./api";
import { refusalLine, refusalOf } from "./refusal";

/** A line above the lists: why an action was refused (Figma toon / 3, states 3–6), and
 * `lines`, what the refusal names one by one (the users of a sound, sound-library D7). */
export type Notice = { tone: "warning" | "error"; title: string; text: string; setupLink: boolean; lines?: string[] };

/** The notice of a refused or failed request: its refusal line, or OFFLINE_TEXT when no
 * refusal came back (no backend); a `warning` for the codes that mean "not now". */
export function noticeOf(title: string, body: unknown, warnings: readonly string[] = []): Notice {
  const refusal = refusalOf(body);
  if (!refusal) return { tone: "error", title, text: OFFLINE_TEXT, setupLink: false };
  return { tone: warnings.includes(refusal.code) ? "warning" : "error", title, ...refusalLine(refusal) };
}

/** "Not now: another job has it, or a model isn't installed." */
export const NOT_NOW = ["gpu_busy", "busy", "not_ready"] as const;
