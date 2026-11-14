import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { OFFLINE_TEXT } from "../../../lib/api";
import { GPU_JOB_PATHS } from "../../../lib/gpu";
import { FakeXhr } from "../../../testing/fakeXhr";
import { findStatusWith } from "../../../testing/statusBox";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { RenderJob, RenderResult } from "../lib/render";
import type { Card, Ep } from "../lib/episodes";
import { GENRE_DEFAULTS, type Series } from "../lib/series";
import type { Sound } from "../../sound-library/lib/sounds";

const SERIES_ID = "s_1a2b3c4d";
const EP_ID = "e_5e6f7a8b";
const SOUNDS = "/api/sounds";
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
    [RENDER_JOB, null],
    [RENDERS, []],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

/** Where the page's own คลังเสียง buttons go; the tab bar's is left out. */
function libraryLinks() {
  return screen
    .getAllByRole("link", { name: "คลังเสียง" })
    .filter((link) => !link.closest("nav"))
    .map((link) => link.getAttribute("href"));
}

describe("คลังเสียงจากการ์ตูนเล่า", () => {
  it("the Series list's คลังเสียง opens the library with a way back to it", async () => {
    open("#/toon", [get("/api/toon/series", [])]);
    await screen.findByRole("heading", { level: 2, name: "การ์ตูนเล่า" });
    expect(libraryLinks()).toEqual(["#/sounds?back=#/toon"]);
    expect(screen.queryByText(/คลังเสียงพื้น/)).not.toBeInTheDocument();
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
    expect(libraryLinks()).toEqual([`#/sounds?back=#/toon/eps/${EP_ID}`]);

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

  it("a refused clip delete says why and the clip stays", async () => {
    const refused = { code: "busy", message: "กำลัง render อยู่" };
    const user = open(`#/toon/eps/${EP_ID}/render`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01")])),
      get(RENDERS, [clip]),
      send("DELETE", `${RENDERS}/${clip.name}`, refused, 409),
    ]);

    const button = `ลบคลิป ep03-คืนที่ไฟดับ-${clip.name}.mp4`;
    await user.click(await screen.findByRole("button", { name: button }));

    // jsdom has no colour: the Alert's Tailwind class is the one sign of its tone.
    expect(await findStatusWith(`ลบคลิป ${clip.name} ไม่ได้`)).toHaveClass("bg-warning-surface");
    expect(screen.getByText(refused.message)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: button })).toBeInTheDocument();
  });

  it("หยุด with no backend says the render didn't stop", async () => {
    const user = open(`#/toon/eps/${EP_ID}/render`, [
      get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01")])),
      get(RENDER_JOB, renderJob({ total: 1 })),
      { method: "DELETE", path: RENDER_JOB, reply: () => Promise.reject(new TypeError("Failed to fetch")) },
    ]);

    await user.click(await screen.findByRole("button", { name: "หยุด" }));

    expect(await findStatusWith("หยุดงานไม่ได้")).toHaveClass("bg-error-surface");
    expect(screen.getByText(OFFLINE_TEXT)).toBeInTheDocument();
  });

  it("a render refused as not now says why as a warning", async () => {
    const busy = { code: "busy", message: "มีงานอื่นทำอยู่" };
    const user = open(`#/toon/eps/${EP_ID}/render`, [get(`/api/toon/eps/${EP_ID}`, epOf([cardOf("k_01")])), send("POST", RENDER, busy, 409)]);

    await user.click(await screen.findByRole("button", { name: "render" }));

    // jsdom has no colour: the Alert's Tailwind class is the one sign of its tone.
    expect(await findStatusWith("ยัง render ไม่ได้")).toHaveClass("bg-warning-surface");
    expect(screen.getByText(busy.message)).toBeInTheDocument();
    expect(sent(fetchMock, "POST", RENDER)).toEqual([{ ep_id: EP_ID }]);
  });

  it("the Saved voice page waits on a render through its own current", () => {
    expect(GPU_JOB_PATHS.toon_render).toBe("/api/toon/render/current");
  });
});
