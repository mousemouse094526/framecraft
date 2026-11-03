import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import xIcon from "../../../components/ui/assets/x.svg";
import { ProgressBar } from "../../../components/ui/ProgressBar";

type Props = {
  headline: string;
  /** Shown as "{n}%" beside the headline; null shows none. */
  percent: number | null;
  /** How full the bar is, or "unknown" for a segment with no size (Figma frame 5); left out → no bar. */
  bar?: number | "unknown";
  cancelling: boolean;
  onCancel: () => void;
  /** Why the job can't be cancelled, said in place of ยกเลิก (D18). */
  noCancelReason?: string;
};

/**
 * Figma component `Download progress`: what a job is doing, its bar, and
 * ยกเลิก. The download and the Transcribe job both use it (D33).
 */
export function ProgressCard({ headline, percent, bar, cancelling, onCancel, noCancelReason }: Props) {
  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center gap-3 text-sm leading-[1.5] whitespace-nowrap">
        <p className="min-w-0 flex-1 truncate font-medium text-foreground">{headline}</p>
        {!cancelling && percent !== null && (
          <p className="shrink-0 font-mono font-medium text-brand">{percent}%</p>
        )}
      </div>
      {bar !== undefined && <ProgressBar percent={bar} label="ความคืบหน้า" cancelling={cancelling} />}
      <div className="flex justify-end">
        {noCancelReason ? (
          <p className="text-[13px] leading-[1.5] text-muted-foreground">{noCancelReason}</p>
        ) : (
          <button type="button" onClick={onCancel} disabled={cancelling} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            <img src={xIcon} alt="" width={16} height={16} />
            ยกเลิก
          </button>
        )}
      </div>
    </section>
  );
}
