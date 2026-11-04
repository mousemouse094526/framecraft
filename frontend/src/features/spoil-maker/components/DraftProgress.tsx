import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import checkWhiteIcon from "../assets/check-white.svg";
import { draftLabel, SETUP_HASH, STYLES, type WholeDraftJob } from "../lib/draft";
import type { DraftProgressView, RetryStep } from "../hooks/useDraftProgress";
import { ReplaceConfirm } from "./ReplaceConfirm";

type Phase = "done" | "running" | "waiting";

/** How each phase's label reads (Figma `Draft progress card`). */
const PHASE_TEXT: Record<Phase, string> = {
  done: "text-foreground",
  running: "font-medium text-foreground",
  waiting: "text-muted-foreground",
};

/** Each phase in the order a whole new draft goes through them (spec › Draft job). */
function phasesOf(job: WholeDraftJob): [Phase, Phase, Phase] {
  if (job.state === "writing") return ["running", "waiting", "waiting"];
  if (job.state === "polishing") return ["done", "running", "waiting"];
  return ["done", "done", "running"];
}

/** Figma `Draft progress card`: what is drafted, the three phases, the bar and ยกเลิก (D81, D85). */
export function DraftProgressCard({ job, onCancel }: { job: WholeDraftJob; onCancel: () => void }) {
  const { order } = job;
  const style = STYLES.find((one) => one.id === order.style)?.label ?? order.style;
  const counting = job.state === "matching";
  const done = job.done ?? 0;
  const total = job.total ?? 0;
  const phases = phasesOf(job);
  const labels = ["เขียนบท", "เรียบเรียง", counting ? `เลือกภาพ ${done}/${total}` : "เลือกภาพ"];
  return (
    <section aria-label="ความคืบหน้าการร่างบท" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6">
      <div className="flex flex-col gap-0.5">
        <p className="text-base leading-6 font-semibold text-foreground">{draftLabel(order)}</p>
        <p className="text-[13px] leading-5 text-mid">
          {style} · {order.target_s} วินาที
        </p>
      </div>
      <ol className="flex flex-col gap-2.5">
        {labels.map((label, index) => (
          <li key={index} aria-current={phases[index] === "running" ? "step" : undefined} className="flex items-center gap-2.5">
            <PhaseIcon phase={phases[index]} />
            <span className={`text-sm leading-[21px] ${PHASE_TEXT[phases[index]]}`}>{label}</span>
          </li>
        ))}
      </ol>
      {/* Only picking counts; writing and polishing have no percent (spec › Draft job). No sentence to pick for is full. */}
      <ProgressBar
        percent={counting ? (total ? Math.floor((done * 100) / total) : 100) : "unknown"}
        label="ความคืบหน้าการร่างบท"
        cancelling={job.cancel_requested}
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <p className="flex-1 text-[13px] leading-5 text-mid">{job.cancel_requested ? "กำลังยกเลิก" : "กำลังร่างบท ใช้เวลาหลายนาที"}</p>
        <button
          type="button"
          onClick={onCancel}
          disabled={job.cancel_requested}
          className={`h-11 w-full px-6 sm:h-10 sm:w-auto ${OUTLINE_BUTTON}`}
        >
          ยกเลิก
        </button>
      </div>
    </section>
  );
}

function PhaseIcon({ phase }: { phase: Phase }) {
  if (phase === "done") {
    return (
      <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-brand-accent">
        <img src={checkWhiteIcon} alt="" width={12} height={12} />
      </span>
    );
  }
  if (phase === "running") {
    return <span className="size-5 shrink-0 rounded-full border-2 border-brand-accent border-t-transparent motion-safe:animate-spin" />;
  }
  return <span className="size-5 shrink-0 rounded-full border-2 border-border" />;
}

type NoticeProps = {
  view: Exclude<DraftProgressView, { kind: "none" | "running" | "offline" }>;
  retryStep: RetryStep;
  onRetry: () => void;
  /** ร่างทับ in the ask before replacing (D86). */
  onReplace: () => void;
  onKeep: () => void;
};

/** Above the script: a failed draft with ลองอีกครั้ง and กลับไปแก้ตั้งค่า, a lost job, or a cancel too late (D83, D85–D87). */
export function DraftNotice({ view, retryStep, onRetry, onReplace, onKeep }: NoticeProps) {
  if (view.kind === "cancelledTooLate") return <Alert tone="info">ยกเลิกไม่ทัน บทร่างเสร็จแล้ว</Alert>;
  const canRetry = view.kind === "failed" && view.canRetry;
  return (
    <div className="flex flex-col gap-2">
      <Alert tone="error">{view.kind === "lost" ? "งานหยุดกลางทาง" : view.text}</Alert>
      <div className="flex gap-2">
        {canRetry && (
          <button
            type="button"
            onClick={onRetry}
            disabled={retryStep !== "idle"}
            className={`h-11 flex-1 px-6 sm:h-10 sm:flex-none ${OUTLINE_BUTTON}`}
          >
            ลองอีกครั้ง
          </button>
        )}
        <a href={SETUP_HASH} className={`flex h-11 flex-1 items-center justify-center px-6 sm:h-10 sm:flex-none ${canRetry ? GHOST_BUTTON : OUTLINE_BUTTON}`}>
          กลับไปแก้ตั้งค่า
        </a>
      </div>
      {retryStep === "confirming" && <ReplaceConfirm onReplace={onReplace} onKeep={onKeep} />}
    </div>
  );
}
