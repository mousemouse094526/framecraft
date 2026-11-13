import { expect, test } from "vitest";

// The library is the app's, not การ์ตูนเล่า's: it reads nothing of the tabs that use it (sound-library D11).
const sources = import.meta.glob<string>(["./**/*.{ts,tsx}", "!./**/*.test.{ts,tsx}"], { query: "?raw", import: "default", eager: true });

test("no file of sound-library imports features/toon or features/spoil-maker", () => {
  const offending = Object.entries(sources)
    .filter(([, source]) => /from "[./]*\/(toon|spoil-maker)\//.test(source))
    .map(([path]) => path);

  expect(Object.keys(sources).length).toBeGreaterThan(0);
  expect(offending).toEqual([]);
});
