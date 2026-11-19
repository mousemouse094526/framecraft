import type { Recent, RecentArea } from "./recent";
import { tabLabel, type TabId } from "./useHash";

// The main menu (ui-nav D1, D2, ADR 0062, ADR 0070): sections, then links, two levels only (nav-ia
// D16) — เล่าเรื่อง and ดนตรี with the topics' links, ล่าสุด while there is something recent, คลัง
// with the libraries, ตั้งค่า with ติดตั้ง. Only ways to a reel, what reels use, or the machine's
// setup belong here (D13); คลัง holds what is shared or written once and picked (nav-ia D2, ADR 0068).
// A page that belongs in the menu is a link here; pages never tell the menu which link they are,
// the hash does (D6, D11), and every page's hash is under its link's (nav-ia D1, ADR 0067).

export type NavItem = {
  label: string;
  hash: string;
  /** The tab (`tabOf`) of the pages under this link: a link is open only while its tab is (nav-ia D19). */
  tab: TabId;
  /** Also open on a deeper hash: `{hash}/…` or `{hash}?…` (D11). */
  prefix?: boolean;
  /** The small line under its name: what a library is used with (D2), or the link a recent item is from (nav-ia D18). */
  detail?: string;
};

/** A heading that is not a link, over its links: two levels, never a group inside (nav-ia D16, ADR 0070). */
export type NavSection = { id: string; label: string; items: readonly NavItem[] };

const SETUP_ITEM: NavItem = { label: "ติดตั้ง", hash: "#/setup", tab: "setup" };

// The topics with pages under their link, and the source line of their recent items (nav-ia D16, D18).
const TOON: NavItem = { label: "การ์ตูนเล่า", hash: "#/toon", tab: "toon", prefix: true };
const COVERS: NavItem = { label: "reel cover", hash: "#/covers", tab: "covers", prefix: true };
const DRUMS: NavItem = { label: "reel กลอง", hash: "#/drums", tab: "drums", prefix: true };

const MUSIC: NavSection = { id: "music", label: "ดนตรี", items: [COVERS, DRUMS] };

const LIBRARY_ITEMS: readonly NavItem[] = [
  { label: "คลังความรู้", hash: "#/stories", tab: "stories", prefix: true, detail: "ใช้กับ สปอย" },
  { label: "คลังเสียง", hash: "#/sounds", tab: "sounds", prefix: true, detail: "ใช้กับ สปอย, การ์ตูนเล่า" },
  { label: "เสียงพากย์", hash: "#/voices", tab: "voices", detail: "ใช้กับ สปอย, การ์ตูนเล่า" },
];

// What goes in the menu is a place to go, never an action ("สร้าง…", a button on the page) or a
// second line to a page another link opens (nav-ia D17).
const NAV_SECTIONS: readonly NavSection[] = [
  {
    id: "story",
    label: "เล่าเรื่อง",
    items: [
      // One page for the one Spoil draft: its steps are the page's, not the menu's (nav-ia D5).
      { label: "ทำสปอย", hash: "#/spoil", tab: "spoil", prefix: true },
      { label: "คลิปทั้งหมด", hash: "#/spoil/clips", tab: "spoil" },
      TOON,
    ],
  },
  MUSIC,
  { id: "library", label: "คลัง", items: LIBRARY_ITEMS },
  { id: "settings", label: "ตั้งค่า", items: [SETUP_ITEM] },
];

// ล่าสุด's order is the menu's, by source, not the storage's (nav-ia D18).
const RECENT_SOURCES: readonly [RecentArea, NavItem][] = [
  ["toon", TOON],
  ["covers", COVERS],
  ["drums", DRUMS],
];

/** The stored recent items as menu links, each saying the link it is from; a page under one (its `/cast`, …) opens it too (ui-nav D5, D11). */
export function recentLinks(recent: Recent): NavItem[] {
  return RECENT_SOURCES.flatMap(([area, source]) =>
    recent[area].map(({ hash, label }) => ({ label, hash, tab: source.tab, prefix: true, detail: source.label })),
  );
}

/** The menu's sections, with ล่าสุด between ดนตรี and คลัง while it has something (nav-ia D18). */
export function menuSections(recent: readonly NavItem[]): readonly NavSection[] {
  if (!recent.length) return NAV_SECTIONS;
  const at = NAV_SECTIONS.indexOf(MUSIC) + 1;
  return [...NAV_SECTIONS.slice(0, at), { id: "recent", label: "ล่าสุด", items: recent }, ...NAV_SECTIONS.slice(at)];
}

/** Whether `item` is open at `hash`: the same hash, or for a prefix item one under it (D11). */
function opens(item: NavItem, hash: string): boolean {
  if (hash === item.hash) return true;
  return !!item.prefix && (hash.startsWith(`${item.hash}/`) || hash.startsWith(`${item.hash}?`));
}

/** The item open at `hash` among `items`: the one with the longest hash, else none (D6, D11). */
function activeItem(hash: string, items: readonly NavItem[]): NavItem | null {
  let best: NavItem | null = null;
  for (const item of items) if (opens(item, hash) && (!best || item.hash.length > best.hash.length)) best = item;
  return best;
}

/** Where the user is: the link open, among the open tab's only (so `#/toon?x`, which opens ติดตั้ง,
 * opens no การ์ตูนเล่า link), and the header's line: the menu's own link open there, never a recent
 * one, so it stays when a page puts itself in ล่าสุด after it loads (D11, nav-ia D19, D20). */
export function locationOf(hash: string, tab: TabId, recent: readonly NavItem[]) {
  const fixed = NAV_SECTIONS.flatMap((section) => section.items).filter((item) => item.tab === tab);
  const own = activeItem(hash, fixed);
  // The longer hash wins, so a recent song is open rather than reel cover, and `#/spoil/clips` is
  // คลิปทั้งหมด rather than ทำสปอย.
  const found = activeItem(hash, [...fixed, ...recent.filter((item) => item.tab === tab)]);
  const item = found ?? (tab === "setup" ? SETUP_ITEM : null);
  return { item, text: own?.label ?? tabLabel(tab) };
}
