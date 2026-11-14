import { sendEdit, type EditReply } from "../../../lib/edit";
import { NOT_NOW } from "../../../lib/notice";
import { isUnfinishedIn } from "../../../lib/job";
import type { Refusal } from "../../../lib/refusal";

// The การ์ตูนเล่า tab's Series, characters and backgrounds as the API sends them
// (toon spec › Series ตัวละคร ฉากหลัง, › API), and the hashes of its pages (D52).

export const SERIES_PATH = "/api/toon/series";
export const JOBS_PATH = "/api/toon/jobs";
export const JOB_PATH = "/api/toon/jobs/current";

export type Layout = "frame" | "full";
export type Genre = "horror" | "comedy";
export type ItemKind = "characters" | "backgrounds";

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
export const GENRE_LABELS: Record<Genre, string> = { horror: "หลอน", comedy: "ตลก" };

/** One character or background, wherever it is named: a page's hash, an item's API path, a Ref
 * job's body. The backend's `series.ItemRef` (D64). */
export type ItemRef = { seriesId: string; itemKind: ItemKind; itemId: string };

export const seriesPath = (seriesId: string) => `${SERIES_PATH}/${seriesId}`;
export const itemPath = ({ seriesId, itemKind, itemId }: ItemRef) => `${seriesPath(seriesId)}/${itemKind}/${itemId}`;
/** The current reference image; `rev` in the query makes a new one load in place of the old. */
export const refUrl = (ref: ItemRef, rev: number) => `${itemPath(ref)}/ref?rev=${rev}`;
export const pendingUrl = (ref: ItemRef, n: number) => `${itemPath(ref)}/ref/pending/${n}`;

// The tab's pages (D52, D53, D56): the Series list, a new Series, a Series' EPs, its characters and
// backgrounds, its settings, the pick of a reference image, an EP: its plot, or its storyline
// once the plot is confirmed (`/plot` opens the plot either way), and its render. The sound library
// is a tab of its own (sound-library D1).
export const LIST_HASH = "#/toon";
export const NEW_HASH = "#/toon/new";
export const seriesHash = (seriesId: string) => `#/toon/series/${seriesId}`;
export const castHash = (seriesId: string) => `#/toon/series/${seriesId}/cast`;
export const settingsHash = (seriesId: string) => `#/toon/series/${seriesId}/settings`;
export const pickHash = ({ seriesId, itemKind, itemId }: ItemRef) => `#/toon/series/${seriesId}/${itemKind}/${itemId}/pick`;
export const epHash = (epId: string) => `#/toon/eps/${epId}`;
export const plotHash = (epId: string) => `#/toon/eps/${epId}/plot`;
export const renderHash = (epId: string) => `#/toon/eps/${epId}/render`;

export type Page =
  | { kind: "list" }
  | { kind: "new" }
  | { kind: "eps"; seriesId: string }
  | { kind: "cast"; seriesId: string }
  | { kind: "settings"; seriesId: string }
  | { kind: "pick"; itemRef: ItemRef }
  | { kind: "ep"; epId: string; plot: boolean }
  | { kind: "render"; epId: string };

/** The page a `#/toon…` hash opens; anything else under the tab is the Series list. */
export function pageOf(hash: string): Page {
  if (hash === NEW_HASH) return { kind: "new" };
  const parts = hash.split("/").slice(2); // after "#", "toon"
  if (parts[0] === "eps" && parts[1] && parts.length === 3 && parts[2] === "render") return { kind: "render", epId: parts[1] };
  if (parts[0] === "eps" && parts[1] && (parts.length === 2 || (parts.length === 3 && parts[2] === "plot"))) {
    return { kind: "ep", epId: parts[1], plot: parts.length === 3 };
  }
  if (parts[0] !== "series" || !parts[1]) return { kind: "list" };
  const seriesId = parts[1];
  if (parts.length === 2) return { kind: "eps", seriesId };
  if (parts.length === 3 && parts[2] === "cast") return { kind: "cast", seriesId };
  if (parts.length === 3 && parts[2] === "settings") return { kind: "settings", seriesId };
  if (parts.length === 5 && (parts[2] === "characters" || parts[2] === "backgrounds") && parts[4] === "pick") {
    return { kind: "pick", itemRef: { seriesId, itemKind: parts[2], itemId: parts[3] } };
  }
  return { kind: "list" };
}

/** A character or background with no reference image yet, and how many cards of an Image job it
 * made skip (D13). */
export type MissingRef = { item_kind: ItemKind; id: string; name: string; cards: number };

/** Which cards an Image job of the whole EP draws: every one with no image, or every
 * `stale_ref` one (D33, D44). */
export type ImageScope = "missing" | "stale_ref";

/** The Toon job as `/jobs/current` sends it (toon spec › Toon job): `plot` and `cards` write an
 * EP and lock it, `ref` draws a reference image, `image` card images, `voice` a card's narration. */
export type ToonJob = {
  kind: "plot" | "cards" | "ref" | "image" | "voice";
  state: "writing" | "translating" | "drawing" | "voicing" | "done" | "failed" | "cancelled";
  series_id: string;
  ep_id: string | null;
  item_id: string | null;
  /** The cards an `image` or `voice` job works on, in order: `card_ids[done]` is the one now (D55). */
  card_ids?: string[] | null;
  /** An `image` job of every card with no image, or every `stale_ref` one; null: of one card. */
  scope?: ImageScope | null;
  done: number | null;
  total: number | null;
  skipped?: number | null;
  missing_refs?: MissingRef[] | null;
  failed_cards?: string[] | null;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
};

export const UNFINISHED_JOB = ["writing", "translating", "drawing", "voicing"] as const;

export const isRunning = isUnfinishedIn<ToonJob["state"]>(UNFINISHED_JOB);

/** `POST /jobs`: starts a Toon job of any kind; `ok` with the job (`202`), else `refused`
 * with the notice titled `title` (`warnings` as `sendEdit`'s). */
export function startToonJob<R extends Refusal = Refusal>(
  body: Record<string, unknown>,
  title: string,
  warnings: readonly string[] = [],
): Promise<EditReply<ToonJob, R>> {
  return sendEdit<ToonJob, R>("POST", JOBS_PATH, body, title, { ok: [202], warnings });
}

/** A Ref job of one item; both the lists and the pick page start one, and "not now" is a warning on both. */
export function startRefJob({ seriesId, itemKind, itemId }: ItemRef) {
  const body = { kind: "ref", series_id: seriesId, item_kind: itemKind, item_id: itemId };
  return startToonJob(body, "ยังสร้างภาพอ้างอิงไม่ได้", NOT_NOW);
}

/** A Ref job draws three pictures to pick from (D31). */
export const REF_PICTURES = 3;
