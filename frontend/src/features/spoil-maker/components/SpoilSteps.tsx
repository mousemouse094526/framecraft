import { Fragment } from "react";
import type { StepLines } from "../lib/steps";

import type { Step } from "../hooks/useStepStatus";

// The steps of สปอย (spoil-maker D53): states of the page at `#/spoil`, not hashes (nav-ia D5).
const STEPS = ["เลือกคลิป", "ตรวจแก้บท", "ผล render"] as const;

/** `current` null: the page doesn't know yet where the work stands, no step is open. */
type Props = { current: Step | null; lines: StepLines; onPick: (step: Step) => void };

/**
 * Figma component `Spoil steps`, after D68: every step is a numbered button that opens it in the
 * page (nav-ia D5), the open one stands out, and each says where it stands; a step whose job runs
 * has a spinner.
 */
export function SpoilSteps({ current, lines, onPick }: Props) {
  return (
    <nav aria-label="ขั้นของสปอย" className="flex w-fit max-w-full items-center gap-2">
      {STEPS.map((step, index) => {
        const open = index === current;
        const { text, busy } = lines[index];
        return (
          <Fragment key={step}>
            {index > 0 && <div className="h-0.5 w-8 shrink-0 bg-border" />}
            <button
              type="button"
              onClick={() => onPick(index as Step)}
              aria-current={open ? "step" : undefined}
              className={`flex min-w-0 items-center gap-2 rounded-full py-1.5 pr-3 pl-2 ${
                open ? "bg-accent-subtle" : "shrink-0 hover:bg-muted"
              }`}
            >
              <span
                className={`flex size-6 shrink-0 items-center justify-center rounded-full font-button text-xs leading-[1.5] font-bold ${
                  open ? "bg-brand-accent text-card" : "border-[1.5px] border-border text-muted-foreground"
                }`}
              >
                {index + 1}
              </span>
              {busy && (
                <span
                  role="img"
                  aria-label="กำลังทำงาน"
                  className="size-3.5 shrink-0 rounded-full border-2 border-brand-accent border-t-transparent motion-safe:animate-spin"
                />
              )}
              {/* A phone names only the open step; the spinners stay (spoil-maker D53, D68). */}
              <span className={`flex min-w-0 flex-col ${open ? "" : "sr-only sm:not-sr-only"}`}>
                <span className={`text-sm leading-[1.5] whitespace-nowrap ${open ? "font-medium text-link" : "text-foreground"}`}>
                  {step}
                </span>
                {text && <span className="max-w-48 truncate text-xs leading-[1.5] text-muted-foreground">{text}</span>}
              </span>
            </button>
          </Fragment>
        );
      })}
    </nav>
  );
}
