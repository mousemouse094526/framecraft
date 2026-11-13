import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { Draft, DraftJob, Sentence, Shot } from "../lib/draft";
import { get, jsonResponse, phased, type Route, send, sent as sentTo, serve } from "../../../testing/testBackend";
import { ALIEN, clipOf, CONAN } from "./setupFixtures";
import { STORIES_PATH, STORY_CLIPS_PATH } from "../../../lib/stories";
import { SOUNDS_PATH, type Sound } from "../../sound-library/lib/sounds";

const DRAFT_PATH = "/api/spoil-maker/draft";
const JOBS_PATH = "/api/spoil-maker/draft-jobs";
const CURRENT_PATH = "/api/spoil-maker/draft-jobs/current";
const VOICE_JOBS = "/api/spoil-maker/voice-jobs";
const VOICE_CURRENT = "/api/spoil-maker/voice-jobs/current";
const RENDERS = "/api/spoil-maker/renders";
const RENDER_CURRENT = "/api/spoil-maker/renders/current";
const SETTINGS_PATH = "/api/spoil-maker/settings";
const EP1 = "aaaaaaaaaaa"; // the draft is of its EP 2, 50–250 s
const RAIN: Sound = { id: "m_0000abcd", name: "ฝนตก", duration_s: 20, source: "file" };
const CRICKETS: Sound = { id: "m_0000ef01", name: "จิ้งหรีด", duration_s: 12, source: "link" };

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
    edited: false,
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
    clip_id: EP1,
    ep: { n: 2, start_s: 50, end_s: 250 },
    clip_title: "Night of the Living Dead",
    style: "fast",
    layout: "A",
    target_s: 30,
    voice_id: "v_0000abcd",
    original_volume: 20,
    top_text: "คดีที่หลอนที่สุด",
    sentences: [sentenceOf("s_00000001"), sentenceOf("s_00000002", { text: "ประโยคสอง" })],
    sound: null,
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
  order: null,
};

