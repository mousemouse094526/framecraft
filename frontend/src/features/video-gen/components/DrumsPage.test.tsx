import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { StatusResponse } from "../../../lib/statusTypes";
import { findStatusWith } from "../../../testing/statusBox";
import { get, jsonResponse, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Lesson, LessonRow } from "../lib/lesson";
import type { DrumRenderJob, RenderResult } from "../lib/render";

const ID = "k3v9x0a1b2c4";
const LIST_PATH = "/api/drums/lessons";
const PATH = `${LIST_PATH}/${ID}`;
const LISTEN_PATH = `${PATH}/listen`;
const RENDER_PATH = "/api/drums/render";
const RENDERS_PATH = `${PATH}/renders`;

const fetchMock = vi.fn<typeof fetch>();
const confirmMock = vi.fn<(message?: string) => boolean>();

/** The lesson a new one starts as: a rock groove of one bar, two chapters (spec › Data). */
function lessonOf(change: Partial<Lesson> = {}): Lesson {
  return {
    version: 1,
    id: ID,
    title: "ร็อกพื้นฐาน",
    subtitle: "",
    caption: "",
    bpm: 100,
    background: "color",
    groove: {
      bars: 1,
      notes: [
        ...[0, 2, 4, 6, 8, 10, 12, 14].map((step) => ({ piece: "hihat_closed" as const, step, hand: "R" as const, hit: "normal" as const })),
        { piece: "snare", step: 4, hand: "L", hit: "normal" },
        { piece: "snare", step: 12, hand: "L", hit: "normal" },
        { piece: "kick", step: 0, hand: null, hit: "normal" },
        { piece: "kick", step: 8, hand: null, hit: "normal" },
      ],
    },
    chapters: [
      { label: "", text: "", focus: [], repeats: 2, speed: 100 },
      { label: "ลองเล่นเอง", text: "", focus: [], repeats: 2, speed: 100 },
    ],
    updated_at: "2026-11-13T10:30:00+07:00",
    length_s: 13.5,
    ...change,
  };
}

function rowOf(change: Partial<LessonRow> = {}): LessonRow {
  return { id: ID, title: "ร็อกพื้นฐาน", length_s: 13.5, renders: 0, updated_at: "2026-11-13T10:30:00+07:00", ...change };
}

/** The `PUT` answer: what was sent, as the backend stores it. */
const savedReply = (): Route => ({
  method: "PUT",
  path: PATH,
  reply: () => {
    const body = sent(fetchMock, "PUT", PATH).at(-1) as Partial<Lesson>;
    return jsonResponse(lessonOf({ ...body, updated_at: "2026-11-13T11:00:00+07:00" }));
  },
});

/** The Status check with the one row a not_ready names: the samples, missing. */
const status: StatusResponse = {
  checked_at: "2026-11-13T10:30:00+07:00",
  ready: false,
  ok_count: 0,
  warning_count: 0,
  missing_count: 1,
  total: 1,
  items: [{ id: "drum_kit", label: "Drum samples", status: "missing", detail: "ไม่พบ marker", fix: "./setup.sh", fix_kind: "command", license: null }],
};

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("confirm", confirmMock);
});

