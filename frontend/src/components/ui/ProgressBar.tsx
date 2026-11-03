type Props = {
  percent: number | "unknown";
  label: string;
  cancelling?: boolean;
};

/** A known percent fills the bar; an unknown one shows a segment (spoil Figma frame 5). */
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
        <div className={`absolute inset-y-0 left-[32%] w-[23%] rounded-[4px] opacity-90 ${fillColor}`} />
      ) : (
        <div className={`absolute inset-y-0 left-0 rounded-[4px] ${fillColor}`} style={{ width: `${percent}%` }} />
      )}
    </div>
  );
}
