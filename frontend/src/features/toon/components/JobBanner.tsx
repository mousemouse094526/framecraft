import { ProgressBar } from "../../../components/ui/ProgressBar";
import refreshIcon from "../../../components/ui/assets/refresh-cw.svg";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import circleAlertIcon from "../assets/circle-alert.svg";
import circleCheckIcon from "../assets/circle-check.svg";
import loaderIcon from "../../../components/ui/assets/loader.svg";
import squareIcon from "../assets/square.svg";

type Props =
  | {
      kind: "running";
      title: string;
      detail: string;
      done: number;
      total: number;
      stopping: boolean;
      onStop: () => void;
      /** What the count says instead of `done/total` (a render's percent). */
      count?: string;
    }
  | { kind: "done"; title: string; detail: string }
  | { kind: "failed"; title: string; detail: string; onRetry: () => void };

const BOX: Record<Props["kind"], string> = {
  running: "border-border bg-card",
  done: "border-success-border bg-success-surface",
  failed: "border-error-border bg-error-surface",
};

const ICON: Record<Props["kind"], string> = { running: loaderIcon, done: circleCheckIcon, failed: circleAlertIcon };

/** Figma `Toon/JobBanner`: a long job running (count, หยุด, progress), done, or failed (ลองอีกครั้ง). */
export function JobBanner(props: Props) {
  return (
    <div role="status" aria-live="polite" className={`flex flex-col gap-3 rounded-2xl border p-4 ${BOX[props.kind]}`}>
      <div className="flex flex-wrap items-center gap-3">
        <img
          src={ICON[props.kind]}
          alt=""
          width={20}
          height={20}
          className={props.kind === "running" ? "motion-safe:animate-spin" : undefined}
        />
        <div className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <p className="text-sm font-medium text-foreground">{props.title}</p>
          <p className="text-[13px] text-mid">{props.detail}</p>
        </div>
        {props.kind === "running" && (
          <>
            <p className="font-mono text-sm text-foreground">{props.count ?? `${props.done}/${props.total}`}</p>
            <button type="button" disabled={props.stopping} onClick={props.onStop} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
              <img src={squareIcon} alt="" width={16} height={16} />
              {props.stopping ? "กำลังหยุด…" : "หยุด"}
            </button>
          </>
        )}
        {props.kind === "failed" && (
          <button type="button" onClick={props.onRetry} className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            <img src={refreshIcon} alt="" width={16} height={16} />
            ลองอีกครั้ง
          </button>
        )}
      </div>
      {props.kind === "running" && (
        <ProgressBar
          label={props.title}
          percent={Math.round((props.done / props.total) * 100)}
          cancelling={props.stopping}
        />
      )}
    </div>
  );
}