function backend(routes: Route[]) {
  const defaults: [string, unknown][] = [
    [DRAFT_PATH, draftOf()],
    [CURRENT_PATH, null],
    [`/api/spoil-maker/clips/${EP1}/shots`, { clip_id: EP1, shots: shotsOf(60) }],
    [VOICE_CURRENT, null],
    [RENDER_CURRENT, null],
    [SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: null }],
    [STORIES_PATH, []],
    [STORY_CLIPS_PATH, {}],
    [SOUNDS_PATH, [RAIN, CRICKETS]],
  ];
  serve(fetchMock, routes, defaults);
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
const sent = (method: string, path: string) => sentTo(fetchMock, method, path);

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
    expect(within(first).getByText("EP 2 · 00:01:40")).toBeInTheDocument();
    expect(within(first).getByText("EP 2 00:01:40")).toBeInTheDocument();
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

  it("a Shot opens the picker on the Shots in the window, and ดูทั้ง EP shows the whole EP", async () => {
    backend([]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));
    const dialog = screen.getByRole("dialog", { name: "เลือกภาพให้ประโยค 1" });

    // 70–134 s: Shots 14 (70–75) to 26 (130–135).
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(13);
    expect(within(dialog).getByText("Shot ภายใน ±30 วินาทีจาก EP 2 00:01:40 · 13 Shot")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "ดูทั้ง EP" }));
    // 50–250 s: Shots 10 (50–55) to 49 (245–250).
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(40);
    expect(within(dialog).getByText("ทุก Shot ของ EP 2 · 40 Shot")).toBeInTheDocument();
    expect(within(dialog).queryByRole("combobox")).not.toBeInTheDocument();
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
    expect(within(dialog).getByText("EP 2 · 00:01:15 – 00:01:20")).toBeInTheDocument();
  });

  it("plays the clip with ?v= from its last trim, so a cached file from before it never plays (spoil D41)", async () => {
    const trimmedAt = "2026-11-05T10:00:00+07:00";
    backend([get(`/api/spoil/clips/${EP1}`, clipOf(EP1, "Night of the Living Dead", { trimmed_at: trimmedAt }))]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));

    const video = screen.getByRole("dialog").querySelector("video");
    expect(video).toHaveAttribute("src", `/api/spoil/clips/${EP1}/video?v=${encodeURIComponent(trimmedAt)}`);
  });

  it("plays the bare path when the clip can't be read (404)", async () => {
    backend([send("GET", `/api/spoil/clips/${EP1}`, { code: "not_found", message: "ไม่พบคลิปนี้" }, 404)]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));

    expect(screen.getByRole("dialog").querySelector("video")).toHaveAttribute("src", `/api/spoil/clips/${EP1}/video`);
  });

  it("a sentence citing no line opens the picker on the whole EP", async () => {
    const inserted = sentenceOf("s_00000001", { refs: [], ref_lines: [], window: null, shots: [null, null], status: "no_shot" });
    backend([get(DRAFT_PATH, draftOf({ sentences: [inserted] }))]);
    const user = await openReview();

    await user.click(within(card(1)).getByRole("button", { name: "เปลี่ยน Shot 1" }));
    const dialog = screen.getByRole("dialog");

    expect(within(dialog).getByRole("button", { name: "ดูทั้ง EP" })).toHaveAttribute("aria-pressed", "true");
    expect(within(dialog).getAllByRole("button", { name: /^Shot / })).toHaveLength(40);
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
    const current = phased(
      RENDER_CURRENT,
      null,
      RENDER,
      { ...RENDER, state: "rendering", percent: 50, done: null, total: null },
      { ...RENDER, state: "done", percent: 100 },
    );
    backend([
      get(DRAFT_PATH, draftOf({ sentences: [readyOf("s_00000001")] })),
      send("POST", RENDERS, RENDER, 202),
      current.route,
      get(RENDERS, []),
    ]);
    const user = await openReview();
    const footer = screen.getByRole("region", { name: "สร้างเสียงและ render" });

    current.phases.at = 1;
    await user.click(within(footer).getByRole("button", { name: "render" }));
    expect(within(footer).getByText("สร้างเสียง 1/3")).toBeInTheDocument();
    current.phases.at = 2;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(within(footer).getByText("render 50%")).toBeInTheDocument();
    current.phases.at = 3;
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

describe("ตรวจแก้บท › เสียงพื้น", () => {
  const picker = () => screen.getByRole("combobox", { name: "เสียงพื้น" });
  const options = () => within(picker()).getAllByRole("option").map((option) => option.textContent);

  it("sits under the original sound: ไม่มีเสียงพื้น first, then the library's sounds", async () => {
    backend([]);
    await openReview();
    await waitFor(() => expect(options()).toEqual(["ไม่มีเสียงพื้น", "ฝนตก", "จิ้งหรีด"]));

    const original = screen.getByRole("slider", { name: "เสียงคลิปต้นฉบับ" });
    expect(original.compareDocumentPosition(picker()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(picker()).toHaveValue("");
    expect(screen.queryByRole("slider", { name: "ความดังเสียงพื้น" })).not.toBeInTheDocument();
  });

  it("choosing a sound sends it without a volume; letting go of the slider sends the volume once", async () => {
    const chosen = draftOf({ sound: { sound_id: RAIN.id, volume: 30 } });
    backend([send("PATCH", DRAFT_PATH, chosen, 200), send("PATCH", DRAFT_PATH, draftOf({ sound: { sound_id: RAIN.id, volume: 45 } }), 200)]);
    const user = await openReview();
    await waitFor(() => expect(options()).toContain("ฝนตก"));

    await user.selectOptions(picker(), "ฝนตก");
    const slider = await screen.findByRole("slider", { name: "ความดังเสียงพื้น" });
    fireEvent.change(slider, { target: { value: "45" } });
    fireEvent.pointerUp(slider);
    fireEvent.blur(slider);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(800);
    });

    expect(sent("PATCH", DRAFT_PATH)).toEqual([{ sound: { sound_id: RAIN.id } }, { sound: { sound_id: RAIN.id, volume: 45 } }]);
    expect(screen.getByRole("button", { name: "ฟัง ฝนตก" })).toBeInTheDocument();
  });

  it("ไม่มีเสียงพื้น sends null", async () => {
    backend([get(DRAFT_PATH, draftOf({ sound: { sound_id: RAIN.id, volume: 30 } })), send("PATCH", DRAFT_PATH, draftOf(), 200)]);
    const user = await openReview();
    await waitFor(() => expect(picker()).toHaveValue(RAIN.id));

    await user.selectOptions(picker(), "ไม่มีเสียงพื้น");

    expect(sent("PATCH", DRAFT_PATH)).toEqual([{ sound: null }]);
  });

  it("an empty library says so with ไปคลังเสียง", async () => {
    backend([get(SOUNDS_PATH, [])]);
    await openReview();

    expect(await screen.findByText("ยังไม่มีเสียงในคลัง")).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "เสียงพื้น" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปคลังเสียง" })).toHaveAttribute("href", "#/sounds?back=#/spoil/review");
  });

  it("ไปคลังเสียง opens the library with ← กลับ, which comes back and reads the sounds again", async () => {
    backend([
      get(SOUNDS_PATH, [RAIN]),
      get(SOUNDS_PATH, [RAIN]),
      get(SOUNDS_PATH, [RAIN, CRICKETS]),
      get("/api/sounds/legacy", { left_behind: null }),
      get("/api/sounds/import/current", null),
    ]);
    const user = await openReview();
    await waitFor(() => expect(options()).toEqual(["ไม่มีเสียงพื้น", "ฝนตก"]));

    await user.click(screen.getByRole("link", { name: "ไปคลังเสียง" }));
    expect(window.location.hash).toBe("#/sounds?back=#/spoil/review");
    await user.click(await screen.findByRole("link", { name: "กลับ" })); // "←" is its icon

    await screen.findByRole("region", { name: "ภาพรวมบท" });
    expect(window.location.hash).toBe("#/spoil/review");
    await waitFor(() => expect(options()).toEqual(["ไม่มีเสียงพื้น", "ฝนตก", "จิ้งหรีด"]));
  });

  it("a sound deleted meanwhile puts the picker back, says so under it and reads the library again", async () => {
    backend([
      send("PATCH", DRAFT_PATH, { code: "sound_not_found", message: "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น" }, 400),
      get(SOUNDS_PATH, [RAIN, CRICKETS]),
      get(SOUNDS_PATH, [CRICKETS]),
    ]);
    const user = await openReview();
    await waitFor(() => expect(options()).toContain("ฝนตก"));

    await user.selectOptions(picker(), "ฝนตก");

    expect(await screen.findByText("เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น")).toBeInTheDocument();
    expect(picker()).toHaveValue("");
    await waitFor(() => expect(options()).toEqual(["ไม่มีเสียงพื้น", "จิ้งหรีด"]));
    expect(screen.getAllByText("เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น")).toHaveLength(1);
  });

  it("a render refused for a sound the library lost says so and reads the draft again", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ sentences: [readyOf("s_00000001")] })),
      send("POST", RENDERS, { code: "sound_not_found", message: "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render" }, 400),
    ]);
    const user = await openReview();
    const draftReads = () => fetchMock.mock.calls.filter(([input, init]) => String(input) === DRAFT_PATH && !init?.method).length;
    const reads = draftReads();

    await user.click(screen.getByRole("button", { name: "render" }));

    expect(await screen.findByText("ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render")).toBeInTheDocument();
    await waitFor(() => expect(draftReads()).toBeGreaterThan(reads));
  });

  it("a refused volume puts the slider back at the draft's", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ sound: { sound_id: RAIN.id, volume: 30 } })),
      send("PATCH", DRAFT_PATH, { code: "draft_locked", message: "รอให้งานที่ใช้ Spoil draft เสร็จก่อนแล้วแก้" }, 409),
    ]);
    await openReview();
    const slider = await screen.findByRole("slider", { name: "ความดังเสียงพื้น" });

    fireEvent.change(slider, { target: { value: "60" } });
    fireEvent.pointerUp(slider);

    expect(await screen.findByText("รอให้งานที่ใช้ Spoil draft เสร็จก่อนแล้วแก้")).toBeInTheDocument();
    expect(screen.getByRole("slider", { name: "ความดังเสียงพื้น" })).toHaveValue("30");
  });

  it("waits while a job changes the draft", async () => {
    backend([get(DRAFT_PATH, draftOf({ locked: true, sound: { sound_id: RAIN.id, volume: 30 } })), get(VOICE_CURRENT, VOICING)]);
    await openReview();
    await waitFor(() => expect(picker()).toHaveValue(RAIN.id));

    expect(picker()).toBeDisabled();
    expect(screen.getByRole("slider", { name: "ความดังเสียงพื้น" })).toBeDisabled();
  });
});

