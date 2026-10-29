import { SetupStatusPage } from "./features/setup-status/components/SetupStatusPage";
import { SpoilPage } from "./features/spoil/components/SpoilPage";
import { useHashTab } from "./lib/useHashTab";

// No router: the hash picks the tab (spoil D10).
export function App() {
  const tab = useHashTab();
  return tab === "spoil" ? <SpoilPage /> : <SetupStatusPage />;
}
