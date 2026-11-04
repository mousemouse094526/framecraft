import { useEffect, useRef, type ReactNode } from "react";

const FOCUSABLE = "button:not(:disabled), input:not(:disabled), select, video, [tabindex]";

type Props = {
  /** The id of the heading that names the dialog. */
  titleId: string;
  onClose: () => void;
  /** The box's width and gaps from `sm` on, e.g. `sm:max-w-[480px] gap-4`. */
  size: string;
  children: ReactNode;
};

/**
 * The Shot picker's frame, shared by every dialog of the สปอย tab: a dimmed overlay, a box
 * full width on a phone and rounded with a shadow from `sm`. Esc closes it, and Tab stays
 * inside it while it is open (Figma `Picker header`).
 */
export function ModalDialog({ titleId, onClose, size, children }: Props) {
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") trapFocus(event, dialog.current);
    };
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-10 flex items-start justify-center overflow-y-auto bg-surface-inverse/50 sm:items-center sm:p-8">
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`flex w-full flex-col bg-card px-4 pt-3 pb-4 sm:rounded-3xl sm:border sm:border-border sm:px-6 sm:pt-5 sm:pb-6 sm:shadow-[0_16px_48px_0_rgba(0,0,0,0.18)] ${size}`}
      >
        {children}
      </div>
    </div>
  );
}

function trapFocus(event: KeyboardEvent, dialog: HTMLElement | null) {
  if (!dialog) return;
  const focusable = dialog.querySelectorAll<HTMLElement>(FOCUSABLE);
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