/** Unmounts the page and opens it again, as a reload does. */
function cleanupAndReopen() {
  cleanup();
  render(<App />);
}

describe("ตรวจแก้บท: ลายน้ำเปิดปิด และคำเตือนลายน้ำทับ (D64)", () => {
  const ON_TOP = { text: "@ช่อง", position: "top_center", size: "small", enabled: true };
  const settingsWith = (...watermarks: unknown[]) => ({ watermarks, original_volume: 20, last_voice_id: null });
  const covers = (what = "") => screen.queryByText(new RegExp(`ลายน้ำ 1 อยู่บนกลาง จะทับ ${what}`));

  it("a watermark's switch is sent, and stays where it was set after a reload", async () => {
    let stored: unknown[] = [{ ...ON_TOP, position: "bottom_right" }];
    const routes: Route[] = [
      { path: SETTINGS_PATH, reply: () => jsonResponse(settingsWith(...stored)) },
      {
        method: "PATCH",
        path: SETTINGS_PATH,
        reply: () => {
          stored = JSON.parse(String(fetchMock.mock.calls.at(-1)?.[1]?.body)).watermarks;
          return jsonResponse(settingsWith(...stored));
        },
      },
      { path: SETTINGS_PATH, reply: () => jsonResponse(settingsWith(...stored)) },
    ];
    backend(routes);
    const user = await openReview();
    const row = await screen.findByRole("group", { name: "ลายน้ำ 1" });

    await user.click(within(row).getByRole("switch", { name: "แสดงลายน้ำ 1" }));
    expect(sent("PATCH", SETTINGS_PATH)).toEqual([{ watermarks: [{ ...ON_TOP, position: "bottom_right", enabled: false }] }]);
    cleanupAndReopen();
    await screen.findByRole("region", { name: "ภาพรวมบท" });

    const reloaded = await screen.findByRole("group", { name: "ลายน้ำ 1" });
    expect(within(reloaded).getByRole("switch", { name: "แสดงลายน้ำ 1" })).toHaveAttribute("aria-checked", "false");
  });

  it("a switched-on watermark at บนกลาง warns that it covers the hook of layout A, and render still works", async () => {
    backend([get(SETTINGS_PATH, settingsWith(ON_TOP)), get(DRAFT_PATH, draftOf({ sentences: [readyOf("s_00000001")] }))]);
    await openReview();

    expect(await screen.findByText(/ลายน้ำ 1 อยู่บนกลาง จะทับ Hook ในวิดีโอ/)).toBeInTheDocument();
    const footer = screen.getByRole("region", { name: "สร้างเสียงและ render" });
    expect(within(footer).getByRole("button", { name: "render" })).toBeEnabled();
  });

  it("in layout C it warns that it covers ชื่อตอน", async () => {
    backend([get(SETTINGS_PATH, settingsWith(ON_TOP)), get(DRAFT_PATH, draftOf({ layout: "C", top_text: "ตอนที่ 1" }))]);
    await openReview();

    expect(await screen.findByText(/ลายน้ำ 1 อยู่บนกลาง จะทับ ชื่อตอน ในวิดีโอ/)).toBeInTheDocument();
  });

  it("no warning in layout B, with an empty hook, or for a switched-off watermark", async () => {
    for (const [draft, mark] of [
      [draftOf({ layout: "B", top_text: "" }), ON_TOP],
      [draftOf({ top_text: "  " }), ON_TOP],
      [draftOf(), { ...ON_TOP, enabled: false }],
      [draftOf(), { ...ON_TOP, position: "top_left" }],
    ] as const) {
      backend([get(SETTINGS_PATH, settingsWith(mark)), get(DRAFT_PATH, draft)]);
      await openReview();
      await screen.findByRole("group", { name: "ลายน้ำ 1" });

      expect(covers()).not.toBeInTheDocument();
      cleanup();
      fetchMock.mockReset();
    }
  });

  it("the warning goes at once when the watermark is switched off or moved", async () => {
    const off = { ...ON_TOP, enabled: false };
    const moved = { ...ON_TOP, position: "top_left" };
    backend([
      get(SETTINGS_PATH, settingsWith(ON_TOP)),
      send("PATCH", SETTINGS_PATH, settingsWith(off), 200),
      send("PATCH", SETTINGS_PATH, settingsWith(ON_TOP), 200),
      send("PATCH", SETTINGS_PATH, settingsWith(moved), 200),
    ]);
    const user = await openReview();
    const row = await screen.findByRole("group", { name: "ลายน้ำ 1" });
    expect(covers("Hook")).toBeInTheDocument();

    await user.click(within(row).getByRole("switch", { name: "แสดงลายน้ำ 1" }));
    expect(covers("Hook")).not.toBeInTheDocument();
    await user.click(within(row).getByRole("switch", { name: "แสดงลายน้ำ 1" }));
    expect(covers("Hook")).toBeInTheDocument();
    await user.click(within(row).getByRole("radio", { name: "บนซ้าย" }));
    expect(covers("Hook")).not.toBeInTheDocument();
  });

  it("clearing the hook hides the warning before it is saved", async () => {
    backend([get(SETTINGS_PATH, settingsWith(ON_TOP))]);
    const user = await openReview();
    expect(await screen.findByText(/จะทับ Hook/)).toBeInTheDocument();

    await user.clear(screen.getByRole("textbox", { name: "Hook" }));

    expect(covers("Hook")).not.toBeInTheDocument();
  });
});

