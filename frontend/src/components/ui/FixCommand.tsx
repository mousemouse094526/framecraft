import { useCopy } from "../../lib/useCopy";
import { OUTLINE_BUTTON } from "./buttonStyles";
import copyIcon from "./assets/copy.svg";

/** A fix to run, as a command line with a copy button (setup-status D20): spoil's notices and a not_ready of สอนกลอง. */
export function FixCommand({ command }: { command: string }) {
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
