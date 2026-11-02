import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { TempClip } from "../../../lib/clips";
import type { DraftJob } from "../lib/draft";
import type { Voice } from "../hooks/useVoices";

const CLIPS_PATH = "/api/spoil/clips";
const VOICES_PATH = "/api/spoil-maker/voices";
const SETTINGS_PATH = "/api/spoil-maker/settings";
const DRAFT_PATH = "/api/spoil-maker/draft";
const JOBS_PATH = "/api/spoil-maker/draft-jobs";
const CURRENT_PATH = "/api/spoil-maker/draft-jobs/current";

function clipOf(id: string, title: string, change: Partial<TempClip> = {}): TempClip {
  return {
    id,
    title,
    channel: "ช่อง",
    source_url: `https://www.youtube.com/watch?v=${id}`,
    duration_s: 1420,
    width: 1920,
    height: 1080,
    orientation: "landscape",
    file_bytes: 1_000_000,
    thumbnail: null,
    downloaded_at: "2026-11-01T10:00:00+07:00",
    yt_dlp_version: "2026.10.26",
    transcribed: true,
    described: true,
    in_draft: false,
    ...change,
  };
}

const EP1 = clipOf("aaaaaaaaaaa", "ไททัน ตอนที่ 1");
const EP2 = clipOf("bbbbbbbbbbb", "ไททัน ตอนที่ 2");
const UNDESCRIBED = clipOf("ccccccccccc", "ไททัน ตอนที่ 3", { described: false });
const UNTRANSCRIBED = clipOf("ddddddddddd", "นางนาก", { transcribed: false, described: false });

const UNCLE: Voice = {
  id: "v_0000abcd",
  name: "ลุงเล่าผี",
  speed: 1,
  chars_per_s: 15,
  created_at: "2026-11-02T10:00:00+07:00",
  in_use: false,
};

function jobOf(change: Partial<DraftJob>): DraftJob {
  return {
    kind: "draft",
    state: "writing",
    done: null,
    total: null,
    error: null,
    cancel_requested: false,
    started_at: "2026-11-02T11:00:00+07:00",
    ...change,
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

type Route = { method?: string; path: string; reply: () => Response };

/** Fake backend: the first matching route answers; one of several for a path answers once, the last keeps answering. */
function backend(routes: Route[]) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  const defaults: [string, unknown][] = [
    [CLIPS_PATH, { clips: [EP1, EP2] }],
    [VOICES_PATH, [UNCLE]],
    [SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: null }],
    [DRAFT_PATH, null],
    [CURRENT_PATH, null],
  ];
  for (const [path, body] of defaults) if (!has(path)) routes.push(get(path, body));
  fetchMock.mockImplementation(async (input, init) => {
    const method = init?.method ?? "GET";
    const url = String(input);
    // Every token count answers by the clips asked, unless a test says otherwise.
    const matches = routes.filter((r) => (r.path === url || (r.path === TOKENS && url.startsWith(TOKENS))) && (r.method ?? "GET") === method);
    if (matches.length === 0) throw new Error(`unexpected ${method} ${url}`);
    const route = matches[0];
    if (matches.length > 1) routes.splice(routes.indexOf(route), 1);
    return route.reply();
  });
}

const TOKENS = "/api/spoil-maker/tokens";
const get = (path: string, body: unknown): Route => ({ path, reply: () => jsonResponse(body) });
const tokens = (total: number): Route => get(TOKENS, { per_clip: {}, total, limit: 32000 });
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

async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
}

