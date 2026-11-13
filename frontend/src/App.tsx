import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { SoundsPage } from "./features/sound-library/components/SoundsPage";
import { ClipsPage } from "./features/spoil/components/ClipsPage";
import { SpoilMakerPage } from "./features/spoil-maker/components/SpoilMakerPage";
import { StoriesPage } from "./features/story-kb/components/StoriesPage";
import { ToonPage } from "./features/toon/components/ToonPage";
import { tabOf, useHash } from "./lib/useHash";

// No router: the hash picks the tab (spoil D10, spoil-maker D53, story-kb D9, toon, sound-library D1).
export function App() {
  const tab = tabOf(useHash());
  if (tab === "clips") return <ClipsPage />;
  if (tab === "stories") return <StoriesPage />;
  if (tab === "sounds") return <SoundsPage />;
  if (tab === "spoil") return <SpoilMakerPage />;
  if (tab === "toon") return <ToonPage />;
  return <SetupStatusPage />;
}
