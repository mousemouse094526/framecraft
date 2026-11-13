import { isUnfinishedIn } from "../../../lib/job";

// A Song of the แกะเพลง tab as `/api/songs` answers it, its import job, its Pick job, and the tab's
// hashes (drum-notes spec › Data, API, Frontend; D2, D3, D5, D18, D20).

export const SONGS_PATH = "/api/songs";
export const IMPORT_PATH = `${SONGS_PATH}/import`;
export const PICK_PATH = `${SONGS_PATH}/pick`;
export const songPath = (id: string) => `${SONGS_PATH}/${id}`;
export const audioUrl = (id: string) => `${songPath(id)}/audio.m4a`;
export const rangePath = (id: string) => `${songPath(id)}/range`;
export const pickPath = (id: string) => `${songPath(id)}/pick`;
export const SONGS_HASH = "#/songs";
export const songHash = (id: string) => `${SONGS_HASH}/${id}`;

export type SourceKind = "link" | "file" | "midi";
export type Mode = "drums" | "melody";
export type Level = "ghost" | "normal" | "accent";
export type Hit = { t: number; piece: string; level: Level };
export type Analysis = { mode: Mode; start_s: number; end_s: number; beats: number[]; downbeats: number[]; hits: Hit[]; picked_at: string };
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
/** Under the melody option, which ticket 04 opens (D14). */
export const MELODY_HINT = "แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน";
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

/** `round(240 / median bar length)` of the 4/4 bars, within 40–240 (D20); null with none. */
export function bpmOf(bars: FoundBar[]): number | null {
  const lengths = bars.filter((bar) => bar.four_four).map((bar) => bar.end_s - bar.start_s).sort((a, b) => a - b);
  if (lengths.length === 0) return null;
  const middle = Math.floor(lengths.length / 2);
  const median = lengths.length % 2 ? lengths[middle] : (lengths[middle - 1] + lengths[middle]) / 2;
  return Math.min(240, Math.max(40, Math.round(240 / median)));
}

/** "12.5 s", a bar's start as the strip shows it. */
export const seconds = (t: number) => `${t.toFixed(1)} s`;
