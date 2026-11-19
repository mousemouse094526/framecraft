import { isUnfinishedIn } from "../../../lib/job";

// A Song of reel cover (once แกะเพลง) as `/api/songs` answers it, its import job, its Pick job, and the tab's
// hashes (drum-notes spec › Data, API, Frontend; D2, D3, D5, D18, D20; reels-only D7).

export const SONGS_PATH = "/api/songs";
export const IMPORT_PATH = `${SONGS_PATH}/import`;
export const PICK_PATH = `${SONGS_PATH}/pick`;
export const songPath = (id: string) => `${SONGS_PATH}/${id}`;
export const audioUrl = (id: string) => `${songPath(id)}/audio.m4a`;
export const rangePath = (id: string) => `${songPath(id)}/range`;
export const pickPath = (id: string) => `${songPath(id)}/pick`;
export const SONGS_HASH = "#/covers"; // reel cover (nav-ia D6)
export const songHash = (id: string) => `${SONGS_HASH}/${id}`;
/** A song's reel page, drum-cover's (drum-cover D11): this tab links to it and reads its renders by HTTP alone (ADR 0052). */
export const reelHash = (id: string) => `${songHash(id)}/cover`;
export const reelRendersPath = (id: string) => `${songPath(id)}/cover/renders`;

export type SourceKind = "link" | "file" | "midi";
export type Mode = "drums" | "melody";
export type Level = "ghost" | "normal" | "accent";
/** A hit the models (or the MIDI file) found, in seconds of the song; not a lesson's `Hit` (its dynamic) in `lib/lesson.ts`. */
export type FoundHit = { t: number; piece: string; level: Level };
/** A melody note found (or read from a MIDI file), its pitch a MIDI number (kalimba-cover D2); not a lesson's `Note`. */
export type MelodyNote = { t: number; pitch: number; level: Level };
/** `notes` null: picked before the melody was kept; `[]`: none heard (kalimba-cover D2). */
export type Analysis = { mode: Mode; start_s: number; end_s: number; beats: number[]; downbeats: number[]; hits: FoundHit[]; notes: MelodyNote[] | null; picked_at: string };
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
  created_at: string;
  updated_at: string;
};

/** One row of `GET /api/songs`: the analysis as its mode and bar count. */
export type SongRow = {
  id: string;
  title: string;
  subtitle: string;
  source_kind: SourceKind;
  duration_s: number;
  analysis: { mode: Mode; bars: number } | null;
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
/** Under the mode options while ทำนอง is picked: what a reel cover plays of it (D14, reels-only D9). */
export const MELODY_HINT = "สำหรับเพลงที่ไม่มีกลอง (piano, kalimba): จังหวะของโน้ตทำนองเป็นสแนร์ใน reel กลอง และโน้ตทำนองเล่นใน reel คาลิมบา";
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
/** The hint on the file box: how a MIDI file's channels are read, and whose file it should be (kalimba-cover D3, D13). */
export const FILE_HINT =
  "ไฟล์เสียงทุกชนิดที่อ่านได้ ไม่เกิน 200 MB · ไฟล์ MIDI (.mid) ไม่เกิน 5 MB · เพลงยาว 4 วินาทีถึง 10 นาที · MIDI: ช่อง 10 เป็นกลอง ช่องอื่นเป็นทำนองสำหรับคาลิมบา · ใช้ไฟล์ MIDI ที่ทำเองหรือมีสิทธิ์ใช้";
export const FILE_ACCEPT = "audio/*,video/*,.mp3,.m4a,.aac,.wav,.flac,.ogg,.opus,.mp4,.webm,.mid,.midi";

export type SongsView = { kind: "list" } | { kind: "song"; id: string };

/** `#/covers/{id}` opens a song; any other hash under `#/covers` is the list (spec › Frontend, nav-ia D6). */
export function songsViewOf(hash: string): SongsView {
  const found = /^#\/covers\/([A-Za-z0-9_-]{1,64})$/.exec(hash);
  return found ? { kind: "song", id: found[1] } : { kind: "list" };
}

/** "12.5 s", a length as the range shows it. */
export const seconds = (t: number) => `${t.toFixed(1)} s`;

// --- where the drums start (drum-cover D9, D19) ---

/** An analysis that found no hit: what the page says above ผลแกะ. */
export const noHitsText = (analysis: Analysis) => `ไม่พบการตีกลองในช่วง ${analysis.start_s.toFixed(1)}–${analysis.end_s.toFixed(1)} วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น`;

/** The first bars found empty, before any hit: how many, where the first hit is, and the range that starts there. */
export type LateStart = { empty: number; first_s: number; range: Range | null };

/**
 * The bars found with no hit from the first on, when no hit comes before them (one before the first
 * downbeat means the drums are there already); null when bar 1 has a hit or nothing was found. The
 * new range starts at the first bar with a hit (or the hit), rounded down to 0.1 s, as long as the
 * old one up to the song's end, and at least 4 s (D9, D19); a MIDI song has no range to move.
 */
export function lateStart(song: Song): LateStart | null {
  const analysis = song.analysis;
  if (!analysis || analysis.hits.length === 0) return null;
  const empty = song.bars.findIndex((bar) => bar.hits > 0);
  const leading = empty < 0 ? song.bars.length : empty;
  const first_s = Math.min(...analysis.hits.map((hit) => hit.t));
  if (leading === 0 || first_s < song.bars[leading - 1].end_s) return null;
  if (!song.range) return { empty: leading, first_s, range: null };
  let start_s = Math.floor((empty < 0 ? first_s : song.bars[empty].start_s) * 10) / 10;
  let end_s = Math.min(song.duration_s, start_s + (song.range.end_s - song.range.start_s));
  if (end_s - start_s < RANGE_MIN_S) {
    start_s = Math.max(0, song.duration_s - RANGE_MIN_S);
    end_s = song.duration_s;
  }
  return { empty: leading, first_s, range: { start_s, end_s, mode: song.range.mode } };
}

export const lateStartText = (late: LateStart) =>
  `${late.empty === 1 ? "ห้อง 1" : `ห้อง 1–${late.empty}`} ไม่มีการตี การตีแรกอยู่ที่ ${late.first_s.toFixed(1)} วินาที`;
