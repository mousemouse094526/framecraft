// The คลังความรู้ tab's Stories as other tabs read them too: the list's rows, the
// Story each clip remembers, and the hashes that open them (story-kb spec › API, › Frontend).

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
