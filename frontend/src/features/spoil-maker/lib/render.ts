// The shapes of the Voice job `sentences`, the Render job, its results and what the tab
// remembers (backend.spoil_maker.voices, .render, .settings; spoil-maker spec › API).

import { sendJson } from "../../../lib/api";
import { busyText } from "../../../lib/gpu";
import { refusalOf, type Refusal } from "../../../lib/refusal";

export type Position = "top_left" | "top_center" | "top_right" | "bottom_left" | "bottom_center" | "bottom_right";
export type MarkSize = "small" | "medium";
export type Watermark = { text: string; position: Position; size: MarkSize };
export type VideoSettings = { watermarks: Watermark[]; original_volume: number; last_voice_id: string | null };

/** The Voice job `sentences`: `done`/`total` sentences voiced. */
export type SentencesJob = {
  kind: "sentences";
  state: "voicing" | "done" | "failed" | "cancelled";
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
};

/** The Render job: `done`/`total` while voicing, `percent` while rendering. */
export type RenderJob = {
  kind: "render";
  state: "voicing" | "rendering" | "done" | "failed" | "cancelled";
  percent: number | null;
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
};

export type RenderResult = {
  name: string;
  created_at: string;
  duration_s: number;
  size_bytes: number;
  /** The Temp clips' titles in EP order (legal 1). */
  sources: string[];
};

export const VOICE_JOBS_PATH = "/api/spoil-maker/voice-jobs";
export const VOICE_JOB_PATH = "/api/spoil-maker/voice-jobs/current";
export const RENDERS_PATH = "/api/spoil-maker/renders";
export const RENDER_JOB_PATH = "/api/spoil-maker/renders/current";

export const WATERMARKS_MAX = 6; // D41
export const WATERMARK_TEXT_MAX = 40;

/** "สร้างเสียง 1/3" or "render 50%" (spec › Design, หน้าตรวจแก้). */
export function progressText(job: SentencesJob | RenderJob): string {
  if (job.cancel_requested) return "กำลังยกเลิก…";
  if (job.state === "rendering") return `render ${job.percent ?? 0}%`;
  return `สร้างเสียง ${job.done ?? 0}/${job.total ?? 0}`;
}

/** The bar's fill: sentences done of all while voicing, the percent while rendering. */
export function progressPercent(job: SentencesJob | RenderJob): number {
  if (job.state === "rendering") return job.percent ?? 0;
  return job.total ? Math.round((100 * (job.done ?? 0)) / job.total) : 0;
}

/** Figma `Review banner`: its tone, two lines, and whether ลองอีกครั้ง can start the job again. */
export type Banner = { tone: "error" | "warning"; title: string; text: string; retry: boolean };

export const LOW_DISK: Banner = {
  tone: "warning",
  title: "ที่ว่างดิสก์ไม่ถึง 1 GiB",
  text: "ลบ render เก่าในหน้าผล render เพื่อเพิ่มที่ว่าง",
  retry: false,
};

/** The banner of a job that ended `failed` (spec › Frontend). */
export function failureOf(job: { error: { code: string; message: string } | null }): Banner {
  const code = job.error?.code;
  if (code === "ffmpeg_failed")
    return { tone: "error", title: "render ไม่สำเร็จ", text: "บทและเสียงยังอยู่ครบ กด render ใหม่ได้", retry: true };
  if (code === "crashed" || code === "model_failed")
    return { tone: "warning", title: "งานหยุดกลางทาง", text: "เสียงที่สร้างเสร็จแล้วยังอยู่: เริ่มต่อได้", retry: true };
  return { tone: "error", title: "ไม่สำเร็จ", text: job.error?.message ?? "ลองอีกครั้ง", retry: true };
}

/** A refusal to show as a line: `gpu_busy` names the running job; `not_ready` links to ติดตั้ง (spec › Frontend). */
export type Refused = { text: string; setupLink: boolean };

export type StartReply<Job> =
  | { kind: "started"; job: Job }
  /** Such a job runs already: follow it. */
  | { kind: "busy" }
  | { kind: "banner"; banner: Banner }
  | { kind: "refused"; refused: Refused }
  | { kind: "offline" };

/** `POST` that starts a job, as the answer a hook acts on. */
export async function startJob<Job>(path: string, body: unknown): Promise<StartReply<Job>> {
  try {
    const reply = await sendJson<Job | Refusal>("POST", path, body);
    if (reply.status === 202) return { kind: "started", job: reply.body as Job };
    const refusal = refusalOf(reply.body);
    if (!refusal) return { kind: "offline" };
    if (refusal.code === "busy") return { kind: "busy" };
    if (refusal.code === "disk_full") return { kind: "banner", banner: LOW_DISK };
    return { kind: "refused", refused: { text: busyText(refusal) ?? refusal.message, setupLink: refusal.code === "not_ready" } };
  } catch {
    return { kind: "offline" };
  }
}

/** A sentence's wav; `v` changes with each new voice so the browser doesn't play an old one (spec › Frontend). */
export function sentenceAudioUrl(sentenceId: string, durationS: number): string {
  return `/api/spoil-maker/draft/sentences/${sentenceId}/audio.wav?v=${durationS}`;
}

export const renderFileUrl = (name: string, suffix: ".mp4" | ".srt") => `${RENDERS_PATH}/${name}${suffix}`;

/** "1 พ.ย. 14:32" in the time zone of this computer. */
export function renderTime(createdAt: string): string {
  const date = new Date(createdAt);
  const day = date.toLocaleDateString("th-TH", { day: "numeric", month: "short" });
  const time = date.toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${day} ${time}`;
}
