import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { StatusResponse } from "../../../lib/statusTypes";
import { FakeXhr } from "../../../testing/fakeXhr";
import { findStatusWith } from "../../../testing/statusBox";
import { get, jsonResponse, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Lesson } from "../../../lib/lesson";
import { PREVIEW_DEBOUNCE_MS } from "../hooks/useLessonPreview";
import type { Analysis, FoundBar, PickJob, Preview, Song, SongImport, SongRow } from "../lib/songs";

const ID = "dQw4w9WgXcQ";
const LIST_PATH = "/api/songs";
const IMPORT_PATH = `${LIST_PATH}/import`;
const PICK_PATH = `${LIST_PATH}/pick`;
const LINK_PATH = `${LIST_PATH}/link`;
const CHECK_PATH = `${LIST_PATH}/check`;
const PATH = `${LIST_PATH}/${ID}`;
const RANGE_PATH = `${PATH}/range`;
const SONG_PICK_PATH = `${PATH}/pick`;
const PREVIEW_PATH = `${PATH}/preview`;
const LISTEN_PATH = `${PATH}/listen`;
const SONG_LESSONS_PATH = `${PATH}/lessons`;
const LESSON_ID = "k3v9x0a1b2c4";
const LESSON_PATH = `/api/drums/lessons/${LESSON_ID}`;
const RENDER_PATH = "/api/drums/render";
const YOUTUBE = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";

const fetchMock = vi.fn<typeof fetch>();

function rowOf(change: Partial<SongRow> = {}): SongRow {
  return { id: ID, title: "Smells Like Teen Spirit", subtitle: "Nirvana", source_kind: "link", duration_s: 301.2, analysis: null, lessons: 0, updated_at: "2026-11-14T10:20:00+07:00", ...change };
}

function songOf(change: Partial<Song> = {}): Song {
  return {
    version: 1,
    id: ID,
    title: "Smells Like Teen Spirit",
    subtitle: "Nirvana",
    source: { kind: "link", url: YOUTUBE, name: null, size: null },
    duration_s: 301.2,
    range: { start_s: 0, end_s: 30, mode: "drums" },
    analysis: null,
    bars: [],
    lessons: [],
    created_at: "2026-11-14T10:20:00+07:00",
    updated_at: "2026-11-14T10:20:00+07:00",
    ...change,
  };
}

/** Two bars at 100 BPM (2.4 s each) as a MIDI file's analysis: three hits in the first, one in the second. */
const midiAnalysis: Analysis = {
  mode: "drums",
  start_s: 0,
  end_s: 4.8,
  beats: [0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8],
  downbeats: [0, 2.4, 4.8],
  hits: [
    { t: 0, piece: "kick", level: "accent" },
    { t: 1.2, piece: "snare", level: "accent" },
    { t: 1.8, piece: "hihat_closed", level: "accent" },
    { t: 2.4, piece: "kick", level: "accent" },
  ],
  picked_at: "2026-11-14T10:20:00+07:00",
};

/** The bars of `midiAnalysis` as the API works them out. */
const midiBars: FoundBar[] = [
  { n: 1, start_s: 0, end_s: 2.4, beats: 4, hits: 3, four_four: true },
  { n: 2, start_s: 2.4, end_s: 4.8, beats: 4, hits: 1, four_four: true },
];

/** A picked song: `midiAnalysis` and its bars. */
const picked = { analysis: midiAnalysis, bars: midiBars };

/** What `POST /preview` answers for the first bar: a kick, a hi-hat and a snare with their hands, one hi-hat dropped (D13). */
function previewOf(change: Partial<Preview> = {}): Preview {
  return {
    groove: {
      bars: 1,
      notes: [
        { piece: "kick", step: 0, hand: null, hit: "accent" },
        { piece: "hihat_closed", step: 0, hand: "R", hit: "accent" },
        { piece: "snare", step: 8, hand: "L", hit: "accent" },
      ],
    },
    bpm: 100,
    dropped: [{ piece: "hihat_closed", step: 8 }],
    ...change,
  };
}

/** The lesson `POST /lessons` made, as `GET /api/drums/lessons/{id}` answers it. */
function lessonOf(): Lesson {
  return {
    version: 1,
    id: LESSON_ID,
    title: "Smells Like Teen Spirit",
    subtitle: "Nirvana",
    caption: "",
    bpm: 100,
    background: "color",
    groove: previewOf().groove,
    chapters: [
      { label: "", text: "", focus: [], repeats: 2, speed: 100 },
      { label: "ลองเล่นเอง", text: "", focus: [], repeats: 2, speed: 100 },
    ],
    updated_at: "2026-11-14T10:40:00+07:00",
    length_s: 23.1,
  };
}

function pickOf(change: Partial<PickJob> = {}): PickJob {
  return { song_id: ID, state: "preparing", percent: 0, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "2026-11-14T10:30:00+07:00", ...change };
}

function jobOf(change: Partial<SongImport> = {}): SongImport {
  return { url: YOUTUBE, state: "checking", title: null, percent: null, error: null, cancel_requested: false, song_id: null, started_at: "2026-11-14T10:20:00+07:00", ...change };
}

