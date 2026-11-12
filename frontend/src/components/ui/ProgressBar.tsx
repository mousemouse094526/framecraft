type Props = {
  percent: number | "unknown";
  label: string;
  cancelling?: boolean;
};

/**
 * A known percent fills the bar; an unknown one shows a segment (spoil Figma frame 5).
 * While the job runs the segment slides and the fill shimmers, so a percent that sits
 * still for a while doesn't read as stuck; a cancelling bar stops moving.
 */
export function ProgressBar({ percent, label, cancelling = false }: Props) {
  const fillColor = cancelling ? "bg-border-strong" : "bg-brand-accent";
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent === "unknown" ? undefined : percent}
      className="relative h-2 w-full overflow-hidden rounded-full bg-muted"
    >
      {percent === "unknown" ? (
        <div
          className={`absolute inset-y-0 left-0 w-[23%] rounded-[4px] opacity-90 ${fillColor} ${
            cancelling ? "translate-x-[140%]" : "motion-safe:animate-progress-slide motion-reduce:translate-x-[140%]"
          }`}
        />
      ) : (
        <div
          className={`absolute inset-y-0 left-0 overflow-hidden rounded-[4px] transition-[width] duration-700 ease-out ${fillColor}`}
          style={{ width: `${percent}%` }}
        >
          {!cancelling && (
            <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/40 to-transparent motion-safe:animate-progress-shimmer motion-reduce:hidden" />
          )}
        </div>
      )}
    </div>
  );
}
