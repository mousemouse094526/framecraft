import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { FakeXhr } from "../../../testing/fakeXhr";
import { get, jsonResponse, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Analysis, FoundBar, Song } from "../../drum-notes/lib/songs";
import type { Cover, CoverRenderJob, CoverRenderResult } from "../lib/cover";

const ID = "Ssz69tFTS7Y";
const SONG_PATH = `/api/songs/${ID}`;
const COVER_PATH = `${SONG_PATH}/cover`;
const LISTEN_PATH = `${COVER_PATH}/listen`;
const START_PATH = `${COVER_PATH}/render`;
const RENDERS_PATH = `${COVER_PATH}/renders`;
const RENDER_PATH = "/api/covers/render";
const CANCEL_PATH = `${RENDER_PATH}/cancel`;
const COVER_HASH = `#/songs/${ID}/cover`;
const BACKGROUND_PATH = `${COVER_PATH}/background`;
const RANGE_PATH = `${SONG_PATH}/range`;
const PICK_PATH = `${SONG_PATH}/pick`;

const fetchMock = vi.fn<typeof fetch>();

/** Yellow's 0–30 s pick: the drums come in at 11.5 s, bar 6 (D9, D15). */
const analysis: Analysis = {
  mode: "drums",
  start_s: 0,
  end_s: 30,
  beats: Array.from({ length: 61 }, (_, n) => n / 2),
  downbeats: [0, 2, 4, 6, 8, 10, 12, 14],
  hits: [
    { t: 11.5, piece: "snare", level: "normal" },
    { t: 12, piece: "kick", level: "normal" },
    { t: 13, piece: "snare", level: "accent" },
  ],
  picked_at: "2026-11-15T10:00:00+07:00",
};

const bars: FoundBar[] = analysis.downbeats.slice(0, -1).map((start, index) => ({
  n: index + 1,
  start_s: start,
  end_s: start + 2,
  beats: 4,
  hits: analysis.hits.filter((hit) => start <= hit.t && hit.t < start + 2).length,
  four_four: true,
}));

function songOf(change: Partial<Song> = {}): Song {
  return {
    version: 1,
    id: ID,
    title: "Yellow - Coldplay (Drum Cover)",
    subtitle: "DRUMMATE",
    source: { kind: "link", url: `https://www.youtube.com/watch?v=${ID}`, name: null, size: null },
    duration_s: 266,
    range: { start_s: 0, end_s: 30, mode: "drums" },
    analysis,
    bars,
    lessons: [],
    created_at: "2026-11-15T10:00:00+07:00",
    updated_at: "2026-11-15T10:00:00+07:00",
    ...change,
  };
}

function coverOf(change: Partial<Cover> = {}): Cover {
  return {
    start_s: 10,
    end_s: 30,
    title: "Yellow - Coldplay (Drum Cover)",
    subtitle: "DRUMMATE",
    caption: "",
    background: "color",
    backing: { on: false, volume: 35 },
    saved: true,
    adjusted: false,
    has_audio: true,
    hits: 3,
    length_s: 20,
    suggested_start_s: 10,
    updated_at: "2026-11-15T10:10:00+07:00",
    ...change,
  };
}

function resultOf(change: Partial<CoverRenderResult> = {}): CoverRenderResult {
  return {
    name: "20261115-103000",
    song_id: ID,
    title: "Yellow",
    length_s: 21.5,
    start_s: 10,
    end_s: 30,
    picked_at: analysis.picked_at,
    backing: { on: false, volume: 35 },
    created_at: "2026-11-15T10:30:00+07:00",
    size_bytes: 1000,
    ...change,
  };
}

function jobOf(change: Partial<CoverRenderJob> = {}): CoverRenderJob {
  return { state: "rendering", song_id: ID, title: "Yellow", percent: 0, result: null, error: null, message: null, ...change };
}

/** The PUT body of the cover as the page shows it, with `change`. */
function bodyOf(cover: Cover, change: Record<string, unknown> = {}) {
  const { start_s, end_s, title, subtitle, caption, background, backing } = cover;
  return { start_s, end_s, title, subtitle, caption, background, backing, ...change };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
  vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: () => "blob:wav", revokeObjectURL: () => {} }));
  vi.stubGlobal(
    "Audio",
    class {
      play = () => Promise.resolve();
      pause = () => {};
    },
  );
});

