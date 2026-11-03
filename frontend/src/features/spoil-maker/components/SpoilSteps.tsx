import { Fragment } from "react";
import checkIcon from "../assets/check.svg";

// The steps of the สปอย tab and their hashes (spoil-maker D53).
const STEPS = [
  { label: "เลือกคลิป", hash: "#/spoil" },
  { label: "ตรวจแก้บท", hash: "#/spoil/review" },
  { label: "ผล render", hash: "#/spoil/renders" },
] as const;

/** The index in `STEPS` a hash opens; a `#/spoil/…` hash it doesn't know opens the first step. */
export function stepOf(hash: string): number {
  return Math.max(0, STEPS.findIndex((step) => step.hash === hash));
}

const DOT = "flex size-6 items-center justify-center rounded-full";

/** Figma component `Spoil steps`: passed steps have a check, the current one stands out; each other step is a link. */
export function SpoilSteps({ current }: { current: number }) {
  return (
    <nav aria-label="ขั้นของสปอย" className="flex w-fit items-center gap-2">
      {STEPS.map((step, index) => (
        <Fragment key={step.hash}>
          {index > 0 && <div className={`h-0.5 w-8 shrink-0 ${index <= current ? "bg-brand-accent" : "bg-border"}`} />}
          {index === current ? (
            <div aria-current="step" className="flex shrink-0 items-center gap-2 rounded-full bg-accent-subtle py-2.5 pr-3 pl-2">
              <span className={`${DOT} bg-brand-accent font-button text-xs leading-[1.5] font-bold text-card`}>
                {index + 1}
              </span>
              <span className="text-sm leading-[1.5] font-medium whitespace-nowrap text-link">{step.label}</span>
            </div>
          ) : (
            <a href={step.hash} className="flex shrink-0 items-center gap-2 rounded-full py-2.5 pr-3 pl-2 hover:bg-muted">
              {index < current ? (
                <span className={`${DOT} bg-accent-subtle`}>
                  <img src={checkIcon} alt="ผ่านแล้ว" width={14} height={14} />
                </span>
              ) : (
                <span className={`${DOT} border-[1.5px] border-border font-button text-xs leading-[1.5] font-bold text-muted-foreground`}>
                  {index + 1}
                </span>
              )}
              {/* A phone names only the current step (spoil-maker D53). */}
              <span
                className={`sr-only text-sm leading-[1.5] whitespace-nowrap sm:not-sr-only ${
                  index < current ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {step.label}
              </span>
            </a>
          )}
        </Fragment>
      ))}
    </nav>
  );
}
