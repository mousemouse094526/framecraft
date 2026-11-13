import { useEffect, useState } from "react";

// The top tabs and their hashes, in the order the tab bar shows them (spoil-maker D53, story-kb D9, sound-library D2).
export const TABS = [
  { id: "setup", label: "ติดตั้ง", hash: "#/setup" },
  { id: "clips", label: "คลิป", hash: "#/clips" },
  { id: "stories", label: "คลังความรู้", hash: "#/stories" },
  { id: "sounds", label: "คลังเสียง", hash: "#/sounds" },
  { id: "spoil", label: "สปอย", hash: "#/spoil" },
  { id: "toon", label: "การ์ตูนเล่า", hash: "#/toon" },
] as const;

export type TabId = (typeof TABS)[number]["id"];

/**
 * `#/spoil/…` is a step of สปอย, `#/stories/…` a Story of คลังความรู้, `#/sounds?…` คลังเสียง
 * with the page it came from (sound-library D11) and `#/toon/…` a page of การ์ตูนเล่า; an empty or
 * unknown hash opens ติดตั้ง (spoil D10, spoil-maker D53, story-kb D9).
 */
export function tabOf(hash: string): TabId {
  if (hash.startsWith("#/spoil/")) return "spoil";
  if (hash.startsWith("#/sounds?")) return "sounds";
  if (hash.startsWith("#/stories/")) return "stories";
  if (hash.startsWith("#/toon/")) return "toon";
  return TABS.find((tab) => tab.hash === hash)?.id ?? "setup";
}

/** Says whether leaving for `next` (a hash) would lose unsaved work. */
export type LeaveGuard = (next: string) => boolean;

export const LEAVE_QUESTION = "ออกโดยไม่บันทึก?";

let guard: LeaveGuard | null = null;

// Added when this module loads, so it runs before every `useHash` listener: after a declined
// leave they read the old hash back and the page stays, with what was typed (story-kb D11, D16).
window.addEventListener("hashchange", (event) => {
  if (!guard?.(window.location.hash) || window.confirm(LEAVE_QUESTION)) return;
  // replaceState puts the old hash back without another `hashchange`, so nothing asks twice.
  history.replaceState(history.state, "", new URL(event.oldURL).hash || window.location.pathname);
});

/**
 * Asks "ออกโดยไม่บันทึก?" before the hash moves on while `unsaved(next)` is true, and lets the
 * browser ask before the tab closes. `unsaved` is read at the moment of leaving, so a page
 * that has just saved can navigate at once. One page holds the guard at a time: the last to mount.
 */
export function useLeaveGuard(unsaved: LeaveGuard) {
  useEffect(() => {
    guard = unsaved;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      // Closing the tab goes nowhere: `next` is the hash it is on.
      if (unsaved(window.location.hash)) event.preventDefault();
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => {
      if (guard === unsaved) guard = null;
      window.removeEventListener("beforeunload", beforeUnload);
    };
  }, [unsaved]);
}

/**
 * The URL hash, kept current. The tabs and steps are plain `#/…` links, so
 * clicking one and the browser's back button both change the hash; this only follows it.
 */
export function useHash(): string {
  const [hash, setHash] = useState(movedHash);

  useEffect(() => {
    const follow = () => setHash(movedHash());
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return hash;
}

// The sound library was a page of การ์ตูนเล่า before it had its own tab (sound-library D6, D11).
const MOVED: Record<string, string> = { "#/toon/sounds": "#/sounds" };

/** The hash, with one of a page that moved put back as its new one: `replaceState` fires no
 * `hashchange`, so the caller reads the new hash straight from the answer. */
function movedHash(): string {
  const moved = MOVED[window.location.hash];
  if (moved) history.replaceState(history.state, "", moved);
  return window.location.hash;
}
