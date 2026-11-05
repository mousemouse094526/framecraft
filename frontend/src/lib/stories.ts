// The คลังความรู้ tab's Stories as other tabs read them too: the list's rows, the
// Story each clip remembers, and the hashes that open them (story-kb spec › API, › Frontend).

import { getJson } from "./api";

export const STORIES_PATH = "/api/stories";
/** `{clip_id: story_id}` of every clip that remembers a Story. */
export const STORY_CLIPS_PATH = "/api/story-clips";

export const STORIES_HASH = "#/stories";
export const NEW_STORY_HASH = "#/stories/new";
export const storyHash = (id: string) => `${STORIES_HASH}/${id}`;

/** One row of `GET /api/stories`. */
export type StoryRow = {
  id: string;
  title: string;
  characters: number;
  clips: number;
  /** The Story block's tokens to Qwen; null without its tokenizer (story-kb D14). */
  tokens: number | null;
  updated_at: string;
};

/** `GET /api/story-clips`: `{clip_id: story_id}` of every clip that remembers a Story. */
export type ClipStories = Record<string, string>;

/** Both reads the สปอย tab makes together: step 1's Story field and the polish choice (story-kb D16, D20). */
export async function readStoryLinks(): Promise<{ rows: StoryRow[]; clipStories: ClipStories }> {
  const [rows, clipStories] = await Promise.all([getJson<StoryRow[]>(STORIES_PATH), getJson<ClipStories>(STORY_CLIPS_PATH)]);
  return { rows, clipStories };
}
