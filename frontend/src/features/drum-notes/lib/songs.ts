import { isUnfinishedIn } from "../../../lib/job";
import type { PieceId } from "../../../lib/kit";
import { BARS_MAX, BPM_MAX, BPM_MIN, notePlace, type Note } from "../../../lib/lesson";

// A Song of the แกะเพลง tab as `/api/songs` answers it, its import job, its Pick job, the lesson
// preview, and the tab's hashes (drum-notes spec › Data, API, Frontend; D2, D3, D5, D11, D18, D20, D21).

export const SONGS_PATH = "/api/songs";
export const IMPORT_PATH = `${SONGS_PATH}/import`;
export const PICK_PATH = `${SONGS_PATH}/pick`;
export const songPath = (id: string) => `${SONGS_PATH}/${id}`;
export const audioUrl = (id: string) => `${songPath(id)}/audio.m4a`;
export const rangePath = (id: string) => `${songPath(id)}/range`;
export const pickPath = (id: string) => `${songPath(id)}/pick`;
export const previewPath = (id: string) => `${songPath(id)}/preview`;
export const listenPath = (id: string) => `${songPath(id)}/listen`;
export const songLessonsPath = (id: string) => `${songPath(id)}/lessons`;
export const SONGS_HASH = "#/songs";
export const songHash = (id: string) => `${SONGS_HASH}/${id}`;

export type SourceKind = "link" | "file" | "midi";
export type Mode = "drums" | "melody";
export type Level = "ghost" | "normal" | "accent";
/** A hit the models (or the MIDI file) found, in seconds of the song; not a lesson's `Hit` (its dynamic) in `lib/lesson.ts`. */
export type FoundHit = { t: number; piece: string; level: Level };
export type Analysis = { mode: Mode; start_s: number; end_s: number; beats: number[]; downbeats: number[]; hits: FoundHit[]; picked_at: string };
export type Range = { start_s: number; end_s: number; mode: Mode };
/** One bar the analysis found, as the API works it out on read: four beats make a 4/4 bar, any other count can't be picked (D20). */
export type FoundBar = { n: number; start_s: number; end_s: number; beats: number; hits: number; four_four: boolean };
export type Song = {
  version: number;
  id: string;
  title: string;
  subtitle: string;
  source: { kind: SourceKind; url: string | null; name: string | null; size: number | null };
  duration_s: number;
  range: Range | null;
  analysis: Analysis | null;
  /** The bars of `analysis`, in time order; empty until picked. */
  bars: FoundBar[];
  lessons: string[];
  created_at: string;
  updated_at: string;
};

/** One row of `GET /api/songs`: the analysis as its mode and bar count, the lessons as a count. */
export type SongRow = {
  id: string;
  title: string;
  subtitle: string;
  source_kind: SourceKind;
  duration_s: number;
  analysis: { mode: Mode; bars: number } | null;
  lessons: number;
  updated_at: string;
};

/** A link's Song import; a file's is one request and never shows here. */
export type SongImport = {
  url: string;
  state: "checking" | "downloading" | "converting" | "done" | "failed" | "cancelled";
  title: string | null;
  percent: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  song_id: string | null;
  started_at: string;
};

export const isImporting = isUnfinishedIn<SongImport["state"]>(["checking", "downloading", "converting"]);

/** The Pick job as `GET /api/songs/pick` answers it (spec › Pick job, D18, D20). */
export type PickJob = {
  song_id: string;
  state: "preparing" | "picking" | "done" | "failed" | "cancelled";
  percent: number;
  error: "no_beats" | "model_broken" | "model_failed" | "internal" | null;
  message: string | null;
  /** `model_broken`: the Status check row of the file that won't open, and the Setup script to run. */
  rows: string[] | null;
  fix: string | null;
  cancel_requested: boolean;
  started_at: string;
};

export const isPicking = isUnfinishedIn<PickJob["state"]>(["preparing", "picking"]);

/** The running Pick job of this song, or null: the one place that asks "is this song being picked". */
export function pickingOf(job: PickJob | null, songId: string): PickJob | null {
  return job !== null && job.song_id === songId && isPicking(job) ? job : null;
}

/** What a running Pick job says on the song page (spec › Design). */
export function pickText(job: PickJob): string {
  return job.state === "preparing" ? "กำลังเตรียมเสียง…" : `กำลังแกะโน้ต… ${job.percent}%`;
}

/** What a running link import says in its row (spec › Design). */
export function importText(job: SongImport): string {
  if (job.state === "checking") return "กำลังเช็คลิงก์…";
  if (job.state === "downloading") return `กำลังโหลด ${job.percent ?? 0}%`;
  return "กำลังแปลงเสียง…";
}

export const SOURCE_LABELS: Record<SourceKind, string> = { link: "ลิงก์", file: "ไฟล์", midi: "MIDI" };

/** The analysis state a row shows: being picked with its percent, picked with its bars, or not yet (spec › Design). */
export function pickedText(row: SongRow, job: PickJob | null): string {
  const picking = pickingOf(job, row.id);
  if (picking) return `กำลังแกะ ${picking.percent}%`;
  return row.analysis ? `แกะแล้ว ${row.analysis.bars} ห้อง` : "ยังไม่แกะ";
}

