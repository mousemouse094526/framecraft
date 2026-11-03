import { useId, useState, type FormEvent, type KeyboardEvent, type ReactNode } from "react";
import { PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import type { RefusalText } from "../hooks/useVoices";

// A Saved voice name is 1–40 letters (spoil-maker spec › Saved voice); the API checks it too.
const NAME_MAX = 40;

type Props = {
  initial?: string;
  /** Focus the field when it opens, as in renaming. */
  autoFocus?: boolean;
  onSave: (name: string) => Promise<RefusalText>;
  /** Escape runs it too. */
  onCancel?: () => void;
  /** Buttons after บันทึก, such as ยกเลิก. */
  extra?: ReactNode;
  /** The classes of each button, which differ between the designer and a row. */
  buttonClass: string;
};

/** Figma field ชื่อเสียง with บันทึก: naming a preview and renaming a voice. The API's refusal shows under it. */
export function NameForm({ initial = "", autoFocus = false, onSave, onCancel, extra, buttonClass }: Props) {
  const [name, setName] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<RefusalText>(null);
  const inputId = useId();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    const refusal = await onSave(name);
    setSaving(false);
    setError(refusal);
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Escape") onCancel?.();
  };

  return (
    <form onSubmit={(event) => void submit(event)} className="flex flex-col gap-2">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:gap-3">
        <div className="flex flex-col gap-2 sm:min-w-0 sm:flex-1">
          <label htmlFor={inputId} className="font-button text-sm leading-5 font-medium text-foreground">
            ชื่อเสียง
          </label>
          <input
            id={inputId}
            autoFocus={autoFocus}
            value={name}
            maxLength={NAME_MAX}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={onKeyDown}
            className="h-10 w-full rounded-lg border border-border bg-card px-3 text-sm leading-5 text-foreground outline-none focus:border-2 focus:border-brand-accent"
          />
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving || name.trim() === ""} className={`${buttonClass} ${PRIMARY_BUTTON}`}>
            บันทึก
          </button>
          {extra}
        </div>
      </div>
      {error && <p className="text-[13px] leading-5 text-destructive">{error}</p>}
    </form>
  );
}
