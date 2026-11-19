import { useEffect, useState } from "react";

// What each hash opens, by its first part, and its name: the main menu's topics and libraries
// (ui-nav D1, D2; the menu itself is `lib/nav.ts`). Every page sits under the hash of the menu item
// it belongs to (nav-ia D1): คลิปทั้งหมด is `#/spoil/clips`, a page of สปอย (nav-ia D2).
const TAB_LABELS = {
  setup: "ติดตั้ง",
  stories: "คลังความรู้",
  sounds: "คลังเสียง",
  voices: "เสียงพากย์",
  spoil: "สปอย",
  toon: "การ์ตูนเล่า",
  drums: "reel กลอง",
  covers: "reel cover",
} as const;

export type TabId = keyof typeof TAB_LABELS;

export const tabLabel = (id: TabId): string => TAB_LABELS[id];

/**
 * `#/spoil/…` is a page of สปอย, `#/stories/…` a Story of คลังความรู้, `#/sounds?…` คลังเสียง
 * with the page it came from (sound-library D11), `#/toon/…` a page of การ์ตูนเล่า,
 * `#/drums/…` a page of reel กลอง and `#/covers/…` a song of reel cover; an empty or
 * unknown hash opens ติดตั้ง (spoil D10, spoil-maker D53, story-kb D9, drum-notes D2, nav-ia D1).
 */
export function tabOf(hash: string): TabId {
  if (hash.startsWith("#/spoil/")) return "spoil";
  if (hash.startsWith("#/sounds?")) return "sounds";
  if (hash.startsWith("#/stories/")) return "stories";
  if (hash.startsWith("#/toon/")) return "toon";
  if (hash.startsWith("#/drums/")) return "drums";
  if (hash.startsWith("#/covers/")) return "covers";
  const id = hash.slice(2);
  return hash.startsWith("#/") && Object.hasOwn(TAB_LABELS, id) ? (id as TabId) : "setup";
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
 * Whether what is on screen may go without the hash moving (a new pick under a reel being edited):
 * nothing unsaved, or the user said yes to "ออกโดยไม่บันทึก?" (nav-ia D14).
 */
export function mayLeave(): boolean {
  return !guard?.(window.location.hash) || window.confirm(LEAVE_QUESTION);
}

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

const ID = "[A-Za-z0-9_-]{1,64}";

// Pages that moved, old hash → new one; the first that matches wins, `$1` is the id (nav-ia D9).
// The sound library was a page of การ์ตูนเล่า before it had its own tab (sound-library D6, D11).
const MOVED: readonly [RegExp, string][] = [
  [/^#\/toon\/sounds$/, "#/sounds"],
  [/^#\/clips$/, "#/spoil/clips"],
  [/^#\/spoil\/voices$/, "#/voices"],
  [/^#\/spoil\/(review|renders)$/, "#/spoil"],
  [/^#\/songs$/, "#/covers"],
  [new RegExp(`^#/songs/(${ID})$`), "#/covers/$1"],
  [new RegExp(`^#/(?:songs|covers)/(${ID})/cover$`), "#/covers/$1"],
  [/^#\/drums\/([a-z0-9]{12})\/renders$/, "#/drums/$1"],
];

/** The hash a moved page has now, or null when `hash` is not one that moved. */
export function movedTo(hash: string): string | null {
  for (const [old, now] of MOVED) if (old.test(hash)) return hash.replace(old, now);
  return null;
}

/** The hash, with one of a page that moved put back as its new one: `replaceState` fires no
 * `hashchange`, so the caller reads the new hash straight from the answer. */
function movedHash(): string {
  const moved = movedTo(window.location.hash);
  if (moved) history.replaceState(history.state, "", moved);
  return window.location.hash;
}
