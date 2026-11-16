/** On or off: the brand-accent track of spoil-maker's selected Position cell (D64), 44 px to tap. `label` names it for screen readers. */
export function Switch({ label, on, onToggle }: { label: string; on: boolean; onToggle: () => void }) {
  return (
    <button type="button" role="switch" aria-checked={on} aria-label={label} onClick={onToggle} className="flex size-11 items-center justify-center">
      <span className={`flex h-5 w-9 items-center rounded-full p-0.5 transition-colors ${on ? "bg-brand-accent" : "bg-border-strong"}`}>
        <span className={`size-4 rounded-full bg-card shadow-sm transition-transform ${on ? "translate-x-4" : ""}`} />
      </span>
    </button>
  );
}
