import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { ClipsPage } from "./features/spoil/components/ClipsPage";
import { SpoilMakerPage } from "./features/spoil-maker/components/SpoilMakerPage";
import { StoriesPage } from "./features/story-kb/components/StoriesPage";
import { tabOf, useHash } from "./lib/useHash";

// No router: the hash picks the tab (spoil D10, spoil-maker D53, story-kb D9).
export function App() {
  const tab = tabOf(useHash());
  if (tab === "clips") return <ClipsPage />;
  if (tab === "stories") return <StoriesPage />;
  if (tab === "spoil") return <SpoilMakerPage />;
  return <SetupStatusPage />;
}
