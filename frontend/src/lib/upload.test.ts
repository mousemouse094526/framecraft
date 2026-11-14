import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT } from "./api";
import { FakeXhr } from "../testing/fakeXhr";
import { send, sent, serve } from "../testing/testBackend";
import { NOT_NOW } from "./notice";
import { sendChecked, type FileToSend } from "./upload";

const IMPORTS = "/api/sounds/imports";
const CHECK = `${IMPORTS}/check`;
const UPLOAD_URL = `${IMPORTS}?size=3`;
const fetchMock = vi.fn<typeof fetch>();
const file = new File(["wav"], "ลม.wav", { type: "audio/wav" });

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

function toSend(change: Partial<FileToSend> = {}): FileToSend {
  return { path: IMPORTS, checkBody: { size: 3 }, query: "size=3", file, title: "เอาไฟล์ ลม.wav เข้าไม่ได้", ...change };
}

const sentOnce = () => vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1)).then(() => FakeXhr.sent[0]);

test.each([200, 201])("checked, the file goes to {path}?{query} as the raw body with its percent; a %i answer is sent with the body", async (status) => {
  serve(fetchMock, [send("POST", CHECK, { size: 3 }, 200)]);
  const started = vi.fn();
  const progress = vi.fn();

  const reply = sendChecked(toSend(), { started, progress });
  const xhr = await sentOnce();
  xhr.progress(1, 2);
  await xhr.respond(status, { id: "m_02" });

  expect(await reply).toEqual({ kind: "ok", value: { id: "m_02" } });
  expect(sent(fetchMock, "POST", CHECK)).toEqual([{ size: 3 }]);
  expect(xhr.url).toBe(UPLOAD_URL);
  expect(xhr.body).toBe(file);
  expect(started).toHaveBeenCalledOnce();
  expect(progress).toHaveBeenCalledWith(50);
});

test("a refused check sends no file; the notice has the refusal's line, a NOT_NOW code a warning", async () => {
  serve(fetchMock, [send("POST", CHECK, { code: "busy", message: "มีงานทำอยู่" }, 409)]);
  const started = vi.fn();

  expect(await sendChecked(toSend({ warnings: NOT_NOW }), { started, progress: () => {} })).toEqual({
    kind: "refused",
    notice: { tone: "warning", title: "เอาไฟล์ ลม.wav เข้าไม่ได้", text: "มีงานทำอยู่", setupLink: false },
  });
  expect(FakeXhr.sent).toHaveLength(0);
  expect(started).not.toHaveBeenCalled();
});

test("no backend at the check is refused with OFFLINE_TEXT", async () => {
  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

  expect(await sendChecked(toSend(), { started: () => {}, progress: () => {} })).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "เอาไฟล์ ลม.wav เข้าไม่ได้", text: OFFLINE_TEXT, setupLink: false },
  });
});

test("a refused upload is refused with its line; a failed one with OFFLINE_TEXT", async () => {
  serve(fetchMock, [send("POST", CHECK, {}, 200), send("POST", CHECK, {}, 200)]);
  const on = { started: () => {}, progress: () => {} };

  const refused = sendChecked(toSend(), on);
  await (await sentOnce()).respond(400, { code: "invalid_request", message: "ไฟล์เสีย" });
  expect(await refused).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "เอาไฟล์ ลม.wav เข้าไม่ได้", text: "ไฟล์เสีย", setupLink: false },
  });

  FakeXhr.sent = [];
  const failed = sendChecked(toSend(), on);
  await (await sentOnce()).fail();
  expect(await failed).toEqual({
    kind: "refused",
    notice: { tone: "error", title: "เอาไฟล์ ลม.wav เข้าไม่ได้", text: OFFLINE_TEXT, setupLink: false },
  });
});

test("the upload handed to started can be aborted: the reply is aborted, no notice", async () => {
  serve(fetchMock, [send("POST", CHECK, {}, 200)]);
  const started = vi.fn();

  const reply = sendChecked(toSend(), { started, progress: () => {} });
  await sentOnce();
  started.mock.calls[0][0].abort();

  expect(await reply).toEqual({ kind: "aborted" });
});
