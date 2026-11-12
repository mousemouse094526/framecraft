import { useHash } from "../../../lib/useHash";
import { storyIdOf } from "../lib/story";
import { StoryEditor } from "./StoryEditor";
import { StoryList } from "./StoryList";

/** The คลังความรู้ tab: `#/stories` lists, `#/stories/new` and `#/stories/{id}` edit (spec › Frontend). */
export function StoriesPage() {
  const id = storyIdOf(useHash());
  // One editor for `new` and the id its first save gets, so the form isn't remounted then.
  return id === undefined ? <StoryList /> : <StoryEditor id={id} />;
}
