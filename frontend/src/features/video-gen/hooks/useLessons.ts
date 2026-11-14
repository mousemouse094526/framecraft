import { useCallback, useEffect } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { lessonHash, lessonPath, LESSONS_PATH, type Lesson, type LessonRow } from "../lib/lesson";

export type ListState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** `failure`: a copy or delete the API refused, until the next one. */
  | { kind: "result"; lessons: LessonRow[]; failure: string | null };

/** รายการบทเรียนกลอง: the lessons, newest edit first as the API sorts them, and their new, copy and delete (D10). */
export function useLessons() {
  const [state, , setIfMounted] = useMountedState<ListState>({ kind: "loading" });

  const reload = useCallback(async (failure: string | null = null) => {
    try {
      setIfMounted({ kind: "result", lessons: await getJson<LessonRow[]>(LESSONS_PATH), failure });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const fail = useCallback(
    (failure: string) => setIfMounted((now) => (now.kind === "result" ? { ...now, failure } : now)),
    [setIfMounted],
  );

  /** `POST` a new lesson, then open it; the refusal's message when there is one. */
  const create = useCallback(async (title: string): Promise<string | null> => {
    try {
      const reply = await sendJson<Lesson>("POST", LESSONS_PATH, { title });
      if (reply.status === 201 && reply.body) {
        window.location.hash = lessonHash(reply.body.id);
        return null;
      }
      return refusalOf(reply.body)?.message ?? OFFLINE_TEXT;
    } catch {
      return OFFLINE_TEXT;
    }
  }, []);

  const copy = useCallback(
    async (id: string) => {
      try {
        const reply = await sendJson("POST", `${lessonPath(id)}/copy`, {});
        if (reply.status === 201) await reload();
        else fail(refusalOf(reply.body)?.message ?? OFFLINE_TEXT);
      } catch {
        fail(OFFLINE_TEXT);
      }
    },
    [reload, fail],
  );

  const remove = useCallback(
    async (id: string) => {
      try {
        const reply = await sendJson("DELETE", lessonPath(id));
        // Already gone is what was asked for.
        if (reply.status === 204 || reply.status === 404) await reload();
        // `in_use` may come after some renders went (spec › API): the list shows what is left.
        else await reload(refusalOf(reply.body)?.message ?? OFFLINE_TEXT);
      } catch {
        fail(OFFLINE_TEXT);
      }
    },
    [reload, fail],
  );

  return { state, reload, create, copy, remove };
}