export const MODE_LABELS: Record<Mode, string> = { drums: "กลอง", melody: "ทำนอง" };
/** Under the mode options while ทำนอง is picked (D14). */
export const MELODY_HINT = "แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน";
/** Under a melody song's preview grid: which notes the app added (spec › Score step 5, D14). */
export const MELODY_BASE = "สแนร์คือจังหวะทำนอง · กระเดื่องจังหวะ 1 และ 3 กับไฮแฮทปิดทุกครึ่งจังหวะ แอปเติมให้";
export const RANGE_MIN_S = 4;
export const RANGE_MAX_S = 90;
/** The one message of a range that breaks a rule, the backend's too (spec › Design). */
export const RANGE_RULE = `ช่วงต้องยาว ${RANGE_MIN_S}–${RANGE_MAX_S} วินาที และอยู่ในเพลง`;

/** The field a range breaks the rules at, before the backend is asked (the same rules as `PUT /range`), or null. */
export function rangeFault(start_s: number, end_s: number, duration_s: number): "start_s" | "end_s" | null {
  if (Number.isNaN(start_s) || start_s < 0) return "start_s";
  if (Number.isNaN(end_s) || end_s > duration_s || end_s - start_s < RANGE_MIN_S || end_s - start_s > RANGE_MAX_S) return "end_s";
  return null;
}

/** Beside the link box: the song is for picking notes alone (legal 1, D15). */
export const NOTES_ONLY = "ใช้เพลงเพื่อแกะโน้ตเท่านั้น เสียงเพลงไม่เข้าคลิป";
/** A link or file that is a song already: shown, then the page goes to that song (D3, D20). */
export const ALREADY_IN = "เพลงนี้มีอยู่แล้ว";
/** The hint on the file box. */
export const FILE_HINT = "ไฟล์เสียงทุกชนิดที่อ่านได้ ไม่เกิน 200 MB · ไฟล์ MIDI (.mid) ไม่เกิน 5 MB · เพลงยาว 4 วินาทีถึง 10 นาที";
export const FILE_ACCEPT = "audio/*,video/*,.mp3,.m4a,.aac,.wav,.flac,.ogg,.opus,.mp4,.webm,.mid,.midi";

export type SongsView = { kind: "list" } | { kind: "song"; id: string };

/** `#/songs/{id}` opens a song; any other hash under `#/songs` is the list (spec › Frontend). */
export function songsViewOf(hash: string): SongsView {
  const found = /^#\/songs\/([A-Za-z0-9_-]{1,64})$/.exec(hash);
  return found ? { kind: "song", id: found[1] } : { kind: "list" };
}

// --- the lesson from the bars picked (spec › Score, D11, D13, D20, D21) ---

/** A hand note the Score dropped because two hands can't play its step (video-gen D20). */
export type Dropped = { piece: PieceId; step: number };
/** What `POST /preview` answers: the Groove as the lesson editor draws it, its BPM, the notes dropped. */
export type Preview = { groove: { bars: number; notes: Note[] }; bpm: number; dropped: Dropped[] };
/** What `POST /preview`, `/listen` and `/lessons` take: the first bar (from 0), how many, and the BPM (left out: the Score's default). Named as the backend's `lesson.Choice`: not the Pick job. */
export type Choice = { bar: number; bars: number; bpm?: number };
/** 1–4: the bar counts the user may pick (D11). */
export const BAR_COUNTS = Array.from({ length: BARS_MAX }, (_, index) => index + 1);
/** What `POST /lessons` answers. */
export type Created = { lesson_id: string; dropped: number };

/** How many 4/4 bars follow in a row from `bar` (itself included), up to four: the counts the user may pick (D11, D20). */
export function pickableFrom(bars: FoundBar[], bar: number): number {
  let count = 0;
  while (count < BARS_MAX && bars[bar + count]?.four_four) count += 1;
  return count;
}

/** The first 4/4 bar, the pick a picked song opens with; -1 with none. */
export const firstPickable = (bars: FoundBar[]) => bars.findIndex((bar) => bar.four_four);

export const NO_FOUR_FOUR = "ไม่มีห้อง 4/4 ให้เลือก ลองแกะช่วงอื่น";
/** The one message of a BPM that breaks the rule, the backend's too. */
export const BPM_RULE = `BPM ต้องเป็นจำนวนเต็ม ${BPM_MIN}–${BPM_MAX}`;

/** Whether a typed BPM is one the backend takes. */
export const bpmOk = (bpm: number) => Number.isInteger(bpm) && bpm >= BPM_MIN && bpm <= BPM_MAX;

/** "ไฮแฮทปิด ห้อง 1 จังหวะ 3": a dropped note as the list under the grid names it, the way its cell would (D20). */
export const droppedText = (dropped: Dropped) => notePlace(dropped.piece, dropped.step);

/** "12.5 s", a bar's start as the strip shows it. */
export const seconds = (t: number) => `${t.toFixed(1)} s`;