/** The Status check with the one row a not_ready names: yt-dlp, missing. */
const status: StatusResponse = {
  checked_at: "2026-11-14T10:20:00+07:00",
  ready: false,
  ok_count: 0,
  warning_count: 0,
  missing_count: 1,
  total: 1,
  items: [{ id: "yt_dlp", label: "yt-dlp", status: "missing", detail: "ยังไม่ได้ติดตั้ง", fix: "./setup.sh", fix_kind: "command", license: null }],
};

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
});

afterEach(() => {
  vi.useRealTimers();
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  // A picked song previews its first bar on open: a test that doesn't watch the preview gets a plain one.
  if (!routes.some((route) => route.method === "POST" && route.path === PREVIEW_PATH)) routes.push(send("POST", PREVIEW_PATH, previewOf(), 200));
  // The polls every page makes: the list, the Import and Pick jobs, and, once สร้างบทเรียนกลอง opens the editor, its Render job.
  serve(fetchMock, routes, [
    [LIST_PATH, []],
    [IMPORT_PATH, null],
    [PICK_PATH, null],
    [RENDER_PATH, null],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

const linkBox = () => screen.getByRole("textbox", { name: "ลิงก์เพลง" });
const bringIn = () => screen.getByRole("button", { name: "เอาเพลงเข้า" });

describe("รายการเพลง", () => {
  it("the แกะเพลง tab after สอนกลอง opens #/songs, inviting the first song and saying the song is for notes only (e2e)", async () => {
    const user = open("#/setup", [get("/api/setup/status", status)]);

    await user.click(screen.getByRole("link", { name: "แกะเพลง" }));

    expect(window.location.hash).toBe("#/songs");
    expect(await screen.findByText("ยังไม่มีเพลง วางลิงก์เพลงแรกหรือเลือกไฟล์ด้านบน")).toBeInTheDocument();
    expect(screen.getByText("ใช้เพลงเพื่อแกะโน้ตเท่านั้น เสียงเพลงไม่เข้าคลิป")).toBeInTheDocument();
  });

  it("shows each song's title, subtitle, where it came from, its length, whether it was picked and its lessons", async () => {
    open("#/songs", [get(LIST_PATH, [rowOf({ analysis: { mode: "drums", bars: 12 }, lessons: 2 }), rowOf({ id: "local-0123456789ab", title: "demo", subtitle: "", source_kind: "midi", duration_s: 4.8 })])]);

    const [first, second] = await screen.findAllByRole("listitem");
    expect(within(first).getByRole("link", { name: /Smells Like Teen Spirit/ })).toHaveAttribute("href", `#/songs/${ID}`);
    expect(first).toHaveTextContent("Nirvana");
    expect(first).toHaveTextContent("ลิงก์");
    expect(first).toHaveTextContent("5:01");
    expect(first).toHaveTextContent("แกะแล้ว 12 ห้อง");
    expect(first).toHaveTextContent("2 บทเรียน");
    expect(second).toHaveTextContent("MIDI");
    expect(second).toHaveTextContent("ยังไม่แกะ");
  });

  it("a pasted link POSTs it, shows the job's percent, and the song joins the list when it is done (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(IMPORT_PATH, null, jobOf({ state: "downloading", title: "Smells Like Teen Spirit", percent: 40 }), jobOf({ state: "done", percent: 100, song_id: ID }));
    const user = open("#/songs", [
      get(LIST_PATH, []),
      get(LIST_PATH, [rowOf()]),
      job.route,
      { method: "POST", path: LINK_PATH, reply: () => ((job.phases.at = 1), jsonResponse(jobOf(), 202)) },
    ]);

    await user.type(await screen.findByRole("textbox", { name: "ลิงก์เพลง" }), YOUTUBE);
    await user.click(bringIn());

    expect(sent(fetchMock, "POST", LINK_PATH)).toEqual([{ url: YOUTUBE }]);
    const running = await screen.findByRole("group", { name: "งานเอาเพลงเข้า" });
    expect(running).toHaveTextContent("กำลังเช็คลิงก์…");
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(running).toHaveTextContent("กำลังโหลด 40%");
    expect(within(running).getByRole("button", { name: "ยกเลิก" })).toBeInTheDocument();

    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    const row = await screen.findByRole("listitem");
    expect(row).toHaveTextContent("ลิงก์");
    expect(row).toHaveTextContent("ยังไม่แกะ");
    expect(row).toHaveTextContent("0 บทเรียน");
    expect(screen.queryByRole("group", { name: "งานเอาเพลงเข้า" })).not.toBeInTheDocument();
    expect(linkBox()).toHaveValue("");
  });

  it("a link that is a song already says so and opens that song (e2e)", async () => {
    const user = open("#/songs", [send("POST", LINK_PATH, { song_id: ID }, 200), get(PATH, songOf())]);

    await user.type(await screen.findByRole("textbox", { name: "ลิงก์เพลง" }), YOUTUBE);
    await user.click(bringIn());

    expect(await findStatusWith("เพลงนี้มีอยู่แล้ว")).toBeInTheDocument();
    expect(window.location.hash).toBe(`#/songs/${ID}`);
    expect(await screen.findByRole("heading", { name: "Smells Like Teen Spirit" })).toBeInTheDocument();
  });

  it("a job that fails too_long says the song is over ten minutes (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(IMPORT_PATH, null, jobOf({ state: "failed", error: { code: "too_long", message: "เพลงยาวเกิน 10 นาที" } }));
    const user = open("#/songs", [job.route, { method: "POST", path: LINK_PATH, reply: () => ((job.phases.at = 1), jsonResponse(jobOf(), 202)) }]);

    await user.type(await screen.findByRole("textbox", { name: "ลิงก์เพลง" }), YOUTUBE);
    await user.click(bringIn());
    await act(() => vi.advanceTimersByTimeAsync(1100));

    expect(await findStatusWith("เพลงยาวเกิน 10 นาที")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "งานเอาเพลงเข้า" })).not.toBeInTheDocument();
  });

  it("not_ready shows the fix of the row it names (e2e)", async () => {
    const user = open("#/songs", [
      send("POST", LINK_PATH, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: yt-dlp", rows: ["yt_dlp"] }, 503),
      get("/api/setup/status", status),
    ]);

    await user.type(await screen.findByRole("textbox", { name: "ลิงก์เพลง" }), YOUTUBE);
    await user.click(bringIn());

    expect(await findStatusWith("ยังติดตั้งไม่ครบ: yt-dlp")).toBeInTheDocument();
    expect(await screen.findByText("./setup.sh")).toBeInTheDocument();
  });

  it("a picked file is checked, PUT as the raw body with its percent, then converts, then its song opens (e2e)", async () => {
    const user = open("#/songs", [send("POST", CHECK_PATH, { size: 3 }, 200), get(PATH, songOf({ source: { kind: "file", url: null, name: "song.mp3", size: 3 }, subtitle: "" }))]);
    await screen.findByRole("textbox", { name: "ลิงก์เพลง" });

    await user.upload(screen.getByLabelText("ไฟล์เพลง"), new File([new Uint8Array([1, 2, 3])], "song.mp3", { type: "audio/mpeg" }));

    expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([{ name: "song.mp3", size: 3 }]);
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    const [xhr] = FakeXhr.sent;
    expect([xhr.method, xhr.url, xhr.headers["Content-Type"], xhr.timeout]).toEqual(["PUT", `${LIST_PATH}?name=song.mp3&size=3`, "application/octet-stream", 0]);
    const sending = screen.getByRole("group", { name: "ส่งไฟล์" });
    xhr.progress(1, 3);
    expect(sending).toHaveTextContent("กำลังส่ง 33%");
    xhr.allSent();
    expect(sending).toHaveTextContent("กำลังแปลงเสียง…");

    await xhr.respond(201, songOf({ source: { kind: "file", url: null, name: "song.mp3", size: 3 } }));

    await waitFor(() => expect(window.location.hash).toBe(`#/songs/${ID}`));
    expect(await screen.findByRole("heading", { name: "Smells Like Teen Spirit" })).toBeInTheDocument();
  });

  it("a file dropped on the box goes in the same way (e2e)", async () => {
    open("#/songs", [send("POST", CHECK_PATH, { size: 3 }, 200)]);
    const box = await screen.findByRole("button", { name: /เลือกไฟล์ในเครื่อง/ });
    const file = new File([new Uint8Array(3)], "drop.mp3", { type: "audio/mpeg" });

    fireEvent.drop(box, { dataTransfer: { files: [file], types: ["Files"] } });

    await waitFor(() => expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([{ name: "drop.mp3", size: 3 }]));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(FakeXhr.sent[0].url).toBe(`${LIST_PATH}?name=drop.mp3&size=3`);
  });

  it("a file that is a song already opens that song; a refused file says why (e2e)", async () => {
    const user = open("#/songs", [
      send("POST", CHECK_PATH, { code: "file_too_large", message: "ไฟล์ใหญ่เกิน 200 MB" }, 413),
      send("POST", CHECK_PATH, { song_id: ID }, 200),
      get(PATH, songOf()),
    ]);
    await screen.findByRole("textbox", { name: "ลิงก์เพลง" });

    await user.upload(screen.getByLabelText("ไฟล์เพลง"), new File([new Uint8Array(3)], "big.mp3"));
    expect(await findStatusWith("ไฟล์ใหญ่เกิน 200 MB")).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);

    await user.upload(screen.getByLabelText("ไฟล์เพลง"), new File([new Uint8Array(3)], "song.mp3"));
    expect(await findStatusWith("เพลงนี้มีอยู่แล้ว")).toBeInTheDocument();
    expect(window.location.hash).toBe(`#/songs/${ID}`);
  });

  it("ลบ asks first, saying the lessons stay, then DELETEs (e2e)", async () => {
    const user = open("#/songs", [get(LIST_PATH, [rowOf()]), get(LIST_PATH, []), send("DELETE", PATH, null, 204)]);

    await user.click(await screen.findByRole("button", { name: "ลบ Smells Like Teen Spirit" }));
    const dialog = screen.getByRole("dialog", { name: "ลบ Smells Like Teen Spirit?" });
    expect(dialog).toHaveTextContent("บทเรียนกลองที่สร้างจากเพลงนี้ยังอยู่");
    await user.click(within(dialog).getByRole("button", { name: "ลบ" }));

    expect(await screen.findByText("ยังไม่มีเพลง วางลิงก์เพลงแรกหรือเลือกไฟล์ด้านบน")).toBeInTheDocument();
    expect(sent(fetchMock, "DELETE", PATH)).toEqual([null]);
  });

  it("a refused delete shows the API's message", async () => {
    const user = open("#/songs", [get(LIST_PATH, [rowOf()]), send("DELETE", PATH, { code: "in_use", message: "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่" }, 409)]);

    await user.click(await screen.findByRole("button", { name: "ลบ Smells Like Teen Spirit" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ลบ" }));

    expect(await findStatusWith("ลบไม่ได้เพราะไฟล์ยังเปิดอยู่")).toBeInTheDocument();
  });
});

describe("หน้าเพลง", () => {
  it("a song with audio has one player of its audio.m4a and, unpicked, says to set the range (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf())]);

    const head = await screen.findByRole("region", { name: "เพลง" });
    expect(head).toHaveTextContent("Nirvana");
    expect(head).toHaveTextContent("ลิงก์");
    expect(head).toHaveTextContent("5:01");
    const player = head.querySelector("audio");
    expect(player).toHaveAttribute("controls");
    expect(player).toHaveAttribute("src", `${PATH}/audio.m4a`);
    expect(document.querySelectorAll("audio")).toHaveLength(1);
    expect(screen.getByText("ตั้งช่วงแล้วกด แกะโน้ต")).toBeInTheDocument();
  });

  it("a MIDI song has no player and shows the bars found, each with its start and hits (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf({ source: { kind: "midi", url: null, name: "rock.mid", size: 300 }, subtitle: "", range: null, duration_s: 4.8, ...picked }))]);

    const head = await screen.findByRole("region", { name: "เพลง" });
    expect(head).toHaveTextContent("MIDI");
    expect(document.querySelectorAll("audio")).toHaveLength(0);
    const bars = within(screen.getByRole("list", { name: "ห้องที่พบ" })).getAllByRole("button");
    expect(bars.map((bar) => bar.textContent)).toEqual(["ห้อง 10.0 s3 การตี", "ห้อง 22.4 s1 การตี"]);
    expect(screen.queryByText("ตั้งช่วงแล้วกด แกะโน้ต")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "ช่วงแกะ" })).not.toBeInTheDocument();
  });

  it("pressing a bar moves the player to its start (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(PATH, songOf(picked))]);

    await user.click(within(await screen.findByRole("list", { name: "ห้องที่พบ" })).getByRole("button", { name: "ห้อง 2" }));

    expect(screen.getByRole("region", { name: "เพลง" }).querySelector("audio")?.currentTime).toBe(2.4);
  });

  it("a bar the API marks as not 4/4 is dimmed and can't be pressed (e2e)", async () => {
    const bars: FoundBar[] = [{ ...midiBars[0], beats: 3, four_four: false }, midiBars[1]];
    open(`#/songs/${ID}`, [get(PATH, songOf({ analysis: midiAnalysis, bars }))]);

    const shown = within(await screen.findByRole("list", { name: "ห้องที่พบ" })).getAllByRole("button");
    expect(shown[0]).toBeDisabled();
    expect(shown[0]).toHaveAttribute("title", "ห้องนี้ไม่ใช่ 4/4");
    expect(shown[1]).toBeEnabled();
  });

  it("a song that isn't there says so with a way back", async () => {
    open(`#/songs/${ID}`, [send("GET", PATH, { code: "not_found", message: "ไม่พบเพลงนี้" }, 404)]);

    expect(await screen.findByText("ไม่พบเพลงนี้")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับไปรายการเพลง" })).toHaveAttribute("href", "#/songs");
  });
});

