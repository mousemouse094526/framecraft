import { useEffect } from "react";
import { readStoryLinks } from "../../../lib/stories";
import { useMountedState } from "../../../lib/useMountedState";

/** The Story a clip remembers: its title, `none` for no Story (or one deleted since), or `unknown`
 * while loading or when the API can't be read — then the polish choice says nothing of it (story-kb D20).
 * The polish job reads the Story again as its request arrives (ADR 0024). */
export type ClipStory = { kind: "unknown" } | { kind: "none" } | { kind: "story"; title: string };

/** Reads `GET /api/story-clips` and `GET /api/stories` as the polish choice opens (story-kb D16). */
export function useClipStory(clipId: string): ClipStory {
  const [story, , setIfMounted] = useMountedState<ClipStory>({ kind: "unknown" });

  useEffect(() => {
    let current = true; // an answer for an earlier clip is dropped
    void (async () => {
      let next: ClipStory;
      try {
        const { rows, clipStories } = await readStoryLinks();
        const row = rows.find((candidate) => candidate.id === clipStories[clipId]);
        next = row ? { kind: "story", title: row.title } : { kind: "none" };
      } catch {
        next = { kind: "unknown" };
      }
      if (current) setIfMounted(next);
    })();
    return () => {
      current = false;
    };
  }, [clipId, setIfMounted]);

  return story;
}
