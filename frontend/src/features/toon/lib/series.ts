import { sendJson, type JsonReply } from "../../../lib/api";
import { isUnfinishedIn } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";

// The การ์ตูนเล่า tab's Series, characters and backgrounds as the API sends them
// (toon spec › Series ตัวละคร ฉากหลัง, › API), and the hashes of its pages (D52).

export const SERIES_PATH = "/api/toon/series";
export const JOBS_PATH = "/api/toon/jobs";
export const JOB_PATH = "/api/toon/jobs/current";

export type Layout = "frame" | "full";
export type Genre = "horror" | "comedy";
export type Kind = "characters" | "backgrounds";

/** A row of `GET /series`. */
export type ListedSeries = {
  id: string;
  name: string;
  channel_name: string;
  layout: Layout;
  genre: Genre;
  ep_count: number;
};

/** A character or a background; `tag` is a character's only. `ref_rev` 0 = no reference image yet (D13). */
export type Item = {
  id: string;
  name: string;
  tag?: string;
  description: string;
  ref_rev: number;
  /** How many pictures of a Ref job wait to be picked: 0, or all three (a job keeps none until it has three). */
  pending: number;
};

export type Series = {
  id: string;
  name: string;
  channel_name: string;
  layout: Layout;
  genre: Genre;
  style: string;
  tone: string;
  acts: string[];
  voice_id: string;
  name_tags: boolean;
  characters: Item[];
  backgrounds: Item[];
};

/** The fields a Series form sends: `layout` and `genre` count only when it is created (D7, D10). */
export type SeriesFields = Pick<
  Series,
  "name" | "channel_name" | "layout" | "genre" | "style" | "tone" | "acts" | "voice_id" | "name_tags"
>;

/** What a new Series starts with by genre, as the backend fills it (D10, D11, D28, D41). */
export const GENRE_DEFAULTS: Record<Genre, Pick<Series, "acts" | "style" | "tone">> = {
  horror: {
    acts: ["เปิด", "ปม", "หักมุม", "จบหลอน"],
    style:
      "flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, " +
      "dark night scene, only light sources are bright and saturated, deep shadows",
    tone: 'เล่าเป็น "ฉัน" น้ำเสียงเรียบ ช้า ชวนขนลุก ประโยคสั้น',
  },
  comedy: {
    acts: ["ตั้งเรื่อง", "ปั่น", "พลิก", "ตบมุก"],
    style:
      "flat 2D cartoon illustration, simple round heads, dot eyes, thick clean outlines, " +
      "bright cheerful colors, soft daylight",
    tone: "เล่ากวนๆ จังหวะเร็ว มีมุกตบท้าย ประโยคสั้น",
  },
};

// The backend's limits (backend/toon/series.py), so a field stops where the API would refuse.
export const NAME_MAX = 60;
export const CHANNEL_MAX = 60;
export const STYLE_MAX = 500;
export const TONE_MAX = 300;
export const ACTS_MAX = 8;
export const ACT_NAME_MAX = 20;
export const ITEM_NAME_MAX = 30;
export const TAG_MAX = 20;
export const DESCRIPTION_MAX = 300;

export const LAYOUT_LABELS: Record<Layout, string> = { frame: "กรอบดำ", full: "เต็มจอ" };

export const seriesPath = (sid: string) => `${SERIES_PATH}/${sid}`;
export const itemPath = (sid: string, kind: Kind, id: string) => `${seriesPath(sid)}/${kind}/${id}`;
/** The current reference image; `rev` in the query makes a new one load in place of the old. */
export const refUrl = (sid: string, kind: Kind, item: Item) => `${itemPath(sid, kind, item.id)}/ref?rev=${item.ref_rev}`;
export const pendingUrl = (sid: string, kind: Kind, id: string, n: number) => `${itemPath(sid, kind, id)}/ref/pending/${n}`;

// The tab's pages (D52): the Series list, a new Series, a Series' characters and backgrounds,
// its settings, and the pick of a reference image.
export const LIST_HASH = "#/toon";
export const NEW_HASH = "#/toon/new";
export const castHash = (sid: string) => `#/toon/series/${sid}`;
export const settingsHash = (sid: string) => `#/toon/series/${sid}/settings`;
export const pickHash = (sid: string, kind: Kind, id: string) => `#/toon/series/${sid}/${kind}/${id}/pick`;

export type Page =
  | { kind: "list" }
  | { kind: "new" }
  | { kind: "cast"; sid: string }
  | { kind: "settings"; sid: string }
  | { kind: "pick"; sid: string; itemKind: Kind; id: string };

/** The page a `#/toon…` hash opens; anything else under the tab is the Series list. */
export function pageOf(hash: string): Page {
  if (hash === NEW_HASH) return { kind: "new" };
  const parts = hash.split("/").slice(2); // after "#", "toon"
  if (parts[0] !== "series" || !parts[1]) return { kind: "list" };
  const sid = parts[1];
  if (parts.length === 2) return { kind: "cast", sid };
  if (parts.length === 3 && parts[2] === "settings") return { kind: "settings", sid };
  if (parts.length === 5 && (parts[2] === "characters" || parts[2] === "backgrounds") && parts[4] === "pick") {
    return { kind: "pick", sid, itemKind: parts[2], id: parts[3] };
  }
  return { kind: "list" };
}

/** The Toon job as `/jobs/current` sends it (toon spec › Toon job); this ticket's kind is `ref`. */
export type ToonJob = {
  kind: "ref";
  state: "translating" | "drawing" | "done" | "failed" | "cancelled";
  series_id: string;
  item_id: string | null;
  done: number | null;
  total: number | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
};

export const UNFINISHED_JOB = ["translating", "drawing"] as const;

export const isRunning = isUnfinishedIn<ToonJob["state"]>(UNFINISHED_JOB);

/** `POST /jobs` for a Ref job of one item; both the lists and the pick page start one. */
export function startRefJob(sid: string, kind: Kind, id: string): Promise<JsonReply<ToonJob | Refusal>> {
  return sendJson("POST", JOBS_PATH, { kind: "ref", series_id: sid, item_kind: kind, item_id: id });
}

/** A Ref job draws three pictures to pick from (D31). */
export const REF_PICTURES = 3;
