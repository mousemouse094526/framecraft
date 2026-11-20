import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
/** The song's one page, its reel under ผลแกะ (nav-ia D6). */
const COVER_HASH = `#/covers/${ID}`;
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
  notes: null, // picked before the melody was kept (kalimba-cover D2)
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
    drums: { on: true, volume: 100 },
    backing: { on: false, volume: 35 },
    saved: true,
    adjusted: false,
    has_audio: true,
    hits: 3,
    length_s: 20,
    suggested_start_s: 10,
    updated_at: "2026-11-15T10:10:00+07:00",
    instrument: "drums",
    kalimba: { on: true, volume: 100 },
    notes: 0,
    notes_picked: false,
    transpose: 0,
    dropped: 0,
    bent: 0,
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
    drums: { on: true, volume: 100 },
    backing: { on: false, volume: 35 },
    instrument: "drums",
    kalimba: { on: true, volume: 100 },
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
  const { start_s, end_s, title, subtitle, caption, background, drums, backing, instrument, kalimba } = cover;
  return { start_s, end_s, title, subtitle, caption, background, drums, backing, instrument, kalimba, ...change };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
  vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: () => "blob:wav", revokeObjectURL: () => {} }));
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
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
  it("a picked song has its Reel cover on the same page, its renders counted, and ไปที่ reel takes the page there (e2e)", async () => {
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    const user = open(`#/covers/${ID}`, [get(RENDERS_PATH, [resultOf(), resultOf({ name: "20261115-104000" })])]);

    const reel = await screen.findByRole("region", { name: "Reel cover" });
    await waitFor(() => expect(reel).toHaveTextContent("ช่วงแกะ 0.0–30.0 วินาที · 3 การตี · render แล้ว 2 ครั้ง"));
    expect(within(reel).getByRole("spinbutton", { name: "เริ่ม reel (วินาที)" })).toHaveValue(10);

    await user.click(screen.getByRole("button", { name: "ไปที่ reel" }));
    expect(scroll.mock.contexts[0]).toBe(reel.parentElement);
    expect(window.location.hash).toBe(`#/covers/${ID}`);
  });

  it("แกะโน้ต under a reel not saved asks ออกโดยไม่บันทึก? first; no keeps the reel and picks nothing (nav-ia D14)", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = open(`#/covers/${ID}`, []);
    const title = await screen.findByRole("textbox", { name: "หัวเรื่อง" });
    await user.type(title, " live");

    await user.click(button("แกะโน้ต"));

    expect(confirm).toHaveBeenCalledWith("ออกโดยไม่บันทึก?");
    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([]);
    expect(sent(fetchMock, "POST", PICK_PATH)).toEqual([]);
    expect(title).toHaveValue("Yellow - Coldplay (Drum Cover) live");
  });

  it("a MIDI song's reel has no way back to a ช่วงแกะ it doesn't have", async () => {
    open(`#/covers/${ID}`, [get(SONG_PATH, songOf({ source: { kind: "midi", url: null, name: "rock.mid", size: 300 }, range: null }))]);

    expect(await screen.findByRole("textbox", { name: "หัวเรื่อง" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "ช่วงแกะ" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /แกะช่วงใหม่/ })).not.toBeInTheDocument();
  });

  it("a song gone since its page loaded says so in the reel, not to pick notes", async () => {
    open(`#/covers/${ID}`, [send("GET", COVER_PATH, { code: "not_found", message: "ไม่พบเพลงนี้" }, 404)]);

    expect(await screen.findByText("ไม่พบเพลงนี้")).toBeInTheDocument();
    expect(screen.queryByText("แกะโน้ตก่อน แล้วกลับมาทำ reel")).not.toBeInTheDocument();
  });

  it("an old reel page's hash opens the song's one page (nav-ia D9)", async () => {
    open(`#/songs/${ID}/cover`, []);

    expect(window.location.hash).toBe(`#/covers/${ID}`);
    expect(await screen.findByRole("region", { name: "ช่วงแกะ" })).toBeInTheDocument();
    expect(await screen.findByRole("region", { name: "Reel cover" })).toBeInTheDocument();
  });

  it("a song picked with its melody counts the notes in Reel cover (kalimba-cover D2) (e2e)", async () => {
    const notes = Array.from({ length: 120 }, (_, n) => ({ t: n / 4, pitch: 60 + (n % 12), level: "normal" as const }));
    open(`#/covers/${ID}`, [get(SONG_PATH, songOf({ analysis: { ...analysis, notes } }))]);

    const reel = await screen.findByRole("region", { name: "Reel cover" });
    await waitFor(() => expect(reel).toHaveTextContent("ช่วงแกะ 0.0–30.0 วินาที · 3 การตี · 120 โน้ตทำนอง"));
  });
});

