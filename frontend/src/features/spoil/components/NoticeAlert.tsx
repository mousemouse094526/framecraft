import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { useCopy } from "../../../lib/useCopy";
import type { Notice } from "../lib/notice";
import copyIcon from "../assets/copy.svg";

/** The message after a job or a refusal; a `fix` is a command line with a copy button (setup-status D20). */
export function NoticeAlert({ notice }: { notice: Notice }) {
  return (
    <div className="flex flex-col gap-2.5">
      <Alert tone={notice.tone}>{notice.text}</Alert>
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
