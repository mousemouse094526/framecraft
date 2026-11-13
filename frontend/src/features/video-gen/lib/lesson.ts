import { isFoot, type PieceId } from "./kit";

// A drum lesson as `/api/drums/lessons` answers it, and the rules the editor checks before a `PUT` (spec › Data).

export type Hand = "R" | "L";
export type Hit = "normal" | "accent" | "ghost" | "flam";
export type Note = { piece: PieceId; step: number; hand: Hand | null; hit: Hit };
export type Chapter = { label: string; text: string; focus: PieceId[]; repeats: number; speed: number };

/** What a `PUT` sends: the whole lesson but `id`, `version`, `updated_at` and `length_s`. */
export type LessonFields = {
  title: string;
  subtitle: string;
  caption: string;
  bpm: number;
  background: "color" | "image";
  groove: { bars: number; notes: Note[] };
  chapters: Chapter[];
};

export type Lesson = LessonFields & { version: number; id: string; updated_at: string; length_s: number };

/** One row of `GET /api/drums/lessons`. */
export type LessonRow = { id: string; title: string; length_s: number; renders: number; updated_at: string };

export const LESSONS_PATH = "/api/drums/lessons";
export const lessonPath = (id: string) => `${LESSONS_PATH}/${id}`;
export const DRUMS_HASH = "#/drums";
export const lessonHash = (id: string) => `${DRUMS_HASH}/${id}`;

/** The lesson `#/drums/{id}` opens; any other hash under `#/drums` is the list (spec › Frontend). */
export function lessonIdOf(hash: string): string | null {
  return /^#\/drums\/([a-z0-9]{12})$/.exec(hash)?.[1] ?? null;
}

export const STEPS_PER_BAR = 16;
export const BARS_MAX = 4;
export const CHAPTERS_MAX = 6;
export const TITLE_MAX = 40;
export const LINE_MAX = 60; // subtitle, caption and a chapter's text
export const LABEL_MAX = 16;
export const BPM_MIN = 40;
export const BPM_MAX = 240;
export const REPEATS_MAX = 8;
export const SPEEDS = [50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100];
/** The longest clip ฟังจังหวะ and render take (D16). */
export const MAX_SECONDS = 90;
const TAIL_SECONDS = 1.5;

export const HITS: { id: Hit; name: string }[] = [
  { id: "normal", name: "ปกติ" },
  { id: "accent", name: "เน้น" },
  { id: "ghost", name: "เบา" },
  { id: "flam", name: "flam" },
];

/** A new chapter at full speed (spec › Data). */
export const NEW_CHAPTER: Chapter = { label: "", text: "", focus: [], repeats: 2, speed: 100 };

/** `length_s` as `backend/video_gen/timeline.py` `length_s` works it out (keep the two alike): a bar of count-in at the first chapter's speed, every chapter, then 1.5 s of tail (D21). */
export function lengthOf(fields: LessonFields): number {
  const bar = (speed: number) => (4 * 60) / ((fields.bpm * speed) / 100);
  const countIn = bar(fields.chapters[0]?.speed ?? 100);
  const chapters = fields.chapters.reduce((sum, c) => sum + c.repeats * fields.groove.bars * bar(c.speed), 0);
  return countIn + chapters + TAIL_SECONDS;
}

/** "2e" for a step's place in its bar: the beat, then e, & or a for the 16ths after it. */
export function countOf(step: number): string {
  const inBar = step % STEPS_PER_BAR;
  return `${Math.floor(inBar / 4) + 1}${["", "e", "&", "a"][inBar % 4]}`;
}

// --- One hand plays one piece at a time (D20); the same rules as the backend's `PUT` ---

/** The hands the step's other hand notes hold; a flam holds both, as it must be the only hand note. */
function handsHeld(notes: Note[], step: number, except?: Note): Set<Hand> {
  const held = new Set<Hand>();
  for (const note of notes) {
    if (note === except || note.step !== step || isFoot(note.piece)) continue;
    if (note.hit === "flam") return new Set(["R", "L"]);
    if (note.hand) held.add(note.hand);
  }
  return held;
}

