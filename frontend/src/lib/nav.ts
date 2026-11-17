import { tabLabel, type TabId } from "./useHash";

// The main menu (ui-nav D1–D3, ADR 0062): ติดตั้ง, then the four main topics with their steps and
// pages, then the libraries. A page that belongs in the menu is an item here; pages never tell the
// menu which item they are, the hash does (D6, D11).

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

export const NAV_TOPICS: readonly NavTopic[] = [
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
  { id: "drums", label: "สอนกลอง", items: [{ label: "บทเรียนทั้งหมด", hash: "#/drums" }] },
  { id: "songs", label: "แกะเพลง", items: [{ label: "เพลงทั้งหมด", hash: "#/songs" }] },
];

export const LIBRARY_LABEL = "คลัง";

export const LIBRARY_ITEMS: readonly NavItem[] = [
  { label: "คลังคลิป", hash: "#/clips", uses: "ใช้กับ สปอย" },
  { label: "คลังความรู้", hash: "#/stories", prefix: true, uses: "ใช้กับ สปอย" },
  { label: "คลังเสียง", hash: "#/sounds", prefix: true, uses: "ใช้กับ สปอย, การ์ตูนเล่า" },
  { label: "เสียงที่บันทึก", hash: "#/spoil/voices", uses: "ใช้กับ สปอย, การ์ตูนเล่า" },
];

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
  // One longest match over both, so `#/spoil/voices` is เสียงที่บันทึก, not เลือกคลิป under `#/spoil`.
  const found = activeItem(hash, [...topicItems, ...LIBRARY_ITEMS]);
  const item = found ?? (tab === "setup" ? SETUP_ITEM : null);
  const text = !found
    ? (tabLabel(tab) ?? "")
    : LIBRARY_ITEMS.includes(found)
      ? `${LIBRARY_LABEL} / ${found.label}`
      : `${topic!.label} / ${found.label}`;
  return { item, text };
}
