import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { SoundsPage } from "./features/sound-library/components/SoundsPage";
import { ClipsPage } from "./features/spoil/components/ClipsPage";
import { SpoilMakerPage } from "./features/spoil-maker/components/SpoilMakerPage";
import { SavedVoicePage } from "./features/spoil-maker/components/SavedVoicePage";
import { StoriesPage } from "./features/story-kb/components/StoriesPage";
import { ToonPage } from "./features/toon/components/ToonPage";
import { SongsPage } from "./features/drum-notes/components/SongsPage";
import { DrumsPage } from "./features/video-gen/components/DrumsPage";
import { CoverPage } from "./features/drum-cover/components/CoverPage";
import { coverViewOf } from "./features/drum-cover/lib/cover";
import { CLIPS_HASH } from "./lib/clips";
import { tabOf, useHash } from "./lib/useHash";

// No router: the hash picks the tab (spoil D10, spoil-maker D53, story-kb D9, toon, sound-library D1, video-gen D9, drum-notes D2);
// a song's reel page is drum-cover's, picked before the reel cover topic sees the hash (drum-cover D11);
// คลิปทั้งหมด is spoil's page under สปอย (nav-ia D2).
export function App() {
  const hash = useHash();
  const cover = coverViewOf(hash);
  if (cover) return <CoverPage id={cover.id} />;
  if (hash === CLIPS_HASH) return <ClipsPage />;
  const tab = tabOf(hash);
  if (tab === "stories") return <StoriesPage />;
  if (tab === "sounds") return <SoundsPage />;
  if (tab === "voices") return <SavedVoicePage />;
  if (tab === "spoil") return <SpoilMakerPage />;
  if (tab === "toon") return <ToonPage />;
  if (tab === "drums") return <DrumsPage />;
  if (tab === "covers") return <SongsPage />;
  return <SetupStatusPage />;
}
