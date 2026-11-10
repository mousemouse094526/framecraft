// An EP of the การ์ตูนเล่า tab as the API sends it: its plot, acts, segments and cards, with each
// card's state and length (toon spec › ข้อมูล, › สถานะการ์ด, › API, D9, D13–D15, D21).

export const EPS_PATH = "/api/toon/eps";
export const epPath = (epId: string) => `${EPS_PATH}/${epId}`;
const cardPath = (epId: string, cardId: string) => `${epPath(epId)}/cards/${cardId}`;
/** A card's image, previous image or narration; `version` makes a picture drawn since load again. */
export const cardImagePath = (epId: string, cardId: string, version: number) => `${cardPath(epId, cardId)}/image?v=${version}`;
export const cardAudioPath = (epId: string, cardId: string, version: number) => `${cardPath(epId, cardId)}/audio?v=${version}`;
export const seriesEpsPath = (seriesId: string) => `/api/toon/series/${seriesId}/eps`;

export type Motion = "still" | "zoom_in" | "zoom_out" | "pan_left" | "pan_right";

export const MOTION_LABELS: Record<Motion, string> = {
  still: "นิ่ง",
  zoom_in: "ซูมเข้า",
  zoom_out: "ซูมออก",
  pan_left: "เลื่อนซ้าย",
  pan_right: "เลื่อนขวา",
};

/** A row of `GET /series/{seriesId}/eps`. */
export type ListedEp = {
  id: string;
  n: number;
  title: string;
  stage: "plot" | "cards";
  cards: number;
  images: number;
  rendered_at: string | null;
};

/** One of the Series' (`id`), or one the plot proposes (`new`, D13). */
export type PlotItem = { id: string | null; new: boolean; name: string; tag: string; description: string };

export type Card = {
  id: string;
  text: string;
  character_ids: string[];
  description: string;
  motion: Motion;
  flicker: boolean;
  hold_s: number;
  edited: boolean;
  image_status: "no_ref" | "no_image" | "stale_ref" | "ready";
  audio_status: "silent" | "no_audio" | "stale_audio" | "ready";
  duration_s: number;
  has_image: boolean;
  has_previous_image: boolean;
};

export type Segment = {
  id: string;
  background_id: string;
  sound: { sound_id: string; volume: number } | null;
  cards: Card[];
};

export type Act = {
  id: string;
  name: string;
  summary: string;
  /** The summary the act was last split from; null: never split (D15). */
  cards_from: string | null;
  segments: Segment[];
};

export type Ep = {
  id: string;
  series_id: string;
  n: number;
  idea: string;
  title: string;
  voice_id: string;
  stage: "plot" | "cards";
  plot: { characters: PlotItem[]; backgrounds: PlotItem[] };
  acts: Act[];
  duration_s: number;
  /** A Plot or Cards job writes it: every field is closed (spec › Toon job). */
  locked: boolean;
};

/** What re-splitting one act throws away, from `409 cards_will_be_lost` (D43). */
export type LostCards = { id: string; name: string; edited: number; images: number; audio: number };

// The backend's limits (backend/toon/episodes.py), so a field stops where the API would refuse.
export const IDEA_MAX = 500;
export const TITLE_MAX = 60;
export const SUMMARY_MAX = 1000;
export const TEXT_MAX = 200;
export const CARD_DESCRIPTION_MAX = 500;
export const CARD_CHARACTERS_MAX = 2;
export const HOLD_MAX = 5;
export const HOLD_STEP = 0.5;

/** The length a clip aims at (D14). */
export const TARGET_MIN_S = 60;
export const TARGET_MAX_S = 120;

/** `EP04`: how the design names an EP. */
/** Every card of the EP in order. */
export const cardsOf = (ep: Ep) => ep.acts.flatMap((act) => act.segments.flatMap((segment) => segment.cards));

/** A card that can't render: it has no picture, or a reference image is missing (spec › Render job). */
export const cannotRender = (card: Card) => card.image_status === "no_image" || card.image_status === "no_ref";

export const epLabel = (n: number) => `EP${String(n).padStart(2, "0")}`;

/** "8 พ.ย. 21:40": when a render was made. */
export const madeAt = (iso: string) =>
  new Date(iso).toLocaleString("th-TH", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

/** Acts a Cards job would split now: every act the first time, then those whose summary changed (D15). */
export function actsToSplit(ep: Ep): Act[] {
  return ep.acts.filter((act) => ep.stage === "plot" || act.summary !== act.cards_from);
}
