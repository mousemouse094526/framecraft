// The fake backend's data for the สปอย tab's step 1 and its drafting (spoil-maker seam 2): clips, a voice, a
// cut of FILM, a Draft job with its order, and the reads every page of the tab makes besides.
import type { TempClip } from "../../../lib/clips";
import { STORIES_PATH, STORY_CLIPS_PATH, type StoryRow } from "../../../lib/stories";
import type { DraftJob, DraftOrder } from "../lib/draft";
import type { Episode, Episodes } from "../hooks/useEpisodes";
import type { Voice } from "../hooks/useVoices";

export const CLIPS_PATH = "/api/spoil/clips";
export const VOICES_PATH = "/api/spoil-maker/voices";
export const SETTINGS_PATH = "/api/spoil-maker/settings";
export const DRAFT_PATH = "/api/spoil-maker/draft";
export const JOBS_PATH = "/api/spoil-maker/draft-jobs";
export const CURRENT_PATH = "/api/spoil-maker/draft-jobs/current";
export const REVIEW_HASH = "#/spoil/review";

export function clipOf(id: string, title: string, change: Partial<TempClip> = {}): TempClip {
  return {
    id,
    title,
    channel: "ช่อง",
    source_url: `https://www.youtube.com/watch?v=${id}`,
    duration_s: 1420,
    width: 1920,
    height: 1080,
    orientation: "landscape",
    file_bytes: 1_000_000,
    thumbnail: null,
    downloaded_at: "2026-11-01T10:00:00+07:00",
    yt_dlp_version: "2026.10.26",
    site: "Youtube",
    transcribed: true,
    described: true,
    in_draft: false,
    trimmed: [],
    trimmed_at: null,
    ...change,
  };
}

export const FILM = clipOf("aaaaaaaaaaa", "คืนสยองผีดิบ", { duration_s: 3600 });
export const OTHER = clipOf("bbbbbbbbbbb", "ไททัน ตอนที่ 2");
export const UNDESCRIBED = clipOf("ccccccccccc", "ไททัน ตอนที่ 3", { described: false });
export const UNTRANSCRIBED = clipOf("ddddddddddd", "นางนาก", { transcribed: false, described: false });

export const UNCLE: Voice = {
  id: "v_0000abcd",
  name: "ลุงเล่าผี",
  speed: 1,
  chars_per_s: 15,
  created_at: "2026-11-02T10:00:00+07:00",
  in_use: false,
};

/** What ร่างบท sent for EP 1 of FILM, as the job keeps it (D82). */
export const ORDER: DraftOrder = {
  clip_id: FILM.id,
  clip_title: FILM.title,
  ep: { n: 1, start_s: 0, end_s: 1799 },
  style: "drama",
  layout: "B",
  target_s: 60,
  voice_id: UNCLE.id,
  story_id: null,
  story_title: null,
};

export function storyRowOf(id: string, title: string, change: Partial<StoryRow> = {}): StoryRow {
  return { id, title, characters: 2, clips: 0, tokens: 3_100, updated_at: "2026-11-05T14:20:00+07:00", ...change };
}

export const CONAN = storyRowOf("st_3fa91c07", "ยอดนักสืบจิ๋วโคนัน", { clips: 1 });
export const ALIEN = storyRowOf("st_0000aaaa", "เอเลี่ยนบุก", { tokens: 900 });

export function jobOf(change: Partial<DraftJob>): DraftJob {
  return {
    kind: "draft",
    state: "writing",
    done: null,
    total: null,
    error: null,
    cancel_requested: false,
    started_at: "2026-11-02T11:00:00+07:00",
    order: ORDER,
    ...change,
  };
}

/** A Spoil draft with no sentences: enough for ตรวจแก้บท and the steps to read (spec › API). */
export const EMPTY_DRAFT = {
  clip_id: OTHER.id,
  ep: { n: 1, start_s: 0, end_s: 1420 },
  clip_title: OTHER.title,
  style: "drama",
  layout: "B",
  target_s: 60,
  voice_id: UNCLE.id,
  original_volume: 20,
  top_text: "",
  sentences: [],
  sound: null,
  estimated_total_s: 0,
  locked: false,
};

export function epOf(n: number, start_s: number, end_s: number, change: Partial<Episode> = {}): Episode {
  return { n, start_s, end_s, thumb_shot: n * 10, lines: 30, tokens: 18_400, renders: 0, in_draft: false, ...change };
}

/** FILM cut at 30 minutes: EP 1 and EP 2 meet at 29:59 (spoil-maker spec › EP). */
export function cutOf(change: Partial<Episodes> = {}): Episodes {
  return {
    clip_id: FILM.id,
    minutes: 30,
    custom: false,
    episodes: [epOf(1, 0, 1799), epOf(2, 1799, 3600, { renders: 2 })],
    limit: 32_000,
    tokens_not_ready: null,
    ...change,
  };
}

export const EPISODES = `/api/spoil-maker/clips/${FILM.id}/episodes`;

/** What a `GET` answers when no route of the test does. */
export function setupDefaults(): [string, unknown][] {
  return [
    [CLIPS_PATH, { clips: [FILM, OTHER] }],
    [VOICES_PATH, [UNCLE]],
    [SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: null, ep_minutes: 30 }],
    [DRAFT_PATH, null],
    [CURRENT_PATH, null],
    [STORIES_PATH, []],
    [STORY_CLIPS_PATH, {}],
    // What the steps and ตรวจแก้บท read besides: the drafting opens ตรวจแก้บท (D81).
    ["/api/spoil-maker/voice-jobs/current", null],
    ["/api/spoil-maker/renders/current", null],
    ["/api/spoil-maker/renders", []],
    ["/api/sounds", []],
    [`/api/spoil-maker/clips/${OTHER.id}/shots`, { shots: [] }],
    [EPISODES, cutOf()],
    [`/api/spoil-maker/clips/${OTHER.id}/episodes`, cutOf({ clip_id: OTHER.id, episodes: [epOf(1, 0, 1420)] })],
  ];
}