afterEach(() => {
  vi.useRealTimers();
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [
    ["/api/songs", []],
    ["/api/songs/import", null],
    ["/api/songs/pick", null],
    ["/api/drums/render", null],
    [SONG_PATH, songOf()],
    [COVER_PATH, coverOf()],
    [RENDERS_PATH, []],
    [RENDER_PATH, null],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

const button = (name: string | RegExp) => screen.getByRole("button", { name });

describe("หน้าเพลง", () => {
  it("a picked song shows Reel cover above สร้างบทเรียน with its renders counted, and ทำ reel cover opens the reel page (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(RENDERS_PATH, [resultOf(), resultOf({ name: "20261115-104000" })]), send("POST", `${SONG_PATH}/preview`, { groove: { bars: 1, notes: [] }, bpm: 120, dropped: [] }, 200)]);

    const reel = await screen.findByRole("region", { name: "Reel cover" });
    await waitFor(() => expect(reel).toHaveTextContent("ช่วงแกะ 0.0–30.0 วินาที · 3 การตี · render แล้ว 2 ครั้ง"));
    const lesson = screen.getByRole("region", { name: "สร้างบทเรียน" });
    expect(reel.compareDocumentPosition(lesson) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    await user.click(within(reel).getByRole("link", { name: "ทำ reel cover" }));
    expect(window.location.hash).toBe(COVER_HASH);
    expect(await screen.findByRole("heading", { name: "Reel cover" })).toBeInTheDocument();
  });
});

describe("หน้าเพลง หลังแกะ", () => {
  const preview = send("POST", `${SONG_PATH}/preview`, { groove: { bars: 1, notes: [] }, bpm: 120, dropped: [] }, 200);

  it("a pick that found no hit says so above ผลแกะ (e2e)", async () => {
    open(`#/songs/${ID}`, [get(SONG_PATH, songOf({ analysis: { ...analysis, hits: [] }, bars: bars.map((bar) => ({ ...bar, hits: 0 })) })), preview]);
    expect(await screen.findByText("ไม่พบการตีกลองในช่วง 0.0–30.0 วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น")).toBeInTheDocument();
  });

  it("empty first bars say where the first hit is, and เริ่มช่วงที่การตีแรก saves the range from there and picks again (e2e)", async () => {
    const late = analysis.hits.map((hit) => ({ ...hit, t: hit.t - 1 })); // the first at 10.5, inside bar 6 (from 10.0): the range starts at the bar (D9)
    const lateBars = bars.map((bar) => ({ ...bar, hits: late.filter((hit) => bar.start_s <= hit.t && hit.t < bar.end_s).length }));
    const user = open(`#/songs/${ID}`, [
      get(SONG_PATH, songOf({ analysis: { ...analysis, hits: late }, bars: lateBars })),
      preview,
      send("PUT", RANGE_PATH, songOf({ range: { start_s: 10, end_s: 40, mode: "drums" } }), 200),
      send("POST", PICK_PATH, { song_id: ID, state: "preparing", percent: 0, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "2026-11-15T10:00:00+07:00" }, 202),
    ]);

    expect(await screen.findByText("ห้อง 1–5 ไม่มีการตี การตีแรกอยู่ที่ 10.5 วินาที")).toBeInTheDocument();
    await user.click(button("เริ่มช่วงที่การตีแรก"));

    await waitFor(() => expect(sent(fetchMock, "POST", PICK_PATH)).toEqual([{}]));
    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 10, end_s: 40, mode: "drums" }]);
  });

  it("near the song's end the new range is still 4 s: bar 6 (10.0) to the end (13.0) is 3 s, so it starts at 9.0 (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [
      get(SONG_PATH, songOf({ duration_s: 13, analysis: { ...analysis, end_s: 13 }, range: { start_s: 0, end_s: 13, mode: "drums" } })),
      preview,
      send("PUT", RANGE_PATH, songOf(), 200),
      send("POST", PICK_PATH, { song_id: ID, state: "preparing", percent: 0, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "" }, 202),
    ]);
    await user.click(await screen.findByRole("button", { name: "เริ่มช่วงที่การตีแรก" }));
    await waitFor(() => expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 9, end_s: 13, mode: "drums" }]) );
  });

  it("a hit before the first downbeat means the drums are there: no empty-bars line", async () => {
    const early = [{ t: 0.5, piece: "kick" as const, level: "normal" as const }, ...analysis.hits];
    open(`#/songs/${ID}`, [get(SONG_PATH, songOf({ analysis: { ...analysis, downbeats: [1, ...analysis.downbeats.slice(1)], hits: early }, bars: [{ ...bars[0], start_s: 1, hits: 0 }, ...bars.slice(1)] })), preview]);
    expect(await screen.findByRole("region", { name: "Reel cover" })).toBeInTheDocument();
    expect(screen.queryByText(/ไม่มีการตี การตีแรกอยู่ที่/)).not.toBeInTheDocument();
  });
});

