import { useHash } from "../../../lib/useHash";
import { drumsViewOf } from "../../../lib/lesson";
import { LessonEditor } from "./LessonEditor";
import { LessonList } from "./LessonList";

/** reel กลอง: `#/drums/{id}` is a reel's one page, its renders under the form; any other `#/drums…` hash lists them (video-gen spec › Frontend, reels-only D5, nav-ia D7). */
export function DrumsPage() {
  const view = drumsViewOf(useHash());
  // Keyed, so another reel's hash starts a fresh page.
  if (view.kind === "edit") return <LessonEditor key={view.id} id={view.id} />;
  return <LessonList />;
}
