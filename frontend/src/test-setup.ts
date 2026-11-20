import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import { resetPlayerForTests } from "./lib/player";

// jsdom has no layout, so no scrolling: pages that take the view to a section (nav-ia D7) call this.
// A test that checks where a page scrolled puts its own `vi.fn()` here.
Element.prototype.scrollIntoView ??= () => {};

// Vitest has no globals here, so Testing Library can't unmount on its own.
afterEach(() => {
  // The one player is module state: each test starts with no sound (audio-player D13). First, so
  // the buttons that unmount next don't pause an element whose stub is already gone.
  resetPlayerForTests();
  cleanup();
});
