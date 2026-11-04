/** `h:mm:ss`, or `m:ss` under an hour: a clip's length (spec › Frontend). */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

/** `hh:mm:ss` of whole seconds, as the backend's `.txt` writes a line's start (D22). */
export function formatClock(seconds: number): string {
  const whole = Math.floor(seconds);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(Math.floor(whole / 3600))}:${pad(Math.floor((whole % 3600) / 60))}:${pad(whole % 60)}`;
}

/** Seconds from `h:mm:ss`, `m:ss` or `s` as a person types them; null for anything else. */
export function parseClock(text: string): number | null {
  const parts = text.trim().split(":");
  if (parts.length > 3 || !parts.every((part) => /^\d+$/.test(part))) return null;
  return parts.reduce((seconds, part) => seconds * 60 + Number(part), 0);
}
