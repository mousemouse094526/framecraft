import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import refreshIcon from "../assets/refresh-cw.svg";
import triangleAlertIcon from "../assets/triangle-alert-24.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { progressPercent, progressText, type RenderJob, type SentencesJob } from "../lib/render";

type Props = {
  /** The voice or render job running now. */
  job: SentencesJob | RenderJob | null;
  /** Another job holds the draft (AI เลือก Shot ใหม่): both buttons wait. */
  waitingFor: string | null;
  /** Sentences with no Shot: render can't start (spec › Render job step 1). */
  noShot: number;
  /** Sentences that aren't `ready`: สร้างเสียงทั้งหมด voices them. */
  unvoiced: number;
  onVoiceAll: () => void;
  onRender: () => void;
  onCancel: () => void;
};

/** Figma `Review footer`, sticky under the page: สร้างเสียงทั้งหมด and render, or the running job with ยกเลิก. */
export function ReviewFooter({ job, waitingFor, noShot, unvoiced, onVoiceAll, onRender, onCancel }: Props) {
  const box =
    "sticky bottom-4 z-10 flex flex-col items-stretch gap-3 rounded-2xl border border-border bg-card p-4 shadow-[0_-2px_6px_rgba(18,18,15,0.08)] lg:flex-row lg:items-center";
  if (job) {
    return (
      <div role="region" aria-label="สร้างเสียงและ render" className={box}>
        <JobProgress job={job} onCancel={onCancel} />
      </div>
    );
  }
  return (
    <div role="region" aria-label="สร้างเสียงและ render" className={`${box} ${waitingFor || noShot ? "" : "lg:justify-end"}`}>
      {waitingFor && <p className="flex-1 text-sm text-mid">{waitingFor}</p>}
      {!waitingFor && noShot > 0 && (
        <p className="flex flex-1 items-center gap-2 text-sm font-medium text-warning">
          <img src={triangleAlertIcon} alt="" width={24} height={24} />
          มี {noShot} ประโยคที่ไม่มี Shot: เลือก Shot ก่อน render
        </p>
      )}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onVoiceAll}
          disabled={waitingFor !== null || unvoiced === 0}
          className={`h-11 flex-1 px-6 lg:flex-none ${OUTLINE_BUTTON}`}
        >
          <img src={refreshIcon} alt="" width={16} height={16} />
          สร้างเสียงทั้งหมด
        </button>
        <button
          type="button"
          onClick={onRender}
          disabled={waitingFor !== null || noShot > 0}
          className={`h-11 flex-1 px-6 lg:flex-none ${PRIMARY_BUTTON}`}
        >
          render
        </button>
      </div>
    </div>
  );
}

/** Figma `Render progress`: "สร้างเสียง x/y" or "render %" over its bar, with ยกเลิก. */
export function JobProgress({ job, onCancel }: { job: SentencesJob | RenderJob; onCancel: () => void }) {
  const text = progressText(job);
  return (
    <>
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <p className="text-sm font-medium text-foreground">{text}</p>
        <ProgressBar percent={progressPercent(job)} label={text} cancelling={job.cancel_requested} />
      </div>
      <button type="button" onClick={onCancel} disabled={job.cancel_requested} className={`h-11 px-6 ${OUTLINE_BUTTON}`}>
        <img src={xIcon} alt="" width={16} height={16} />
        ยกเลิก
      </button>
    </>
  );
}
