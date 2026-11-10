import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { GPU_JOB_PATHS } from "../../../lib/gpu";
import { FakeXhr } from "../../../testing/fakeXhr";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { RenderJob, RenderResult } from "../lib/render";
import type { Card, Ep } from "../lib/episodes";
import { GENRE_DEFAULTS, type Series } from "../lib/series";
import type { Sound } from "../lib/sounds";

const SERIES_ID = "s_1a2b3c4d";
const EP_ID = "e_5e6f7a8b";
const SOUNDS = "/api/toon/sounds";
const IMPORT = "/api/toon/sounds/import/current";
const RENDER = "/api/toon/render";
const RENDER_JOB = "/api/toon/render/current";
const RENDERS = `/api/toon/eps/${EP_ID}/renders`;

const fetchMock = vi.fn<typeof fetch>();

const rain: Sound = { id: "m_01", name: "ฝนตกในป่า", duration_s: 222, source: "file" };

const series: Series = {
  id: SERIES_ID,
  name: "รุ่นพี่เล่าว่า…",
  channel_name: "รุ่นพี่เล่าว่า",
  layout: "frame",
  genre: "horror",
  voice_id: "v_01",
  name_tags: true,
  ...GENRE_DEFAULTS.horror,
  characters: [],
  backgrounds: [{ id: "b_01", name: "กองไฟในป่า", description: "", ref_rev: 1, pending: 0 }],
};

function cardOf(id: string, change: Partial<Card> = {}): Card {
  return {
    id,
    text: "คืนนั้นเราตั้งแคมป์",
    character_ids: [],
    description: "",
    motion: "still",
    flicker: false,
    hold_s: 0,
    edited: false,
    image_status: "ready",
    audio_status: "no_audio",
    duration_s: 2,
    has_image: true,
    has_previous_image: false,
    ...change,
  };
}

function epOf(cards: Card[], sound: Sound | null = null): Ep {
  return {
    id: EP_ID,
    series_id: SERIES_ID,
    n: 3,
    idea: "ไฟดับ",
    title: "คืนที่ไฟดับ",
    voice_id: "v_01",
    stage: "cards",
    plot: { characters: [], backgrounds: [] },
    acts: [
      {
        id: "a_01",
        name: "เปิด",
        summary: "",
        cards_from: "",
        segments: [{ id: "g_01", background_id: "b_01", sound: sound && { sound_id: sound.id, volume: 30 }, cards }],
      },
    ],
    duration_s: 84,
    locked: false,
  };
}

function renderJob(change: Partial<RenderJob>): RenderJob {
  return {
    kind: "render",
    state: "voicing",
    series_id: SERIES_ID,
    ep_id: EP_ID,
    percent: null,
    done: 0,
    total: 1,
    name: null,
    error: null,
    cancel_requested: false,
    ...change,
  };
}

