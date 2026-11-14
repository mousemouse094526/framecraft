import { useEffect } from "react";
import { getJson } from "../../../lib/api";
import { LESSONS_PATH, type LessonRow } from "../../../lib/lesson";
import { useMountedState } from "../../../lib/useMountedState";

/**
 * The titles of the lessons `ids` name, read once from the สอนกลอง tab's list (D28): a song remembers
 * only its lessons' ids (D12). Empty until the list is read; a lesson the list lacks, or a list that
 * can't be read, leaves its id out, and the page says "บทเรียน n" for it.
 */
export function useLessonTitles(ids: string[]): Map<string, string> {
  const [titles, , setIfMounted] = useMountedState<Map<string, string>>(new Map());
  const key = ids.join(",");

  useEffect(() => {
    if (key === "") return;
    getJson<LessonRow[]>(LESSONS_PATH)
      .then((rows) => setIfMounted(new Map(rows.filter((row) => ids.includes(row.id)).map((row) => [row.id, row.title]))))
      .catch(() => {});
    // `ids` is a new array each render: `key` is its content.
  }, [key, setIfMounted]);

  return titles;
}
