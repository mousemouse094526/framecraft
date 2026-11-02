import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { Voice, VoiceJob } from "../hooks/useVoices";

const VOICES_PATH = "/api/spoil-maker/voices";
const JOBS_PATH = "/api/spoil-maker/voice-jobs";
const CURRENT_PATH = "/api/spoil-maker/voice-jobs/current";
const TRANSCRIBE_PATH = "/api/spoil/transcriptions/current";
const DESCRIBE_PATH = "/api/spoil-maker/describes/current";
const PREVIEW_PATH = "/api/spoil-maker/voice-jobs/preview.wav";

function voiceOf(change: Partial<Voice>): Voice {
  return {
    id: "v_0000abcd",
    name: "ลุงเล่าผี",
    speed: 1,
    chars_per_s: 14.2,
    created_at: "2026-11-02T10:00:00+07:00",
    in_use: false,
    ...change,
  };
}

function jobOf(change: Partial<VoiceJob>): VoiceJob {
  return {
    kind: "design_preview",
    state: "voicing",
    error: null,
    cancel_requested: false,
    started_at: "2026-11-02T10:05:00+07:00",
    ...change,
  };
}

const UNCLE = voiceOf({});
const SISTER = voiceOf({ id: "v_1111abcd", name: "พี่สาวเล่าหนัง", speed: 0.95 });

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type Route = { method?: string; path: string; reply: () => Response | Promise<Response> };

/**
 * Fake backend: each request takes the first route that matches it. A route
 * answers once, so routes for the same path play out in order; the last one
 * keeps answering. With no route for the list it is empty, and with none for
 * a job's `…/current` there is no such job.
 */
function backend(routes: Route[]) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  for (const path of [CURRENT_PATH, TRANSCRIBE_PATH, DESCRIBE_PATH]) if (!has(path)) routes.push(get(path, null));
  if (!has(VOICES_PATH)) routes.push(get(VOICES_PATH, []));
  fetchMock.mockImplementation(async (input, init) => {
    const method = init?.method ?? "GET";
    const matches = routes.filter((r) => r.path === String(input) && (r.method ?? "GET") === method);
    if (matches.length === 0) throw new Error(`unexpected ${method} ${String(input)}`);
    const route = matches[0];
    if (matches.length > 1) routes.splice(routes.indexOf(route), 1);
    return route.reply();
  });
}

const get = (path: string, body: unknown): Route => ({ path, reply: () => jsonResponse(body) });
const send = (method: string, path: string, body: unknown, code: number): Route => ({
  method,
  path,
  reply: () => jsonResponse(body, code),
});

const previewThere = (): Route => ({ method: "HEAD", path: PREVIEW_PATH, reply: () => new Response(null) });

function sent(method: string, path: string): unknown[] {
  return fetchMock.mock.calls
    .filter(([input, init]) => String(input) === path && init?.method === method)
    .map(([, init]) => (init?.body ? JSON.parse(String(init.body)) : null));
}

async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
}

function designer(): HTMLElement {
  return screen.getByRole("region", { name: "ออกแบบเสียง" });
}

function row(name: string): HTMLElement {
  return screen.getByRole("listitem", { name });
}

async function openPage() {
  window.location.hash = "#/spoil/voices";
  render(<App />);
  await screen.findByRole("region", { name: "ออกแบบเสียง" });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const fetchMock = vi.fn<typeof fetch>();
const played: string[] = [];

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
  // jsdom has no media playback (docs/library-notes/vitest.md): the src is what counts.
  vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(function (this: HTMLMediaElement) {
    played.push(this.src);
    return Promise.resolve();
  });
});

