import { tabLabel, type TabId } from "./useHash";

// The main menu (ui-nav D1, D2, ADR 0062, ADR 0070): sections, then links, two levels only (nav-ia
// D16) — เล่าเรื่อง and ดนตรี with the topics' links, คลัง with the libraries, ตั้งค่า with
// ติดตั้ง; no ล่าสุด (nav-ia D22). Only ways to a reel, what reels use, or the machine's setup belong
// here (D13); คลัง holds what is shared or written once and picked (nav-ia D2, ADR 0068).
// A page that belongs in the menu is a link here; pages never tell the menu which link they are,
// the hash does (D6, D11), and every page's hash is under its link's (nav-ia D1, ADR 0067).

export type NavItem = {
  label: string;
  hash: string;
  /** The tab (`tabOf`) of the pages under this link: a link is open only while its tab is (nav-ia D19). */
  tab: TabId;
  /** Also open on a deeper hash: `{hash}/…` or `{hash}?…` (D11). */
  prefix?: boolean;
  /** The small line under its name: what a library is used with (D2). */
  detail?: string;
};

/** A heading that is not a link, over its links: two levels, never a group inside (nav-ia D16, ADR 0070). */
export type NavSection = { id: string; label: string; items: readonly NavItem[] };

const SETUP_ITEM: NavItem = { label: "ติดตั้ง", hash: "#/setup", tab: "setup" };

const LIBRARY_ITEMS: readonly NavItem[] = [
  { label: "คลังความรู้", hash: "#/stories", tab: "stories", prefix: true, detail: "ใช้กับ สปอย" },
  { label: "คลังเสียง", hash: "#/sounds", tab: "sounds", prefix: true, detail: "ใช้กับ สปอย, การ์ตูนเล่า" },
  { label: "เสียงพากย์", hash: "#/voices", tab: "voices", detail: "ใช้กับ สปอย, การ์ตูนเล่า" },
];

// What goes in the menu is a place to go, never an action ("สร้าง…", a button on the page) or a
// second line to a page another link opens (nav-ia D17).
export const NAV_SECTIONS: readonly NavSection[] = [
  {
    id: "story",
    label: "เล่าเรื่อง",
    items: [
      // One page for the one Spoil draft: its steps are the page's, not the menu's (nav-ia D5).
      { label: "ทำสปอย", hash: "#/spoil", tab: "spoil", prefix: true },
      { label: "คลิปทั้งหมด", hash: "#/spoil/clips", tab: "spoil" },
      { label: "การ์ตูนเล่า", hash: "#/toon", tab: "toon", prefix: true },
    ],
  },
  {
    id: "music",
    label: "ดนตรี",
    items: [
      { label: "reel cover", hash: "#/covers", tab: "covers", prefix: true },
      { label: "reel กลอง", hash: "#/drums", tab: "drums", prefix: true },
    ],
  },
  { id: "library", label: "คลัง", items: LIBRARY_ITEMS },
  { id: "settings", label: "ตั้งค่า", items: [SETUP_ITEM] },
];

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
 * opens no การ์ตูนเล่า link), and the header's line: that link's name (D11, nav-ia D19, D20). */
export function locationOf(hash: string, tab: TabId) {
  const own = activeItem(hash, NAV_SECTIONS.flatMap((section) => section.items).filter((item) => item.tab === tab));
  // The longer hash wins, so `#/spoil/clips` is คลิปทั้งหมด rather than ทำสปอย.
  return { item: own ?? (tab === "setup" ? SETUP_ITEM : null), text: own?.label ?? tabLabel(tab) };
}
