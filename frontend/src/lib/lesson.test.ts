import { expect, test } from "vitest";
import { inReelShape, canTakeHand, canTakeHit, drumsViewOf, fieldErrors, isReelShape, lengthOf, noteFor, plainChapters, repeatsOf, type Chapter, type LessonFields, type Note } from "./lesson";

const chapter = (change: Partial<Chapter> = {}): Chapter => ({ label: "", text: "", focus: [], repeats: 2, speed: 100, ...change });

const note = (piece: Note["piece"], step: number, hand: Note["hand"] = "R", hit: Note["hit"] = "normal"): Note => ({ piece, step, hand, hit });

const fields = (change: Partial<LessonFields> = {}): LessonFields => ({
  title: "Groove",
  subtitle: "",
  caption: "",
  bpm: 120,
  background: "color",
  groove: { bars: 1, notes: [] },
  chapters: plainChapters(2),
  ...change,
});

test("an empty cell takes the free hand, R first, and a foot takes none", () => {
  expect(noteFor([], "snare", 0)).toEqual(note("snare", 0, "R"));
  expect(noteFor([note("snare", 0, "R")], "tom_high", 0)).toEqual(note("tom_high", 0, "L"));
  expect(noteFor([note("snare", 0, "R"), note("tom_high", 0, "L")], "crash", 0)).toBeNull();
  expect(noteFor([note("snare", 0, "R"), note("tom_high", 0, "L")], "kick", 0)).toEqual(note("kick", 0, null));
});

test("one hi-hat note per step: an open one can't join a closed one", () => {
  expect(noteFor([note("hihat_closed", 4)], "hihat_open", 4)).toBeNull();
});

test("a note can't take the hand another note of its step holds; a flam holds both (D20)", () => {
  const snare = note("snare", 0, "R");
  const tom = note("tom_high", 0, "L");

  expect(canTakeHand([snare, tom], tom, "R")).toBe(false);
  expect(canTakeHand([snare, tom], tom, "L")).toBe(true);
  expect(canTakeHand([note("snare", 0, "R", "flam"), tom], tom, "L")).toBe(false);
});

test("a flam only on a hand piece alone in its step", () => {
  const snare = note("snare", 0);

  expect(canTakeHit([snare], snare, "flam")).toBe(true);
  expect(canTakeHit([snare, note("kick", 0, null)], snare, "flam")).toBe(true);
  expect(canTakeHit([snare, note("tom_high", 0, "L")], snare, "flam")).toBe(false);
  expect(canTakeHit([note("kick", 0, null)], note("kick", 0, null), "flam")).toBe(false);
  expect(canTakeHit([snare, note("tom_high", 0, "L")], snare, "accent")).toBe(true);
});

test("the fields' errors are keyed as the backend's, counting letters as code points", () => {
  const errors = fieldErrors(fields({ title: " ", bpm: 241, subtitle: "ก".repeat(61) }));

  expect(Object.keys(errors).sort()).toEqual(["bpm", "subtitle", "title"]);
  expect(fieldErrors(fields({ title: "😀".repeat(40) }))).toEqual({});
});

test("the length is a bar of count-in, every chapter and 1.5 s of tail", () => {
  // 120 BPM: a bar is 2 s, 4 s at 50 %; two chapters of 2 repeats × 1 bar.
  const chapters = [chapter({ speed: 50 }), chapter()];

  expect(lengthOf(fields({ chapters }))).toBe(4 + 2 * 4 + 2 * 2 + 1.5);
});

test("the hash picks the list, a lesson's editor or its renders", () => {
  expect(drumsViewOf("#/drums")).toEqual({ kind: "list" });
  expect(drumsViewOf("#/drums/abcdef123456")).toEqual({ kind: "edit", id: "abcdef123456" });
  expect(drumsViewOf("#/drums/abcdef123456/renders")).toEqual({ kind: "renders", id: "abcdef123456" });
  expect(drumsViewOf("#/drums/../x")).toEqual({ kind: "list" });
});

test("a reel's chapters are one plain chapter; any label, text, focus, slower speed or second chapter is the old shape (reels-only D4)", () => {
  expect(plainChapters(5)).toEqual([{ label: "", text: "", focus: [], repeats: 5, speed: 100 }]);
  expect(isReelShape(plainChapters(3))).toBe(true);
  expect(isReelShape([chapter({ label: "KICK" })])).toBe(false);
  expect(isReelShape([chapter({ text: "ช้าๆ" })])).toBe(false);
  expect(isReelShape([chapter({ focus: ["kick"] })])).toBe(false);
  expect(isReelShape([chapter({ speed: 80 })])).toBe(false);
  expect(isReelShape([chapter(), chapter()])).toBe(false);
});

test("an old shape's repeats add up, at most 8, and say what they added up to", () => {
  expect(repeatsOf([chapter(), chapter(), chapter()])).toEqual({ repeats: 6, total: 6 });
  expect(repeatsOf([chapter({ repeats: 4 }), chapter({ repeats: 4 }), chapter({ repeats: 4 })])).toEqual({ repeats: 8, total: 12 });
});

test("as a reel, the fields keep everything but the chapters, merged into one", () => {
  const old = fields({ title: "Fill", chapters: [chapter({ label: "KICK", speed: 75 }), chapter({ repeats: 3 })] });

  expect(inReelShape(old)).toEqual({ ...old, chapters: plainChapters(5) });
  expect(inReelShape(fields())).toEqual(fields());
});