async function openSetup() {
  window.location.hash = "#/spoil";
  render(<App />);
  await screen.findByRole("region", { name: "เลือกตอน" });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const draftButton = () => screen.getByRole("button", { name: "ร่างบท" });

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  window.location.hash = "";
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("ตั้งค่าคลิปสปอย", () => {
  it("#/spoil opens the สปอย tab on step 1 with the setup", async () => {
    backend([]);
    await openSetup();

    const steps = screen.getByRole("navigation", { name: "ขั้นของสปอย" });
    expect(within(steps).getByText("เลือกคลิป").closest("[aria-current]")).toHaveAttribute("aria-current", "step");
    expect(screen.getByRole("region", { name: "ตั้งค่า" })).toBeInTheDocument();
  });

  it("numbers the picked clips by episode and moves them", async () => {
    backend([tokens(18_400)]);
    const user = await openSetup();

    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 2" }));
    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));
    expect(within(screen.getByRole("listitem", { name: "ไททัน ตอนที่ 2" })).getByText("ตอน 1")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "เลื่อน ไททัน ตอนที่ 1 ขึ้น" }));

    expect(within(screen.getByRole("listitem", { name: "ไททัน ตอนที่ 1" })).getByText("ตอน 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "เลื่อน ไททัน ตอนที่ 1 ขึ้น" })).toBeDisabled();
    expect(fetchMock.mock.calls.map(([input]) => String(input))).toContain(`${TOKENS}?clip_ids=aaaaaaaaaaa,bbbbbbbbbbb`);
  });

  it("over 32,000 tokens the draft button can't be pressed and the meter says so", async () => {
    backend([tokens(40_000)]);
    const user = await openSetup();

    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));
    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 2" }));

    expect(await screen.findByText("40,000 / 32,000")).toBeInTheDocument();
    expect(screen.getByText("Transcript รวม 40,000 token เกิน 32,000")).toBeInTheDocument();
    expect(draftButton()).toBeDisabled();
  });

  it("a clip not described can't be picked and says why, with a way to the คลิป tab", async () => {
    backend([get(CLIPS_PATH, { clips: [EP1, UNDESCRIBED, UNTRANSCRIBED] })]);
    await openSetup();

    const undescribed = screen.getByRole("listitem", { name: "ไททัน ตอนที่ 3" });
    expect(within(undescribed).getByRole("checkbox")).toBeDisabled();
    expect(within(undescribed).getByText("ยังไม่บรรยายฉาก")).toBeInTheDocument();
    expect(within(undescribed).getByRole("link", { name: "ไปบรรยายฉาก" })).toHaveAttribute("href", "#/clips");
    expect(within(screen.getByRole("listitem", { name: "นางนาก" })).getByText("ยังไม่ถอด")).toBeInTheDocument();
  });

  it("with no clip ready, says so with a link to the clips", async () => {
    backend([get(CLIPS_PATH, { clips: [UNDESCRIBED] })]);
    await openSetup();

    expect(screen.getByText("ยังไม่มีคลิปที่ถอดและบรรยายฉากแล้ว")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปที่รายการคลิป" })).toHaveAttribute("href", "#/clips");
    expect(draftButton()).toBeDisabled();
  });

  it("picking เล่าละครหักมุม picks layout B, and the layout can change to A", async () => {
    backend([]);
    const user = await openSetup();

    await user.click(screen.getByRole("radio", { name: "ปั่นตัดเร็ว" }));
    expect(screen.getByRole("radio", { name: "Layout A" })).toBeChecked();
    await user.click(screen.getByRole("radio", { name: "เล่าละครหักมุม" }));
    expect(screen.getByRole("radio", { name: "Layout B" })).toBeChecked();
    await user.click(screen.getByRole("radio", { name: "Layout A" }));

    expect(screen.getByRole("radio", { name: "Layout A" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "เล่าละครหักมุม" })).toBeChecked();
  });

  it("with no Saved voice, links to the voice page and the draft button can't be pressed", async () => {
    backend([get(VOICES_PATH, []), tokens(100)]);
    const user = await openSetup();

    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));

    expect(screen.getByRole("link", { name: "สร้างเสียงบรรยาย" })).toHaveAttribute("href", "#/spoil/voices");
    expect(draftButton()).toBeDisabled();
  });

  it("starts from the voice of the last draft", async () => {
    const sister = { ...UNCLE, id: "v_1111abcd", name: "พี่สาว" };
    backend([get(VOICES_PATH, [UNCLE, sister]), get(SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: sister.id })]);
    await openSetup();

    expect(screen.getByRole("combobox", { name: "เสียงบรรยาย" })).toHaveValue(sister.id);
  });

  it("ร่างบท sends the order, shows กำลังเขียนบท then กำลังเลือกภาพ x/y, and opens ตรวจแก้บท when done", async () => {
    backend([
      tokens(18_400),
      send("POST", JOBS_PATH, jobOf({}), 202),
      get(CURRENT_PATH, null),
      get(CURRENT_PATH, jobOf({ state: "matching", done: 4, total: 15 })),
      get(CURRENT_PATH, jobOf({ state: "done", done: 15, total: 15 })),
      get(DRAFT_PATH, null),
    ]);
    const user = await openSetup();
    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));
    await screen.findByText("18,400 / 32,000");

    await user.click(draftButton());

    expect(await screen.findByText("กำลังเขียนบท")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ยกเลิก" })).toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([
      { kind: "draft", clip_ids: [EP1.id], style: "drama", layout: "B", target_s: 60, voice_id: UNCLE.id, replace: false },
    ]);
    await nextPoll();
    expect(screen.getByText("กำลังเลือกภาพ")).toBeInTheDocument();
    expect(screen.getByText("4/15")).toBeInTheDocument();
    await nextPoll();
    expect(window.location.hash).toBe("#/spoil/review");
  });

  it("with a Spoil draft there, asks before sending replace: true", async () => {
    backend([get(DRAFT_PATH, { clip_ids: [] }), tokens(100), send("POST", JOBS_PATH, jobOf({}), 202)]);
    const user = await openSetup();
    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));
    await screen.findByText("100 / 32,000");

    await user.click(draftButton());

    expect(screen.getByText("มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม")).toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([]);
    await user.click(screen.getByRole("button", { name: "ร่างทับ" }));
    expect(sent("POST", JOBS_PATH)).toEqual([expect.objectContaining({ replace: true })]);
  });

  it("ยกเลิก while drafting sends DELETE", async () => {
    backend([get(CURRENT_PATH, jobOf({})), send("DELETE", CURRENT_PATH, jobOf({ cancel_requested: true }), 202)]);
    const user = await openSetup();

    await user.click(screen.getByRole("button", { name: "ยกเลิก" }));

    expect(sent("DELETE", CURRENT_PATH)).toHaveLength(1);
    expect(screen.getByText("กำลังยกเลิก…")).toBeInTheDocument();
  });

  it("a failed draft says AI ร่างบทไม่สำเร็จ 3 ครั้ง with ลองอีกครั้ง", async () => {
    backend([
      get(CURRENT_PATH, jobOf({})),
      get(CURRENT_PATH, jobOf({ state: "failed", error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } })),
    ]);
    await openSetup();

    await nextPoll();

    expect(screen.getByText("AI ร่างบทไม่สำเร็จ 3 ครั้ง")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ลองอีกครั้ง" })).toBeInTheDocument();
  });

  it("gpu_busy names the running job", async () => {
    backend([
      tokens(100),
      send("POST", JOBS_PATH, { code: "gpu_busy", message: "รอให้งานบรรยายฉากเสร็จก่อน", running: "describe" }, 409),
    ]);
    const user = await openSetup();
    await user.click(screen.getByRole("checkbox", { name: "เลือก ไททัน ตอนที่ 1" }));
    await screen.findByText("100 / 32,000");

    await user.click(draftButton());

    expect(await screen.findByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();
  });
});