const clip: RenderResult = {
  name: "20261108-214000",
  title: "คืนที่ไฟดับ",
  n: 3,
  duration_s: 84.2,
  created_at: "2026-11-08T21:40:00+07:00",
  size_bytes: 1000,
};

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [
    ["/api/toon/jobs/current", null],
    [`/api/toon/series/${SERIES_ID}`, series],
    [SOUNDS, [rain]],
    [IMPORT, null],
    [RENDER_JOB, null],
    [RENDERS, []],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

describe("คลังเสียงพื้น", () => {
  it("#/toon/sounds lists the library with each sound's length; the Series list links to it", async () => {
    open("#/toon", [get("/api/toon/series", [])]);
    expect(await screen.findByRole("link", { name: "คลังเสียงพื้น" })).toHaveAttribute("href", "#/toon/sounds");
    act(() => {
      window.location.hash = "#/toon/sounds";
    });

    const row = await screen.findByRole("listitem", { name: "ฝนตกในป่า" });
    expect(row).toHaveTextContent("3:42");
    expect(screen.getByText("เสียงพื้น 1 เสียง")).toBeInTheDocument();
  });

  it("ฟัง plays that sound of the library", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    const user = open("#/toon/sounds", [get(SOUNDS, [rain, { ...rain, id: "m_02", name: "ลมพัด" }])]);

    await user.click(await screen.findByRole("button", { name: "ฟัง ลมพัด" }));

    expect(play).toHaveBeenCalledOnce();
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toMatch(/\/api\/toon\/sounds\/m_02\/file$/);
  });

  it("shows legal item 4 before the file picker and the link field (e2e)", async () => {
    open("#/toon/sounds", []);

    const rights = await screen.findByText(
      "ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด", // legal.md item 4
    );
    const picker = screen.getByLabelText("เลือกไฟล์เสียง");
    const link = screen.getByRole("textbox", { name: /ลิงก์เสียง/ });
    expect(rights.compareDocumentPosition(picker) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(rights.compareDocumentPosition(link) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("a file is checked, sent with its % out, and comes into the list", async () => {
    const user = open("#/toon/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);

    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));

    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(sent(fetchMock, "POST", `${SOUNDS}/imports/check`)).toEqual([{ name: "ลม.wav", size: 3 }]);
    expect(FakeXhr.sent[0].url).toBe(`${SOUNDS}/imports?name=${encodeURIComponent("ลม.wav")}&size=3`);
    FakeXhr.sent[0].progress(1, 2);
    expect(await screen.findByText("50%")).toBeInTheDocument();
    await FakeXhr.sent[0].respond(201, { id: "m_02", name: "ลม", duration_s: 61, source: "file" });
    expect(await screen.findByRole("listitem", { name: "ลม" })).toHaveTextContent("1:01");
  });

  it("ยกเลิก while a file is sent stops it: no notice, nothing comes in", async () => {
    const user = open("#/toon/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);
    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await user.click(screen.getByRole("button", { name: "ยกเลิก" }));

    expect(FakeXhr.sent[0].abort).toHaveBeenCalledOnce();
    await waitFor(() => expect(screen.queryByRole("button", { name: "ยกเลิก" })).not.toBeInTheDocument());
    expect(screen.queryByText("เอาไฟล์ ลม.wav เข้าไม่ได้")).not.toBeInTheDocument();
    expect(screen.queryByRole("listitem", { name: "ลม" })).not.toBeInTheDocument();
  });

  it("a file the check refuses is not sent and says why", async () => {
    const busy = { code: "busy", message: "มีงานเอาเสียงเข้าอยู่" };
    const user = open("#/toon/sounds", [send("POST", `${SOUNDS}/imports/check`, busy, 409)]);

    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));

    expect(await screen.findByText("เอาไฟล์ ลม.wav เข้าไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("มีงานเอาเสียงเข้าอยู่")).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("a link loads with its % and its sound comes in; a refused one says why", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const loading = { url: "https://youtu.be/x", state: "downloading", title: "ลม", percent: 63, error: null, cancel_requested: false, sound_id: null };
    const job = phased(IMPORT, loading, { ...loading, state: "done", percent: 100, sound_id: "m_02" });
    const user = open("#/toon/sounds", [
      send("POST", `${SOUNDS}/downloads`, { code: "invalid_url", message: "ลิงก์นี้ใช้ไม่ได้" }, 400),
      send("POST", `${SOUNDS}/downloads`, loading, 202),
      get(IMPORT, null),
      job.route,
    ]);
    const field = await screen.findByRole("textbox", { name: /ลิงก์เสียง/ });

    await user.type(field, "ftp://x");
    await user.click(screen.getByRole("button", { name: "โหลด" }));
    expect(await screen.findByText("ลิงก์นี้ใช้ไม่ได้")).toBeInTheDocument();

    await user.clear(field);
    await user.type(field, "https://youtu.be/x");
    await user.click(screen.getByRole("button", { name: "โหลด" }));
    expect(await screen.findByText("กำลังโหลด 63%")).toBeInTheDocument();
    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    await waitFor(() => expect(screen.queryByText("กำลังโหลด 63%")).not.toBeInTheDocument());
    expect(sent(fetchMock, "POST", `${SOUNDS}/downloads`)).toEqual([{ url: "ftp://x" }, { url: "https://youtu.be/x" }]);
  });

  it("a sound in use can't be deleted: the EPs that play it show", async () => {
    const inUse = { code: "in_use", message: "ยังมี EP ที่ใช้เสียงนี้อยู่", eps: [{ series_name: "รุ่นพี่เล่าว่า…", n: 3, title: "คืนที่ไฟดับ" }] };
    const user = open("#/toon/sounds", [send("DELETE", `${SOUNDS}/m_01`, inUse, 409)]);

    await user.click(await screen.findByRole("button", { name: "ลบ ฝนตกในป่า" }));

    expect(await screen.findByText("ยังใช้อยู่ใน รุ่นพี่เล่าว่า… EP03 คืนที่ไฟดับ")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: "ฝนตกในป่า" })).toBeInTheDocument();
  });

  it("asks before leaving while a file is sent", async () => {
    const user = open("#/toon/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);
    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);

    act(() => {
      window.location.hash = "#/toon";
    });

    await waitFor(() => expect(confirm).toHaveBeenCalled());
    expect(window.location.hash).toBe("#/toon/sounds");
  });
});

describe("เสียงพื้นของช่วง", () => {
  it("a segment's sound is picked from the library or turned off, and its volume set", async () => {
    const user = open(`#/toon/eps/${EP_ID}`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01")], rain)),
      send("PATCH", `/api/toon/eps/${EP_ID}/segments/g_01`, epOf([cardOf("k_01")]), 200),
    ]);

    const select = await screen.findByRole("combobox", { name: "เสียงพื้นของช่วง 1" });
    expect(select).toHaveValue("m_01");
    expect(screen.getByRole("slider", { name: "ความดังของช่วง 1" })).toHaveValue("30");
    expect(screen.getByRole("link", { name: "ไปหน้า render" })).toHaveAttribute("href", `#/toon/eps/${EP_ID}/render`);

    await user.selectOptions(select, "ไม่มีเสียงพื้น");

    expect(sent(fetchMock, "PATCH", `/api/toon/eps/${EP_ID}/segments/g_01`)).toEqual([{ sound: null }]);
    await waitFor(() => expect(screen.getByRole("slider", { name: "ความดังของช่วง 1" })).toBeDisabled());
  });
});

describe("render และผล", () => {
  it("render shows voicing, then rendering with its %, then the clip in the list (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(
      RENDER_JOB,
      renderJob({ state: "voicing", done: 1, total: 2 }),
      renderJob({ state: "rendering", percent: 64, done: null, total: null }),
      renderJob({ state: "done", percent: 100, name: clip.name }),
    );
    const user = open(`#/toon/eps/${EP_ID}/render`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01"), cardOf("k_02", { audio_status: "ready" })])),
      get(RENDER_JOB, null),
      get(RENDERS, []),
      send("POST", RENDER, renderJob({ total: 2 }), 202),
      job.route,
      get(RENDERS, [clip]),
    ]);

    expect(await screen.findByText(/เสียงเล่าครบ 1\/2 \(ที่ขาดสร้างให้ตอน render\)/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "render" }));
    expect(await screen.findByText("กำลังสร้างเสียงเล่าที่ขาด")).toBeInTheDocument();

    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(await screen.findByText("1/2")).toBeInTheDocument();
    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(await screen.findByText("กำลัง render")).toBeInTheDocument();
    expect(screen.getByText("64%")).toBeInTheDocument();
    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));

    const row = await screen.findByRole("listitem", { name: "ep03-คืนที่ไฟดับ-20261108-214000.mp4" });
    expect(within(row).getByRole("link", { name: "ดาวน์โหลด" })).toHaveAttribute("href", `${RENDERS}/${clip.name}`);
    expect(sent(fetchMock, "POST", RENDER)).toEqual([{ ep_id: EP_ID }]);
  });

  it("cards with no picture keep render off and link to them", async () => {
    open(`#/toon/eps/${EP_ID}/render`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01"), cardOf("k_02", { image_status: "no_image", has_image: false })])),
    ]);

    expect(await screen.findByText("การ์ด 1 ใบยังไม่มีภาพ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "render" })).toBeDisabled();
    expect(screen.getByRole("link", { name: "ไปที่การ์ด 2" })).toHaveAttribute("href", `#/toon/eps/${EP_ID}`);
  });

  it("a clip is deleted from the list", async () => {
    const user = open(`#/toon/eps/${EP_ID}/render`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01")])),
      get(RENDERS, [clip]),
      send("DELETE", `${RENDERS}/${clip.name}`, null, 204),
    ]);

    await user.click(await screen.findByRole("button", { name: "ลบคลิป ep03-คืนที่ไฟดับ-20261108-214000.mp4" }));

    expect(await screen.findByText("ยังไม่มีคลิปของ EP นี้")).toBeInTheDocument();
  });

  it("the Saved voice page waits on a render through its own current", () => {
    expect(GPU_JOB_PATHS.toon_render).toBe("/api/toon/render/current");
  });
});
