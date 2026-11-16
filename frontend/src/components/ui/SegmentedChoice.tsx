/** One of two (or a few) pill buttons, as a radiogroup named `label`: a reel's instrument and its sound (kalimba-cover D14). */
export function SegmentedChoice<T extends string | boolean>({ label, options, value, onChoose }: { label: string; options: { value: T; label: string; disabled?: boolean }[]; value: T; onChoose: (value: T) => void }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.label}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          disabled={option.disabled}
          onClick={() => onChoose(option.value)}
          className={`h-11 rounded-lg border px-4 font-button text-sm font-medium sm:h-10 ${value === option.value ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card text-mid hover:bg-muted"} disabled:opacity-40`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
