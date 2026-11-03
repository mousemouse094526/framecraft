import type { ReactNode } from "react";
import errorIcon from "./assets/alert-error.svg";
import infoIcon from "./assets/alert-info.svg";
import successIcon from "./assets/alert-success.svg";
import warningIcon from "./assets/alert-warning.svg";

export type Tone = "success" | "info" | "warning" | "error";

const TONE_LOOK: Record<Tone, { icon: string; boxClass: string }> = {
  success: { icon: successIcon, boxClass: "border-success-border bg-success-surface" },
  info: { icon: infoIcon, boxClass: "border-info-border bg-info-surface" },
  warning: { icon: warningIcon, boxClass: "border-warning-border bg-warning-surface" },
  error: { icon: errorIcon, boxClass: "border-error-border bg-error-surface" },
};

type Props = {
  tone: Tone;
  children: ReactNode;
  /** A button or link at the right end (desktop) or under the text (phone). */
  action?: ReactNode;
};

/** Figma component `Alert`: a toned box with its icon and a message (spoil D33, spoil-maker setup and review banners). */
export function Alert({ tone, children, action }: Props) {
  const look = TONE_LOOK[tone];
  return (
    <div role="status" className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${look.boxClass}`}>
      <img src={look.icon} alt="" width={18} height={18} className="mt-px shrink-0" />
      <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <div className="min-w-0 flex-1 font-button text-sm leading-5 break-words text-foreground">{children}</div>
        {action}
      </div>
    </div>
  );
}
