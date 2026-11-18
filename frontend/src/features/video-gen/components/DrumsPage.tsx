import { useHash } from "../../../lib/useHash";
import { drumsViewOf } from "../../../lib/lesson";
import { LessonEditor } from "./LessonEditor";
import { LessonList } from "./LessonList";
import { RendersPage } from "./RendersPage";

/** reel กลอง: `#/drums/{id}` edits a reel, `#/drums/{id}/renders` shows its renders, any other `#/drums…` hash lists them (video-gen spec › Frontend, reels-only D5). */
export function DrumsPage() {
  const view = drumsViewOf(useHash());
  // Keyed, so another reel's hash starts a fresh page.
  if (view.kind === "edit") return <LessonEditor key={view.id} id={view.id} />;
  if (view.kind === "renders") return <RendersPage key={view.id} id={view.id} />;
  return <LessonList />;
}
