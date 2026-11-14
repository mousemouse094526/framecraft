import { useEffect, type RefObject } from "react";

/**
 * Closes a disclosure's panel while it is open: on `Esc`, with the focus put back on its button
 * (it would fall to `<body>` with the panel gone), or on a press outside both the button and
 * the panel. The button itself toggles, so a press on it is left to its own `onClick`.
 */
export function useDismiss(
  open: boolean,
  close: () => void,
  button: RefObject<HTMLElement | null>,
  panel: RefObject<HTMLElement | null>,
) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      close();
      button.current?.focus();
    };
    const onPointer = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!panel.current?.contains(target) && !button.current?.contains(target)) close();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open, close, button, panel]);
}
