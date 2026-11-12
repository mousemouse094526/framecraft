import { expect, test } from "vitest";
import backendDefaults from "../../../../../backend/tests/golden/toon_genre_defaults.json";
import { GENRE_DEFAULTS, itemPath, pageOf, pendingUrl, pickHash, refUrl, type ItemRef } from "./series";

// The backend's test checks `DEFAULTS` of backend/toon/series.py against the same file, so
// a value changed on one side only fails one of the two (toon D59).
test("the page shows the genre defaults the backend fills a new Series with", () => {
  expect(GENRE_DEFAULTS).toEqual(backendDefaults);
});

test("an ItemRef names the item's API paths and its pick page", () => {
  const ref: ItemRef = { seriesId: "s_1", itemKind: "backgrounds", itemId: "b_01" };

  expect(itemPath(ref)).toBe("/api/toon/series/s_1/backgrounds/b_01");
  expect(refUrl(ref, 2)).toBe("/api/toon/series/s_1/backgrounds/b_01/ref?rev=2");
  expect(pendingUrl(ref, 3)).toBe("/api/toon/series/s_1/backgrounds/b_01/ref/pending/3");
  expect(pickHash(ref)).toBe("#/toon/series/s_1/backgrounds/b_01/pick");
  expect(pageOf(pickHash(ref))).toEqual({ kind: "pick", itemRef: ref });
});
