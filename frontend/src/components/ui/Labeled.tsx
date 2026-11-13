import type { ReactNode } from "react";

// A labelled field with its hint and error line; the input inside takes `inputClass` (inputStyles). The lesson editor and the song page use it.

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
