import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { useCopy } from "../../../lib/useCopy";
import type { Notice } from "../lib/notice";
import errorIcon from "../assets/alert-error.svg";
import infoIcon from "../assets/alert-info.svg";
import successIcon from "../assets/alert-success.svg";
import warningIcon from "../assets/alert-warning.svg";
import copyIcon from "../assets/copy.svg";

const TONE_LOOK: Record<Notice["tone"], { icon: string; boxClass: string }> = {
  success: { icon: successIcon, boxClass: "border-success-border bg-success-surface" },
  info: { icon: infoIcon, boxClass: "border-info-border bg-info-surface" },
  warning: { icon: warningIcon, boxClass: "border-warning-border bg-warning-surface" },
  error: { icon: errorIcon, boxClass: "border-error-border bg-error-surface" },
};

/** The message after a job or a refusal; a `fix` is a command line with a copy button (setup-status D20). */
export function NoticeAlert({ notice }: { notice: Notice }) {
  const look = TONE_LOOK[notice.tone];
  return (
    <div className="flex flex-col gap-2.5">
      <div role="status" className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${look.boxClass}`}>
        <img src={look.icon} alt="" width={18} height={18} className="mt-px shrink-0" />
        <p className="min-w-0 flex-1 font-button text-sm leading-5 break-words text-foreground">{notice.text}</p>
      </div>
      {notice.fix && <FixCommand command={notice.fix} />}
    </div>
  );
}

function FixCommand({ command }: { command: string }) {
  const { copied, copy } = useCopy(command);
  return (
    <div className="flex items-center gap-2">
      <code className="min-w-0 flex-1 overflow-x-auto rounded-lg border border-border bg-card px-3 py-2 font-mono text-[13px] leading-[1.5] whitespace-nowrap text-foreground">
        {command}
      </code>
      <button
        type="button"
        onClick={copy}
        aria-label={`คัดลอก ${command}`}
        title={copied ? "คัดลอกแล้ว" : "คัดลอก"}
        className={`h-8 px-3 ${OUTLINE_BUTTON}`}
      >
        <img src={copyIcon} alt="" width={16} height={16} />
        {/* English, as on the Button in Figma frame 7 (D19). */}
        Copy
      </button>
    </div>
  );
}
