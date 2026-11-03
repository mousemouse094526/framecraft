import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { Draft, DraftJob, Sentence, Shot } from "../lib/draft";

const DRAFT_PATH = "/api/spoil-maker/draft";
const JOBS_PATH = "/api/spoil-maker/draft-jobs";
const CURRENT_PATH = "/api/spoil-maker/draft-jobs/current";
const VOICE_JOBS = "/api/spoil-maker/voice-jobs";
const VOICE_CURRENT = "/api/spoil-maker/voice-jobs/current";
const RENDERS = "/api/spoil-maker/renders";
const RENDER_CURRENT = "/api/spoil-maker/renders/current";
const SETTINGS_PATH = "/api/spoil-maker/settings";
const EP1 = "aaaaaaaaaaa";
const EP2 = "bbbbbbbbbbb";

/** A Shot every 5 s: Shot n is n × 5 s. */
function shotsOf(count: number): Shot[] {
  return Array.from({ length: count }, (_, n) => ({ n, start: 5 * n, end: 5 * n + 5, description: `Shot ${n} picture.` }));
}

function sentenceOf(id: string, change: Partial<Sentence> = {}): Sentence {
  return {
    id,
    text: "ชายคนหนึ่งตื่นขึ้นมา",
    refs: [{ clip_id: EP1, line: 4 }],
    shots: [
      { clip_id: EP1, n: 20 },
      { clip_id: EP1, n: 21 },
    ],
    audio: null,
    status: "no_audio",
    estimated_s: 4.8,
    ref_lines: [{ clip_id: EP1, line: 4, start: 100, end: 104, text: "Where am I?" }],
    window: { clip_id: EP1, start: 70, end: 134 },
    ...change,
  };
}

function draftOf(change: Partial<Draft> = {}): Draft {
  return {
    clip_ids: [EP1, EP2],
    style: "fast",
    layout: "A",
    target_s: 30,
    voice_id: "v_0000abcd",
    original_volume: 20,
    top_text: "คดีที่หลอนที่สุด",
    sentences: [sentenceOf("s_00000001"), sentenceOf("s_00000002", { text: "ประโยคสอง" })],
    estimated_total_s: 31,
    locked: false,
    ...change,
  };
}

const PICK: DraftJob = {
  kind: "pick",
  state: "matching",
  done: 0,
  total: 1,
  error: null,
  cancel_requested: false,
  started_at: "2026-11-02T11:00:00+07:00",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

type Route = { method?: string; path: string; reply: () => Response };

function backend(routes: Route[]) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  const defaults: [string, unknown][] = [
    [DRAFT_PATH, draftOf()],
    [CURRENT_PATH, null],
    [`/api/spoil-maker/clips/${EP1}/shots`, { clip_id: EP1, shots: shotsOf(60) }],
    [`/api/spoil-maker/clips/${EP2}/shots`, { clip_id: EP2, shots: shotsOf(8) }],
    [VOICE_CURRENT, null],
    [RENDER_CURRENT, null],
    [SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: null }],
  ];
  for (const [path, body] of defaults) if (!has(path)) routes.push(get(path, body));
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

function sent(method: string, path: string): unknown[] {
  return fetchMock.mock.calls
    .filter(([input, init]) => String(input) === path && init?.method === method)
    .map(([, init]) => (init?.body ? JSON.parse(String(init.body)) : null));
}

async function openReview() {
  window.location.hash = "#/spoil/review";
  render(<App />);
  await screen.findByRole("region", { name: "ภาพรวมบท" });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const card = (number: number) => screen.getByRole("listitem", { name: `ประโยค ${number}` });
const shotImages = (element: HTMLElement) => [...element.querySelectorAll("img")].map((img) => img.getAttribute("src"));

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
});

