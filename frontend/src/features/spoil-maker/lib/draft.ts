// The shapes of the Spoil draft, the Draft job and Shots (backend.spoil_maker.draft, spoil-maker spec › API).

export type Style = "fast" | "drama" | "chrono";
export type Layout = "A" | "B" | "C";
export type SentenceStatus = "no_shot" | "no_audio" | "stale_audio" | "ready";

export type ShotRef = { clip_id: string; n: number };

export type Sentence = {
  id: string;
  text: string;
  refs: { clip_id: string; line: number }[];
  /** Always two slots; an empty one is null. */
  shots: (ShotRef | null)[];
  audio: { tts_text: string; voice_id: string; duration_s: number } | null;
  status: SentenceStatus;
  /** Null only when the draft's voice is gone. */
  estimated_s: number | null;
  ref_lines: { clip_id: string; line: number; start: number; end: number; text: string }[];
  /** ±30 s around the cited lines, inside the EP; null without refs (D26, D70). */
  window: { clip_id: string; start: number; end: number } | null;
};

/** An EP of a Temp clip by its number and range: [start_s, end_s) (spoil-maker spec › EP). */
export type EpRange = { n: number; start_s: number; end_s: number };

export type Draft = {
  clip_id: string;
  /** The EP as the clip was cut when the draft was written (D70). */
  ep: EpRange;
  clip_title: string;
  style: Style;
  layout: Layout;
  target_s: number;
  voice_id: string;
  original_volume: number;
  top_text: string;
  sentences: Sentence[];
  estimated_total_s: number;
  /** A job changes the draft: every field waits (D51). */
  locked: boolean;
};

export type DraftJobState = "writing" | "matching" | "done" | "failed" | "cancelled";

export type DraftJob = {
  kind: "draft" | "pick";
  state: DraftJobState;
  /** Sentences matched so far, and of how many: `matching` only. */
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
};

export type Shot = { n: number; start: number; end: number; description: string };

export const DRAFT_PATH = "/api/spoil-maker/draft";
export const DRAFT_JOBS_PATH = "/api/spoil-maker/draft-jobs";
export const DRAFT_JOB_PATH = "/api/spoil-maker/draft-jobs/current";
export const SETTINGS_PATH = "/api/spoil-maker/settings";
export const VOICES_PATH = "/api/spoil-maker/voices";

// The สปอย tab's hashes: its steps and the Saved voice page (spoil-maker D53, D59).
export const SETUP_HASH = "#/spoil";
export const REVIEW_HASH = "#/spoil/review";
export const RENDERS_HASH = "#/spoil/renders";
export const VOICES_HASH = "#/spoil/voices";

/** Whether the job still runs; null is no job. */
export const isDrafting = (job: DraftJob | null): boolean =>
  job !== null && (job.state === "writing" || job.state === "matching");

/** A model or a child that stopped says the same thing (spec › Frontend); the rest say the API's message. */
export function jobFailureText(job: DraftJob): string {
  const code = job.error?.code;
  if (code === "crashed" || code === "model_failed") return "งานหยุดกลางทาง";
  return job.error?.message ?? "ร่างบทไม่สำเร็จ";
}

export function shotsPath(clipId: string): string {
  return `/api/spoil-maker/clips/${clipId}/shots`;
}

export function shotImageUrl(clipId: string, n: number): string {
  return `/api/spoil-maker/clips/${clipId}/shots/${n}.jpg`;
}

/** "EP 2" (D70). */
export function epLabel(n: number): string {
  return `EP ${n}`;
}

/** Whether a Shot shows part of the EP: it starts before the EP ends and ends after it starts (D71). */
export function inEp(shot: Shot, ep: EpRange): boolean {
  return shot.start < ep.end_s && shot.end > ep.start_s;
}
