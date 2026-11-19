import { tabLabel, type TabId } from "./useHash";

// The main menu (ui-nav D1–D3, D12, ADR 0062): four sections — เล่าเรื่อง and ดนตรี with the main
// topics and their steps and pages, คลัง with the libraries, ตั้งค่า with ติดตั้ง. Only ways to a reel,
// what reels use, or the machine's setup belong here (D13). A page that belongs in the menu is an
// item here; pages never tell the menu which item they are, the hash does (D6, D11).

export type NavItem = {
  label: string;
  hash: string;
  /** Also open on a deeper hash: `{hash}/…` or `{hash}?…` (D11). */
  prefix?: boolean;
  /** The step number of สปอย's steps (D3). */
  step?: number;
  /** The topics a library is used with, the line under its name (D2). */
  uses?: string;
};

export type NavTopic = { id: TabId; label: string; items: readonly NavItem[] };

export const SETUP_ITEM: NavItem = { label: "ติดตั้ง", hash: "#/setup" };

/** A heading that is not a link, over its topics and its own items (D12). */
export type NavSection = { id: string; label: string; topics: readonly NavTopic[]; items: readonly NavItem[] };

const [SPOIL, TOON, DRUMS, SONGS]: readonly NavTopic[] = [
  {
    id: "spoil",
    label: "สปอย",
    items: [
      { label: "เลือกคลิป", hash: "#/spoil", prefix: true, step: 1 },
      { label: "ตรวจแก้บท", hash: "#/spoil/review", step: 2 },
      { label: "ผล render", hash: "#/spoil/renders", step: 3 },
    ],
  },
  {
    id: "toon",
    label: "การ์ตูนเล่า",
    items: [
      { label: "ชุดทั้งหมด", hash: "#/toon" },
      { label: "สร้างชุดใหม่", hash: "#/toon/new" },
    ],
  },
  { id: "drums", label: "reel กลอง", items: [{ label: "reel ทั้งหมด", hash: "#/drums" }] },
  { id: "songs", label: "แกะเพลง", items: [{ label: "เพลงทั้งหมด", hash: "#/songs" }] },
];

export const LIBRARY_LABEL = "คลัง";

export const LIBRARY_ITEMS: readonly NavItem[] = [
  { label: "คลังคลิป", hash: "#/clips", uses: "ใช้กับ สปอย" },
  { label: "คลังความรู้", hash: "#/stories", prefix: true, uses: "ใช้กับ สปอย" },
  { label: "คลังเสียง", hash: "#/sounds", prefix: true, uses: "ใช้กับ สปอย, การ์ตูนเล่า" },
  { label: "เสียงพากย์", hash: "#/spoil/voices", uses: "ใช้กับ สปอย, การ์ตูนเล่า" },
];

export const NAV_SECTIONS: readonly NavSection[] = [
  { id: "story", label: "เล่าเรื่อง", topics: [SPOIL, TOON], items: [] },
  { id: "music", label: "ดนตรี", topics: [SONGS, DRUMS], items: [] },
  { id: "library", label: LIBRARY_LABEL, topics: [], items: LIBRARY_ITEMS },
  { id: "settings", label: "ตั้งค่า", topics: [], items: [SETUP_ITEM] },
];

export const NAV_TOPICS: readonly NavTopic[] = NAV_SECTIONS.flatMap((section) => section.topics);

/** Whether `item` is open at `hash`: the same hash, or for a prefix item one under it (D11). */
function opens(item: NavItem, hash: string): boolean {
  if (hash === item.hash) return true;
  return !!item.prefix && (hash.startsWith(`${item.hash}/`) || hash.startsWith(`${item.hash}?`));
}

/** The item open at `hash` among `items`: the one with the longest hash, else none (D6, D11). */
export function activeItem<T extends NavItem>(hash: string, items: readonly T[]): T | null {
  let best: T | null = null;
  for (const item of items) if (opens(item, hash) && (!best || item.hash.length > best.hash.length)) best = item;
  return best;
}

/** Where the user is: the item open, and the header's line for it (D11). `extra` holds the items
 * a topic shows beyond its fixed ones, such as its recent ones. */
export function locationOf(hash: string, tab: TabId, extra: (topic: TabId) => readonly NavItem[] = () => []) {
  const topic = NAV_TOPICS.find((t) => t.id === tab);
  const topicItems = topic ? [...topic.items, ...extra(topic.id)] : [];
  // One longest match over both, so `#/spoil/voices` is เสียงพากย์, not เลือกคลิป under `#/spoil`.
  const found = activeItem(hash, [...topicItems, ...LIBRARY_ITEMS]);
  const item = found ?? (tab === "setup" ? SETUP_ITEM : null);
  const text = !found
    ? (tabLabel(tab) ?? "")
    : LIBRARY_ITEMS.includes(found)
      ? `${LIBRARY_LABEL} / ${found.label}`
      : `${topic!.label} / ${found.label}`;
  return { item, text };
}
