import { vi } from "vitest";

/** A `matchMedia` whose every query matches while `matches` is true; `change(to)` flips it and
 * tells the listeners, as a window crossing a breakpoint would. jsdom has none of its own. */
export function stubMatchMedia(matches: boolean) {
  const listeners = new Set<(event: MediaQueryListEvent) => void>();
  const lists: { matches: boolean }[] = [];
  vi.stubGlobal("matchMedia", (media: string) => {
    const list = {
      media,
      matches,
      addEventListener: (_: "change", listener: (event: MediaQueryListEvent) => void) => listeners.add(listener),
      removeEventListener: (_: "change", listener: (event: MediaQueryListEvent) => void) => listeners.delete(listener),
    };
    lists.push(list);
    return list;
  });
  return {
    change(to: boolean) {
      matches = to;
      for (const list of lists) list.matches = to;
      for (const listener of [...listeners]) listener({ matches: to } as MediaQueryListEvent);
    },
  };
}
