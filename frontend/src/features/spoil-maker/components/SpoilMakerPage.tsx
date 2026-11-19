import { useCallback, useEffect, useRef, useState } from "react";
import { PageLayout } from "../../../components/ui/PageLayout";
import { DraftRunContext, StepGoContext, StepsRefreshContext, useStepStatus, type Step } from "../hooks/useStepStatus";
import { runningDraft } from "../lib/draft";
import { stepLines } from "../lib/steps";
import { RenderResults } from "./RenderResults";
import { ScriptReview } from "./ScriptReview";
import { SpoilerSetup } from "./SpoilerSetup";
import { SpoilSteps } from "./SpoilSteps";

/**
 * ทำสปอย (`#/spoil`): one page for the one Spoil draft, the steps on top and the open step below
 * (spoil-maker D53, nav-ia D5): ตั้งค่าคลิปสปอย, ตรวจแก้บท, ผล render. The steps are the page's
 * state, not hashes; the steps hold what every step shows (D68), and the open step tells them when
 * it changed something.
 */
export function SpoilMakerPage() {
  const { status, refresh, draftRun } = useStepStatus();
  const [step, setStep] = useState<Step | null>(null);
  // A step the user picked wins over the one the first read would open (nav-ia D14).
  const picked = useRef(false);

  // Once, after the first read: where the work stands, a draft (or one being written) is ตรวจแก้บท,
  // nothing (or no answer) is เลือกคลิป (nav-ia D5).
  const ready = draftRun.loaded;
  const startsAtReview = Boolean(status.draft) || runningDraft(status.draftJob) !== null;
  useEffect(() => {
    if (ready && !picked.current) setStep((open) => open ?? (startsAtReview ? 1 : 0));
  }, [ready, startsAtReview]);

  const pick = useCallback((next: Step) => {
    picked.current = true;
    setStep(next);
  }, []);

  return (
    <PageLayout tab="spoil" wide>
      <SpoilSteps current={step} lines={stepLines(status)} onPick={pick} />
      <StepsRefreshContext value={refresh}>
        <DraftRunContext value={draftRun}>
          <StepGoContext value={pick}>
            {step === null && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
            {step === 0 && <SpoilerSetup />}
            {step === 1 && <ScriptReview />}
            {step === 2 && <RenderResults />}
          </StepGoContext>
        </DraftRunContext>
      </StepsRefreshContext>
    </PageLayout>
  );
}