afterEach(() => {
  fetchMock.mockReset();
  played.length = 0;
  window.location.hash = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("หน้า Saved voice", () => {
  it("opens under the สปอย tab from #/spoil/voices, without the steps, with a link back", async () => {
    backend([]);
    await openPage();

    expect(screen.getByRole("link", { name: "สปอย" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("navigation", { name: "ขั้นของสปอย" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "เสียงบรรยาย" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับ" })).toHaveAttribute("href", "#/spoil");
  });

  it("says how to start when no voice is saved", async () => {
    backend([]);
    await openPage();

    expect(screen.getByText("ยังไม่มีเสียง กดสุ่มเพื่อออกแบบเสียงแรก")).toBeInTheDocument();
    expect(within(designer()).queryByRole("button", { name: "ฟัง" })).not.toBeInTheDocument();
    expect(within(designer()).queryByLabelText("ชื่อเสียง")).not.toBeInTheDocument();
  });

  it("lists saved voices with ฟัง, เปลี่ยนชื่อ and ลบ", async () => {
    backend([get(VOICES_PATH, [SISTER, UNCLE])]);
    const user = await openPage();

    expect(screen.getAllByRole("listitem").map((item) => item.getAttribute("aria-label"))).toEqual([
      "พี่สาวเล่าหนัง",
      "ลุงเล่าผี",
    ]);
    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ฟัง" }));
    expect(played).toEqual([expect.stringMatching(/\/api\/spoil-maker\/voices\/v_0000abcd\/sample\.wav$/)]);
  });

  it("สุ่ม sends the choices, shows the job, then ฟัง and the name field once it is done", async () => {
    backend([
      send("POST", JOBS_PATH, jobOf({}), 202),
      get(CURRENT_PATH, null),
      get(CURRENT_PATH, jobOf({ state: "done" })),
    ]);
    const user = await openPage();

    await user.click(within(designer()).getByRole("radio", { name: "หญิง" }));
    await user.selectOptions(within(designer()).getByLabelText("วัย"), "วัยกลางคน");
    await user.selectOptions(within(designer()).getByLabelText("ระดับเสียง"), "ต่ำ");
    await user.click(within(designer()).getByRole("button", { name: "สุ่ม" }));

    expect(sent("POST", JOBS_PATH)).toEqual([
      { kind: "design_preview", gender: "female", age: "middle-aged", pitch: "low pitch", speed: 1 },
    ]);
    expect(within(designer()).getByText("กำลังสุ่มเสียง…")).toBeInTheDocument();
    expect(within(designer()).getByRole("button", { name: "สุ่ม" })).toBeDisabled();

    await nextPoll();

    await user.click(within(designer()).getByRole("button", { name: "ฟัง" }));
    expect(played).toEqual([expect.stringMatching(/\/voice-jobs\/preview\.wav\?v=2026-11-02T10%3A05%3A00%2B07%3A00$/)]);
    expect(within(designer()).getByLabelText("ชื่อเสียง")).toBeInTheDocument();
    expect(within(designer()).getByRole("button", { name: "สุ่ม" })).toBeEnabled();
  });

  it("shows the speed it will send", async () => {
    backend([send("POST", JOBS_PATH, jobOf({}), 202), get(CURRENT_PATH, null)]);
    const user = await openPage();
    // user-event can't move a range input in jsdom; a change event is what the browser sends.
    fireEvent.change(within(designer()).getByLabelText("ความเร็ว"), { target: { value: "1.05" } });
    await user.click(within(designer()).getByRole("button", { name: "สุ่ม" }));

    expect(within(designer()).getByText("1.05×")).toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([expect.objectContaining({ speed: 1.05 })]);
  });

  it("opens with the preview of a design that finished before the page did", async () => {
    backend([get(CURRENT_PATH, jobOf({ state: "done" })), previewThere()]);
    await openPage();

    expect(within(designer()).getByRole("button", { name: "ฟัง" })).toBeInTheDocument();
  });

  it("shows no preview when the finished design's preview was saved already", async () => {
    backend([get(CURRENT_PATH, jobOf({ state: "done" })), send("HEAD", PREVIEW_PATH, null, 404)]);
    await openPage();

    expect(within(designer()).queryByRole("button", { name: "ฟัง" })).not.toBeInTheDocument();
    expect(within(designer()).queryByLabelText("ชื่อเสียง")).not.toBeInTheDocument();
  });

  it("บันทึก saves the preview and puts the voice on top of the list", async () => {
    const saved = voiceOf({ id: "v_2222abcd", name: "เสียงใหม่" });
    backend([
      get(VOICES_PATH, [UNCLE]),
      get(CURRENT_PATH, jobOf({ state: "done" })),
      previewThere(),
      send("POST", VOICES_PATH, saved, 201),
    ]);
    const user = await openPage();

    await user.type(within(designer()).getByLabelText("ชื่อเสียง"), "เสียงใหม่");
    await user.click(within(designer()).getByRole("button", { name: "บันทึก" }));

    expect(sent("POST", VOICES_PATH)).toEqual([{ name: "เสียงใหม่" }]);
    expect(screen.getAllByRole("listitem").map((item) => item.getAttribute("aria-label"))).toEqual([
      "เสียงใหม่",
      "ลุงเล่าผี",
    ]);
    expect(within(designer()).queryByLabelText("ชื่อเสียง")).not.toBeInTheDocument();
  });

  it("shows why a name was refused under the field", async () => {
    backend([
      get(CURRENT_PATH, jobOf({ state: "done" })),
      previewThere(),
      send("POST", VOICES_PATH, { code: "invalid_voice", message: "ชื่อเสียงต้องยาว 1–40 ตัวอักษร" }, 400),
    ]);
    const user = await openPage();

    await user.type(within(designer()).getByLabelText("ชื่อเสียง"), "x");
    await user.click(within(designer()).getByRole("button", { name: "บันทึก" }));

    expect(within(designer()).getByText("ชื่อเสียงต้องยาว 1–40 ตัวอักษร")).toBeInTheDocument();
  });

  it("เปลี่ยนชื่อ sends PATCH and shows the new name", async () => {
    backend([
      get(VOICES_PATH, [UNCLE]),
      send("PATCH", `${VOICES_PATH}/v_0000abcd`, { ...UNCLE, name: "ผู้ชายเสียงต่ำ" }, 200),
    ]);
    const user = await openPage();

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "เปลี่ยนชื่อ" }));
    const field = within(row("ลุงเล่าผี")).getByLabelText("ชื่อเสียง");
    await user.clear(field);
    await user.type(field, "ผู้ชายเสียงต่ำ{Enter}");

    expect(sent("PATCH", `${VOICES_PATH}/v_0000abcd`)).toEqual([{ name: "ผู้ชายเสียงต่ำ" }]);
    expect(row("ผู้ชายเสียงต่ำ")).toBeInTheDocument();
  });

  it("Escape leaves the rename without sending", async () => {
    backend([get(VOICES_PATH, [UNCLE])]);
    const user = await openPage();

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "เปลี่ยนชื่อ" }));
    await user.keyboard("{Escape}");

    expect(within(row("ลุงเล่าผี")).queryByLabelText("ชื่อเสียง")).not.toBeInTheDocument();
    expect(sent("PATCH", `${VOICES_PATH}/v_0000abcd`)).toEqual([]);
  });

  it("ลบ asks first, then sends DELETE and drops the row", async () => {
    backend([get(VOICES_PATH, [SISTER, UNCLE]), send("DELETE", `${VOICES_PATH}/v_0000abcd`, null, 204)]);
    const user = await openPage();

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ลบ" }));
    expect(within(row("ลุงเล่าผี")).getByText("ลบเสียง “ลุงเล่าผี”?")).toBeInTheDocument();
    expect(sent("DELETE", `${VOICES_PATH}/v_0000abcd`)).toEqual([]);

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ลบ" }));

    expect(sent("DELETE", `${VOICES_PATH}/v_0000abcd`)).toHaveLength(1);
    expect(screen.queryByRole("listitem", { name: "ลุงเล่าผี" })).not.toBeInTheDocument();
  });

  it("ยกเลิก in the confirm keeps the voice", async () => {
    backend([get(VOICES_PATH, [UNCLE])]);
    const user = await openPage();

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ลบ" }));
    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ยกเลิก" }));

    expect(sent("DELETE", `${VOICES_PATH}/v_0000abcd`)).toEqual([]);
    expect(within(row("ลุงเล่าผี")).getByRole("button", { name: "ฟัง" })).toBeInTheDocument();
  });

  it("keeps สุ่ม disabled, saying why, while a Describe job runs, and frees it when that ends", async () => {
    backend([get(DESCRIBE_PATH, { state: "describing" }), get(DESCRIBE_PATH, { state: "done" })]);
    await openPage();

    expect(within(designer()).getByRole("button", { name: "สุ่ม" })).toBeDisabled();
    expect(within(designer()).getByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();

    await nextPoll();

    expect(within(designer()).getByRole("button", { name: "สุ่ม" })).toBeEnabled();
    expect(within(designer()).queryByText("รอให้งานบรรยายฉากเสร็จก่อน")).not.toBeInTheDocument();
  });

  it("a gpu_busy answer to สุ่ม names the running job", async () => {
    backend([
      send("POST", JOBS_PATH, { code: "gpu_busy", message: "x", running: "transcribe" }, 409),
      get(TRANSCRIBE_PATH, null),
      get(TRANSCRIBE_PATH, { state: "transcribing" }),
    ]);
    const user = await openPage();

    await user.click(within(designer()).getByRole("button", { name: "สุ่ม" }));

    expect(within(designer()).getByText("รอให้งานถอดบทพูดเสร็จก่อน")).toBeInTheDocument();
    expect(within(designer()).getByRole("button", { name: "สุ่ม" })).toBeDisabled();
  });

  it("not_ready names what is missing and links to ติดตั้ง", async () => {
    backend([
      send("POST", JOBS_PATH, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: OmniVoice model", rows: [] }, 503),
    ]);
    const user = await openPage();

    await user.click(within(designer()).getByRole("button", { name: "สุ่ม" }));

    expect(within(designer()).getByRole("alert")).toHaveTextContent("ยังติดตั้งไม่ครบ: OmniVoice model");
    expect(within(designer()).getByRole("link", { name: "ไปหน้าติดตั้ง" })).toHaveAttribute("href", "#/setup");
  });

  it("a design whose model failed says งานหยุดกลางทาง", async () => {
    backend([
      send("POST", JOBS_PATH, jobOf({}), 202),
      get(CURRENT_PATH, null),
      get(CURRENT_PATH, jobOf({ state: "failed", error: { code: "model_failed", message: "x" } })),
    ]);
    const user = await openPage();

    await user.click(within(designer()).getByRole("button", { name: "สุ่ม" }));
    await nextPoll();

    expect(within(designer()).getByRole("alert")).toHaveTextContent("งานหยุดกลางทาง");
    expect(within(designer()).queryByRole("button", { name: "ฟัง" })).not.toBeInTheDocument();
  });

  it("a refused delete stays on the row with the reason", async () => {
    backend([
      get(VOICES_PATH, [UNCLE]),
      send("DELETE", `${VOICES_PATH}/v_0000abcd`, { code: "voice_in_use", message: "เสียงนี้ใช้อยู่ใน Spoil draft" }, 409),
    ]);
    const user = await openPage();

    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ลบ" }));
    await user.click(within(row("ลุงเล่าผี")).getByRole("button", { name: "ลบ" }));

    expect(within(row("ลุงเล่าผี")).getByRole("alert")).toHaveTextContent("เสียงนี้ใช้อยู่ใน Spoil draft");
  });

  it("shows the offline panel when the backend doesn't answer", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    window.location.hash = "#/spoil/voices";
    render(<App />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });
});