describe("หน้าเพลง หลังแกะ", () => {
  it("a pick that found no hit says so above the reel cover (e2e)", async () => {
    open(`#/covers/${ID}`, [get(SONG_PATH, songOf({ analysis: { ...analysis, hits: [] }, bars: bars.map((bar) => ({ ...bar, hits: 0 })) }))]);
    expect(await screen.findByText("ไม่พบการตีกลองในช่วง 0.0–30.0 วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น")).toBeInTheDocument();
  });

  it("empty first bars say where the first hit is, and เริ่มช่วงที่การตีแรก saves the range from there and picks again (e2e)", async () => {
    const late = analysis.hits.map((hit) => ({ ...hit, t: hit.t - 1 })); // the first at 10.5, inside bar 6 (from 10.0): the range starts at the bar (D9)
    const lateBars = bars.map((bar) => ({ ...bar, hits: late.filter((hit) => bar.start_s <= hit.t && hit.t < bar.end_s).length }));
    const user = open(`#/covers/${ID}`, [
      get(SONG_PATH, songOf({ analysis: { ...analysis, hits: late }, bars: lateBars })),
      send("PUT", RANGE_PATH, songOf({ range: { start_s: 10, end_s: 40, mode: "drums" } }), 200),
      send("POST", PICK_PATH, { song_id: ID, state: "preparing", percent: 0, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "2026-11-15T10:00:00+07:00" }, 202),
    ]);

    expect(await screen.findByText("ห้อง 1–5 ไม่มีการตี การตีแรกอยู่ที่ 10.5 วินาที")).toBeInTheDocument();
    await user.click(button("เริ่มช่วงที่การตีแรก"));

    await waitFor(() => expect(sent(fetchMock, "POST", PICK_PATH)).toEqual([{}]));
    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 10, end_s: 40, mode: "drums" }]);
  });

  it("near the song's end the new range is still 4 s: bar 6 (10.0) to the end (13.0) is 3 s, so it starts at 9.0 (e2e)", async () => {
    const user = open(`#/covers/${ID}`, [
      get(SONG_PATH, songOf({ duration_s: 13, analysis: { ...analysis, end_s: 13 }, range: { start_s: 0, end_s: 13, mode: "drums" } })),
      send("PUT", RANGE_PATH, songOf(), 200),
      send("POST", PICK_PATH, { song_id: ID, state: "preparing", percent: 0, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "" }, 202),
    ]);
    await user.click(await screen.findByRole("button", { name: "เริ่มช่วงที่การตีแรก" }));
    await waitFor(() => expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 9, end_s: 13, mode: "drums" }]) );
  });

  it("a hit before the first downbeat means the drums are there: no empty-bars line", async () => {
    const early = [{ t: 0.5, piece: "kick" as const, level: "normal" as const }, ...analysis.hits];
    open(`#/covers/${ID}`, [get(SONG_PATH, songOf({ analysis: { ...analysis, downbeats: [1, ...analysis.downbeats.slice(1)], hits: early }, bars: [{ ...bars[0], start_s: 1, hits: 0 }, ...bars.slice(1)] }))]);
    expect(await screen.findByRole("region", { name: "Reel cover" })).toBeInTheDocument();
    expect(screen.queryByText(/ไม่มีการตี การตีแรกอยู่ที่/)).not.toBeInTheDocument();
  });
});

