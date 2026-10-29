/** A message after a job or a refusal, shown as an Alert (spec › Frontend, D33). */
export type Notice = {
  tone: "success" | "info" | "warning" | "error";
  text: string;
  /** A command to copy, from `error.fix` (D8). */
  fix: string | null;
  /** The clip this message is about: a highlighted list row (D12), or the panel's clip (D33). */
  clipId: string | null;
};

export function notice(tone: Notice["tone"], text: string, clipId: string | null = null): Notice {
  return { tone, text, fix: null, clipId };
}
