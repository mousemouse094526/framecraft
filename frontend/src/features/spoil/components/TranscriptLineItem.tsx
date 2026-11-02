import { useState, type FormEvent, type KeyboardEvent } from "react";
import { GHOST_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import type { LineEditResult, TranscriptLine } from "../hooks/useTranscribe";
import pencilIcon from "../assets/pencil.svg";
import { formatClock } from "../../../lib/format";

type Props = {
  line: TranscriptLine;
  editing: boolean;
  onJump: () => void;
  onStartEdit: () => void;
  onClose: () => void;
  onSave: (text: string) => Promise<LineEditResult>;
};

/** Figma component `Transcript line`: default, hover (แก้), edited (แก้แล้ว), editing (spoil-maker D54). */
export function TranscriptLineItem({ line, editing, onJump, onStartEdit, onClose, onSave }: Props) {
  const time = `[${formatClock(line.start_s)}]`;

  if (editing) {
    return (
      <li aria-label={time} className="flex flex-col gap-2 rounded-lg bg-accent-subtle p-2">
        <p className="font-mono text-[13px] whitespace-nowrap text-link">{time}</p>
        <LineEditor label={`แก้บรรทัด ${time}`} initial={line.text} onClose={onClose} onSave={onSave} />
      </li>
    );
  }

  return (
    <li aria-label={time} className="group flex items-center gap-3 rounded-md px-2 py-1 hover:bg-surface-strong">
      {/* The time and text are one button: a click plays the clip from the line. */}
      <button type="button" onClick={onJump} className="flex min-w-0 flex-1 items-start gap-3 text-left">
        <span className="shrink-0 font-mono text-[13px] whitespace-nowrap text-link">{time}</span>
        <span className="min-w-0 flex-1 text-sm break-words text-foreground">{line.text}</span>
      </button>
      {line.edited && (
        <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 font-button text-xs leading-4 font-medium whitespace-nowrap text-brand">
          แก้แล้ว
        </span>
      )}
      {/* Shown on hover or focus; a touch screen has no hover, so there it always shows. */}
      <button
        type="button"
        onClick={onStartEdit}
        aria-label={`แก้ ${time}`}
        className={`h-8 px-3 ${GHOST_BUTTON} hidden group-focus-within:flex group-hover:flex pointer-coarse:flex`}
      >
        <img src={pencilIcon} alt="" width={16} height={16} />
        แก้
      </button>
    </li>
  );
}

type EditorProps = {
  label: string;
  initial: string;
  onClose: () => void;
  onSave: (text: string) => Promise<LineEditResult>;
};

/** The field with บันทึก and ยกเลิก; a refusal keeps it open with its message so the text isn't lost. */
function LineEditor({ label, initial, onClose, onSave }: EditorProps) {
  const [text, setText] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (saving || text.trim() === "") return;
    setSaving(true);
    setError(null);
    const result = await onSave(text);
    // `saved` closes the field and `offline` replaces the page, so only a refusal is left here.
    if (result.kind === "refused") {
      setError(result.message);
      setSaving(false);
    }
  };

  // A line is one line of text: Enter (with Shift too) saves rather than breaking it; Escape is ยกเลิก.
  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void submit();
    } else if (event.key === "Escape") {
      onClose();
    }
  };

  return (
    <form onSubmit={(event) => void submit(event)} className="flex flex-col gap-2">
      <textarea
        aria-label={label}
        value={text}
        rows={1}
        autoFocus
        disabled={saving}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={onKeyDown}
        className="field-sizing-content w-full resize-none rounded-lg border-2 border-brand-accent bg-card px-3 py-2 text-sm leading-[1.5] text-foreground outline-none"
      />
      {error && <p className="text-sm leading-[1.5] text-destructive">{error}</p>}
      <div className="flex items-center gap-2">
        <button type="submit" disabled={saving || text.trim() === ""} className={`h-8 px-3 ${PRIMARY_BUTTON}`}>
          บันทึก
        </button>
        <button
          type="button"
          onClick={onClose}
          disabled={saving}
          className={`h-8 px-3 ${GHOST_BUTTON}`}
        >
          ยกเลิก
        </button>
      </div>
    </form>
  );
}
