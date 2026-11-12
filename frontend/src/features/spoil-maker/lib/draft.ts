// The shapes of the Spoil draft, the Draft job and Shots (backend.spoil_maker.draft, spoil-maker spec › API).
import { sendJson } from "../../../lib/api";
import { isRunning } from "../../../lib/job";
import { refusalOf, type Refusal } from "../../../lib/refusal";

export type Style = "fast" | "drama" | "chrono";
export type Layout = "A" | "B" | "C";

/** What the text on top of the video is called in each layout; B has none (D19). */
export const TOP_TEXT_LABELS: Partial<Record<Layout, string>> = { A: "Hook", C: "ชื่อตอน" };

// The styles and how each tells the story (spoil-maker D7, D84); the layout is picked apart (D90).
export const STYLES: { id: Style; label: string; hint: string }[] = [
  { id: "fast", label: "ปั่นตัดเร็ว", hint: "ประโยคสั้น ตลก เร็ว เล่าเหตุการณ์เด่น" },
  { id: "drama", label: "เล่าละครหักมุม", hint: "hook เรื่อง หักมุม แรงจูงใจ คำถามชวนคอมเมนต์ท้ายคลิป" },
  { id: "chrono", label: "เล่าตามลำดับ", hint: "เล่าทีละฉากตามเวลา มีบทพูดตัวละครแทรกได้" },
];
export type SentenceStatus = "no_shot" | "no_audio" | "stale_audio" | "ready";

export type ShotRef = { clip_id: string; n: number };

export type Sentence = {
  id: string;
  text: string;
  refs: { clip_id: string; line: number }[];
  /** Always two slots; an empty one is null. */
  shots: (ShotRef | null)[];
  /** The user changed its text or inserted it: เรียบเรียงใหม่ keeps it unless told (D74, D75). */
  edited: boolean;
  audio: { tts_text: string; voice_id: string; duration_s: number } | null;
  status: SentenceStatus;
  /** Null only when the draft's voice is gone. */
  estimated_s: number | null;
  ref_lines: { clip_id: string; line: number; start: number; end: number; text: string }[];
  /** ±30 s around the cited lines, inside the EP; null without refs (D26, D70). */
  window: { clip_id: string; start: number; end: number } | null;
};

/** An EP of a Temp clip by its number and range: [start_s, end_s) (spoil-maker spec › EP). */
export type Ep = { n: number; start_s: number; end_s: number };

export type Draft = {
  clip_id: string;
  /** The EP as the clip was cut when the draft was written (D70). */
  ep: Ep;
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

export type DraftJobState = "writing" | "polishing" | "matching" | "done" | "failed" | "cancelled";

/** What a `kind: "draft"` job was asked for; the job keeps it after it ends (D82). */
export type DraftOrder = {
  clip_id: string;
  clip_title: string;
  ep: Ep;
  style: Style;
  layout: Layout;
  target_s: number;
  voice_id: string;
  /** The Story the job uses, null for "ไม่ใช้", and its title as the job started (story-kb D15). */
  story_id: string | null;
  story_title: string | null;
};

export type DraftJob = {
  kind: "draft" | "pick" | "polish";
  state: DraftJobState;
  /** Sentences matched so far, and of how many: `matching` only. A `polish` that is `done`:
   * the sentences whose text changed, of those asked (D76). */
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
  /** `kind: "draft"` only; null for the others. */
  order: DraftOrder | null;
};

/** What ร่างบท sends with `kind: "draft"`: one EP of one clip (D66, D71); the job's order without the titles it adds. */
export type DraftAsk = Omit<DraftOrder, "clip_title" | "story_title">;

export function askOf({ clip_title: _title, story_title: _story, ...ask }: DraftOrder): DraftAsk {
  return ask;
}

/** `POST /draft-jobs` of a whole new draft, as the answer a step acts on; `replace` once the user agreed (D28). */
export async function sendDraft(
  ask: DraftAsk,
  replace: boolean,
): Promise<{ kind: "started"; job: DraftJob } | { kind: "refused"; status: number; refusal: Refusal | null } | { kind: "offline" }> {
  try {
    const reply = await sendJson<DraftJob | Refusal>("POST", DRAFT_JOBS_PATH, { kind: "draft", ...ask, replace });
    if (reply.status === 202) return { kind: "started", job: reply.body as DraftJob };
    return { kind: "refused", status: reply.status, refusal: refusalOf(reply.body) };
  } catch {
    return { kind: "offline" };
  }
}

/** Another tab is drafting: what ร่างบท and ลองอีกครั้ง say to `busy` (D87). */
export const BUSY_TEXT = "มีงานร่างบทอยู่แล้ว";

/** A whole new draft, with its order (D81, D82). */
export type WholeDraftJob = DraftJob & { kind: "draft"; order: DraftOrder };

/** The latest Draft job when it is a whole new draft; null when it is none or another kind. */
export const wholeDraft = (job: DraftJob | null): WholeDraftJob | null =>
  job?.kind === "draft" && job.order !== null ? (job as WholeDraftJob) : null;

/** The whole new draft that still runs: it locks step 1 and shows its card on step 2 (D81, D82). */
export const runningDraft = (job: DraftJob | null): WholeDraftJob | null => {
  const whole = wholeDraft(job);
  return whole && isRunning(whole) ? whole : null;
};

/** "{clip title} · EP {n}": what a draft or an order is of (D68, D82). */
export const draftLabel = (of: { clip_title: string; ep: Ep }): string => `${of.clip_title} · ${epLabel(of.ep.n)}`;

/** What ตรวจแก้บท says of the Draft jobs it starts, which change the draft it shows (D25, D72). */
const REVIEW_JOB_TEXT: Record<"pick" | "polish", { doing: string; label: string; waitingFor: string }> = {
  pick: { doing: "AI กำลังเลือก Shot ใหม่", label: "ความคืบหน้าการเลือก Shot", waitingFor: "รอให้ AI เลือก Shot เสร็จก่อน" },
  polish: { doing: "กำลังเรียบเรียง", label: "ความคืบหน้าการเรียบเรียง", waitingFor: "รอให้ AI เรียบเรียงเสร็จก่อน" },
};

/** The text of a Draft job ตรวจแก้บท started; only `pick` and `polish` run while it is open. */
export function reviewJobText(job: DraftJob) {
  return REVIEW_JOB_TEXT[job.kind === "polish" ? "polish" : "pick"];
}

export type Shot = { n: number; start: number; end: number; description: string };

export const DRAFT_PATH = "/api/spoil-maker/draft";
export const DRAFT_JOBS_PATH = "/api/spoil-maker/draft-jobs";
export const DRAFT_JOB_PATH = "/api/spoil-maker/draft-jobs/current";
export const SETTINGS_PATH = "/api/spoil-maker/settings";

// The สปอย tab's hashes: its steps and the Saved voice page (spoil-maker D53, D59).
export const SETUP_HASH = "#/spoil";
export const REVIEW_HASH = "#/spoil/review";
export const RENDERS_HASH = "#/spoil/renders";


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
export function inEp(shot: Shot, ep: Ep): boolean {
  return shot.start < ep.end_s && shot.end > ep.start_s;
}
