import { useHash } from "../../../lib/useHash";
import { drumsViewOf } from "../../../lib/lesson";
import { LessonEditor } from "./LessonEditor";
import { LessonList } from "./LessonList";
import { RendersPage } from "./RendersPage";

/** The สอนกลอง tab: `#/drums/{id}` edits a lesson, `#/drums/{id}/renders` shows its renders, any other `#/drums…` hash lists them (spec › Frontend). */
export function DrumsPage() {
  const view = drumsViewOf(useHash());
  // Keyed, so another lesson's hash starts a fresh page.
  if (view.kind === "edit") return <LessonEditor key={view.id} id={view.id} />;
  if (view.kind === "renders") return <RendersPage key={view.id} id={view.id} />;
  return <LessonList />;
}
