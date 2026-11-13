import type { ReactNode } from "react";

// The editor's labelled fields, red while the field has an error (as story-kb's editor).

export const inputClass = (error: boolean) =>
  `h-10 w-full rounded-lg border bg-card px-3 text-sm leading-5 text-foreground outline-none focus:border-2 focus:border-brand-accent ${
    error ? "border-destructive" : "border-border"
  }`;

type LabeledProps = { label: string; htmlFor: string; error?: string; hint?: string; children: ReactNode };

export function Labeled({ label, htmlFor, error, hint, children }: LabeledProps) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={htmlFor} className="font-button text-sm leading-5 font-medium text-foreground">
        {label}
      </label>
      {children}
      {hint && <p className="text-xs leading-4 text-muted-foreground">{hint}</p>}
      {error && <p className="font-button text-xs leading-4 text-destructive">{error}</p>}
    </div>
  );
}