afterEach(() => {
  vi.useRealTimers();
  fetchMock.mockReset();
  confirmMock.mockReset();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [
    [LIST_PATH, []],
    [RENDER_PATH, null],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

async function openEditor(routes: Route[] = [], lesson = lessonOf()) {
  const user = open(`#/drums/${ID}`, [get(PATH, lesson), ...routes]);
  await screen.findByRole("button", { name: "บันทึก" });
  return user;
}

const cell = (piece: string, count: string, bar = 1) => screen.getByRole("button", { name: `${piece} ห้อง ${bar} จังหวะ ${count}` });
const noteBox = () => screen.getByRole("group", { name: "โน้ตที่เลือก" });
const chapter = (n: number) => screen.getByRole("group", { name: `ท่อน ${n}` });
const save = () => screen.getByRole("button", { name: "บันทึก" });

async function hashSettles() {
  // `hashchange` is a task of its own; let it and React's answer to it run.
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("รายการบทเรียนกลอง", () => {
  it("the สอนกลอง tab after การ์ตูนเล่า opens #/drums, which invites the first lesson when there is none", async () => {
    const user = open("#/setup", [get("/api/setup/status", status)]);

    await user.click(screen.getByRole("link", { name: "สอนกลอง" }));

    expect(window.location.hash).toBe("#/drums");
    expect(await screen.findByText("ยังไม่มีบทเรียนกลอง")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "สร้างบทเรียนแรก" })).toBeInTheDocument();
  });

  it("shows each lesson's title, length, renders and last edit", async () => {
    open("#/drums", [get(LIST_PATH, [rowOf({ renders: 2 })])]);

    const row = await screen.findByRole("listitem");
    expect(within(row).getByRole("link", { name: /ร็อกพื้นฐาน/ })).toHaveAttribute("href", `#/drums/${ID}`);
    expect(row).toHaveTextContent("0:14");
    expect(row).toHaveTextContent("render 2 ครั้ง");
    expect(row).toHaveTextContent("แก้ล่าสุด 13 พ.ย. 10:30");
  });

  it("asks a new lesson's title, POSTs it and opens the new lesson", async () => {
    const user = open("#/drums", [send("POST", LIST_PATH, lessonOf({ title: "Teen Spirit" }), 201), get(PATH, lessonOf({ title: "Teen Spirit" }))]);

    await user.click(await screen.findByRole("button", { name: "บทเรียนใหม่" }));
    const dialog = screen.getByRole("dialog", { name: "บทเรียนใหม่" });
    await user.type(within(dialog).getByRole("textbox", { name: "หัวเรื่อง" }), "Teen Spirit");
    await user.click(within(dialog).getByRole("button", { name: "สร้าง" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/drums/${ID}`));
    expect(sent(fetchMock, "POST", LIST_PATH)).toEqual([{ title: "Teen Spirit" }]);
    expect(await screen.findByRole("textbox", { name: "หัวเรื่อง" })).toHaveValue("Teen Spirit");
  });

  it("shows the API's message in the dialog when the title is refused", async () => {
    const user = open("#/drums", [
      send("POST", LIST_PATH, { code: "invalid_request", message: "หัวเรื่องยาวเกิน 40 ตัวอักษร", field: "title" }, 400),
    ]);

    await user.click(await screen.findByRole("button", { name: "บทเรียนใหม่" }));
    const dialog = screen.getByRole("dialog", { name: "บทเรียนใหม่" });
    await user.type(within(dialog).getByRole("textbox", { name: "หัวเรื่อง" }), "ยาว");
    await user.click(within(dialog).getByRole("button", { name: "สร้าง" }));

    expect(await within(dialog).findByText("หัวเรื่องยาวเกิน 40 ตัวอักษร")).toBeInTheDocument();
    expect(window.location.hash).toBe("#/drums");
  });

  it("ทำซ้ำ POSTs copy and shows the list again", async () => {
    const copy = rowOf({ id: "a1b2c3d4e5f6", title: "ร็อกพื้นฐาน (สำเนา)" });
    const user = open("#/drums", [
      get(LIST_PATH, [rowOf()]),
      get(LIST_PATH, [copy, rowOf()]),
      send("POST", `${PATH}/copy`, lessonOf({ id: copy.id, title: copy.title }), 201),
    ]);

    await user.click(await screen.findByRole("button", { name: "ทำซ้ำ ร็อกพื้นฐาน" }));

    expect(await screen.findByRole("link", { name: /ร็อกพื้นฐาน \(สำเนา\)/ })).toBeInTheDocument();
    expect(sent(fetchMock, "POST", `${PATH}/copy`)).toEqual([{}]);
  });

  it("ลบ asks first, saying how many renders go with the lesson, then DELETEs it", async () => {
    const user = open("#/drums", [get(LIST_PATH, [rowOf({ renders: 3 })]), get(LIST_PATH, []), send("DELETE", PATH, null, 204)]);

    await user.click(await screen.findByRole("button", { name: "ลบ ร็อกพื้นฐาน" }));
    const dialog = screen.getByRole("dialog", { name: "ลบ ร็อกพื้นฐาน?" });
    expect(dialog).toHaveTextContent("ผล render 3 รายการจะหายไปด้วย");
    await user.click(within(dialog).getByRole("button", { name: "ลบ" }));

    expect(await screen.findByText("ยังไม่มีบทเรียนกลอง")).toBeInTheDocument();
    expect(sent(fetchMock, "DELETE", PATH)).toEqual([null]);
  });

  it("ยกเลิก in the delete dialog sends nothing", async () => {
    const user = open("#/drums", [get(LIST_PATH, [rowOf()])]);

    await user.click(await screen.findByRole("button", { name: "ลบ ร็อกพื้นฐาน" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ยกเลิก" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(sent(fetchMock, "DELETE", PATH)).toEqual([]);
  });

  it("a refused delete shows the API's message", async () => {
    const user = open("#/drums", [
      get(LIST_PATH, [rowOf({ renders: 1 })]),
      send("DELETE", PATH, { code: "in_use", message: "ไฟล์ยังเปิดอยู่ในโปรแกรมอื่น" }, 409),
    ]);

    await user.click(await screen.findByRole("button", { name: "ลบ ร็อกพื้นฐาน" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ลบ" }));

    expect(await findStatusWith("ไฟล์ยังเปิดอยู่ในโปรแกรมอื่น")).toBeInTheDocument();
  });
});

describe("ตาราง Groove", () => {
  it("an empty cell where R plays another piece adds a note for L; a cell where both hands play can't be pressed", async () => {
    const user = await openEditor([savedReply()]);

    await user.click(cell("สแนร์", "1"));

    expect(cell("สแนร์", "1")).toHaveTextContent("L");
    expect(cell("แครช", "1")).toBeDisabled();
    // A foot is free whatever the hands do.
    expect(cell("ไฮแฮทเท้า", "1")).toBeEnabled();
    await user.click(save());
    await waitFor(() => expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1));
    const body = sent(fetchMock, "PUT", PATH)[0] as Lesson;
    expect(body.groove.notes).toContainEqual({ piece: "snare", step: 0, hand: "L", hit: "normal" });
  });

  it("a new note takes R first", async () => {
    const user = await openEditor();

    await user.click(cell("แครช", "1e"));

    expect(cell("แครช", "1e")).toHaveTextContent("R");
  });

  it("ไฮแฮทเปิด can't be added where ไฮแฮทปิด plays", async () => {
    await openEditor();

    expect(cell("ไฮแฮทเปิด", "1")).toBeDisabled();
    expect(cell("ไฮแฮทเปิด", "1e")).toBeEnabled();
  });

  it("a selected note turned into a flam is PUT as hit flam", async () => {
    const lesson = lessonOf({ groove: { bars: 1, notes: [{ piece: "snare", step: 4, hand: "L", hit: "normal" }] } });
    const user = await openEditor([savedReply()], lesson);

    await user.click(cell("สแนร์", "2"));
    await user.click(within(noteBox()).getByRole("radio", { name: "flam" }));
    await user.click(save());

    await waitFor(() => expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1));
    expect((sent(fetchMock, "PUT", PATH)[0] as Lesson).groove.notes).toEqual([{ piece: "snare", step: 4, hand: "L", hit: "flam" }]);
  });

  it("options that would clash the hands can't be picked", async () => {
    const user = await openEditor();

    // Step 4: ไฮแฮทปิด R and สแนร์ L.
    await user.click(cell("สแนร์", "2"));

    const box = noteBox();
    expect(within(box).getByRole("radio", { name: "L" })).toBeChecked();
    expect(within(box).getByRole("radio", { name: "R" })).toBeDisabled();
    expect(within(box).getByRole("radio", { name: "flam" })).toBeDisabled();
    expect(within(box).getByRole("radio", { name: "เน้น" })).toBeEnabled();
  });

  it("a foot's note has no stick and no flam", async () => {
    const user = await openEditor();

    await user.click(cell("กระเดื่อง", "1"));

    const box = noteBox();
    expect(within(box).queryByRole("radio", { name: "R" })).not.toBeInTheDocument();
    expect(within(box).queryByRole("radio", { name: "flam" })).not.toBeInTheDocument();
    expect(within(box).getByRole("radio", { name: "เบา" })).toBeEnabled();
  });

  it("ลบโน้ต removes the selected note", async () => {
    const user = await openEditor();

    await user.click(cell("กระเดื่อง", "3"));
    await user.click(within(noteBox()).getByRole("button", { name: "ลบโน้ต" }));

    expect(cell("กระเดื่อง", "3")).toBeEmptyDOMElement();
    expect(screen.queryByRole("group", { name: "โน้ตที่เลือก" })).not.toBeInTheDocument();
  });

  it("removing a bar with notes asks first, then drops them", async () => {
    const lesson = lessonOf({
      groove: {
        bars: 2,
        notes: [
          { piece: "snare", step: 4, hand: "L", hit: "normal" },
          { piece: "kick", step: 16, hand: null, hit: "normal" },
        ],
      },
    });
    const user = await openEditor([savedReply()], lesson);
    expect(cell("กระเดื่อง", "1", 2)).toHaveTextContent("●");

    confirmMock.mockReturnValueOnce(false);
    await user.click(screen.getByRole("button", { name: "ลดห้อง" }));
    expect(confirmMock).toHaveBeenCalledWith("ลดเหลือ 1 ห้อง โน้ต 1 ตัวที่เลยห้องสุดท้ายจะถูกลบ");
    expect(cell("กระเดื่อง", "1", 2)).toBeInTheDocument();

    confirmMock.mockReturnValueOnce(true);
    await user.click(screen.getByRole("button", { name: "ลดห้อง" }));
    expect(screen.queryByRole("button", { name: "กระเดื่อง ห้อง 2 จังหวะ 1" })).not.toBeInTheDocument();
    await user.click(save());

    await waitFor(() => expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1));
    expect((sent(fetchMock, "PUT", PATH)[0] as Lesson).groove).toEqual({
      bars: 1,
      notes: [{ piece: "snare", step: 4, hand: "L", hit: "normal" }],
    });
  });

  it("an empty bar goes without asking", async () => {
    const user = await openEditor([], lessonOf({ groove: { bars: 2, notes: [] } }));

    await user.click(screen.getByRole("button", { name: "ลดห้อง" }));

    expect(confirmMock).not.toHaveBeenCalled();
    expect(screen.getByText("1 ห้อง")).toBeInTheDocument();
  });
});

describe("ท่อนสอน", () => {
  it("added, moved and deleted chapters are PUT in their new order", async () => {
    const user = await openEditor([savedReply()]);

    await user.click(screen.getByRole("button", { name: "เพิ่มท่อน" }));
    await user.type(within(chapter(3)).getByRole("textbox", { name: "ป้าย" }), "KICK");
    await user.click(within(chapter(3)).getByRole("checkbox", { name: "กระเดื่อง" }));
    await user.selectOptions(within(chapter(3)).getByRole("combobox", { name: "ความเร็ว" }), "75");
    await user.click(screen.getByRole("button", { name: "เลื่อนท่อน 3 ขึ้น" }));
    await user.click(screen.getByRole("button", { name: "ลบท่อน 1" }));
    await user.click(save());

    await waitFor(() => expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1));
    expect((sent(fetchMock, "PUT", PATH)[0] as Lesson).chapters).toEqual([
      { label: "KICK", text: "", focus: ["kick"], repeats: 2, speed: 75 },
      { label: "ลองเล่นเอง", text: "", focus: [], repeats: 2, speed: 100 },
    ]);
  });

  it("the first chapter's label hints that empty shows the title, and the last one can't be deleted", async () => {
    const user = await openEditor();

    expect(within(chapter(1)).getByText("ว่าง = แสดงหัวเรื่อง")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ลบท่อน 2" }));
    expect(screen.getByRole("button", { name: "ลบท่อน 1" })).toBeDisabled();
  });
});

describe("ความยาวคลิป", () => {
  it("over 90 s says by how much; บันทึก still works but ฟังจังหวะ can't be pressed", async () => {
    const user = await openEditor([savedReply()]);

    expect(screen.getByText("ความยาวคลิป 13.5 / 90 วินาที")).toBeInTheDocument();
    for (const n of [1, 2]) await user.selectOptions(within(chapter(n)).getByRole("combobox", { name: "รอบ" }), "8");
    const bpm = screen.getByRole("spinbutton", { name: "BPM" });
    await user.clear(bpm);
    await user.type(bpm, "40");

    // A bar is 6 s at 40 BPM: 6 count-in + 16 × 6 + 1.5 tail = 103.5.
    expect(screen.getByText("ยาวเกิน 90 วินาทีไป 13.5 วินาที")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ฟังจังหวะ" })).toBeDisabled();
    await user.click(save());
    await waitFor(() => expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1));
  });
});

describe("ฟังจังหวะ", () => {
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

  it("saves, then mixes with the button saying so, then plays the wav", async () => {
    const { play } = stubAudio();
    let answer: (response: Response) => void = () => {};
    const user = await openEditor([savedReply(), { method: "POST", path: LISTEN_PATH, reply: () => new Promise((resolve) => (answer = resolve)) }]);

    await user.click(cell("แครช", "1e"));
    await user.click(screen.getByRole("button", { name: "ฟังจังหวะ" }));

    const mixing = await screen.findByRole("button", { name: "กำลังผสมเสียง…" });
    expect(mixing).toBeDisabled();
    expect(sent(fetchMock, "PUT", PATH)).toHaveLength(1);
    expect(sent(fetchMock, "POST", LISTEN_PATH)).toEqual([{}]);
    const order = fetchMock.mock.calls.map(([input, init]) => `${init?.method ?? "GET"} ${String(input)}`);
    expect(order.indexOf(`PUT ${PATH}`)).toBeLessThan(order.indexOf(`POST ${LISTEN_PATH}`));

    await act(async () => answer(wav()));
    await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("button", { name: "ฟังจังหวะ" })).toBeEnabled();
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toBe("blob:wav-1");
  });

  it("pressed again while playing stops the first wav before the second", async () => {
    const { play, pause, revokeObjectURL } = stubAudio();
    const user = await openEditor([{ method: "POST", path: LISTEN_PATH, reply: wav }]);

    await user.click(screen.getByRole("button", { name: "ฟังจังหวะ" }));
    await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
    await user.click(screen.getByRole("button", { name: "ฟังจังหวะ" }));
    await waitFor(() => expect(play).toHaveBeenCalledTimes(2));

    expect(pause.mock.contexts[0]).toBe(play.mock.contexts[0]);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-1");
    // Nothing was unsaved: no PUT before mixing.
    expect(sent(fetchMock, "PUT", PATH)).toEqual([]);
  });

  it("not_ready shows the drum_kit row's fix under the button", async () => {
    stubAudio();
    const user = await openEditor([
      send("POST", LISTEN_PATH, { code: "not_ready", message: "ยังติดตั้งไม่ครบ: Drum samples", rows: ["drum_kit"] }, 503),
      get("/api/setup/status", status),
    ]);

    await user.click(screen.getByRole("button", { name: "ฟังจังหวะ" }));

    expect(await findStatusWith("ยังติดตั้งไม่ครบ: Drum samples")).toBeInTheDocument();
    expect(await screen.findByText("./setup.sh")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ฟังจังหวะ" })).toBeEnabled();
  });
});

describe("บันทึก", () => {
  it("an invalid_request shows its message at the field it names", async () => {
    const user = await openEditor([
      send("PUT", PATH, { code: "invalid_request", message: "ป้ายยาวเกิน 16 ตัวอักษร", field: "chapters[1].label" }, 400),
    ]);

    await user.type(within(chapter(2)).getByRole("textbox", { name: "ป้าย" }), "!");
    await user.click(save());

    expect(await within(chapter(2)).findByText("ป้ายยาวเกิน 16 ตัวอักษร")).toBeInTheDocument();
    expect(within(chapter(2)).getByRole("textbox", { name: "ป้าย" })).toHaveAttribute("aria-invalid", "true");
  });

  it("an invalid_request on a field with no input of its own still shows its message", async () => {
    const user = await openEditor([
      send("PUT", PATH, { code: "invalid_request", message: "ความเร็วต้องเป็นทีละ 5%", field: "chapters[0].speed" }, 400),
    ]);

    await user.type(screen.getByRole("textbox", { name: "คำบรรยาย" }), "x");
    await user.click(save());

    expect(await screen.findByText("ความเร็วต้องเป็นทีละ 5%")).toBeInTheDocument();
  });

  it("an invalid_request on a note marks its cell", async () => {
    const user = await openEditor([
      send("PUT", PATH, { code: "invalid_request", message: "มือเดียวตีสองชิ้นในช่องเดียวกัน", field: "groove.notes[0]" }, 400),
    ]);

    await user.type(screen.getByRole("textbox", { name: "คำบรรยาย" }), "x");
    await user.click(save());

    expect(await screen.findByText("มือเดียวตีสองชิ้นในช่องเดียวกัน")).toBeInTheDocument();
    expect(cell("ไฮแฮทปิด", "1")).toHaveAttribute("aria-invalid", "true");
  });

  it("leaving before saving asks, and staying keeps the edit", async () => {
    const user = await openEditor();

    await user.type(screen.getByRole("textbox", { name: "หัวเรื่อง" }), "!");
    confirmMock.mockReturnValue(false);
    await user.click(screen.getByRole("link", { name: "สอนกลอง" }));
    await hashSettles();

    expect(confirmMock).toHaveBeenCalledWith("ออกโดยไม่บันทึก?");
    expect(window.location.hash).toBe(`#/drums/${ID}`);
    expect(screen.getByRole("textbox", { name: "หัวเรื่อง" })).toHaveValue("ร็อกพื้นฐาน!");
  });

  it("leaving after saving doesn't ask", async () => {
    const user = await openEditor([savedReply()]);

    await user.type(screen.getByRole("textbox", { name: "หัวเรื่อง" }), "!");
    await user.click(save());
    await screen.findByText("บันทึกแล้ว");
    await user.click(screen.getByRole("link", { name: "สอนกลอง" }));
    await hashSettles();

    expect(confirmMock).not.toHaveBeenCalled();
    expect(window.location.hash).toBe("#/drums");
  });

  it("a lesson that isn't there says so", async () => {
    open(`#/drums/${ID}`, [send("GET", PATH, { code: "not_found", message: "ไม่พบ" }, 404)]);

    expect(await screen.findByText("ไม่พบบทเรียนนี้")).toBeInTheDocument();
  });
});

function jobOf(change: Partial<DrumRenderJob> = {}): DrumRenderJob {
  return { state: "rendering", lesson_id: ID, title: "ร็อกพื้นฐาน", percent: 0, result: null, error: null, message: null, ...change };
}

function resultOf(name: string): RenderResult {
  return { name, lesson_id: ID, title: "ร็อกพื้นฐาน", length_s: 13.5, created_at: "2026-11-13T11:00:00+07:00", size_bytes: 1_000_000 };
}

describe("render", () => {
  it("saves first, shows the percent with ยกเลิก, then opens the results with the newest playing", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(RENDER_PATH, null, jobOf({ percent: 40 }), jobOf({ state: "done", percent: 100, result: "20261113-110500" }));
    const user = await openEditor([
      savedReply(),
      job.route,
      { method: "POST", path: RENDER_PATH, reply: () => ((job.phases.at = 1), jsonResponse(jobOf(), 202)) },
      get(RENDERS_PATH, [resultOf("20261113-110500"), resultOf("20261113-100000")]),
    ]);

    await user.click(cell("แครช", "1e"));
    await user.click(screen.getByRole("button", { name: "render" }));

    expect(await screen.findByRole("progressbar", { name: "กำลัง render" })).toBeInTheDocument();
    expect(sent(fetchMock, "POST", RENDER_PATH)).toEqual([{ lesson_id: ID }]);
    const order = fetchMock.mock.calls.map(([input, init]) => `${init?.method ?? "GET"} ${String(input)}`);
    expect(order.indexOf(`PUT ${PATH}`)).toBeLessThan(order.indexOf(`POST ${RENDER_PATH}`));
    await act(() => vi.advanceTimersByTimeAsync(1100));
    expect(await screen.findByText("40%")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ยกเลิก" })).toBeInTheDocument();

    job.phases.at = 2;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    await waitFor(() => expect(window.location.hash).toBe(`#/drums/${ID}/renders`));
    expect(await screen.findByLabelText("ผล render 20261113-110500")).toBeInTheDocument();
  });

  it("ยกเลิก POSTs the cancel; a cancelled render says so with ลองอีกครั้ง", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(RENDER_PATH, jobOf({ percent: 20 }), jobOf({ state: "cancelled", percent: 20 }));
    const user = await openEditor([job.route, { method: "POST", path: `${RENDER_PATH}/cancel`, reply: () => ((job.phases.at = 1), jsonResponse(jobOf({ percent: 20 }))) }]);

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));
    expect(sent(fetchMock, "POST", `${RENDER_PATH}/cancel`)).toEqual([{}]);
    await act(() => vi.advanceTimersByTimeAsync(1100));

    expect(await screen.findByText("ยกเลิก render แล้ว")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ลองอีกครั้ง" })).toBeInTheDocument();
  });

  it("a render this page didn't start ends done without leaving the page", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(RENDER_PATH, jobOf({ percent: 42 }), jobOf({ state: "done", percent: 100, result: "20261113-110500" }));
    await openEditor([job.route]);
    expect(await screen.findByText("42%")).toBeInTheDocument();

    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    await waitFor(() => expect(screen.queryByText("42%")).not.toBeInTheDocument());
    expect(window.location.hash).toBe(`#/drums/${ID}`);
  });

  it("a failed render shows its message, and ลองอีกครั้ง starts it again", async () => {
    const failed = jobOf({ state: "failed", error: "ffmpeg_failed", message: "render ไม่สำเร็จ: Error opening output files" });
    const user = await openEditor([get(RENDER_PATH, failed), send("POST", RENDER_PATH, jobOf(), 202)]);

    expect(await screen.findByText("render ไม่สำเร็จ: Error opening output files")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "ลองอีกครั้ง" }));

    await waitFor(() => expect(sent(fetchMock, "POST", RENDER_PATH)).toEqual([{ lesson_id: ID }]));
    expect(await screen.findByRole("progressbar", { name: "กำลัง render" })).toBeInTheDocument();
  });

  it("another lesson's render is named and render can't be pressed", async () => {
    await openEditor([get(RENDER_PATH, jobOf({ lesson_id: "zzzzzzzzzzzz", title: "เพลงอื่น", percent: 10 }))]);

    expect(await screen.findByText("กำลัง render เพลงอื่น อยู่ รอให้เสร็จก่อน")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "render" })).toBeDisabled();
  });

  it("busy says which lesson renders", async () => {
    const user = await openEditor([send("POST", RENDER_PATH, { code: "busy", message: "กำลัง render เพลงอื่น อยู่", lesson_id: "zzzzzzzzzzzz" }, 409)]);

    await user.click(screen.getByRole("button", { name: "render" }));
    expect(await screen.findByText("กำลัง render เพลงอื่น อยู่")).toBeInTheDocument();
  });

  it("a lesson over 90 s can't be rendered", async () => {
    await openEditor([], lessonOf({ bpm: 40, chapters: [{ label: "", text: "", focus: [], repeats: 8, speed: 50 }] }));

    expect(screen.getByRole("button", { name: "render" })).toBeDisabled();
  });

  it("the list badges the lesson that renders with its percent", async () => {
    open("#/drums", [get(LIST_PATH, [rowOf(), rowOf({ id: "zzzzzzzzzzzz", title: "เพลงอื่น" })]), get(RENDER_PATH, jobOf({ percent: 35 }))]);

    expect(await screen.findByText("กำลัง render 35%")).toBeInTheDocument();
    expect(screen.getAllByText(/กำลัง render/)).toHaveLength(1);
  });
});

