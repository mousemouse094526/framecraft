import type { StatusResponse } from "../../../lib/statusTypes";

// The Checklist items each job needs (D9, D27); the backend gates on the same.
export const DOWNLOAD_ITEMS = ["ffmpeg", "yt_dlp", "deno"];
// `device` is a warning on `cpu`, so it isn't ok there (ADR 0006).
export const TRANSCRIBE_ITEMS = ["torch", "transformers", "ffmpeg", "model_whisper", "device"];

/** The labels of the items in `ids` that aren't ok, in Status check order. */
export function missingLabels(status: StatusResponse, ids: string[]): string[] {
  return status.items.filter((item) => ids.includes(item.id) && item.status !== "ok").map((item) => item.label);
}