describe("ช่วงแกะและแกะโน้ต", () => {
  const startBox = () => screen.getByRole("spinbutton", { name: "เริ่ม (วินาที)" });
  const endBox = () => screen.getByRole("spinbutton", { name: "จบ (วินาที)" });
  const pickButton = () => screen.getByRole("button", { name: "แกะโน้ต" });

  it("the fields start from the saved range, say the length against the cap of 90, and take the player's time (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(PATH, songOf({ range: { start_s: 10, end_s: 40, mode: "drums" } }))]);

    const section = await screen.findByRole("region", { name: "ช่วงแกะ" });
    expect(startBox()).toHaveValue(10);
    expect(endBox()).toHaveValue(40);
    expect(section).toHaveTextContent("ยาว 30.0 s (ไม่เกิน 90 วินาที)");
    const player = screen.getByRole("region", { name: "เพลง" }).querySelector("audio") as HTMLAudioElement;
    player.currentTime = 12.34;
    await user.click(screen.getByRole("button", { name: "ใช้เวลาที่เล่นอยู่เป็นเริ่ม (วินาที)" }));
    expect(startBox()).toHaveValue(12.3);
    player.currentTime = 70;
    await user.click(screen.getByRole("button", { name: "ใช้เวลาที่เล่นอยู่เป็นจบ (วินาที)" }));
    expect(endBox()).toHaveValue(70);
    expect(section).toHaveTextContent("ยาว 57.7 s (ไม่เกิน 90 วินาที)");
    expect(within(section).getByRole("radio", { name: "กลอง" })).toHaveAttribute("aria-checked", "true");
    expect(within(section).getByRole("radio", { name: "ทำนอง" })).toBeEnabled();
  });

  it("a range that breaks a rule shows the message at its field and asks the backend nothing (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(PATH, songOf())]);
    await screen.findByRole("region", { name: "ช่วงแกะ" });

    await user.clear(endBox());
    await user.type(endBox(), "2");
    await user.click(pickButton());

    expect(screen.getByText("ช่วงต้องยาว 4–90 วินาที และอยู่ในเพลง")).toBeInTheDocument();
    expect(endBox()).toHaveAttribute("aria-invalid", "true");
    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([]);
    await user.clear(startBox());
    await user.type(startBox(), "-1");
    expect(startBox()).toHaveAttribute("aria-invalid", "true");
  });

  it("แกะโน้ต saves the range, starts the job, shows its bar and ยกเลิก, then the bars found (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(PICK_PATH, null, pickOf({ state: "picking", percent: 50 }), pickOf({ state: "done", percent: 100 }));
    const user = open(`#/songs/${ID}`, [
      get(PATH, songOf()),
      get(PATH, songOf({ range: { start_s: 5, end_s: 35, mode: "drums" }, ...picked })),
      send("PUT", RANGE_PATH, songOf({ range: { start_s: 5, end_s: 35, mode: "drums" } }), 200),
      { method: "POST", path: SONG_PICK_PATH, reply: () => ((job.phases.at = 1), jsonResponse(pickOf(), 202)) },
      job.route,
    ]);
    await screen.findByRole("region", { name: "ช่วงแกะ" });
    await user.clear(startBox());
    await user.type(startBox(), "5");
    await user.clear(endBox());
    await user.type(endBox(), "35");

    await user.click(pickButton());

    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 5, end_s: 35, mode: "drums" }]);
    expect(sent(fetchMock, "POST", SONG_PICK_PATH)).toEqual([{}]);
    const running = await screen.findByRole("group", { name: "งานแกะโน้ต" });
    expect(running).toHaveTextContent("กำลังเตรียมเสียง…");
    expect(within(running).getByRole("button", { name: "ยกเลิก" })).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(running).toHaveTextContent("กำลังแกะโน้ต… 50%");
    expect(within(running).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");

    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(await screen.findByRole("region", { name: "ผลแกะ" })).toHaveTextContent("ห้องที่พบ 2 ห้อง · โหมดกลอง");
    expect(within(screen.getByRole("list", { name: "ห้องที่พบ" })).getAllByRole("button")).toHaveLength(2);
    expect(screen.queryByRole("group", { name: "งานแกะโน้ต" })).not.toBeInTheDocument();
    expect(pickButton()).toBeEnabled();
  });

  it("ทำนอง can be pressed and says what it does; แกะโน้ต saves mode melody, the result names the mode, and the grid has the kick and hi-hat the app adds (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // The page reads only an analysis's mode and the bars the API made of it, so the MIDI one's beats serve with melody hits.
    const melody: Analysis = { ...midiAnalysis, mode: "melody", hits: [{ t: 0.6, piece: "snare", level: "normal" }, { t: 1.2, piece: "snare", level: "normal" }] };
    const base: Preview["groove"]["notes"] = [
      ...[0, 8].map((step) => ({ piece: "kick", step, hand: null, hit: "normal" }) as const),
      ...[0, 2, 4, 6, 8, 10, 12, 14].map((step) => ({ piece: "hihat_closed", step, hand: "R", hit: "normal" }) as const),
    ];
    const snares: Preview["groove"]["notes"] = [4, 8].map((step) => ({ piece: "snare", step, hand: "L", hit: "normal" }) as const);
    const job = phased(PICK_PATH, null, pickOf({ state: "done", percent: 100 }));
    const user = open(`#/songs/${ID}`, [
      get(PATH, songOf()),
      get(PATH, songOf({ range: { start_s: 0, end_s: 30, mode: "melody" }, analysis: melody, bars: midiBars })),
      send("PUT", RANGE_PATH, songOf({ range: { start_s: 0, end_s: 30, mode: "melody" } }), 200),
      { method: "POST", path: SONG_PICK_PATH, reply: () => ((job.phases.at = 1), jsonResponse(pickOf(), 202)) },
      job.route,
      send("POST", PREVIEW_PATH, previewOf({ groove: { bars: 1, notes: [...base, ...snares] }, bpm: 100, dropped: [] }), 200),
    ]);
    const section = await screen.findByRole("region", { name: "ช่วงแกะ" });
    expect(section).not.toHaveTextContent("แกะจังหวะของโน้ตทำนอง");

    await user.click(within(section).getByRole("radio", { name: "ทำนอง" }));

    expect(within(section).getByRole("radio", { name: "ทำนอง" })).toHaveAttribute("aria-checked", "true");
    expect(section).toHaveTextContent("แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน");
    await user.click(pickButton());
    expect(sent(fetchMock, "PUT", RANGE_PATH)).toEqual([{ start_s: 0, end_s: 30, mode: "melody" }]);
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(await screen.findByRole("region", { name: "ผลแกะ" })).toHaveTextContent("ห้องที่พบ 2 ห้อง · โหมดทำนอง");
    const grid = await screen.findByRole("table");
    expect(within(grid).getByLabelText("กระเดื่อง ห้อง 1 จังหวะ 1")).toHaveTextContent("●");
    expect(within(grid).getByLabelText("กระเดื่อง ห้อง 1 จังหวะ 3")).toHaveTextContent("●");
    expect(within(grid).getByLabelText("ไฮแฮทปิด ห้อง 1 จังหวะ 2&")).toHaveTextContent("R");
    expect(within(grid).getByLabelText("สแนร์ ห้อง 1 จังหวะ 2")).toHaveTextContent("L");
    expect(screen.getByRole("region", { name: "สร้างบทเรียน" })).toHaveTextContent("สแนร์คือจังหวะทำนอง · กระเดื่องจังหวะ 1 และ 3 กับไฮแฮทปิดทุกครึ่งจังหวะ แอปเติมให้");
  });

  it("ยกเลิก POSTs the cancel and the job ends cancelled with the old result kept (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(PICK_PATH, pickOf({ state: "picking", percent: 20 }), pickOf({ state: "cancelled", percent: 20, cancel_requested: true }));
    const user = open(`#/songs/${ID}`, [get(PATH, songOf(picked)), job.route, send("POST", `${PICK_PATH}/cancel`, pickOf({ state: "picking", percent: 20, cancel_requested: true }), 200)]);

    const running = await screen.findByRole("group", { name: "งานแกะโน้ต" });
    await user.click(within(running).getByRole("button", { name: "ยกเลิก" }));

    expect(sent(fetchMock, "POST", `${PICK_PATH}/cancel`)).toEqual([{}]);
    expect(within(running).getByRole("button", { name: "ยกเลิก" })).toBeDisabled();
    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(screen.queryByRole("group", { name: "งานแกะโน้ต" })).not.toBeInTheDocument();
    expect(screen.getByRole("region", { name: "ผลแกะ" })).toHaveTextContent("ห้องที่พบ 2 ห้อง");
  });

  it("not_ready shows the fix of the row it names; busy says which song (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [
      get(PATH, songOf()),
      send("PUT", RANGE_PATH, songOf(), 200),
      send("POST", SONG_PICK_PATH, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: ADTOF drum model", rows: ["model_adtof"] }, 503),
      send("POST", SONG_PICK_PATH, { code: "busy", message: "กำลังแกะ Come As You Are อยู่ รอให้เสร็จก่อน", song_id: "other" }, 409),
      get("/api/setup/status", { ...status, items: [{ ...status.items[0], id: "model_adtof", label: "ADTOF drum model" }] }),
    ]);
    await screen.findByRole("region", { name: "ช่วงแกะ" });

    await user.click(pickButton());
    expect(await findStatusWith("ยังติดตั้งไม่ครบ: ADTOF drum model")).toBeInTheDocument();
    expect(await screen.findByText("./setup.sh")).toBeInTheDocument();

    await user.click(pickButton());
    expect(await findStatusWith("กำลังแกะ Come As You Are อยู่ รอให้เสร็จก่อน")).toBeInTheDocument();
  });

  it("a job that failed no_beats says to try another range, and the song stays unpicked (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf()), get(PICK_PATH, pickOf({ state: "failed", error: "no_beats", message: "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น" }))]);

    expect(await findStatusWith("หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น")).toBeInTheDocument();
    expect(screen.getByText("ตั้งช่วงแล้วกด แกะโน้ต")).toBeInTheDocument();
  });

  it("a job that failed model_failed shows the model's first line (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf()), get(PICK_PATH, pickOf({ state: "failed", error: "model_failed", message: "โมเดลทำงานผิดพลาด: Non-zero status code" }))]);

    expect(await findStatusWith("โมเดลทำงานผิดพลาด: Non-zero status code")).toBeInTheDocument();
  });

  it("a job that failed model_broken shows the Setup script to run (e2e)", async () => {
    open(`#/songs/${ID}`, [
      get(PATH, songOf()),
      get(PICK_PATH, pickOf({ state: "failed", error: "model_broken", message: "ไฟล์โมเดลเสีย รัน Setup script ใหม่ (ADTOF drum model)", rows: ["model_adtof"], fix: "./setup.sh" })),
    ]);

    expect(await findStatusWith("ไฟล์โมเดลเสีย รัน Setup script ใหม่ (ADTOF drum model)")).toBeInTheDocument();
    expect(screen.getByText("./setup.sh")).toBeInTheDocument();
  });

  it("another song's failure is not shown here, and its running job only disables แกะโน้ต", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf()), get(PICK_PATH, pickOf({ song_id: "other", state: "picking", percent: 30 }))]);

    await screen.findByRole("region", { name: "ช่วงแกะ" });
    await waitFor(() => expect(pickButton()).toBeDisabled());
    expect(screen.getByText("กำลังแกะเพลงอื่นอยู่ รอให้เสร็จก่อน")).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "งานแกะโน้ต" })).not.toBeInTheDocument();
  });

  it("the list says กำลังแกะ with the percent while a song is picked and แกะแล้ว with its bars after (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(PICK_PATH, pickOf({ state: "picking", percent: 35 }), pickOf({ state: "done", percent: 100 }));
    open("#/songs", [get(LIST_PATH, [rowOf()]), get(LIST_PATH, [rowOf({ analysis: { mode: "drums", bars: 12 } })]), job.route]);

    const row = await screen.findByRole("listitem");
    expect(row).toHaveTextContent("กำลังแกะ 35%");

    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    await waitFor(() => expect(row).toHaveTextContent("แกะแล้ว 12 ห้อง"));
  });
});