afterEach(() => {
  fetchMock.mockReset();
  window.location.hash = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("ตรวจแก้บท", () => {
  it("without a Spoil draft links to ตั้งค่าคลิปสปอย", async () => {
    backend([get(DRAFT_PATH, null)]);
    window.location.hash = "#/spoil/review";
    render(<App />);

    expect(await screen.findByText("ยังไม่มีบท")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปที่ตั้งค่าคลิปสปอย" })).toHaveAttribute("href", "#/spoil");
  });

  it("shows the hook, the length, and each sentence with its Shots, status and cited line", async () => {
    backend([]);
    await openReview();

    expect(screen.getByRole("textbox", { name: "Hook" })).toHaveValue("คดีที่หลอนที่สุด");
    expect(screen.getByText("ความยาวประมาณ 31 / 30 วินาที · 2 ประโยค")).toBeInTheDocument();
    const first = card(1);
    expect(within(first).getByText("ยังไม่มีเสียง")).toBeInTheDocument();
    expect(within(first).getByText("4.8 วิ")).toBeInTheDocument();
    expect(within(first).getByText("EP1 · 00:01:40")).toBeInTheDocument();
    expect(within(first).getByText("EP1 00:01:40")).toBeInTheDocument();
    expect(within(first).getByText('"Where am I?"')).toBeInTheDocument();
    expect(shotImages(first)).toContain(`/api/spoil-maker/clips/${EP1}/shots/20.jpg`);
  });

  it("warns when the estimate is more than 25% off the target", async () => {
    backend([get(DRAFT_PATH, draftOf({ estimated_total_s: 40 }))]);
    await openReview();

    expect(screen.getByText("ความยาวประมาณ 40 / 30 วินาที · 2 ประโยค").closest("p")).toHaveClass("text-warning");
  });

  it("a no_shot sentence shows เลือก Shot instead of a picture", async () => {
    const empty = sentenceOf("s_00000001", { shots: [null, null], status: "no_shot", refs: [], ref_lines: [], window: null });
    backend([get(DRAFT_PATH, draftOf({ sentences: [empty] }))]);
    await openReview();

    expect(within(card(1)).getByText("ไม่มี Shot")).toBeInTheDocument();
    expect(within(card(1)).getAllByText("เลือก Shot")).toHaveLength(2);
    expect(shotImages(card(1)).some((src) => src?.endsWith(".jpg"))).toBe(false);
  });

  it("edited text is sent on blur and the sentence then needs a new voice", async () => {
    const stale = draftOf({ sentences: [sentenceOf("s_00000001", { text: "ใหม่", status: "stale_audio" })] });
    backend([send("PATCH", `${DRAFT_PATH}/sentences/s_00000001`, stale, 200)]);
    const user = await openReview();
    const field = within(card(1)).getByRole("textbox", { name: "ประโยค 1" });

    // One change, then leave the field: typing key by key could outlast the 800 ms save under a busy run.
    await user.click(field);
    fireEvent.change(field, { target: { value: "ใหม่" } });
    await user.tab();

    expect(await within(card(1)).findByText("ต้องสร้างเสียงใหม่")).toBeInTheDocument();
    expect(sent("PATCH", `${DRAFT_PATH}/sentences/s_00000001`)).toEqual([{ text: "ใหม่" }]);
  });

  it("text saves itself 800 ms after the last key", async () => {
    backend([send("PATCH", `${DRAFT_PATH}/sentences/s_00000002`, draftOf(), 200)]);
    await openReview();

    // One change with no key delays, so the clock is only what the test moves.
    fireEvent.change(within(card(2)).getByRole("textbox"), { target: { value: "ประโยคสอง!" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(700);
    });
    expect(sent("PATCH", `${DRAFT_PATH}/sentences/s_00000002`)).toEqual([]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(200);
    });

    await waitFor(() => expect(sent("PATCH", `${DRAFT_PATH}/sentences/s_00000002`)).toEqual([{ text: "ประโยคสอง!" }]));
  });

  it("ลบ asks first, then sends DELETE", async () => {
    backend([send("DELETE", `${DRAFT_PATH}/sentences/s_00000001`, draftOf({ sentences: [sentenceOf("s_00000002")] }), 200)]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "ลบประโยค 1" }));
    expect(within(card(1)).getByText("ลบประโยคนี้?")).toBeInTheDocument();
    expect(sent("DELETE", `${DRAFT_PATH}/sentences/s_00000001`)).toEqual([]);
    await user.click(within(card(1)).getByRole("button", { name: "ลบ" }));

    expect(sent("DELETE", `${DRAFT_PATH}/sentences/s_00000001`)).toHaveLength(1);
    expect(screen.queryByRole("listitem", { name: "ประโยค 2" })).not.toBeInTheDocument();
  });

  it("แทรกใต้ adds a sentence under this one", async () => {
    const inserted = sentenceOf("s_000000ff", { text: "ประโยคใหม่", refs: [], ref_lines: [], window: null, shots: [null, null], status: "no_shot" });
    const after = draftOf({ sentences: [sentenceOf("s_00000001"), inserted, sentenceOf("s_00000002")] });
    backend([send("POST", `${DRAFT_PATH}/sentences`, after, 201)]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "แทรกใต้" }));

    expect(sent("POST", `${DRAFT_PATH}/sentences`)).toEqual([{ after_id: "s_00000001", text: "ประโยคใหม่" }]);
    expect(await within(card(2)).findByRole("textbox")).toHaveValue("ประโยคใหม่");
  });

  it("a Shot opens the picker on the Shots in the window, and ดูทั้งคลิป shows the whole episode", async () => {
    backend([]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));
    const dialog = screen.getByRole("dialog", { name: "เลือกภาพให้ประโยค 1" });

    // 70–134 s: Shots 14 (70–75) to 26 (130–135).
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(13);
    expect(within(dialog).getByText("Shot ภายใน ±30 วินาทีจาก EP1 00:01:40 · 13 Shot")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "ดูทั้งคลิป" }));
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(60);
    await user.selectOptions(within(dialog).getByRole("combobox", { name: "ตอน" }), EP2);
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(8);
  });

  it("picking a Shot sends both slots and closes the picker", async () => {
    backend([send("PATCH", `${DRAFT_PATH}/sentences/s_00000001`, draftOf(), 200)]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 2" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Shot 00:01:15" }));

    expect(sent("PATCH", `${DRAFT_PATH}/sentences/s_00000001`)).toEqual([
      { shots: [{ clip_id: EP1, n: 20 }, { clip_id: EP1, n: 15 }] },
    ]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("pointing at a Shot shows its description and plays from its start", async () => {
    backend([]);
    const user = await openReview();
    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));
    const dialog = screen.getByRole("dialog");

    await user.hover(within(dialog).getByRole("button", { name: "Shot 00:01:15" }));

    expect(within(dialog).getByRole("tooltip")).toHaveTextContent("Shot 15 picture.");
    expect(dialog.querySelector("video")?.currentTime).toBe(75);
    expect(within(dialog).getByText("EP1 · 00:01:15 – 00:01:20")).toBeInTheDocument();
  });

  it("a sentence citing no line opens the picker on the whole first episode", async () => {
    const inserted = sentenceOf("s_00000001", { refs: [], ref_lines: [], window: null, shots: [null, null], status: "no_shot" });
    backend([get(DRAFT_PATH, draftOf({ sentences: [inserted] }))]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));
    const dialog = screen.getByRole("dialog");

    expect(within(dialog).getByRole("button", { name: "ดูทั้งคลิป" })).toHaveAttribute("aria-pressed", "true");
    expect(within(dialog).getByRole("combobox", { name: "ตอน" })).toHaveValue(EP1);
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(60);
  });

  it("Esc closes the picker", async () => {
    backend([]);
    const user = await openReview();
    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("เลือก Shot ใหม่ runs a pick and every field waits until it ends", async () => {
    backend([
      send("POST", JOBS_PATH, PICK, 202),
      get(CURRENT_PATH, null),
      get(CURRENT_PATH, { ...PICK, state: "done", done: 1 }),
    ]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เลือก Shot ใหม่" }));

    expect(sent("POST", JOBS_PATH)).toEqual([{ kind: "pick", sentence_id: "s_00000001" }]);
    expect(within(card(1)).getByText("AI กำลังเลือก Shot ใหม่")).toBeInTheDocument();
    expect(within(card(2)).getByRole("textbox")).toBeDisabled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(within(card(2)).getByRole("textbox")).not.toBeDisabled();
  });

  it("a pick running when the page opens shows its progress with ยกเลิก", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ locked: true })),
      get(CURRENT_PATH, PICK),
      send("DELETE", CURRENT_PATH, { ...PICK, cancel_requested: true }, 202),
    ]);
    const user = await openReview();

    expect(screen.getByText("AI กำลังเลือก Shot ใหม่")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ยกเลิก" }));

    expect(sent("DELETE", CURRENT_PATH)).toHaveLength(1);
    expect(screen.getByText("กำลังยกเลิก…")).toBeInTheDocument();
  });

  it("a locked draft with a pick running disables every field", async () => {
    backend([get(DRAFT_PATH, draftOf({ locked: true })), get(CURRENT_PATH, PICK)]);
    await openReview();

    expect(screen.getByRole("textbox", { name: "Hook" })).toBeDisabled();
    for (const number of [1, 2]) {
      expect(within(card(number)).getByRole("textbox")).toBeDisabled();
      for (const button of within(card(number)).getAllByRole("button")) expect(button).toBeDisabled();
    }
  });

  it("a sentence citing no line can't ask AI for new Shots", async () => {
    const inserted = sentenceOf("s_00000001", { refs: [], ref_lines: [], window: null });
    backend([get(DRAFT_PATH, draftOf({ sentences: [inserted] }))]);
    await openReview();

    expect(within(card(1)).getByRole("button", { name: "เลือก Shot ใหม่" })).toBeDisabled();
  });

  it("layout B has no text on top; C calls it ชื่อตอน", async () => {
    backend([get(DRAFT_PATH, draftOf({ layout: "B" }))]);
    await openReview();

    expect(screen.queryByRole("textbox", { name: "Hook" })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "ชื่อตอน" })).not.toBeInTheDocument();
  });

  it("a refused change shows its reason", async () => {
    backend([
      send("PATCH", DRAFT_PATH, { code: "invalid_request", message: "ข้อความด้านบนยาวได้ไม่เกิน 40 ตัวอักษร" }, 400),
    ]);
    const user = await openReview();
    const hook = screen.getByRole("textbox", { name: "Hook" });

    await user.click(hook);
    fireEvent.change(hook, { target: { value: "ยาว" } });
    await user.tab();

    expect(await screen.findByText("ข้อความด้านบนยาวได้ไม่เกิน 40 ตัวอักษร")).toBeInTheDocument();
  });
});

