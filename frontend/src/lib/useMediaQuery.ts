import { useEffect, useState } from "react";

/** Whether the window matches `query`, kept current; with no `matchMedia` (jsdom) it never does. */
export function useMediaQuery(query: string): boolean {
  const [list] = useState(() => (typeof window.matchMedia === "function" ? window.matchMedia(query) : null));
  const [matches, setMatches] = useState(list?.matches ?? false);
  useEffect(() => {
    if (!list) return;
    const follow = (event: MediaQueryListEvent) => setMatches(event.matches);
    list.addEventListener("change", follow);
    return () => list.removeEventListener("change", follow);
  }, [list]);
  return matches;
}
