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

/** A count with thousands separators, `32,000`: token counts and letter limits. */
export const grouped = (n: number) => n.toLocaleString("en-US");

const THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];

/**
 * "5 พ.ย. 14:20" from `2026-11-05T14:20:00+07:00`: the wall time the backend wrote, which is
 * the machine's own clock, read straight from the text so no time zone can shift it.
 */
export function editedAt(iso: string): string {
  const [, month, day, hour, minute] = /^\d{4}-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso) ?? [];
  if (!month) return iso;
  return `${Number(day)} ${THAI_MONTHS[Number(month) - 1]} ${hour}:${minute}`;
}