describe("หน้า reel", () => {
  it("opens with the saved cover, its hint and the way back to pick another stretch (e2e)", async () => {
    open(COVER_HASH, []);

    expect(await screen.findByRole("spinbutton", { name: "เริ่ม reel (วินาที)" })).toHaveValue(10);
    expect(screen.getByRole("spinbutton", { name: "จบ reel (วินาที)" })).toHaveValue(30);
    expect(screen.getByRole("textbox", { name: "หัวเรื่อง" })).toHaveValue("Yellow - Coldplay (Drum Cover)");
    expect(screen.getByText("ค่าตั้งต้นมาจากชื่อคลิปและช่อง แก้เป็นชื่อเพลงและศิลปิน")).toBeInTheDocument();
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;
    fireEvent.click(screen.getByRole("button", { name: "อยากได้ท่อนอื่น? แกะช่วงใหม่ด้านบน" }));
    expect(scroll.mock.contexts[0]).toBe(screen.getByRole("region", { name: "ช่วงแกะ" }));
    expect(screen.getByText("ยังไม่เคย render reel นี้")).toBeInTheDocument();
  });

  it("a song not picked yet has no reel, only the way to pick (e2e)", async () => {
    open(COVER_HASH, [get(SONG_PATH, songOf({ analysis: null, bars: [] }))]);

    expect(await screen.findByText("ตั้งช่วงแล้วกด แกะโน้ต")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Reel cover" })).not.toBeInTheDocument();
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
    expect(screen.getByRole("spinbutton", { name: "เริ่ม reel (วินาที)" })).toHaveValue(10.5);
    await user.click(button(/บันทึก/));

    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { title: "Yellow", start_s: 10.5 })]);
    await waitFor(() => expect(screen.queryByText("· ยังไม่บันทึก")).not.toBeInTheDocument());

    await user.type(screen.getByRole("textbox", { name: "คำบรรยายล่าง" }), "x");
    await user.click(button("ฟัง reel"));
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

  it("ความดังกลอง at 60 is saved as the drums' volume (e2e)", async () => {
    const user = open(COVER_HASH, [send("PUT", COVER_PATH, coverOf({ drums: { on: true, volume: 60 } }), 200)]);

    // user-event can't drag a range input to a value: set it the way the browser reports a drag.
    fireEvent.change(await screen.findByRole("slider", { name: "ความดังกลอง" }), { target: { value: "60" } });
    expect(screen.getByText("60%")).toBeInTheDocument();
    await user.click(button(/บันทึก/));

    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { drums: { on: true, volume: 60 } })]);
  });

  it("ปิดเสียงกลอง hides the slider; with no backing nothing would play, so ฟัง and render reel wait for it (e2e)", async () => {
    const user = open(COVER_HASH, [send("PUT", COVER_PATH, coverOf({ drums: { on: false, volume: 100 }, backing: { on: true, volume: 35 } }), 200)]);

    await user.click(await screen.findByRole("switch", { name: "ปิดเสียงกลอง" }));

    expect(screen.queryByRole("slider", { name: "ความดังกลอง" })).not.toBeInTheDocument();
    expect(screen.getByText("เปิดเสียงกลองหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง")).toBeInTheDocument();
    expect(button("ฟัง reel")).toBeDisabled();
    expect(button("render reel")).toBeDisabled();

    await user.click(screen.getByRole("radio", { name: "กลอง + เพลงต้นฉบับ" }));
    expect(screen.queryByText("เปิดเสียงกลองหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง")).not.toBeInTheDocument();
    expect(button("ฟัง reel")).toBeEnabled();
    expect(button("render reel")).toBeEnabled();
    await user.click(button(/บันทึก/));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { drums: { on: false, volume: 100 }, backing: { on: true, volume: 35 } })]);
  });

  it("a render's row says when its drums were off or not at full volume (e2e)", async () => {
    open(COVER_HASH, [
      get(RENDERS_PATH, [
        resultOf({ name: "20261115-120000", drums: { on: false, volume: 100 }, backing: { on: true, volume: 35 } }),
        resultOf({ name: "20261115-110000", drums: { on: true, volume: 60 } }),
        resultOf(),
      ]),
    ]);

    const rows = within(await screen.findByRole("list", { name: "ผล render ทั้งหมด" })).getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("ไม่มีเสียงกลอง");
    expect(rows[0]).not.toHaveTextContent("กลอง 100%");
    expect(rows[1]).toHaveTextContent("กลอง 60%");
    expect(rows[2]).not.toHaveTextContent(/ไม่มีเสียงกลอง|กลอง \d+%/);
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
    expect(button("ฟัง reel")).toBeDisabled();
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
    window.location.hash = `#/covers/${ID}`;
    window.dispatchEvent(new HashChangeEvent("hashchange", { oldURL: `http://localhost/${COVER_HASH}`, newURL: `http://localhost/#/covers/${ID}` }));
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
    await user.clear(await screen.findByRole("spinbutton", { name: "เริ่ม reel (วินาที)" }));
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

describe("หน้า reel คาลิมบา", () => {
  /** A song picked with its melody: the stretch's 48 notes moved up 2, 3 dropped and 4 bent (kalimba-cover D4, D14). */
  const arranged = { notes_picked: true, notes: 48, transpose: 2, dropped: 3, bent: 4 };
  const instruments = () => screen.getByRole("radiogroup", { name: "เครื่องดนตรี" });

  it("opens on กลอง; คาลิมบา shows its sound row and how the notes were laid, unsaved, and บันทึก sends it (e2e)", async () => {
    const user = open(COVER_HASH, [get(COVER_PATH, coverOf(arranged)), send("PUT", COVER_PATH, coverOf({ ...arranged, instrument: "kalimba" }), 200)]);

    expect(await within(await screen.findByRole("radiogroup", { name: "เครื่องดนตรี" })).findByRole("radio", { name: "กลอง" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "ปิดเสียงกลอง" })).toBeInTheDocument();
    expect(screen.queryByText(/โน้ตทำนองในช่วง/)).not.toBeInTheDocument();

    await user.click(within(instruments()).getByRole("radio", { name: "คาลิมบา" }));

    expect(screen.getByText("48 โน้ตทำนองในช่วง · ย้ายคีย์ +2 · ตัด 3 โน้ต · ปรับ 4 โน้ตให้เข้าสเกล")).toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "ปิดเสียงคาลิมบา" })).toBeInTheDocument();
    expect(screen.queryByRole("switch", { name: "ปิดเสียงกลอง" })).not.toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "คาลิมบาล้วน" })).toBeChecked();
    expect(screen.getByText("· ยังไม่บันทึก")).toBeInTheDocument();
    await user.click(button(/บันทึก/));

    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { instrument: "kalimba", kalimba: { on: true, volume: 100 } })]);
  });

  it("a melody-only song opens on คาลิมบา with no drum Alerts; with backing the key move is warned of (e2e)", async () => {
    const user = open(COVER_HASH, [
      get(SONG_PATH, songOf({ analysis: { ...analysis, mode: "melody", hits: [] } })),
      get(COVER_PATH, coverOf({ ...arranged, instrument: "kalimba", hits: 0 })),
    ]);

    expect(await within(await screen.findByRole("radiogroup", { name: "เครื่องดนตรี" })).findByRole("radio", { name: "คาลิมบา" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "ปิดเสียงคาลิมบา" })).toBeInTheDocument();
    expect(screen.queryByText(/ช่วงนี้ไม่มีการตีกลอง/)).not.toBeInTheDocument();
    expect(screen.queryByText("เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์")).not.toBeInTheDocument();
    expect(button("ฟัง reel")).toBeEnabled();

    await user.click(screen.getByRole("radio", { name: "คาลิมบา + เพลงต้นฉบับ" }));
    expect(screen.getByText("คาลิมบาย้ายคีย์ +2 เสียงจะไม่ตรงกับเพลงต้นฉบับ")).toBeInTheDocument();
  });

  it("a song picked before notes were kept, or a stretch with none, says so and can't be heard or rendered (e2e)", async () => {
    open(COVER_HASH, [get(COVER_PATH, coverOf({ instrument: "kalimba" }))]);

    expect(await screen.findByText("เพลงนี้แกะก่อนมีคาลิมบา แกะใหม่ด้านบนเพื่อได้โน้ตทำนอง")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ไปที่ช่วงแกะ" })).toBeInTheDocument();
    expect(button("ฟัง reel")).toBeDisabled();
    expect(button("render reel")).toBeDisabled();
  });

  it("a stretch with no notes says so (e2e)", async () => {
    open(COVER_HASH, [get(COVER_PATH, coverOf({ ...arranged, notes: 0, transpose: 0, instrument: "kalimba" }))]);

    expect(await screen.findByText("ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง")).toBeInTheDocument();
    expect(button("ฟัง reel")).toBeDisabled();
    expect(button("render reel")).toBeDisabled();
  });

  it("a MIDI song imported before notes were kept says to import its file again", async () => {
    open(COVER_HASH, [get(SONG_PATH, songOf({ source: { kind: "midi", url: null, name: "yellow.mid", size: 1 } })), get(COVER_PATH, coverOf({ instrument: "kalimba", has_audio: false }))]);

    expect(await screen.findByText("เพลงนี้นำเข้าก่อนมีคาลิมบา นำเข้าไฟล์ MIDI เดิมอีกครั้ง")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปรายการเพลง" })).toHaveAttribute("href", "#/covers");
  });

  it("ความดังคาลิมบา at 60 is saved; ปิดเสียงคาลิมบา with คาลิมบาล้วน would be silent (e2e)", async () => {
    const user = open(COVER_HASH, [get(COVER_PATH, coverOf({ ...arranged, instrument: "kalimba" })), send("PUT", COVER_PATH, coverOf({ ...arranged, instrument: "kalimba", kalimba: { on: true, volume: 60 } }), 200)]);

    fireEvent.change(await screen.findByRole("slider", { name: "ความดังคาลิมบา" }), { target: { value: "60" } });
    await user.click(button(/บันทึก/));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { instrument: "kalimba", kalimba: { on: true, volume: 60 } })]);

    await user.click(screen.getByRole("switch", { name: "ปิดเสียงคาลิมบา" }));
    expect(screen.queryByRole("slider", { name: "ความดังคาลิมบา" })).not.toBeInTheDocument();
    expect(screen.getByText("เปิดเสียงคาลิมบาหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง")).toBeInTheDocument();
    expect(button("ฟัง reel")).toBeDisabled();
    expect(button("render reel")).toBeDisabled();
  });

  it("ฟัง saves first then plays the kalimba's mix (e2e)", async () => {
    const user = open(COVER_HASH, [
      get(COVER_PATH, coverOf(arranged)),
      send("PUT", COVER_PATH, coverOf({ ...arranged, instrument: "kalimba" }), 200),
      { method: "POST", path: LISTEN_PATH, reply: () => new Response(new Blob(["RIFF"]), { status: 200, headers: { "Content-Type": "audio/wav" } }) },
    ]);

    await user.click(await within(await screen.findByRole("radiogroup", { name: "เครื่องดนตรี" })).findByRole("radio", { name: "คาลิมบา" }));
    await user.click(button("ฟัง reel"));

    await waitFor(() => expect(sent(fetchMock, "POST", LISTEN_PATH)).toEqual([{}]));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { instrument: "kalimba" })]);
    expect(await screen.findByRole("button", { name: "หยุดชั่วคราว ฟัง reel" })).toBeEnabled();
  });
  it("render reel on คาลิมบา saves first, shows its percent, and the new render is chosen with its คาลิมบา badge (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(RENDER_PATH, null, jobOf({ percent: 40 }), jobOf({ state: "done", percent: 100, result: "20261116-110000" }));
    const user = open(COVER_HASH, [
      job.route,
      get(COVER_PATH, coverOf(arranged)),
      send("PUT", COVER_PATH, coverOf({ ...arranged, instrument: "kalimba" }), 200),
      get(RENDERS_PATH, [resultOf()]),
      get(RENDERS_PATH, [resultOf({ name: "20261116-110000", instrument: "kalimba" }), resultOf()]),
      { method: "POST", path: START_PATH, reply: () => ((job.phases.at = 1), jsonResponse(jobOf(), 202)) },
    ]);

    await user.click(await within(await screen.findByRole("radiogroup", { name: "เครื่องดนตรี" })).findByRole("radio", { name: "คาลิมบา" }));
    expect(button("render reel")).toBeEnabled();
    await user.click(button("render reel"));

    await waitFor(() => expect(sent(fetchMock, "POST", START_PATH)).toEqual([{}]));
    expect(sent(fetchMock, "PUT", COVER_PATH)).toEqual([bodyOf(coverOf(), { instrument: "kalimba" })]);
    const running = await screen.findByRole("group", { name: "งาน render" });
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(running).toHaveTextContent("40%");
    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    const rows = within(await screen.findByRole("list", { name: "ผล render ทั้งหมด" })).getAllByRole("listitem");
    expect(rows[0]).toHaveAttribute("aria-current", "true");
    expect(rows[0]).toHaveTextContent("คาลิมบา");
    expect(rows[1]).not.toHaveTextContent("คาลิมบา");
    expect(screen.getByLabelText("ผล render 20261116-110000")).toBeInTheDocument();
  });

  it("a kalimba render's row says when the kalimba was off or not at full volume (e2e)", async () => {
    open(COVER_HASH, [
      get(RENDERS_PATH, [
        resultOf({ name: "20261116-120000", instrument: "kalimba", kalimba: { on: false, volume: 100 }, backing: { on: true, volume: 35 } }),
        resultOf({ name: "20261116-110000", instrument: "kalimba", kalimba: { on: true, volume: 60 } }),
      ]),
    ]);

    const rows = within(await screen.findByRole("list", { name: "ผล render ทั้งหมด" })).getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("ไม่มีเสียงคาลิมบา");
    expect(rows[1]).toHaveTextContent("คาลิมบา 60%");
    expect(rows[1]).not.toHaveTextContent("กลอง");
  });

  it("a render refused for no notes says the backend's message (e2e)", async () => {
    const user = open(COVER_HASH, [
      get(COVER_PATH, coverOf({ ...arranged, instrument: "kalimba" })),
      { method: "POST", path: START_PATH, reply: () => jsonResponse({ code: "no_notes", message: "ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง" }, 409) },
    ]);

    await user.click(await screen.findByRole("button", { name: "render reel" }));

    expect(await screen.findByText("ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง")).toBeInTheDocument();
    expect(screen.getByText("ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง").closest("[role=status]")).not.toBeNull();
  });
});
