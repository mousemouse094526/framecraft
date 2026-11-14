import { getJson } from "../../../lib/api";
import { isUnfinishedIn } from "../../../lib/job";
import { tabLabel } from "../../../lib/useHash";

// The sound library of the whole app (sound-library spec, ADR 0037) as the API sends it: its
// page, a segment's sound of การ์ตูนเล่า and a clip's of สปอย all read it.

export const SOUNDS_PATH = "/api/sounds";
export const SOUND_IMPORT_PATH = "/api/sounds/import/current";
export const LEGACY_PATH = "/api/sounds/legacy";
export const soundPath = (soundId: string) => `${SOUNDS_PATH}/${soundId}`;
export const soundFilePath = (soundId: string) => `${soundPath(soundId)}/file`;

const WITH_BACK = "#/sounds?back=";
/** The library's page with a "← กลับ" link to `back`, the hash of the page that opens it (D11). */
export const soundsHash = (back: string) => `${WITH_BACK}${back}`;

/** Where "← กลับ" goes: the `back` of `#/sounds?back=…` when it is a page of สปอย or การ์ตูนเล่า, else nowhere (D11, D15). */
export function backOf(hash: string): string | null {
  const back = hash.startsWith(WITH_BACK) ? hash.slice(WITH_BACK.length) : "";
  return back.startsWith("#/spoil/") || back.startsWith("#/toon/") || back === "#/toon" ? back : null;
}

/** A tab's thing that plays a sound, as `in_use` names it (D7). */
export type SoundUser = { tab: "toon" | "spoil"; label: string };
export const userLine = (user: SoundUser) => `${tabLabel(user.tab)} · ${user.label}`;

/** The old library's folder while start-up could not move all of it (D10). */
export type Legacy = { left_behind: string | null };

export type Sound = { id: string; name: string; duration_s: number; source: "file" | "link" };

/** A sound of the library a toon segment or a Spoil draft plays, and its volume 0–100. */
export type PlayedSound = { sound_id: string; volume: number };

/** `GET /api/sounds`: every sound of the library. */
export const fetchSounds = () => getJson<Sound[]>(SOUNDS_PATH);

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

// The backend's limits (backend/sounds.py).
export const SOUND_NAME_MAX = 60;

/** `m:ss`, a sound's length in the list. */
export function soundLength(seconds: number): string {
  const whole = Math.round(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}
