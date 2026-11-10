import { expect, test } from "vitest";
import backendDefaults from "../../../../../backend/tests/golden/toon_genre_defaults.json";
import { GENRE_DEFAULTS } from "./series";

// The backend's test checks `DEFAULTS` of backend/toon/series.py against the same file, so
// a value changed on one side only fails one of the two (toon D59).
test("the page shows the genre defaults the backend fills a new Series with", () => {
  expect(GENRE_DEFAULTS).toEqual(backendDefaults);
});
