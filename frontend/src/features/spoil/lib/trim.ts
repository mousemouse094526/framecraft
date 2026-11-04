import type { Range } from "../../../lib/clips";

// D41's limits; backend.spoil.trim checks the same (MAX_RANGES, MIN_RANGE_S, MIN_KEPT_S).
export const MAX_RANGES = 20;
export const MIN_RANGE_S = 0.5;
export const MIN_KEPT_S = 10;
/** What เพิ่มช่วง adds at the playhead (spec › Frontend). */
const ADDED_S = 30;

/** A range as the user edits it: the two fields' text, so a half-typed time stays as typed. */
export type RangeDraft = { start: string; end: string };

/** Which end of a range: its field, its "= ตอนนี้" button and its timeline handle. */
export type Side = keyof RangeDraft;

/** The words each end shows (Figma `Trim range row`, `Trim timeline`). */
export const SIDE_WORDS: Record<Side, { field: string; now: string; handle: string }> = {
  start: { field: "เริ่ม", now: "เริ่ม = ตอนนี้", handle: "จุดเริ่ม" },
  end: { field: "จบ", now: "จบ = ตอนนี้", handle: "จุดจบ" },
};

/** Why ถอดบทพูด waits while the clip's own Trim job runs (D45); the API's `409 trimming` says the same. */
export const TRIMMING_THIS_CLIP = "กำลังตัดคลิปนี้อยู่";

/** Times move in tenths of a second (spec › Frontend). */
export const toTenth = (seconds: number): number => Math.round(seconds * 10) / 10;

/** `h:mm:ss.s`, the fields' form: 95.34 → "0:01:35.3". */
export function formatTime(seconds: number): string {
  const tenths = Math.round(seconds * 10);
  const h = Math.floor(tenths / 36000);
  const m = Math.floor((tenths % 36000) / 600);
  const s = (tenths % 600) / 10;
  return `${h}:${String(m).padStart(2, "0")}:${s.toFixed(1).padStart(4, "0")}`;
}

/** `h:mm:ss` of whole seconds, the timeline axis's form: 7082 → "1:58:02". */
export function formatAxisTime(seconds: number): string {
  const whole = Math.round(seconds);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${Math.floor(whole / 3600)}:${pad(Math.floor((whole % 3600) / 60))}:${pad(whole % 60)}`;
}

const WHOLE = /^\d+$/;
const SECONDS = /^\d+(?:\.\d*)?$/;

/** `h:mm:ss.s`, `m:ss` or `ss` (a fraction on the seconds only) as seconds; anything else → null. */
export function parseTime(text: string): number | null {
  const parts = text.trim().split(":");
  if (parts.length > 3) return null;
  const last = parts.length - 1;
  if (!parts.every((part, i) => (i === last ? SECONDS : WHOLE).test(part))) return null;
  const [seconds, minutes = 0, hours = 0] = parts.map(Number).reverse();
  // Seconds after a colon, and minutes after another, stay under 60; a lone number may be any.
  if ((parts.length > 1 && seconds >= 60) || (parts.length > 2 && minutes >= 60)) return null;
  return toTenth(hours * 3600 + minutes * 60 + seconds);
}

/** Why a field is wrong, per side: malformed, outside the clip, or not before its end (D41). */
export type RangeErrors = { start: boolean; end: boolean };

export function rangeErrors(draft: RangeDraft, length: number): RangeErrors {
  const start = parseTime(draft.start);
  const end = parseTime(draft.end);
  const startBad = start === null || start > length;
  const endBad = end === null || end > length;
  // A range shorter than D41's least is the end's fault: the end is what the user moves past the start.
  const order = !startBad && !endBad && end! - start! < MIN_RANGE_S;
  return { start: startBad, end: endBad || order };
}

/** The draft as seconds, or null while either field is wrong. */
export function rangeOf(draft: RangeDraft, length: number): Range | null {
  const errors = rangeErrors(draft, length);
  if (errors.start || errors.end) return null;
  return { start_s: parseTime(draft.start)!, end_s: parseTime(draft.end)! };
}

export const draftOf = (range: Range): RangeDraft => ({ start: formatTime(range.start_s), end: formatTime(range.end_s) });

/** Sorted, with overlapping or touching ranges joined: the way the backend reads them (backend.spoil.trim.merged). */
export function merged(ranges: Range[]): Range[] {
  const joined: Range[] = [];
  for (const one of [...ranges].sort((a, b) => a.start_s - b.start_s)) {
    const last = joined.at(-1);
    if (last && one.start_s <= last.end_s) last.end_s = Math.max(last.end_s, one.end_s);
    else joined.push({ ...one });
  }
  return joined;
}

export const cutSeconds = (ranges: Range[]): number =>
  merged(ranges).reduce((sum, one) => sum + one.end_s - one.start_s, 0);

/**
 * เพิ่มช่วง: 30 s from the playhead, cut short at the clip's end or the next range; null
 * when the playhead is in a range or the space there is under D41's least (spec › Frontend).
 */
export function rangeAt(playhead: number, ranges: Range[], length: number): Range | null {
  const start = toTenth(Math.min(Math.max(playhead, 0), length));
  if (ranges.some((one) => one.start_s <= start && start < one.end_s)) return null;
  const next = Math.min(length, ...ranges.filter((one) => one.start_s > start).map((one) => one.start_s));
  const end = Math.min(start + ADDED_S, next);
  return end - start < MIN_RANGE_S ? null : { start_s: start, end_s: end };
}

/**
 * Where a handle may go: past neither the other end of its range (less D41's least) nor
 * a neighbouring range (spec › Frontend). `others` are the other ranges that are valid.
 */
export function handleBounds(range: Range, side: Side, others: Range[], length: number): [number, number] {
  if (side === "start") {
    const low = Math.max(0, ...others.filter((one) => one.end_s <= range.start_s).map((one) => one.end_s));
    return [low, Math.max(low, range.end_s - MIN_RANGE_S)];
  }
  const high = Math.min(length, ...others.filter((one) => one.start_s >= range.end_s).map((one) => one.start_s));
  return [Math.min(high, range.start_s + MIN_RANGE_S), high];
}

/** What a trim deletes of a clip (`derived` of `409 has_derived`, spec › API). */
export type DerivedKind = "transcript" | "shots" | "episodes" | "draft";

// What each kind of data from the clip is called in the confirm (D37); shots and EP cuts go together.
const DERIVED_WORDS: Record<DerivedKind, string> = {
  transcript: "Transcript (รวมบรรทัดที่แก้ไว้)",
  shots: "ภาพฉากและการตัด EP",
  episodes: "ภาพฉากและการตัด EP",
  draft: "Spoil draft",
};

/** "ตัดคลิปจะลบ {รายการ} ของคลิปนี้ ตัดต่อไหม?" from the API's `derived` kinds; null when there is nothing to lose. */
export function derivedQuestion(derived: DerivedKind[]): string | null {
  const words = [...new Set(derived.map((kind) => DERIVED_WORDS[kind] ?? kind))];
  return words.length === 0 ? null : `ตัดคลิปจะลบ ${words.join(", ")} ของคลิปนี้ ตัดต่อไหม?`;
}

/** The kinds the list already knows the clip has (`transcribed`, `described`, `in_draft`). */
export function derivedOf(clip: { transcribed: boolean; described: boolean; in_draft: boolean }): DerivedKind[] {
  const kinds: DerivedKind[] = [];
  if (clip.transcribed) kinds.push("transcript");
  if (clip.described) kinds.push("shots");
  if (clip.in_draft) kinds.push("draft");
  return kinds;
}
