import { useEffect, useMemo, useSyncExternalStore } from "react";

// ล่าสุด: the Series or EPs, drum lessons and songs last opened in this browser, newest first, at
// most 3 per topic, under their topic in the main menu (ui-nav D5, D10, D11). A convenience of
// this browser only: no storage, or a broken value, is just no recent items.

export type RecentArea = "toon" | "drums" | "songs";

export type RecentItem = {
  hash: string;
  label: string;
  /** An EP's Series, so deleting the Series forgets its EPs too (D11). */
  parent?: string;
};

export type Recent = Record<RecentArea, RecentItem[]>;

const KEY = "framecraft.nav.recent";
const MAX = 3;
const LABEL_MAX = 80;
const CHANGED = "framecraft:recent";

const ID = "[A-Za-z0-9_-]{1,64}";
// The hashes each topic's pages have, as their parsers read them; a stored hash of any other shape is dropped (D10).
const SHAPES: Record<RecentArea, RegExp> = {
  toon: new RegExp(`^#/toon/(series|eps)/${ID}$`),
  drums: /^#\/drums\/[a-z0-9]{12}$/,
  songs: new RegExp(`^#/songs/${ID}$`),
};
const SERIES_SHAPE = new RegExp(`^#/toon/series/${ID}$`);

const AREAS = Object.keys(SHAPES) as RecentArea[];

const empty = (): Recent => ({ toon: [], drums: [], songs: [] });

function readRaw(): string {
  try {
    return window.localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

/** The stored recent items, keeping only well-formed ones (D10). */
function parse(raw: string): Recent {
  const recent = empty();
  let stored: unknown;
  try {
    stored = JSON.parse(raw);
  } catch {
    return recent;
  }
  if (!stored || typeof stored !== "object") return recent;
  for (const area of AREAS) {
    const items = (stored as Record<string, unknown>)[area];
    if (!Array.isArray(items)) continue;
    for (const entry of items) {
      const item = itemOf(area, entry);
      if (item && !recent[area].some((known) => known.hash === item.hash)) recent[area].push(item);
    }
    recent[area] = recent[area].slice(0, MAX);
  }
  return recent;
}

function itemOf(area: RecentArea, entry: unknown): RecentItem | null {
  if (!entry || typeof entry !== "object") return null;
  const { hash, label, parent } = entry as Record<string, unknown>;
  if (typeof hash !== "string" || !SHAPES[area].test(hash)) return null;
  if (typeof label !== "string" || !label.trim()) return null;
  // By character, not UTF-16 unit, so an emoji is never cut in half.
  const item: RecentItem = { hash, label: Array.from(label.trim()).slice(0, LABEL_MAX).join("") };
  if (area === "toon" && typeof parent === "string" && SERIES_SHAPE.test(parent)) item.parent = parent;
  return item;
}

/** Reads the storage again right before writing, so another browser tab's items are kept (D10). */
function change(update: (recent: Recent) => void) {
  const recent = parse(readRaw());
  update(recent);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(recent));
  } catch {
    return;
  }
  window.dispatchEvent(new Event(CHANGED));
}

/** Puts `hash` first under `area` with its current name, dropping the oldest past 3 (D5). */
export function rememberRecent(area: RecentArea, hash: string, label: string, parent?: string) {
  const item = itemOf(area, { hash, label, parent });
  if (!item) return;
  change((recent) => {
    recent[area] = [item, ...recent[area].filter((known) => known.hash !== hash)].slice(0, MAX);
  });
}

/** Forgets `hash`, and the EPs whose Series it is (D11). */
export function forgetRecent(hash: string) {
  change((recent) => {
    for (const area of AREAS) recent[area] = recent[area].filter((item) => item.hash !== hash && item.parent !== hash);
  });
}

function subscribe(onChange: () => void) {
  window.addEventListener(CHANGED, onChange);
  // Another browser tab wrote it.
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGED, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** The recent items, kept current. */
export function useRecent(): Recent {
  const raw = useSyncExternalStore(subscribe, readRaw);
  return useMemo(() => parse(raw), [raw]);
}

/**
 * What a page of one Series, EP, lesson or song tells ล่าสุด: its name once loaded, or that it is
 * gone (`not_found`), which forgets it; `null` while it loads (D5, D11).
 */
export function useRecentPage(area: RecentArea, hash: string, page: { label: string; parent?: string } | "gone" | null) {
  const label = page && page !== "gone" ? page.label : null;
  const parent = page && page !== "gone" ? page.parent : undefined;
  const gone = page === "gone";
  useEffect(() => {
    if (gone) forgetRecent(hash);
    else if (label !== null) rememberRecent(area, hash, label, parent);
  }, [area, hash, label, parent, gone]);
}