const HIHATS: ReadonlySet<PieceId> = new Set(["hihat_open", "hihat_closed"]);

/** The note a click on an empty cell adds, with the free hand (R first); null when the cell can't take one. */
export function noteFor(notes: Note[], piece: PieceId, step: number): Note | null {
  if (isFoot(piece)) return { piece, step, hand: null, hit: "normal" };
  if (HIHATS.has(piece) && notes.some((n) => n.step === step && HIHATS.has(n.piece))) return null;
  const held = handsHeld(notes, step);
  const hand = (["R", "L"] as const).find((h) => !held.has(h));
  return hand ? { piece, step, hand, hit: "normal" } : null;
}

/** Whether `note` may take `hand`: no other hand note of its step holds it. */
export const canTakeHand = (notes: Note[], note: Note, hand: Hand) => !handsHeld(notes, note.step, note).has(hand);

/** Whether `note` may be played as `hit`: a flam only on a hand piece alone in its step. */
export function canTakeHit(notes: Note[], note: Note, hit: Hit): boolean {
  if (hit !== "flam") return true;
  return !isFoot(note.piece) && !notes.some((n) => n !== note && n.step === note.step && !isFoot(n.piece));
}

/** The notes past the last of `bars` bars, which fewer bars drop. */
export const notesPast = (notes: Note[], bars: number) => notes.filter((n) => n.step >= bars * STEPS_PER_BAR);

// --- Fields ---

export function fieldsOf(lesson: Lesson): LessonFields {
  const { title, subtitle, caption, bpm, background, groove, chapters } = lesson;
  return { title, subtitle, caption, bpm, background, groove, chapters };
}

export const sameFields = (a: LessonFields, b: LessonFields) => JSON.stringify(a) === JSON.stringify(b);

/** Field key → message; the keys are the API's `field` (`bpm`, `chapters[1].label`, `groove.notes[3]`). */
export type FieldErrors = Record<string, string>;

/** The text and number rules a `PUT` would refuse, checked first so the page answers at once (spec › Data). */
export function fieldErrors(fields: LessonFields): FieldErrors {
  const errors: FieldErrors = {};
  // Letters are code points, as the backend counts them (story-kb D12).
  const length = (text: string) => [...text].length;
  const title = fields.title.trim();
  if (!title) errors.title = "ใส่หัวเรื่อง";
  else if (length(title) > TITLE_MAX) errors.title = `หัวเรื่องยาวเกิน ${TITLE_MAX} ตัวอักษร`;
  if (length(fields.subtitle) > LINE_MAX) errors.subtitle = `บรรทัดรองยาวเกิน ${LINE_MAX} ตัวอักษร`;
  if (length(fields.caption) > LINE_MAX) errors.caption = `คำบรรยายยาวเกิน ${LINE_MAX} ตัวอักษร`;
  if (!Number.isInteger(fields.bpm) || fields.bpm < BPM_MIN || fields.bpm > BPM_MAX) {
    errors.bpm = `BPM ต้องเป็นจำนวนเต็ม ${BPM_MIN}–${BPM_MAX}`;
  }
  fields.chapters.forEach((chapter, index) => {
    if (length(chapter.label) > LABEL_MAX) errors[`chapters[${index}].label`] = `ป้ายยาวเกิน ${LABEL_MAX} ตัวอักษร`;
    if (length(chapter.text) > LINE_MAX) errors[`chapters[${index}].text`] = `คำอธิบายยาวเกิน ${LINE_MAX} ตัวอักษร`;
  });
  return errors;
}

/** The index of the note an error names (`groove.notes[3]`), or null. */
export function noteIndexOf(field: string): number | null {
  const match = /^groove\.notes\[(\d+)\]/.exec(field);
  return match ? Number(match[1]) : null;
}
