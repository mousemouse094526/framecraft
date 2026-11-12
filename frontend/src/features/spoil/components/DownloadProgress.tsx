import type { DownloadJob } from "../hooks/useSpoilDownload";
import { ProgressCard } from "./ProgressCard";

type Props = {
  job: DownloadJob;
  onCancel: () => void;
};

/** An unfinished download: what it is doing, its bar, and ยกเลิก (D6, D15, D18). */
export function DownloadProgress({ job, onCancel }: Props) {
  return (
    <ProgressCard
      headline={headline(job)}
      percent={job.state === "downloading" ? job.percent : null}
      bar={barPercent(job)}
      cancelling={job.cancel_requested}
      onCancel={onCancel}
      noCancelReason={job.state === "merging" ? "ยกเลิกไม่ได้ระหว่างรวมไฟล์" : undefined}
    />
  );
}

function headline(job: DownloadJob): string {
  if (job.cancel_requested) return "กำลังยกเลิก…";
  if (job.state === "checking") return "กำลังเช็คลิงก์…";
  if (job.state === "merging") return "กำลังรวมไฟล์…";
  return `กำลังโหลด ${job.title ?? ""}`.trim();
}

/** No bar while checking; merging fills it (Figma frame 5). */
function barPercent(job: DownloadJob): number | "unknown" | undefined {
  if (job.state === "checking") return undefined;
  if (job.state === "merging") return 100;
  return job.percent ?? "unknown";
}
