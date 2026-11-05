import { useEffect, useState } from "react";

// The top tabs and their hashes, in the order the tab bar shows them (spoil-maker D53, story-kb D9).
export const TABS = [
  { id: "setup", label: "ติดตั้ง", hash: "#/setup" },
  { id: "clips", label: "คลิป", hash: "#/clips" },
  { id: "stories", label: "คลังความรู้", hash: "#/stories" },
  { id: "spoil", label: "สปอย", hash: "#/spoil" },
] as const;

export type TabId = (typeof TABS)[number]["id"];

/**
 * `#/spoil/…` is a step of สปอย and `#/stories/…` a Story of คลังความรู้; an empty or
 * unknown hash opens ติดตั้ง (spoil D10, spoil-maker D53, story-kb D9).
 */
export function tabOf(hash: string): TabId {
  if (hash.startsWith("#/spoil/")) return "spoil";
  if (hash.startsWith("#/stories/")) return "stories";
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
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const follow = () => setHash(window.location.hash);
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return hash;
}
