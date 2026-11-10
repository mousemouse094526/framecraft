import { isUnfinishedIn } from "../../../lib/job";
import { epPath } from "./episodes";

export const RENDER_PATH = "/api/toon/render";
export const RENDER_JOB_PATH = "/api/toon/render/current";
export const rendersPath = (epId: string) => `${epPath(epId)}/renders`;
export const renderFilePath = (epId: string, name: string) => `${rendersPath(epId)}/${name}`;

/** The Render job as `/render/current` sends it (spec › Render job, D38, D45). */
export type RenderJob = {
  kind: "render";
  state: "voicing" | "rendering" | "done" | "failed" | "cancelled";
  series_id: string;
  ep_id: string;
  percent: number | null;
  done: number | null;
  total: number | null;
  name: string | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
};

/** One finished render of the EP, newest first. */
export type RenderResult = { name: string; title: string; n: number; duration_s: number; created_at: string; size_bytes: number };

export const isRendering = isUnfinishedIn<RenderJob["state"]>(["voicing", "rendering"]);
