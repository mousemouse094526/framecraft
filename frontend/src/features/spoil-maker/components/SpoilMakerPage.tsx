import { PageLayout } from "../../../components/ui/PageLayout";
import { useHash } from "../../../lib/useHash";
import { SpoilSteps, stepOf } from "./SpoilSteps";

/** The สปอย tab: the steps on top, then the open step (spoil-maker D53). Each step's content comes in its own ticket. */
export function SpoilMakerPage() {
  const step = stepOf(useHash());
  return (
    <PageLayout tab="spoil" wide>
      <SpoilSteps current={step} />
    </PageLayout>
  );
}
