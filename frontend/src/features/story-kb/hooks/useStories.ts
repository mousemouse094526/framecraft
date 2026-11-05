import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { STORIES_PATH, type StoryRow } from "../lib/story";

export type StoriesState = { kind: "loading" } | { kind: "offline" } | { kind: "result"; stories: StoryRow[] };

/** `GET /api/stories` for the list of คลังความรู้: latest edit first, as the backend sorts it. */
export function useStories() {
  const [state, , setIfMounted] = useMountedState<StoriesState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      setIfMounted({ kind: "result", stories: await getJson<StoryRow[]>(STORIES_PATH) });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const reload = useCallback(() => {
    setIfMounted({ kind: "loading" });
    void load();
  }, [load, setIfMounted]);

  return { state, reload };
}
