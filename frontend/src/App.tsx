import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { ClipsPage } from "./features/spoil/components/ClipsPage";
import { SpoilMakerPage } from "./features/spoil-maker/components/SpoilMakerPage";
import { StoriesPage } from "./features/story-kb/components/StoriesPage";
import { ToonPage } from "./features/toon/components/ToonPage";
import { SongsPage } from "./features/drum-notes/components/SongsPage";
import { DrumsPage } from "./features/video-gen/components/DrumsPage";
import { tabOf, useHash } from "./lib/useHash";

// No router: the hash picks the tab (spoil D10, spoil-maker D53, story-kb D9, toon, video-gen D9, drum-notes D2).
export function App() {
  const tab = tabOf(useHash());
  if (tab === "clips") return <ClipsPage />;
  if (tab === "stories") return <StoriesPage />;
  if (tab === "spoil") return <SpoilMakerPage />;
  if (tab === "toon") return <ToonPage />;
  if (tab === "drums") return <DrumsPage />;
  if (tab === "songs") return <SongsPage />;
  return <SetupStatusPage />;
}