const VOICING = { kind: "sentences", state: "voicing", done: 1, total: 3, error: null, cancel_requested: false, started_at: "" };
const RENDER = { kind: "render", state: "voicing", percent: null, done: 1, total: 3, error: null, cancel_requested: false, started_at: "" };
const readyOf = (id: string, change: Partial<Sentence> = {}) =>
  sentenceOf(id, { status: "ready", audio: { tts_text: "x", voice_id: "v_0000abcd", duration_s: 2.5 }, ...change });

describe("ตรวจแก้บท: เสียง ลายน้ำ และ render", () => {
  it("a no_shot sentence disables render and says why", async () => {
    backend([get(DRAFT_PATH, draftOf({ sentences: [sentenceOf("s_00000001", { shots: [null, null], status: "no_shot" })] }))]);
    await openReview();

    expect(screen.getByRole("button", { name: "render" })).toBeDisabled();
    expect(screen.getByText("มี 1 ประโยคที่ไม่มี Shot: เลือก Shot ก่อน render")).toBeInTheDocument();
  });

  it("a locked draft with the Voice job at 1/3 shows its progress with ยกเลิก and every text waits", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ locked: true })),
      get(VOICE_CURRENT, VOICING),
      send("DELETE", VOICE_CURRENT, { ...VOICING, cancel_requested: true }, 202),
    ]);
    const user = await openReview();
    const footer = await screen.findByRole("region", { name: "สร้างเสียงและ render" });

    expect(await within(footer).findByText("สร้างเสียง 1/3")).toBeInTheDocument();
    expect(within(card(1)).getByRole("textbox")).toBeDisabled();
    await user.click(within(footer).getByRole("button", { name: "ยกเลิก" }));
    expect(sent("DELETE", VOICE_CURRENT)).toHaveLength(1);
  });

  it("สร้างเสียงใหม่ voices that sentence; สร้างเสียงทั้งหมด every one that isn't ready", async () => {
    const draft = draftOf({ sentences: [readyOf("s_00000001"), sentenceOf("s_00000002"), sentenceOf("s_00000003", { status: "stale_audio" })] });
    backend([
      get(DRAFT_PATH, draft),
      send("POST", VOICE_JOBS, { ...VOICING, done: 0, total: 1 }, 202),
      send("POST", VOICE_JOBS, { ...VOICING, done: 0, total: 2 }, 202),
      get(VOICE_CURRENT, null),
    ]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "สร้างเสียงใหม่" }));
    expect(sent("POST", VOICE_JOBS)).toEqual([{ kind: "sentences", sentence_ids: ["s_00000001"] }]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    await user.click(await screen.findByRole("button", { name: "สร้างเสียงทั้งหมด" }));
    expect(sent("POST", VOICE_JOBS)[1]).toEqual({ kind: "sentences", sentence_ids: ["s_00000002", "s_00000003"] });
  });

  it("ฟัง plays the sentence's voice, new after each voicing", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    backend([get(DRAFT_PATH, draftOf({ sentences: [readyOf("s_00000001")] }))]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "ฟัง" }));

    expect(play).toHaveBeenCalledOnce();
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toContain("/api/spoil-maker/draft/sentences/s_00000001/audio.wav?v=2.5");
  });

  it("two watermarks added stay after a reload", async () => {
    let stored: unknown[] = [];
    const settings = () => ({ watermarks: stored, original_volume: 20, last_voice_id: null });
    const routes: Route[] = [{ path: SETTINGS_PATH, reply: () => jsonResponse(settings()) }];
    for (let i = 0; i < 2; i++)
      routes.push({
        method: "PATCH",
        path: SETTINGS_PATH,
        reply: () => {
          stored = JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body)).watermarks;
          return jsonResponse(settings());
        },
      });
    routes.push({ path: SETTINGS_PATH, reply: () => jsonResponse(settings()) });
    backend(routes);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "เพิ่มลายน้ำ" }));
    await user.click(await screen.findByRole("button", { name: "เพิ่มลายน้ำ" }));
    expect(await screen.findByRole("group", { name: "ลายน้ำ 2" })).toBeInTheDocument();
    cleanupAndReopen();
    await screen.findByRole("region", { name: "ภาพรวมบท" });

    expect(await screen.findByRole("group", { name: "ลายน้ำ 2" })).toBeInTheDocument();
    expect(screen.getByText("2/6")).toBeInTheDocument();
  });

  it("a watermark's spot and size are sent with it", async () => {
    const mark = { text: "@ช่อง", position: "bottom_right", size: "small" };
    backend([
      get(SETTINGS_PATH, { watermarks: [mark], original_volume: 20, last_voice_id: null }),
      send("PATCH", SETTINGS_PATH, { watermarks: [{ ...mark, position: "top_left" }], original_volume: 20, last_voice_id: null }, 200),
    ]);
    const user = await openReview();
    const row = await screen.findByRole("group", { name: "ลายน้ำ 1" });

    await user.click(within(row).getByRole("radio", { name: "บนซ้าย" }));

    expect(sent("PATCH", SETTINGS_PATH)).toEqual([{ watermarks: [{ ...mark, position: "top_left" }] }]);
    expect(within(row).getByRole("radio", { name: "บนซ้าย" })).toHaveAttribute("aria-checked", "true");
  });

  it("the original sound's level is saved to the draft", async () => {
    backend([send("PATCH", DRAFT_PATH, draftOf({ original_volume: 35 }), 200)]);
    await openReview();

    fireEvent.change(screen.getByRole("slider", { name: "เสียงคลิปต้นฉบับ" }), { target: { value: "35" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });

    expect(sent("PATCH", DRAFT_PATH)).toEqual([{ original_volume: 35 }]);
  });

  it("render voices first, renders, then opens ผล render", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ sentences: [readyOf("s_00000001")] })),
      send("POST", RENDERS, RENDER, 202),
      get(RENDER_CURRENT, null),
      get(RENDER_CURRENT, { ...RENDER, state: "rendering", percent: 50, done: null, total: null }),
      get(RENDER_CURRENT, { ...RENDER, state: "done", percent: 100 }),
      get(RENDERS, []),
    ]);
    const user = await openReview();
    const footer = screen.getByRole("region", { name: "สร้างเสียงและ render" });

    await user.click(within(footer).getByRole("button", { name: "render" }));
    expect(within(footer).getByText("สร้างเสียง 1/3")).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(within(footer).getByText("render 50%")).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    await waitFor(() => expect(window.location.hash).toBe("#/spoil/renders"));
  });

  it("a render that failed in ffmpeg says render ไม่สำเร็จ with ลองอีกครั้ง", async () => {
    const failed = { ...RENDER, state: "failed", error: { code: "ffmpeg_failed", message: "render ไม่สำเร็จ: x" } };
    backend([get(RENDER_CURRENT, { ...RENDER, state: "rendering", percent: 10 }), get(RENDER_CURRENT, failed)]);
    await openReview();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(await screen.findByText("render ไม่สำเร็จ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ลองอีกครั้ง" })).toBeInTheDocument();
  });

  it("an install missing a row links to ติดตั้ง", async () => {
    backend([send("POST", RENDERS, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: Kanit font", rows: ["font_kanit"] }, 503)]);
    const user = await openReview();

    await user.click(screen.getByRole("button", { name: "render" }));

    expect(await screen.findByText(/ยังติดตั้งไม่ครบ: Kanit font/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปหน้าติดตั้ง" })).toHaveAttribute("href", "#/setup");
  });

  it("too little disk says so", async () => {
    backend([send("POST", RENDERS, { code: "disk_full", message: "ที่ว่างดิสก์ไม่ถึง 1 GiB" }, 507)]);
    const user = await openReview();

    await user.click(screen.getByRole("button", { name: "render" }));

    expect(await screen.findByText("ลบ render เก่าในหน้าผล render เพื่อเพิ่มที่ว่าง")).toBeInTheDocument();
  });
});

/** Unmounts the page and opens it again, as a reload does. */
function cleanupAndReopen() {
  cleanup();
  render(<App />);
}
