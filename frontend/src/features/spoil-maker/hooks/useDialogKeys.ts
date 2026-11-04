import { useEffect, useRef } from "react";

const FOCUSABLE = "button:not(:disabled), input:not(:disabled), select, video, [tabindex]";

/**
 * A modal dialog's keys: Esc closes it, and Tab stays inside it while it is open
 * (Figma `Picker header`). Returns the ref for the dialog's box.
 */
export function useDialogKeys(onClose: () => void) {
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") trapFocus(event, dialog.current);
    };
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [onClose]);

  return dialog;
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
