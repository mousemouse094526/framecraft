import { expect, test } from "vitest";
import { downloadName, isRendering, jobOf, renderingOf, type DrumRenderJob, type RenderResult } from "./render";

const job = (change: Partial<DrumRenderJob> = {}): DrumRenderJob => ({
  state: "rendering",
  lesson_id: "abcdef123456",
  title: "Groove",
  percent: 40,
  result: null,
  error: null,
  message: null,
  ...change,
});

test("only a rendering job is rendering", () => {
  expect(isRendering(job())).toBe(true);
  expect(isRendering(job({ state: "done" }))).toBe(false);
  expect(isRendering(null)).toBe(false);
});

test("a lesson's job is the latest only when it is the lesson's own", () => {
  const failed = job({ state: "failed" });

  expect(jobOf(failed, "abcdef123456")).toBe(failed);
  expect(jobOf(failed, "zzzzzz000000")).toBeNull();
});

test("a lesson is rendering only while its own job renders", () => {
  expect(renderingOf(job(), "abcdef123456")?.percent).toBe(40);
  expect(renderingOf(job(), "zzzzzz000000")).toBeNull();
  expect(renderingOf(job({ state: "cancelled" }), "abcdef123456")).toBeNull();
});

test("a download is named after the title, without characters a file name can't hold", () => {
  const result: RenderResult = { name: "20261113-103000", lesson_id: "abcdef123456", title: "Smells Like: Teen/Spirit", length_s: 31.2, created_at: "", size_bytes: 1 };

  expect(downloadName(result, ".mp4")).toBe("smells-like-teen-spirit-20261113-103000.mp4");
  expect(downloadName({ ...result, title: "  " }, ".srt")).toBe("20261113-103000.srt");
});
