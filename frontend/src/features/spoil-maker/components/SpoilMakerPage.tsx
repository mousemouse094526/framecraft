import { PageLayout } from "../../../components/ui/PageLayout";
import { useHash } from "../../../lib/useHash";
import { SavedVoicePage } from "./SavedVoicePage";
import { SpoilSteps, stepOf } from "./SpoilSteps";

export const VOICES_HASH = "#/spoil/voices";

/**
 * The สปอย tab: the steps on top, then the open step (spoil-maker D53). Each step's
 * content comes in its own ticket. Saved voices are a page of their own, without the steps.
 */
export function SpoilMakerPage() {
  const hash = useHash();
  if (hash === VOICES_HASH) return <SavedVoicePage />;
  const step = stepOf(hash);
  return (
    <PageLayout tab="spoil" wide>
      <SpoilSteps current={step} />
    </PageLayout>
  );
}
