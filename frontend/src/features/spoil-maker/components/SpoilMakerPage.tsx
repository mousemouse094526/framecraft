import { PageLayout } from "../../../components/ui/PageLayout";
import { useHash } from "../../../lib/useHash";
import { DraftRunContext, StepsRefreshContext, useStepStatus } from "../hooks/useStepStatus";
import { VOICES_HASH } from "../lib/draft";
import { stepLines } from "../lib/steps";
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
  return <SpoilSteppedPage step={stepOf(hash)} />;
}

/** The steps hold what every step shows (D68); the open step tells them when it changed something. */
function SpoilSteppedPage({ step }: { step: number }) {
  const { status, refresh, draftRun } = useStepStatus();
  return (
    <PageLayout tab="spoil" wide>
      <SpoilSteps current={step} lines={stepLines(status)} />
      <StepsRefreshContext value={refresh}>
        <DraftRunContext value={draftRun}>
          {step === 0 && <SpoilerSetup />}
          {step === 1 && <ScriptReview />}
          {step === 2 && <RenderResults />}
        </DraftRunContext>
      </StepsRefreshContext>
    </PageLayout>
  );
}
