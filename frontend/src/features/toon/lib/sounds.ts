import { isUnfinishedIn } from "../../../lib/job";

// The background sound library of the tab (toon spec › คลังเสียงพื้น, D5, D16, D39) as the API
// sends it: the library page and a segment's sound both read it.

export const SOUNDS_PATH = "/api/toon/sounds";
export const SOUND_IMPORT_PATH = "/api/toon/sounds/import/current";
export const soundPath = (mid: string) => `${SOUNDS_PATH}/${mid}`;
export const soundFilePath = (mid: string) => `${soundPath(mid)}/file`;

export type Sound = { id: string; name: string; duration_s: number; source: "file" | "link" };

/** A link's Sound import; a file's is one request and never shows here. */
export type SoundImport = {
  url: string;
  state: "checking" | "downloading" | "converting" | "done" | "failed" | "cancelled";
  title: string | null;
  percent: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  sound_id: string | null;
};

export const isImporting = isUnfinishedIn<SoundImport["state"]>(["checking", "downloading", "converting"]);

// The backend's limits (backend/toon/sounds.py).
export const SOUND_NAME_MAX = 60;
export const UPLOAD_MAX_BYTES = 200 * 1024 ** 2;
export const VOLUME_MAX = 100;
export const DEFAULT_VOLUME = 30; // spec › Cards job step 5

/** `m:ss`, a sound's length in the list. */
export function soundLength(seconds: number): string {
  const whole = Math.round(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}
