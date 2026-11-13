import { lessonPath } from "./lesson";

// The Render job of the สอนกลอง tab and its results, as `/api/drums` answers them (spec › API).

export type DrumRenderJob = {
  state: "rendering" | "done" | "failed" | "cancelled";
  lesson_id: string;
  /** The lesson's title as the render started (D34). */
  title: string;
  percent: number;
  /** The render's name, once `done`. */
  result: string | null;
  error: "ffmpeg_failed" | "internal" | null;
  message: string | null;
};

export type RenderResult = { name: string; lesson_id: string; title: string; length_s: number; created_at: string; size_bytes: number };

export const RENDER_PATH = "/api/drums/render";
export const CANCEL_PATH = `${RENDER_PATH}/cancel`;
export const rendersPath = (id: string) => `${lessonPath(id)}/renders`;
export const renderPath = (id: string, name: string) => `${rendersPath(id)}/${name}`;
export const renderFile = (id: string, name: string, suffix: ".mp4" | ".srt") => `${renderPath(id, name)}${suffix}`;

export function isRendering(job: DrumRenderJob | null): job is DrumRenderJob {
  return job?.state === "rendering";
}

/** The lesson's job, when the latest is its own. */
export function jobOf(job: DrumRenderJob | null, lessonId: string): DrumRenderJob | null {
  return job?.lesson_id === lessonId ? job : null;
}

/** The file a download saves as: `smells-like-teen-spirit-20261113-103000.mp4`. */
export function downloadName(result: RenderResult, suffix: ".mp4" | ".srt"): string {
  const title = result.title.trim().replace(/[\\/:*?"<>|\s]+/g, "-").toLowerCase();
  return `${title ? `${title}-` : ""}${result.name}${suffix}`;
}
