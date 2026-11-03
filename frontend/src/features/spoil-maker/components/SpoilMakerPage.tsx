import { PageLayout } from "../../../components/ui/PageLayout";
import { useHash } from "../../../lib/useHash";
import { VOICES_HASH } from "../lib/draft";
import { RenderResults } from "./RenderResults";
import { SavedVoicePage } from "./SavedVoicePage";
import { ScriptReview } from "./ScriptReview";
import { SpoilerSetup } from "./SpoilerSetup";
import { SpoilSteps, stepOf } from "./SpoilSteps";

/**
 * The สปอย tab: the steps on top, then the open step (spoil-maker D53): ตั้งค่าคลิปสปอย,
 * ตรวจแก้บท, ผล render. Saved voices are a page of their own, without the steps.
 */
export function SpoilMakerPage() {
  const hash = useHash();
  if (hash === VOICES_HASH) return <SavedVoicePage />;
  const step = stepOf(hash);
  return (
    <PageLayout tab="spoil" wide>
      <SpoilSteps current={step} />
      {step === 0 && <SpoilerSetup />}
      {step === 1 && <ScriptReview />}
      {step === 2 && <RenderResults />}
    </PageLayout>
  );
}