describe("สร้างบทเรียน", () => {
  const midiSong = (change: Partial<Song> = {}) => songOf({ source: { kind: "midi", url: null, name: "rock.mid", size: 300 }, range: null, duration_s: 4.8, ...picked, ...change });
  const section = () => screen.findByRole("region", { name: "สร้างบทเรียน" });
  const cell = (label: string) => within(screen.getByRole("table")).getByLabelText(label);
  const barCount = (n: number) => within(screen.getByRole("radiogroup", { name: "จำนวนห้อง" })).getByRole("radio", { name: String(n) });
  const bpmBox = () => screen.getByRole("spinbutton", { name: "BPM" });

  it("a picked song previews its first bar on open: the grid with sticks, the notes dropped, and the BPM the API gave (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, midiSong()), send("POST", PREVIEW_PATH, previewOf(), 200)]);

    await section();
    await waitFor(() => expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }]));
    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(cell("กระเดื่อง ห้อง 1 จังหวะ 1")).toHaveTextContent("●");
    expect(cell("ไฮแฮทปิด ห้อง 1 จังหวะ 1")).toHaveTextContent("R");
    expect(cell("สแนร์ ห้อง 1 จังหวะ 3")).toHaveTextContent("L");
    expect(cell("แครช ห้อง 1 จังหวะ 1")).toHaveTextContent("");
    expect(within(screen.getByRole("table")).queryAllByRole("button")).toHaveLength(0);
    const dropped = screen.getByRole("list", { name: "ตัดโน้ตที่มือตีไม่ได้" });
    expect(within(dropped).getAllByRole("listitem").map((item) => item.textContent)).toEqual(["ไฮแฮทปิด ห้อง 1 จังหวะ 3"]);
    expect(bpmBox()).toHaveValue(100);
    expect(screen.getByText("ห้องแรก: ห้อง 1")).toBeInTheDocument();
  });

  it("pressing a bar makes it the first bar, counts past the 4/4 bars left can't be picked, and each change previews once after 300 ms (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const bars: FoundBar[] = [...midiBars, { n: 3, start_s: 4.8, end_s: 7.2, beats: 4, hits: 2, four_four: true }, { n: 4, start_s: 7.2, end_s: 8.4, beats: 2, hits: 0, four_four: false }];
    const user = open(`#/songs/${ID}`, [get(PATH, midiSong({ bars, duration_s: 8.4 })), send("POST", PREVIEW_PATH, previewOf(), 200), send("POST", PREVIEW_PATH, previewOf({ dropped: [] }), 200)]);

    await section();
    await act(() => vi.advanceTimersByTimeAsync(350));
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }]);
    expect(barCount(1)).toBeEnabled();
    expect(barCount(3)).toBeEnabled();
    expect(barCount(4)).toBeDisabled();

    await user.click(barCount(2));
    await user.click(barCount(3));
    await act(() => vi.advanceTimersByTimeAsync(350));
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }, { bar: 0, bars: 3 }]);
    expect(screen.queryByRole("list", { name: "ตัดโน้ตที่มือตีไม่ได้" })).not.toBeInTheDocument();

    await user.click(within(screen.getByRole("list", { name: "ห้องที่พบ" })).getByRole("button", { name: "ห้อง 3" }));
    expect(screen.getByText("ห้องแรก: ห้อง 3")).toBeInTheDocument();
    expect(document.querySelectorAll("audio")).toHaveLength(0);
    expect(barCount(1)).toBeChecked();
    expect(barCount(2)).toBeDisabled();
    await act(() => vi.advanceTimersByTimeAsync(350));
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }, { bar: 0, bars: 3 }, { bar: 2, bars: 1 }]);
  });

  it("the first bar pressed moves the player too, and a changed BPM goes with the preview; one outside 40–240 says so and asks nothing (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = open(`#/songs/${ID}`, [get(PATH, songOf(picked)), send("POST", PREVIEW_PATH, previewOf(), 200), send("POST", PREVIEW_PATH, previewOf({ bpm: 95 }), 200)]);

    await section();
    await waitFor(() => expect(sent(fetchMock, "POST", PREVIEW_PATH)).toHaveLength(1));
    await user.click(within(screen.getByRole("list", { name: "ห้องที่พบ" })).getByRole("button", { name: "ห้อง 2" }));
    expect(screen.getByRole("region", { name: "เพลง" }).querySelector("audio")?.currentTime).toBe(2.4);
    await waitFor(() => expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }, { bar: 1, bars: 1 }]));

    await user.clear(bpmBox());
    await user.type(bpmBox(), "95");
    await waitFor(() => expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([{ bar: 0, bars: 1 }, { bar: 1, bars: 1 }, { bar: 1, bars: 1, bpm: 95 }]));
    expect(bpmBox()).toHaveValue(95);

    await user.clear(bpmBox());
    await user.type(bpmBox(), "20");
    expect(await screen.findByText("BPM ต้องเป็นจำนวนเต็ม 40–240")).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS + 100));
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toHaveLength(3);
  });

  it("a song whose bars are none of them 4/4 says there is nothing to pick", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf({ analysis: midiAnalysis, bars: midiBars.map((bar) => ({ ...bar, beats: 3, four_four: false })) }))]);

    expect(await screen.findByText("ไม่มีห้อง 4/4 ให้เลือก ลองแกะช่วงอื่น")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "สร้างบทเรียน" })).not.toBeInTheDocument();
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([]);
  });

  function stubAudio() {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    const pause = vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
    let made = 0;
    const createObjectURL = vi.fn(() => `blob:wav-${++made}`);
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL, revokeObjectURL }));
    return { play, pause, revokeObjectURL };
  }

  const wav = () => new Response(new Blob(["RIFF"], { type: "audio/wav" }), { status: 200, headers: { "Content-Type": "audio/wav" } });

  it("ฟัง posts the bars picked with the BPM shown, says กำลังผสมเสียง… until the wav plays, and pressed again stops the first (e2e)", async () => {
    const { play, pause, revokeObjectURL } = stubAudio();
    let answer: (response: Response) => void = () => {};
    const user = open(`#/songs/${ID}`, [
      get(PATH, midiSong()),
      { method: "POST", path: LISTEN_PATH, reply: () => new Promise((resolve) => (answer = resolve)) },
      { method: "POST", path: LISTEN_PATH, reply: wav },
    ]);

    await section();
    await waitFor(() => expect(bpmBox()).toHaveValue(100));
    await user.click(screen.getByRole("button", { name: "ฟัง" }));

    const mixing = await screen.findByRole("button", { name: "กำลังผสมเสียง…" });
    expect(mixing).toBeDisabled();
    expect(sent(fetchMock, "POST", LISTEN_PATH)).toEqual([{ bar: 0, bars: 1, bpm: 100 }]);
    await act(async () => answer(wav()));
    await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toBe("blob:wav-1");

    await user.click(screen.getByRole("button", { name: "ฟัง" }));
    await waitFor(() => expect(play).toHaveBeenCalledTimes(2));
    expect(pause.mock.contexts[0]).toBe(play.mock.contexts[0]);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-1");
  });

  it("a refused ฟัง shows why, with the fix of a row a not_ready names (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [
      get(PATH, midiSong()),
      send("POST", LISTEN_PATH, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: ชุดเสียงกลอง", rows: ["drum_kit"] }, 503),
      get("/api/setup/status", { ...status, items: [{ ...status.items[0], id: "drum_kit", label: "ชุดเสียงกลอง" }] }),
    ]);

    await section();
    await waitFor(() => expect(bpmBox()).toHaveValue(100));
    await user.click(screen.getByRole("button", { name: "ฟัง" }));

    expect(await findStatusWith("ยังติดตั้งไม่ครบ: ชุดเสียงกลอง")).toBeInTheDocument();
    expect(screen.getByText("./setup.sh")).toBeInTheDocument();
  });

  it("สร้างบทเรียนกลอง posts the bars picked and opens the new lesson's editor, which shows the same grid (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(PATH, midiSong()), send("POST", SONG_LESSONS_PATH, { lesson_id: LESSON_ID, dropped: 1 }, 201), get(LESSON_PATH, lessonOf())]);

    await section();
    await waitFor(() => expect(bpmBox()).toHaveValue(100));
    await user.click(screen.getByRole("button", { name: "สร้างบทเรียนกลอง" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/drums/${LESSON_ID}`));
    expect(sent(fetchMock, "POST", SONG_LESSONS_PATH)).toEqual([{ bar: 0, bars: 1, bpm: 100 }]);
    const form = await screen.findByRole("form", { name: "Smells Like Teen Spirit" });
    expect(within(form).getByRole("button", { name: "สแนร์ ห้อง 1 จังหวะ 3" })).toHaveTextContent("L");
    expect(within(form).getByRole("button", { name: "กระเดื่อง ห้อง 1 จังหวะ 1" })).toHaveTextContent("●");
  });

  it("a refused สร้างบทเรียนกลอง shows the API's message and stays (e2e)", async () => {
    const user = open(`#/songs/${ID}`, [get(PATH, midiSong()), send("POST", SONG_LESSONS_PATH, { code: "invalid_request", message: "ห้องนี้ไม่ใช่ 4/4", field: "bar" }, 400)]);

    await section();
    await waitFor(() => expect(bpmBox()).toHaveValue(100));
    await user.click(screen.getByRole("button", { name: "สร้างบทเรียนกลอง" }));

    expect(await findStatusWith("ห้องนี้ไม่ใช่ 4/4")).toBeInTheDocument();
    expect(window.location.hash).toBe(`#/songs/${ID}`);
  });

  it("บทเรียนจากเพลงนี้ links every lesson still there, or says there is none yet (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, midiSong({ lessons: [LESSON_ID, "zzzzzzzzzzzz"] }))]);

    const made = await screen.findByRole("region", { name: "บทเรียนจากเพลงนี้" });
    const links = within(made).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([`#/drums/${LESSON_ID}`, "#/drums/zzzzzzzzzzzz"]);
    expect(links[0]).toHaveTextContent("บทเรียน 1");
    expect(links[1]).toHaveTextContent("บทเรียน 2");
  });

  it("a song with no lessons says ยังไม่มี, and an unpicked song has no lesson section (e2e)", async () => {
    open(`#/songs/${ID}`, [get(PATH, songOf())]);

    const made = await screen.findByRole("region", { name: "บทเรียนจากเพลงนี้" });
    expect(made).toHaveTextContent("ยังไม่มี");
    expect(screen.queryByRole("region", { name: "สร้างบทเรียน" })).not.toBeInTheDocument();
    expect(sent(fetchMock, "POST", PREVIEW_PATH)).toEqual([]);
  });
});