const POLISH: DraftJob = { ...PICK, kind: "polish", state: "polishing", done: null, total: null };
const edited = (id: string, change: Partial<Sentence> = {}) => sentenceOf(id, { edited: true, text: "ที่แก้เอง", ...change });

/** The calls made, in order, as "METHOD path". */
const calls = () => fetchMock.mock.calls.map(([input, init]) => `${init?.method ?? "GET"} ${String(input)}`);

async function openPolish(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "เรียบเรียงใหม่" }));
  return screen.getByRole("dialog", { name: "เรียบเรียงบทใหม่" });
}

const HOOK_NOTE = "hook และชื่อตอนไม่ถูกเรียบเรียง แก้เองได้ที่ช่องด้านบน";

describe("ตรวจแก้บท: เรียบเรียงใหม่ กับเรื่องในคลังความรู้ (story-kb D5, D16)", () => {
  it("the clip remembers a Story: the choice says ใช้เรื่อง with its title", async () => {
    backend([get(STORIES_PATH, [ALIEN, CONAN]), get(STORY_CLIPS_PATH, { [EP1]: CONAN.id, other: ALIEN.id })]);
    const user = await openReview();

    const dialog = await openPolish(user);

    expect(await within(dialog).findByText(`ใช้เรื่อง: ${CONAN.title}`)).toBeInTheDocument();
    expect(calls()).toContain(`GET ${STORY_CLIPS_PATH}`);
  });

  it.each([
    ["remembers none", {}],
    ["remembers a Story since deleted", { [EP1]: "st_deadbeef" }],
  ])("the clip %s: the choice says ไม่ได้ใช้เรื่องในคลังความรู้", async (_, clipStories) => {
    backend([get(STORIES_PATH, [CONAN]), get(STORY_CLIPS_PATH, clipStories)]);
    const user = await openReview();

    const dialog = await openPolish(user);

    expect(await within(dialog).findByText("ไม่ได้ใช้เรื่องในคลังความรู้")).toBeInTheDocument();
    expect(within(dialog).queryByText(/ใช้เรื่อง:/)).not.toBeInTheDocument();
  });

  it("the Stories can't be read: no Story line, and เรียบเรียง still works", async () => {
    backend([{ method: "GET", path: STORY_CLIPS_PATH, reply: () => Promise.reject(new TypeError("offline")) }, send("POST", JOBS_PATH, POLISH, 202)]);
    const user = await openReview();

    const dialog = await openPolish(user);
    await waitFor(() => expect(calls()).toContain(`GET ${STORY_CLIPS_PATH}`));

    expect(within(dialog).queryByText(/^ใช้เรื่อง:/)).not.toBeInTheDocument();
    expect(within(dialog).queryByText("ไม่ได้ใช้เรื่องในคลังความรู้")).not.toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));
    await waitFor(() => expect(sent("POST", JOBS_PATH)).toHaveLength(1));
  });

  it.each([
    ["A", true],
    ["C", true],
    ["B", false],
  ] as const)("layout %s: the hook and episode-title note shows: %s", async (layout, shown) => {
    backend([get(DRAFT_PATH, draftOf({ layout, top_text: layout === "B" ? "" : "คดีที่หลอนที่สุด" }))]);
    const user = await openReview();

    const dialog = await openPolish(user);

    expect(within(dialog).queryByText(HOOK_NOTE) !== null).toBe(shown);
  });
});