describe("หน้า reel", () => {
  it("opens with the saved cover, its hint and the way back to pick another stretch (e2e)", async () => {
    open(COVER_HASH, []);

    expect(await screen.findByRole("spinbutton", { name: "เริ่ม (วินาที)" })).toHaveValue(10);
    expect(screen.getByRole("spinbutton", { name: "จบ (วินาที)" })).toHaveValue(30);
    expect(screen.getByRole("textbox", { name: "หัวเรื่อง" })).toHaveValue("Yellow - Coldplay (Drum Cover)");
    expect(screen.getByText("ค่าตั้งต้นมาจากชื่อคลิปและช่อง แก้เป็นชื่อเพลงและศิลปิน")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "อยากได้ท่อนอื่น? แกะช่วงใหม่ที่หน้าเพลง" })).toHaveAttribute("href", `#/songs/${ID}`);
    expect(screen.getByText("ยังไม่เคย render reel นี้")).toBeInTheDocument();
  });

  it("a song not picked yet asks to pick first (e2e)", async () => {
    open(COVER_HASH, [get(SONG_PATH, songOf({ analysis: null, bars: [] })), send("GET", COVER_PATH, { code: "no_analysis", message: "แกะโน้ตก่อน แล้วกลับมาทำ reel" }, 409)]);

    expect(await screen.findByText("แกะโน้ตก่อน แล้วกลับมาทำ reel")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับไปหน้าเพลง" })).toHaveAttribute("href", `#/songs/${ID}`);
  });

  it("บันทึก PUTs the edited cover, เริ่มที่การตีแรก sets the start, and ฟัง saves first then plays the mix (e2e)", async () => {
    const saved = coverOf({ start_s: 10.5 });
    const user = open(COVER_HASH, [
      get(COVER_PATH, coverOf({ suggested_start_s: 10.5, start_s: 0 })),
      send("PUT", COVER_PATH, coverOf({ title: "Yellow", start_s: 10.5, suggested_start_s: 10.5 }), 200),
      send("PUT", COVER_PATH, saved, 200),
      { method: "POST", path: LISTEN_PATH, reply: () => new Response(new Blob(["RIFF"]), { status: 200, headers: { "Content-Type": "audio/wav" } }) },
    ]);
    const title = await screen.findByRole("textbox", { name: "หัวเรื่อง" });

    await user.clear(title);
    await user.type(title, "Yellow");
    expect(screen.getByText("· ยังไม่บันทึก")).toBeInTheDocument();
    await user.click(button("เริ่มที่การตีแรก"));
    expect(screen.getByRole("spinbutton", { name: "เริ่ม (วินาที)" })).toHaveValue(10.5);
    await user.click(button(/บันทึก/));

    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { title: "Yellow", start_s: 10.5 })]);
    await waitFor(() => expect(screen.queryByText("· ยังไม่บันทึก")).not.toBeInTheDocument());

    await user.type(screen.getByRole("textbox", { name: "คำบรรยายล่าง" }), "x");
    await user.click(button("ฟัง"));
    await waitFor(() => expect(sent(fetchMock, "POST", LISTEN_PATH)).toEqual([{}]));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toHaveLength(2);
  });

  it("กลอง + เพลงต้นฉบับ shows the volume and the warning and saves the backing; a MIDI song can't choose it (e2e)", async () => {
    const user = open(COVER_HASH, [send("PUT", COVER_PATH, coverOf({ backing: { on: true, volume: 35 } }), 200)]);

    await user.click(await screen.findByRole("radio", { name: "กลอง + เพลงต้นฉบับ" }));
    expect(screen.getByRole("spinbutton", { name: "ความดังเพลง" })).toHaveValue(35);
    expect(screen.getByText(/เพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim/)).toBeInTheDocument();
    await user.click(button(/บันทึก/));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { backing: { on: true, volume: 35 } })]);
  });

  it("a song with no audio of its own can't take the backing", async () => {
    open(COVER_HASH, [get(COVER_PATH, coverOf({ has_audio: false }))]);
    expect(await screen.findByRole("radio", { name: "กลอง + เพลงต้นฉบับ" })).toBeDisabled();
    expect(screen.getByText("เพลงจาก MIDI ไม่มีเสียงต้นฉบับ")).toBeInTheDocument();
  });

  it("render reel starts the job, shows its percent, and the new render plays when it is done (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(RENDER_PATH, null, jobOf({ percent: 40 }), jobOf({ state: "done", percent: 100, result: "20261115-110000" }));
    const user = open(COVER_HASH, [
      job.route,
      get(RENDERS_PATH, []),
      get(RENDERS_PATH, [resultOf({ name: "20261115-110000", backing: { on: true, volume: 35 } }), resultOf()]),
      { method: "POST", path: START_PATH, reply: () => ((job.phases.at = 1), jsonResponse(jobOf(), 202)) },
    ]);

    await user.click(await screen.findByRole("button", { name: "render reel" }));

    expect(sent(fetchMock, "POST", START_PATH)).toEqual([{}]);
    const running = await screen.findByRole("group", { name: "งาน render" });
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(running).toHaveTextContent("40%");
    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    const list = await screen.findByRole("list", { name: "ผล render ทั้งหมด" });
    expect(within(list).getAllByRole("listitem")[0]).toHaveTextContent("มีเพลงต้นฉบับ");
    expect(screen.getByLabelText("ผล render 20261115-110000")).toBeInTheDocument();
  });

  it("a render that failed says why and offers ลองอีกครั้ง (e2e)", async () => {
    open(COVER_HASH, [get(RENDER_PATH, jobOf({ state: "failed", error: "ffmpeg_failed", message: "render ไม่สำเร็จ: boom" }))]);

    expect(await screen.findByText("render ไม่สำเร็จ: boom")).toBeInTheDocument();
    expect(button("ลองอีกครั้ง")).toBeEnabled();
  });

  it("a stretch with no hit says so and can't be heard or rendered; a pulled-in stretch says so; an old render is marked (e2e)", async () => {
    open(COVER_HASH, [get(COVER_PATH, coverOf({ start_s: 0, end_s: 10, hits: 0, adjusted: true })), get(RENDERS_PATH, [resultOf({ picked_at: "2026-11-14T00:00:00Z" })])]);

    expect(await screen.findByText("ช่วงนี้ไม่มีการตีกลอง เลื่อนช่วงหรือกด เริ่มที่การตีแรก")).toBeInTheDocument();
    expect(button("ฟัง")).toBeDisabled();
    expect(button("render reel")).toBeDisabled();
    expect(screen.getByText("ช่วงแกะเปลี่ยน ช่วงของ reel ถูกปรับเป็น 0.0–10.0 วินาที")).toBeInTheDocument();
    expect(screen.getByText("· ยังไม่บันทึก")).toBeInTheDocument();
    expect(await screen.findByText("แกะใหม่แล้ว")).toBeInTheDocument();
  });

  it("asks before leaving unsaved, and deletes a render after asking (e2e)", async () => {
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);
    const user = open(COVER_HASH, [get(RENDERS_PATH, [resultOf()]), get(RENDERS_PATH, []), send("DELETE", `${RENDERS_PATH}/20261115-103000`, null, 204)]);

    await user.click(await screen.findByRole("button", { name: "ลบผล render 20261115-103000" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ลบ" }));
    await waitFor(() => expect(sent(fetchMock, "DELETE", `${RENDERS_PATH}/20261115-103000`)).toEqual([null]));
    expect(await screen.findByText("ยังไม่เคย render reel นี้")).toBeInTheDocument();

    await user.type(screen.getByRole("textbox", { name: "คำบรรยายล่าง" }), "x");
    window.location.hash = `#/songs/${ID}`;
    window.dispatchEvent(new HashChangeEvent("hashchange", { oldURL: `http://localhost/${COVER_HASH}`, newURL: `http://localhost/#/songs/${ID}` }));
    expect(confirm).toHaveBeenCalledWith("ออกโดยไม่บันทึก?");
  });

  it("cancels a running render", async () => {
    const user = open(COVER_HASH, [get(RENDER_PATH, jobOf({ percent: 20 })), send("POST", CANCEL_PATH, jobOf({ state: "cancelled" }), 200)]);
    const running = await screen.findByRole("group", { name: "งาน render" });
    await user.click(within(running).getByRole("button", { name: "ยกเลิก" }));
    expect(sent(fetchMock, "POST", CANCEL_PATH)).toEqual([{}]);
    expect(await screen.findByText("ยกเลิก render แล้ว")).toBeInTheDocument();
  });

  it("an empty start box is no number: its rule shows and nothing is saved", async () => {
    const user = open(COVER_HASH, []);
    await user.clear(await screen.findByRole("spinbutton", { name: "เริ่ม (วินาที)" }));
    await user.click(button(/บันทึก/));
    expect(screen.getAllByText("ช่วงต้องยาว 2–90 วินาที และอยู่ในช่วงแกะ").length).toBeGreaterThan(0);
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([]);
  });

  it("กลองล้วน puts a volume the backend would refuse back to the saved one", async () => {
    const user = open(COVER_HASH, [send("PUT", COVER_PATH, coverOf(), 200)]);
    await user.click(await screen.findByRole("radio", { name: "กลอง + เพลงต้นฉบับ" }));
    await user.clear(screen.getByRole("spinbutton", { name: "ความดังเพลง" }));
    await user.click(screen.getByRole("radio", { name: "กลองล้วน" }));
    await user.type(screen.getByRole("textbox", { name: "คำบรรยายล่าง" }), "x");
    await user.click(button(/บันทึก/));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { caption: "x" })]);
  });

  it("the bar strip shows the found bars the stretch takes in", async () => {
    open(COVER_HASH, []);
    const strip = await screen.findByRole("list", { name: "ห้องที่พบ" });
    expect(within(strip).getAllByText(/^ห้อง \d+$/).map((bar) => bar.textContent)).toEqual(["ห้อง 6", "ห้อง 7"]); // 10–30 s: bars from 10.0 and 12.0
  });

  it("a picked picture is checked, PUT as the raw body and shown; ลบภาพ goes back to the app's colours; a refusal shows by the button (e2e)", async () => {
    const pictured = coverOf({ background: "image", updated_at: "2026-11-15T11:00:00+07:00" });
    const user = open(COVER_HASH, [send("POST", `${BACKGROUND_PATH}/check`, { size: 3 }, 200), send("DELETE", BACKGROUND_PATH, coverOf(), 200)]);
    const section = await screen.findByRole("region", { name: "พื้นหลัง" });
    expect(within(section).getByText("ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม")).toBeInTheDocument();

    await user.upload(within(section).getByLabelText("ไฟล์ภาพพื้นหลัง"), new File(["png"], "me.png", { type: "image/png" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect([FakeXhr.sent[0].method, FakeXhr.sent[0].url]).toEqual(["PUT", `${BACKGROUND_PATH}?size=3`]);
    await FakeXhr.sent[0].respond(200, pictured);
    expect(await within(section).findByRole("img", { name: "ภาพพื้นหลัง" })).toHaveAttribute("src", `${COVER_PATH}/background.jpg?v=${encodeURIComponent("2026-11-15T11:00:00+07:00")}`);
    expect(screen.queryByText("· ยังไม่บันทึก")).not.toBeInTheDocument();

    await user.click(within(section).getByRole("button", { name: "ลบภาพ" }));
    expect(await within(section).findByText("สีของแอป")).toBeInTheDocument();
    await user.upload(within(section).getByLabelText("ไฟล์ภาพพื้นหลัง"), new File(["txt"], "a.png", { type: "image/png" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(2));
    await FakeXhr.sent[1].respond(415, { code: "unsupported_image", message: "รับเฉพาะไฟล์ภาพ PNG หรือ JPG" });
    expect(await within(section).findByText("รับเฉพาะไฟล์ภาพ PNG หรือ JPG")).toBeInTheDocument();
  });
});
