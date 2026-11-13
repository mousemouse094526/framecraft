import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT } from "./api";
import { send, sent, serve } from "../testing/testBackend";
import { sendEdit } from "./edit";

const PATH = "/api/toon/eps/e_1";
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => vi.stubGlobal("fetch", fetchMock));

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

test.each([200, 201])("a %i answer is ok with the value as it is now", async (status) => {
  serve(fetchMock, [send("PATCH", PATH, { title: "ใหม่" }, status)]);

  expect(await sendEdit("PATCH", PATH, { title: "ใหม่" }, "บันทึกไม่ได้")).toEqual({ kind: "ok", value: { title: "ใหม่" } });
  expect(sent(fetchMock, "PATCH", PATH)).toEqual([{ title: "ใหม่" }]);
});

test("a refusal is refused with the notice, titled, with the refusal's message", async () => {
  serve(fetchMock, [send("PATCH", PATH, { code: "busy", message: "มีงานทำอยู่" }, 409)]);

  expect(await sendEdit("PATCH", PATH, {}, "บันทึกไม่ได้")).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "บันทึกไม่ได้", text: "มีงานทำอยู่", setupLink: false },
    refusal: { code: "busy", message: "มีงานทำอยู่" },
  });
});

test("a status in `ok` is ok; a 204 has no value", async () => {
  serve(fetchMock, [send("DELETE", PATH, null, 204)]);

  expect(await sendEdit("DELETE", PATH, undefined, "ลบไม่ได้", { ok: [204] })).toEqual({ kind: "ok", value: null });
});

// An answer outside `ok` with no refusal in it reads as no backend, as `noticeOf` does.
test("a 200 is refused when `ok` doesn't name it", async () => {
  serve(fetchMock, [send("POST", PATH, { id: "j_1" }, 200)]);

  const reply = await sendEdit("POST", PATH, {}, "ยังเริ่มไม่ได้", { ok: [202] });

  expect(reply).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "ยังเริ่มไม่ได้", text: OFFLINE_TEXT, setupLink: false },
    refusal: null,
  });
});

test("a code in `warnings` is a warning, and the refusal comes back with its own fields", async () => {
  const body = { code: "cards_not_ready", message: "ยังไม่ครบ", card_ids: ["c_1"] };
  serve(fetchMock, [send("POST", PATH, body, 409)]);

  const reply = await sendEdit<null, { code: string; message: string; card_ids: string[] }>("POST", PATH, {}, "ยัง render ไม่ได้", {
    ok: [202],
    warnings: ["cards_not_ready"],
  });

  expect(reply).toEqual({
    kind: "refused",
    notice: { tone: "warning", title: "ยัง render ไม่ได้", text: "ยังไม่ครบ", setupLink: false },
    refusal: body,
  });
});

test("no backend is refused with OFFLINE_TEXT", async () => {
  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

  expect(await sendEdit("DELETE", PATH, undefined, "ลบไม่ได้")).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "ลบไม่ได้", text: OFFLINE_TEXT, setupLink: false },
    refusal: null,
  });
});
