import { useHash } from "../../../lib/useHash";
import { lessonIdOf } from "../lib/lesson";
import { LessonEditor } from "./LessonEditor";
import { LessonList } from "./LessonList";

/** The สอนกลอง tab: `#/drums/{id}` edits a lesson, any other `#/drums…` hash lists them (spec › Frontend). */
export function DrumsPage() {
  const id = lessonIdOf(useHash());
  // Keyed, so another lesson's hash starts a fresh editor.
  return id === null ? <LessonList /> : <LessonEditor key={id} id={id} />;
}
