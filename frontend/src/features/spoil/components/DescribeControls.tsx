import { useId, useState } from "react";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import type { DescribeError, DescribeJob } from "../hooks/useDescribe";
import type { TempClip } from "../../../lib/clips";
import deleteErrorIcon from "../assets/delete-error.svg";
import eyeIcon from "../assets/eye.svg";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { DraftWarning } from "./DraftWarning";

/** What the clip list knows about the one Describe job (spoil-maker D16, D45). */
export type DescribeProps = {
  /** The unfinished job, of any clip. */
  job: DescribeJob | null;
  /** A row's last refusal or failure, by clip id. */
  errors: Record<string, DescribeError>;
  /** Why no clip can start one now: another GPU job runs. */
  busyReason: string | null;
  /** `confirmDraftLoss`: the user went on past the Spoil draft warning (spoil-maker D49). */
  onStart: (clipId: string, confirmDraftLoss?: boolean) => void;
  onCancel: () => void;
};

type Props = { clip: TempClip; describe: DescribeProps };

// Mobile stacks full width with 44 px buttons; from lg (the two-column page) the row's text column, 108 px in, holds one line.
const AREA = "flex flex-col gap-2 lg:flex-row lg:items-center lg:gap-3 lg:pl-[108px]";
const BUTTON_SIZE = "h-11 w-full px-4 lg:h-9 lg:w-auto";
const HINT = "ให้ AI เขียนว่าแต่ละฉากมีภาพอะไร ใช้ตอนร่างบทสปอย";

/**
 * Figma component `Clip row`, its บรรยายฉาก part: ready, describing (% and
 * ยกเลิก), blocked with the reason, failed, and the ask before describing a
 * described clip again: the Spoil draft warning when the draft is made from it
 * (spoil-maker D16, D45, D49).
 */
export function DescribeControls({ clip, describe }: Props) {
  const [asking, setAsking] = useState(false);
  const reasonId = useId();
  const job = describe.job?.clip_id === clip.id ? describe.job : null;

  // Three views, in this order: this clip's job, the ask, then ready (which may be blocked or show an error).
  if (job) return <Progress job={job} onCancel={describe.onCancel} />;

  if (asking && clip.in_draft) {
    const go = () => {
      setAsking(false);
      describe.onStart(clip.id, true);
    };
    return (
      <div className="lg:pl-[108px]">
        <DraftWarning onGo={go} onCancel={() => setAsking(false)} />
      </div>
    );
  }

  if (asking) {
    return (
      <div className={AREA}>
        <div className="flex flex-1 flex-col gap-3 rounded-lg bg-muted p-3">
          <div className="flex flex-col gap-0.5 leading-[1.5]">
            <p className="text-sm font-medium text-foreground">บรรยายฉากคลิปนี้ใหม่?</p>
            <p className="text-[13px] text-mid">ผลเดิมจะถูกแทนที่เมื่อบรรยายฉากเสร็จ</p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              // Figma: the ask opens with focus on บรรยายฉากใหม่.
              autoFocus
              onClick={() => {
                setAsking(false);
                describe.onStart(clip.id);
              }}
              className={`h-11 flex-1 px-4 lg:h-9 lg:flex-none ${PRIMARY_BUTTON}`}
            >
              บรรยายฉากใหม่
            </button>
            <button
              type="button"
              onClick={() => setAsking(false)}
              className={`h-11 flex-1 px-4 lg:h-9 lg:flex-none ${OUTLINE_BUTTON}`}
            >
              ยกเลิก
            </button>
          </div>
        </div>
      </div>
    );
  }

  // The clip being described shows its progress above; every other clip waits for it.
  const busyReason = describe.busyReason;
  const error = busyReason ? null : (describe.errors[clip.id] ?? null);
  return (
    <div className={AREA}>
      {error && <ErrorLine error={error} />}
      <button
        type="button"
        disabled={busyReason !== null}
        aria-describedby={reasonId}
        onClick={() => (clip.described ? setAsking(true) : describe.onStart(clip.id))}
        className={`${BUTTON_SIZE} ${OUTLINE_BUTTON} disabled:opacity-50`}
      >
        <img src={eyeIcon} alt="" width={16} height={16} />
        บรรยายฉาก
      </button>
      {/* What the button does, until another GPU job says why it waits (D58). */}
      <p id={reasonId} className="text-[13px] leading-[1.5] text-mid lg:flex-1">
        {busyReason ?? HINT}
      </p>
    </div>
  );
}

function ErrorLine({ error }: { error: DescribeError }) {
  return (
    <p className="flex items-center gap-1.5 text-[13px] leading-[1.5] text-destructive">
      <img src={deleteErrorIcon} alt="" width={14} height={14} className="shrink-0" />
      {error.text}
      {error.setupLink && (
        <a href="#/setup" className="font-medium text-link underline">
          ไปหน้าติดตั้ง
        </a>
      )}
    </p>
  );
}

/** Cutting shows its own percent, then describing the Shots done of the total. */
function Progress({ job, onCancel }: { job: DescribeJob; onCancel: () => void }) {
  const cutting = job.state === "cutting";
  const percent = cutting ? (job.percent ?? 0) : job.total ? Math.floor(((job.done ?? 0) * 100) / job.total) : 0;
  const headline = job.cancel_requested ? "กำลังยกเลิก…" : cutting ? "กำลังแบ่งฉาก" : "กำลังบรรยายฉาก";
  return (
    <div className={AREA}>
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="flex items-center gap-3 leading-[1.5]">
          <p className="min-w-0 flex-1 text-[13px] text-mid">{headline}</p>
          <p className="shrink-0 font-mono text-sm font-medium text-brand">{percent}%</p>
        </div>
        <ProgressBar percent={percent} label="ความคืบหน้าการบรรยายฉาก" cancelling={job.cancel_requested} />
      </div>
      <button type="button" onClick={onCancel} disabled={job.cancel_requested} className={`${BUTTON_SIZE} ${OUTLINE_BUTTON}`}>
        ยกเลิก
      </button>
    </div>
  );
}
