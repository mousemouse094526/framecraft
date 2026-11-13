import { ProgressBar } from "../../../components/ui/ProgressBar";

/** A render's bar and its percent beside it: the editor's render control and the results page. */
export function RenderProgress({ percent }: { percent: number }) {
  return (
    <>
      <ProgressBar percent={percent} label="กำลัง render" />
      <span className="text-[13px] leading-[1.5] text-mid">{percent}%</span>
    </>
  );
}
