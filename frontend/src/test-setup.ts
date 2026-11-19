import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom has no layout, so no scrolling: pages that take the view to a section (nav-ia D7) call this.
// A test that checks where a page scrolled puts its own `vi.fn()` here.
Element.prototype.scrollIntoView ??= () => {};

// Vitest has no globals here, so Testing Library can't unmount on its own.
afterEach(() => {
  cleanup();
});
