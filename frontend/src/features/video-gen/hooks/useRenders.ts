import { useCallback, useEffect } from "react";
import { getJson, getReply, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { lessonPath, type Lesson } from "../../../lib/lesson";
import { renderPath, rendersPath, type RenderResult } from "../lib/render";

export type RendersState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "not_found" }
  /** `failure`: a delete the API refused (`in_use`), until the next one. */
  | { kind: "ready"; title: string; renders: RenderResult[]; failure: string | null };

/** ผล render ของบทเรียน: the lesson's title and its renders, newest first as the API sorts them, and their delete (D10). */
export function useRenders(id: string) {
  const [state, , setIfMounted] = useMountedState<RendersState>({ kind: "loading" });

  const reload = useCallback(
    async (failure: string | null = null) => {
      try {
        const lesson = await getReply<Lesson>(lessonPath(id));
        if (lesson.status === 404) return setIfMounted({ kind: "not_found" });
        if (lesson.status !== 200 || !lesson.body) return setIfMounted({ kind: "offline" });
        const renders = await getJson<RenderResult[]>(rendersPath(id));
        setIfMounted({ kind: "ready", title: lesson.body.title, renders, failure });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [id, setIfMounted],
  );

  useEffect(() => {
    void reload();
  }, [reload]);

  const remove = useCallback(
    async (name: string) => {
      try {
        const reply = await sendJson("DELETE", renderPath(id, name));
        // Already gone is what was asked for.
        if (reply.status === 204 || reply.status === 404) await reload();
        else await reload(refusalOf(reply.body)?.message ?? OFFLINE_TEXT);
      } catch {
        setIfMounted((now) => (now.kind === "ready" ? { ...now, failure: OFFLINE_TEXT } : now));
      }
    },
    [id, reload, setIfMounted],
  );

  return { state, reload, remove };
}
