import { isUnfinishedIn } from "../../../lib/job";

// A Song of the แกะเพลง tab as `/api/songs` answers it, its import job, and the tab's hashes
// (drum-notes spec › Data, API, Frontend; D2, D3, D18).

export const SONGS_PATH = "/api/songs";
export const IMPORT_PATH = `${SONGS_PATH}/import`;
export const songPath = (id: string) => `${SONGS_PATH}/${id}`;
export const audioUrl = (id: string) => `${songPath(id)}/audio.m4a`;
export const SONGS_HASH = "#/songs";
export const songHash = (id: string) => `${SONGS_HASH}/${id}`;

export type SourceKind = "link" | "file" | "midi";
export type Mode = "drums" | "melody";
export type Level = "ghost" | "normal" | "accent";
export type Hit = { t: number; piece: string; level: Level };
export type Analysis = { mode: Mode; start_s: number; end_s: number; beats: number[]; downbeats: number[]; hits: Hit[]; picked_at: string };
export type Song = {
  version: number;
  id: string;
  title: string;
  subtitle: string;
  source: { kind: SourceKind; url: string | null; name: string | null; size: number | null };
  duration_s: number;
  range: { start_s: number; end_s: number; mode: Mode } | null;
  analysis: Analysis | null;
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

/** What a running link import says in its row (spec › Design). */
export function importText(job: SongImport): string {
  if (job.state === "checking") return "กำลังเช็คลิงก์…";
  if (job.state === "downloading") return `กำลังโหลด ${job.percent ?? 0}%`;
  return "กำลังแปลงเสียง…";
}

export const SOURCE_LABELS: Record<SourceKind, string> = { link: "ลิงก์", file: "ไฟล์", midi: "MIDI" };

/** The analysis state a row shows: picked with its bars, or not yet (the running Pick job comes with its ticket). */
export function pickedText(row: SongRow): string {
  return row.analysis ? `แกะแล้ว ${row.analysis.bars} ห้อง` : "ยังไม่แกะ";
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

/** One bar the analysis found: between two downbeats, with its beats and hits counted (D6, D20). */
export type Bar = {
  n: number; // from 1, as shown
  start_s: number;
  end_s: number;
  beats: number;
  hits: number;
  /** Four beats make a 4/4 bar; any other count can't be picked for a lesson (D20). */
  fourFour: boolean;
};

/** The bars between consecutive downbeats; the stretch after the last downbeat is no bar. */
export function barsOf(analysis: Analysis): Bar[] {
  return analysis.downbeats.slice(0, -1).map((start, index) => {
    const end = analysis.downbeats[index + 1];
    const beats = analysis.beats.filter((t) => t >= start && t < end).length;
    return { n: index + 1, start_s: start, end_s: end, beats, hits: analysis.hits.filter((hit) => hit.t >= start && hit.t < end).length, fourFour: beats === 4 };
  });
}

/** `round(240 / median bar length)` of the 4/4 bars, within 40–240 (D20); null with none. */
export function bpmOf(bars: Bar[]): number | null {
  const lengths = bars.filter((bar) => bar.fourFour).map((bar) => bar.end_s - bar.start_s).sort((a, b) => a - b);
  if (lengths.length === 0) return null;
  const middle = Math.floor(lengths.length / 2);
  const median = lengths.length % 2 ? lengths[middle] : (lengths[middle - 1] + lengths[middle]) / 2;
  return Math.min(240, Math.max(40, Math.round(240 / median)));
}

/** "12.5 s", a bar's start as the strip shows it. */
export const seconds = (t: number) => `${t.toFixed(1)} s`;
