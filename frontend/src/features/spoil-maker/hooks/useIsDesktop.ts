import { useEffect, useState } from "react";

const DESKTOP = "(min-width: 1024px)"; // Tailwind's `lg`, where the Figma desktop frames start

/** Whether the window is desktop-wide: ผล render plays in a panel beside the list there, inline below a row on a phone. */
export function useIsDesktop(): boolean {
  const [query] = useState(() => (typeof window.matchMedia === "function" ? window.matchMedia(DESKTOP) : null));
  const [desktop, setDesktop] = useState(query?.matches ?? false);
  useEffect(() => {
    if (!query) return;
    const follow = (event: MediaQueryListEvent) => setDesktop(event.matches);
    query.addEventListener("change", follow);
    return () => query.removeEventListener("change", follow);
  }, [query]);
  return desktop;
}