describe("ตรวจแก้บท: เรียบเรียงใหม่ (D72–D76)", () => {
  it("a sentence the user edited shows แก้เอง, the others don't", async () => {
    backend([get(DRAFT_PATH, draftOf({ sentences: [sentenceOf("s_00000001"), edited("s_00000002")] }))]);
    await openReview();

    expect(within(card(1)).queryByText("แก้เอง")).not.toBeInTheDocument();
    expect(within(card(2)).getByText("แก้เอง")).toBeInTheDocument();
  });

  it("เรียบเรียงใหม่ asks first; เรียบเรียง without the tick reads the draft again and sends include_edited false", async () => {
    const sentences = [readyOf("s_00000001"), edited("s_00000002")];
    backend([get(DRAFT_PATH, draftOf({ sentences })), send("POST", JOBS_PATH, POLISH, 202)]);
    const user = await openReview();

    const dialog = await openPolish(user);
    const tick = within(dialog).getByRole("checkbox", { name: "เรียบเรียงประโยคที่แก้เองด้วย" });
    expect(tick).not.toBeChecked();
    expect(within(dialog).getByText("ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่")).toBeInTheDocument();
    expect(within(dialog).queryByText(/จะถูกเขียนทับ/)).not.toBeInTheDocument();
    const before = calls().length;
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));

    await waitFor(() => expect(sent("POST", JOBS_PATH)).toEqual([{ kind: "polish", include_edited: false }]));
    expect(calls().slice(before)).toContain(`GET ${DRAFT_PATH}`);
    expect(calls().indexOf(`GET ${DRAFT_PATH}`, before)).toBeLessThan(calls().indexOf(`POST ${JOBS_PATH}`));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("ticked, it warns the edited text goes and sends include_edited true", async () => {
    backend([get(DRAFT_PATH, draftOf({ sentences: [sentenceOf("s_00000001"), edited("s_00000002")] })), send("POST", JOBS_PATH, POLISH, 202)]);
    const user = await openReview();

    const dialog = await openPolish(user);
    await user.click(within(dialog).getByRole("checkbox", { name: "เรียบเรียงประโยคที่แก้เองด้วย" }));

    expect(within(dialog).getByText("ข้อความที่แก้เอง 1 ประโยคจะถูกเขียนทับ ย้อนกลับไม่ได้")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));
    await waitFor(() => expect(sent("POST", JOBS_PATH)).toEqual([{ kind: "polish", include_edited: true }]));
  });

  it("with no edited and no voiced sentence there is no tick and no voice warning", async () => {
    backend([]);
    const user = await openReview();

    const dialog = await openPolish(user);

    expect(within(dialog).queryByRole("checkbox")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่")).not.toBeInTheDocument();
  });

  it("every sentence edited and no tick: เรียบเรียง waits for the tick and says why", async () => {
    backend([get(DRAFT_PATH, draftOf({ sentences: [edited("s_00000001"), edited("s_00000002")] }))]);
    const user = await openReview();

    const dialog = await openPolish(user);

    expect(within(dialog).getByRole("button", { name: "เรียบเรียง" })).toBeDisabled();
    expect(within(dialog).getByText("ทุกประโยคแก้เองแล้ว: ติ๊กเพื่อเรียบเรียงทับ")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("checkbox", { name: "เรียบเรียงประโยคที่แก้เองด้วย" }));
    expect(within(dialog).getByRole("button", { name: "เรียบเรียง" })).toBeEnabled();
  });

  it("ยกเลิก closes the choice and sends nothing", async () => {
    backend([]);
    const user = await openReview();

    const dialog = await openPolish(user);
    await user.click(within(dialog).getByRole("button", { name: "ยกเลิก" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([]);
  });

  it("waits for a sentence's save that is still out before it sends", async () => {
    let answer: (response: Response) => void = () => {};
    const saving = new Promise<Response>((resolve) => (answer = resolve));
    backend([
      { method: "PATCH", path: `${DRAFT_PATH}/sentences/s_00000001`, reply: () => saving as unknown as Response },
      send("POST", JOBS_PATH, POLISH, 202),
    ]);
    const user = await openReview();

    await user.type(within(card(1)).getByRole("textbox"), "ใหม่");
    const dialog = await openPolish(user); // the click blurs the text: it saves now
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));
    expect(sent("PATCH", `${DRAFT_PATH}/sentences/s_00000001`)).toHaveLength(1);
    expect(sent("POST", JOBS_PATH)).toEqual([]);

    answer(jsonResponse(draftOf()));
    await waitFor(() => expect(sent("POST", JOBS_PATH)).toHaveLength(1));
  });

  it("a polish running when the page opens says กำลังเรียบเรียง with ยกเลิก, and every text waits", async () => {
    backend([
      get(DRAFT_PATH, draftOf({ locked: true })),
      get(CURRENT_PATH, POLISH),
      send("DELETE", CURRENT_PATH, { ...POLISH, cancel_requested: true }, 202),
    ]);
    const user = await openReview();

    const progress = screen.getByRole("region", { name: "งานที่กำลังทำ" });
    expect(within(progress).getByText("กำลังเรียบเรียง")).toBeInTheDocument();
    expect(within(card(1)).getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "เรียบเรียงใหม่" })).toBeDisabled();
    await user.click(within(progress).getByRole("button", { name: "ยกเลิก" }));

    expect(sent("DELETE", CURRENT_PATH)).toHaveLength(1);
    expect(within(progress).getByText("กำลังยกเลิก…")).toBeInTheDocument();
  });

  it.each([
    [{ ...POLISH, state: "done", done: 2, total: 2 }, "เรียบเรียง 2 ประโยค"],
    [{ ...POLISH, state: "done", done: 0, total: 2 }, "ไม่มีประโยคที่เปลี่ยน"],
    [
      { ...POLISH, state: "failed", error: { code: "polish_failed", message: "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน" } },
      "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน",
    ],
  ])("a polish that ends says how it went: %#", async (ended, text) => {
    const current = phased(CURRENT_PATH, null, ended);
    backend([send("POST", JOBS_PATH, POLISH, 202), current.route]);
    const user = await openReview();

    const dialog = await openPolish(user);
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));
    const progress = await screen.findByRole("region", { name: "งานที่กำลังทำ" });
    expect(within(progress).getByText("กำลังเรียบเรียง")).toBeInTheDocument();
    expect(within(card(1)).getByRole("textbox")).toBeDisabled();
    current.phases.at = 1;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });

    expect(await screen.findByText(text)).toBeInTheDocument();
    expect(within(card(1)).getByRole("textbox")).not.toBeDisabled();
  });

  it("a refused polish shows its reason", async () => {
    const refusal = { code: "nothing_to_polish", message: "ทุกประโยคแก้เองแล้ว ไม่มีอะไรให้เรียบเรียง" };
    backend([send("POST", JOBS_PATH, refusal, 400)]);
    const user = await openReview();

    const dialog = await openPolish(user);
    await user.click(within(dialog).getByRole("button", { name: "เรียบเรียง" }));

    expect(await screen.findByText(refusal.message)).toBeInTheDocument();
  });
});
