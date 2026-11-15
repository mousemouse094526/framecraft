import { isUnfinishedIn } from "../../../lib/job";
import { reelRendersPath, songPath, type Song } from "../../drum-notes/lib/songs";

// A song's reel cover as `/api/songs/{id}/cover` answers it, its Render job and its results, and
// the page's hash (drum-cover spec › Data, API, Frontend; D2, D6, D7, D11, D12, D18, D19).
export const coverPath = (id: string) => `${songPath(id)}/cover`;
export const coverListenPath = (id: string) => `${coverPath(id)}/listen`;
export const coverRenderPath = (id: string) => `${coverPath(id)}/render`;
export const coverRenderFile = (id: string, name: string, suffix: ".mp4" | ".srt") => `${reelRendersPath(id)}/${name}${suffix}`;
export const COVER_RENDER_PATH = "/api/covers/render";
export const COVER_CANCEL_PATH = `${COVER_RENDER_PATH}/cancel`;

/** `#/songs/{id}/cover` is a song's reel page; App picks it before the แกะเพลง tab sees the hash (D11). */
export function coverViewOf(hash: string): { id: string } | null {
  const found = /^#\/songs\/([A-Za-z0-9_-]{1,64})\/cover$/.exec(hash);
  return found ? { id: found[1] } : null;
}

export type Backing = { on: boolean; volume: number };

/** What `PUT /cover` takes. */
export type CoverFields = {
  start_s: number;
  end_s: number;
  title: string;
  subtitle: string;
  caption: string;
  background: "color" | "image";
  backing: Backing;
};

/** What `GET`/`PUT /cover` answer: the fields and what the page says about them (D18). */
export type Cover = CoverFields & {
  saved: boolean;
  /** The stored stretch was pulled into a new pick's range: the page shows it unsaved. */
  adjusted: boolean;
  /** False for a MIDI song: no backing to choose. */
  has_audio: boolean;
  /** The hits in the stretch: none → no ฟัง, no render. */
  hits: number;
  length_s: number;
  suggested_start_s: number;
  updated_at: string | null;
};

export const fieldsOf = (cover: Cover): CoverFields => ({
  start_s: cover.start_s,
  end_s: cover.end_s,
  title: cover.title,
  subtitle: cover.subtitle,
  caption: cover.caption,
  background: cover.background,
  backing: cover.backing,
});

export type CoverRenderJob = {
  state: "rendering" | "done" | "failed" | "cancelled";
  song_id: string;
  title: string;
  percent: number;
  result: string | null;
  error: "ffmpeg_failed" | "internal" | null;
  message: string | null;
};

export const isCoverRendering = (job: CoverRenderJob | null) => job !== null && isUnfinishedIn<CoverRenderJob["state"]>(["rendering"])(job);

export type CoverRenderResult = {
  name: string;
  song_id: string;
  title: string;
  length_s: number;
  start_s: number;
  end_s: number;
  picked_at: string;
  backing: Backing;
  created_at: string;
  size_bytes: number;
};

/** A render made from a pick before the song's current one (ADR 0034, D18). */
export const isStale = (result: CoverRenderResult, song: Song) => song.analysis !== null && result.picked_at !== song.analysis.picked_at;

export const MIN_S = 2;
export const MAX_S = 90;
export const TITLE_MAX = 40;
export const LINE_MAX = 60;
export const VOLUME_MIN = 10;
export const VOLUME_MAX = 100;
/** The one message of a stretch that breaks a rule, the backend's too. */
export const RANGE_RULE = `ช่วงต้องยาว ${MIN_S}–${MAX_S} วินาที และอยู่ในช่วงแกะ`;

/** The field a stretch breaks the rules at, before the backend is asked (`PUT /cover`'s rules), or null. */
export function stretchFault(start_s: number, end_s: number, picked: { start_s: number; end_s: number }): "start_s" | "end_s" | null {
  if (Number.isNaN(start_s) || start_s < picked.start_s) return "start_s";
  if (Number.isNaN(end_s) || end_s > picked.end_s || end_s - start_s < MIN_S || end_s - start_s > MAX_S) return "end_s";
  return null;
}

/** The hits a song's analysis has in a stretch, as the backend counts them. */
export const hitsIn = (song: Song, start_s: number, end_s: number) => song.analysis?.hits.filter((hit) => start_s <= hit.t && hit.t < end_s).length ?? 0;

export const NO_ANALYSIS = "แกะโน้ตก่อน แล้วกลับมาทำ reel";
export const NO_HITS = "ช่วงนี้ไม่มีการตีกลอง เลื่อนช่วงหรือกด เริ่มที่การตีแรก";
export const NO_AUDIO = "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ";
export const MELODY_ONLY = "เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์";
export const TITLE_HINT = "ค่าตั้งต้นมาจากชื่อคลิปและช่อง แก้เป็นชื่อเพลงและศิลปิน";
/** Beside the backing choice (legal 2, D7). */
export const BACKING_WARNING = "เพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim ปิดเสียง หรือบล็อกคลิป เปิดเมื่อคุณมีสิทธิ์ใช้เสียงนี้";
export const adjustedText = (cover: Cover) => `ช่วงแกะเปลี่ยน ช่วงของ reel ถูกปรับเป็น ${cover.start_s.toFixed(1)}–${cover.end_s.toFixed(1)} วินาที`;
export const downloadName = (song: Song, result: CoverRenderResult, suffix: string) => `${song.title} - reel ${result.name}${suffix}`;
