import type { Refusal } from "./refusal";

// How the app names the job holding the GPU (spoil-maker spec › Frontend, `gpu_busy`).
const RUNNING_NAMES: Record<string, string> = {
  transcribe: "ถอดบทพูด",
  describe: "บรรยายฉาก",
  draft: "ร่างบท",
  voice: "สร้างเสียง",
};

/** The `…/current` of each GPU job a page can poll to see it end; later jobs add theirs. */
export const GPU_JOB_PATHS: Record<string, string> = {
  transcribe: "/api/spoil/transcriptions/current",
  describe: "/api/spoil-maker/describes/current",
  draft: "/api/spoil-maker/draft-jobs/current",
};

/** "รอให้งาน{running}เสร็จก่อน": why a GPU job can't start while `running` holds the GPU (spoil-maker D45). */
export function gpuBusyText(running: string): string {
  return `รอให้งาน${RUNNING_NAMES[running] ?? running}เสร็จก่อน`;
}

/**
 * What to tell the user for a refusal that means "not now, another job has it":
 * `gpu_busy` names the running job, `clip_busy` says the API's message. Null for any other refusal.
 */
export function busyText(refusal: Refusal | null): string | null {
  if (refusal?.code === "gpu_busy") return gpuBusyText(refusal.running ?? "");
  if (refusal?.code === "clip_busy") return refusal.message;
  return null;
}
