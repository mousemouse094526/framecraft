import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import type { DownloadJob } from "../hooks/useSpoilDownload";
import cancelIcon from "../assets/cancel-x.svg";

type Props = {
  job: DownloadJob;
  onCancel: () => void;
};

/** An unfinished job: what it is doing, its bar, and ยกเลิก (D6, D15, D18). */
export function DownloadProgress({ job, onCancel }: Props) {
  const cancelling = job.cancel_requested;
  const percent = job.state === "downloading" ? job.percent : null;

  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center gap-3 text-sm leading-[1.5] whitespace-nowrap">
        <p className="min-w-0 flex-1 truncate font-medium text-foreground">{headline(job)}</p>
        {!cancelling && percent !== null && <p className="shrink-0 font-mono font-medium text-brand">{percent}%</p>}
      </div>
      {job.state !== "checking" && <Bar job={job} percent={percent} />}
      <div className="flex justify-end">
        {job.state === "merging" ? (
          <p className="text-[13px] leading-[1.5] text-muted-foreground">ยกเลิกไม่ได้ระหว่างรวมไฟล์</p>
        ) : (
          <button
            type="button"
            onClick={onCancel}
            disabled={cancelling}
            className={`h-8 px-3 ${OUTLINE_BUTTON}`}
          >
            <img src={cancelIcon} alt="" width={16} height={16} />
            ยกเลิก
          </button>
        )}
      </div>
    </section>
  );
}

function headline(job: DownloadJob): string {
  if (job.cancel_requested) return "กำลังยกเลิก…";
  if (job.state === "checking") return "กำลังเช็คลิงก์…";
  if (job.state === "merging") return "กำลังรวมไฟล์…";
  return `กำลังโหลด ${job.title ?? ""}`.trim();
}

/** A known percent fills the bar; an unknown size shows a segment and no number (Figma frame 5). */
function Bar({ job, percent }: { job: DownloadJob; percent: number | null }) {
  const fillColor = job.cancel_requested ? "bg-border-strong" : "bg-brand-accent";
  const fillPercent = job.state === "merging" ? 100 : percent;
  return (
    <div
      role="progressbar"
      aria-label="ความคืบหน้า"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={fillPercent ?? undefined}
      className="relative h-2 w-full overflow-hidden rounded-full bg-muted"
    >
      {fillPercent === null ? (
        <div className={`absolute inset-y-0 left-[32%] w-[23%] rounded-[4px] opacity-90 ${fillColor}`} />
      ) : (
        <div className={`absolute inset-y-0 left-0 rounded-[4px] ${fillColor}`} style={{ width: `${fillPercent}%` }} />
      )}
    </div>
  );
}
