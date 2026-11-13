import { useEffect, useState } from "react";

/** The tab groups in order with their names: the narrow screen's menu shows them as headings,
 * the tab bar only as `aria-label` (sound-library D3). */
export const TAB_GROUPS = [
  { id: "prep", label: "เตรียมของ" },
  { id: "make", label: "ทำคลิป" },
] as const;

type TabGroupId = (typeof TAB_GROUPS)[number]["id"];

// The top tabs and their hashes, in the order the tab bar shows them (spoil-maker D53, story-kb D9,
// sound-library D2), with the group each sits in; ติดตั้ง is in none (sound-library D3). The bar
// and the menu draw the tabs in no group first, then each group, so those stay at the top.
export const TABS = [
  { id: "setup", label: "ติดตั้ง", hash: "#/setup", group: null },
  { id: "clips", label: "คลิป", hash: "#/clips", group: "prep" },
  { id: "stories", label: "คลังความรู้", hash: "#/stories", group: "prep" },
  { id: "sounds", label: "คลังเสียง", hash: "#/sounds", group: "prep" },
  { id: "spoil", label: "สปอย", hash: "#/spoil", group: "make" },
  { id: "toon", label: "การ์ตูนเล่า", hash: "#/toon", group: "make" },
] as const satisfies readonly { id: string; label: string; hash: string; group: TabGroupId | null }[];

export type TabId = (typeof TABS)[number]["id"];

export const tabLabel = (id: TabId) => TABS.find((tab) => tab.id === id)?.label;

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
