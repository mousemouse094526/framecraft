import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT } from "../../../lib/api";
import { send, sent, serve } from "../../../testing/testBackend";
import { sendEdit } from "./edit";

const PATH = "/api/toon/eps/e_1";
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => vi.stubGlobal("fetch", fetchMock));

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

test.each([200, 201])("a %i answer is saved with the value as it is now", async (status) => {
  serve(fetchMock, [send("PATCH", PATH, { title: "ใหม่" }, status)]);

  expect(await sendEdit("PATCH", PATH, { title: "ใหม่" }, "บันทึกไม่ได้")).toEqual({ kind: "saved", value: { title: "ใหม่" } });
  expect(sent(fetchMock, "PATCH", PATH)).toEqual([{ title: "ใหม่" }]);
});

test("a refusal is refused with the notice, titled, with the refusal's message", async () => {
  serve(fetchMock, [send("PATCH", PATH, { code: "busy", message: "มีงานทำอยู่" }, 409)]);

  expect(await sendEdit("PATCH", PATH, {}, "บันทึกไม่ได้")).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "บันทึกไม่ได้", text: "มีงานทำอยู่", setupLink: false },
  });
});

test("no backend is refused with OFFLINE_TEXT", async () => {
  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

  expect(await sendEdit("DELETE", PATH, undefined, "ลบไม่ได้")).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "ลบไม่ได้", text: OFFLINE_TEXT, setupLink: false },
  });
});