describe("ผล render", () => {
  it("plays the newest in a 9:16 player, links the mp4 and .srt, and deletes after asking", async () => {
    const user = open(`#/drums/${ID}/renders`, [
      get(PATH, lessonOf()),
      get(RENDERS_PATH, [resultOf("20261113-110500"), resultOf("20261113-100000")]),
      send("DELETE", `${RENDERS_PATH}/20261113-100000`, null, 204),
      get(RENDERS_PATH, [resultOf("20261113-110500")]),
    ]);

    const player = await screen.findByLabelText("ผล render 20261113-110500");
    expect(player).toHaveAttribute("src", `${RENDERS_PATH}/20261113-110500.mp4`);
    expect(player).toHaveClass("aspect-[9/16]");
    const [newest] = within(screen.getByRole("list", { name: "ผล render ทั้งหมด" })).getAllByRole("listitem");
    expect(within(newest).getByRole("link", { name: "mp4" })).toHaveAttribute("href", `${RENDERS_PATH}/20261113-110500.mp4`);
    expect(within(newest).getByRole("link", { name: ".srt" })).toHaveAttribute("href", `${RENDERS_PATH}/20261113-110500.srt`);

    await user.click(screen.getByRole("button", { name: "ลบผล render 20261113-100000" }));
    await user.click(screen.getByRole("button", { name: "ลบ" }));
    await waitFor(() => expect(sent(fetchMock, "DELETE", `${RENDERS_PATH}/20261113-100000`)).toEqual([null]));
    await waitFor(() => expect(screen.queryByRole("button", { name: "ลบผล render 20261113-100000" })).not.toBeInTheDocument());
  });

  it("with none says it was never rendered, and this lesson's render shows its percent on top", async () => {
    open(`#/drums/${ID}/renders`, [get(PATH, lessonOf()), get(RENDERS_PATH, []), get(RENDER_PATH, jobOf({ percent: 55 }))]);

    expect(await screen.findByText("ยังไม่เคย render บทเรียนนี้")).toBeInTheDocument();
    expect(await screen.findByRole("progressbar", { name: "กำลัง render" })).toHaveAttribute("aria-valuenow", "55");
  });

  it("a render held open says in_use", async () => {
    const user = open(`#/drums/${ID}/renders`, [
      get(PATH, lessonOf()),
      get(RENDERS_PATH, [resultOf("20261113-110500")]),
      send("DELETE", `${RENDERS_PATH}/20261113-110500`, { code: "in_use", message: "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง" }, 409),
    ]);

    await user.click(await screen.findByRole("button", { name: "ลบผล render 20261113-110500" }));
    await user.click(screen.getByRole("button", { name: "ลบ" }));
    expect(await screen.findByText("ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง")).toBeInTheDocument();
  });
});
