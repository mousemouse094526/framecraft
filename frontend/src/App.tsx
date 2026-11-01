import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { ClipsPage } from "./features/spoil/components/ClipsPage";
import { SpoilMakerPage } from "./features/spoil-maker/components/SpoilMakerPage";
import { tabOf, useHash } from "./lib/useHash";

// No router: the hash picks the tab (spoil D10, spoil-maker D53).
export function App() {
  const tab = tabOf(useHash());
  if (tab === "clips") return <ClipsPage />;
  if (tab === "spoil") return <SpoilMakerPage />;
  return <SetupStatusPage />;
}
