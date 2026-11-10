import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { FakeXhr } from "../../../testing/fakeXhr";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import { GENRE_DEFAULTS, type Item, type ListedSeries, type Series, type ToonJob } from "../lib/series";
import { CHARACTER_FILE_NOTICE } from "./CastPage";

const SID = "s_1a2b3c4d";
const SERIES_PATH = "/api/toon/series";
const ONE_PATH = `${SERIES_PATH}/${SID}`;
const JOB_PATH = "/api/toon/jobs/current";
const VOICES_PATH = "/api/spoil-maker/voices";

const fetchMock = vi.fn<typeof fetch>();

const listed: ListedSeries = { id: SID, name: "รุ่นพี่เล่าว่า…", channel_name: "ช่อง เล่าก่อนนอน", layout: "frame", genre: "horror", ep_count: 12 };

const peak: Item = { id: "c_01", name: "พีค", tag: "สายแฟ", description: "ผู้ชายผมสั้น เสื้อฮาวาย", ref_rev: 0, pending: 0 };
const camp: Item = { id: "b_01", name: "กองไฟในป่า", description: "ลานโล่งกลางป่า", ref_rev: 1, pending: 0 };

function seriesOf(change: Partial<Series> = {}): Series {
  return {
    id: SID,
    name: "รุ่นพี่เล่าว่า…",
    channel_name: "ช่อง เล่าก่อนนอน",
    layout: "frame",
    genre: "horror",
    voice_id: "v_01",
    name_tags: true,
    ...GENRE_DEFAULTS.horror,
    characters: [peak],
    backgrounds: [camp],
    ...change,
  };
}

function jobOf(change: Partial<ToonJob> = {}): ToonJob {
  return {
    kind: "ref",
    state: "drawing",
    series_id: SID,
    ep_id: null,
    item_id: "c_01",
    done: 1,
    total: 3,
    error: null,
    cancel_requested: false,
    ...change,
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [[JOB_PATH, null]]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup();
}

describe("รายการ Series", () => {
  it("#/toon opens the การ์ตูนเล่า tab with each Series' name, channel, EP count and layout", async () => {
    open("#/toon", [get(SERIES_PATH, [listed])]);

    const row = await screen.findByRole("listitem");
    expect(within(row).getByRole("link")).toHaveAttribute("href", `#/toon/series/${SID}`);
    expect(row).toHaveTextContent("รุ่นพี่เล่าว่า…");
    expect(row).toHaveTextContent("ช่อง เล่าก่อนนอน");
    expect(row).toHaveTextContent("12 EP");
    expect(row).toHaveTextContent("กรอบดำ");
    expect(screen.getByRole("link", { name: "การ์ตูนเล่า", current: "page" })).toBeInTheDocument();
  });

  it("asks to create the first Series when there is none", async () => {
    open("#/toon", [get(SERIES_PATH, [])]);

    expect(await screen.findByText("ยังไม่มีชุด สร้างชุดแรกเพื่อเริ่มทำการ์ตูนเล่า")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "สร้าง Series" })[0]).toHaveAttribute("href", "#/toon/new");
  });

  it("ลบชุด asks with the EP count first, then sends it as confirm_eps (D26)", async () => {
    const user = open("#/toon", [get(SERIES_PATH, [listed]), send("DELETE", ONE_PATH, null, 204), get(SERIES_PATH, [])]);

    await user.click(await screen.findByRole("button", { name: "ลบชุด รุ่นพี่เล่าว่า…" }));
    const dialog = screen.getByRole("dialog", { name: "ลบชุด รุ่นพี่เล่าว่า…?" });
    expect(dialog).toHaveTextContent("EP ทั้งหมด 12 ตอน");
    await user.click(within(dialog).getByRole("button", { name: "ลบชุด" }));

    expect(await screen.findByText("ยังไม่มีชุด สร้างชุดแรกเพื่อเริ่มทำการ์ตูนเล่า")).toBeInTheDocument();
    expect(sent(fetchMock, "DELETE", ONE_PATH)).toEqual([{ confirm_eps: 12 }]);
  });

  it("a delete refused while a job works on the Series says why", async () => {
    const busy = { code: "series_busy", message: "ลบไม่ได้ระหว่างที่มีงานของชุดนี้ทำอยู่" };
    const user = open("#/toon", [get(SERIES_PATH, [listed]), send("DELETE", ONE_PATH, busy, 409)]);

    await user.click(await screen.findByRole("button", { name: "ลบชุด รุ่นพี่เล่าว่า…" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ลบชุด" }));

    expect(await screen.findByText("ลบ รุ่นพี่เล่าว่า… ไม่ได้")).toBeInTheDocument();
    expect(screen.getByText(busy.message)).toBeInTheDocument();
  });
});

describe("ตั้งค่า Series", () => {
  it("a genre fills style, tone and acts; the new Series is sent whole and its page opens", async () => {
    const created = seriesOf({ genre: "comedy", ...GENRE_DEFAULTS.comedy });
    const user = open("#/toon/new", [
      get(VOICES_PATH, [{ id: "v_01", name: "พี่โอ๊ต" }]),
      send("POST", SERIES_PATH, created, 201),
      get(ONE_PATH, created),
    ]);

    await user.type(await screen.findByLabelText("ชื่อชุด"), "แก๊งป่วน");
    await user.click(screen.getByRole("radio", { name: "ตลก" }));
    expect(screen.getByLabelText("ชื่อองก์ 1")).toHaveValue("ตั้งเรื่อง");
    await user.clear(screen.getByLabelText("ชื่อองก์ 4"));
    await user.type(screen.getByLabelText("ชื่อองก์ 4"), "จบ");
    await user.click(screen.getByRole("button", { name: "บันทึก" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SID}`));
    expect(sent(fetchMock, "POST", SERIES_PATH)).toEqual([
      expect.objectContaining({
        name: "แก๊งป่วน",
        layout: "frame",
        genre: "comedy",
        voice_id: "v_01",
        tone: GENRE_DEFAULTS.comedy.tone,
        acts: ["ตั้งเรื่อง", "ปั่น", "พลิก", "จบ"],
      }),
    ]);
  });

  it("without a Saved voice it links to the สปอย tab's Saved voice page (e2e)", async () => {
    open("#/toon/new", [get(VOICES_PATH, [])]);

    expect(await screen.findByText("ยังไม่มี Saved voice")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปสร้างเสียงที่ tab สปอย" })).toHaveAttribute("href", "#/spoil/voices");
    expect(screen.getByRole("button", { name: "บันทึก" })).toBeDisabled();
  });

  it("an existing Series keeps its layout and genre: the PATCH leaves them out (D7, D10)", async () => {
    const user = open(`#/toon/series/${SID}/settings`, [
      get(VOICES_PATH, [{ id: "v_01", name: "พี่โอ๊ต" }]),
      get(ONE_PATH, seriesOf()),
      send("PATCH", ONE_PATH, seriesOf({ name: "ใหม่" }), 200),
    ]);

    await screen.findByLabelText("ชื่อชุด");
    expect(screen.queryByRole("radio", { name: /ตลก/ })).not.toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /กรอบดำ/ })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByText("แก้แล้วมีผลกับ EP ใหม่เท่านั้น")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("ชื่อชุด"));
    await user.type(screen.getByLabelText("ชื่อชุด"), "ใหม่");
    await user.click(screen.getByRole("button", { name: "บันทึก" }));

    await waitFor(() => expect(sent(fetchMock, "PATCH", ONE_PATH)).toHaveLength(1));
    const [patch] = sent(fetchMock, "PATCH", ONE_PATH) as Record<string, unknown>[];
    expect(patch.name).toBe("ใหม่");
    expect(patch).not.toHaveProperty("layout");
    expect(patch).not.toHaveProperty("genre");
  });
});

describe("ตัวละครและฉากหลัง", () => {
  it("shows ยังไม่มีภาพ, the reference image, and a set waiting to be picked", async () => {
    const mind: Item = { ...peak, id: "c_02", name: "มายด์", pending: 3 };
    open(`#/toon/series/${SID}/cast`, [get(ONE_PATH, seriesOf({ characters: [peak, mind] }))]);

    const characters = await screen.findByRole("region", { name: "ตัวละคร" });
    expect(within(characters).getByRole("listitem", { name: "พีค" })).toHaveTextContent("ยังไม่มีภาพ");
    const waiting = within(characters).getByRole("listitem", { name: "มายด์" });
    expect(within(waiting).getByRole("link", { name: "เลือกภาพ" })).toHaveAttribute(
      "href",
      `#/toon/series/${SID}/characters/c_02/pick`,
    );
    expect(within(waiting).getByRole("button", { name: "สร้างภาพ 3 แบบ" })).toBeEnabled();
    const background = within(screen.getByRole("region", { name: "ฉากหลัง" })).getByRole("img", { name: "ภาพอ้างอิง กองไฟในป่า" });
    expect(background).toHaveAttribute("src", `${ONE_PATH}/backgrounds/b_01/ref?rev=1`);
  });

  it("เอาไฟล์เข้า of a character shows the legal notice before the file picker (e2e)", async () => {
    const user = open(`#/toon/series/${SID}/cast`, [get(ONE_PATH, seriesOf())]);
    const tile = await screen.findByRole("listitem", { name: "พีค" });
    const picker = vi.spyOn(within(tile).getByLabelText<HTMLInputElement>("ไฟล์ภาพ พีค"), "click");

    await user.click(within(tile).getByRole("button", { name: "เอาไฟล์เข้า" }));

    const dialog = screen.getByRole("dialog", { name: "ก่อนเอาไฟล์ภาพตัวละครเข้า" });
    expect(dialog).toHaveTextContent(CHARACTER_FILE_NOTICE);
    expect(picker).not.toHaveBeenCalled();
    await user.click(within(dialog).getByRole("button", { name: "เลือกไฟล์" }));
    expect(picker).toHaveBeenCalledOnce();
  });

  it("a picked file is checked, then sent as the raw body; the answer's reference image shows", async () => {
    const check = `${ONE_PATH}/characters/c_01/ref/upload/check`;
    const user = open(`#/toon/series/${SID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", check, { size: 3 }, 200)]);
    const tile = await screen.findByRole("listitem", { name: "พีค" });

    await user.upload(within(tile).getByLabelText("ไฟล์ภาพ พีค"), new File(["png"], "peak.png", { type: "image/png" }));

    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(sent(fetchMock, "POST", check)).toEqual([{ size: 3 }]);
    expect(FakeXhr.sent[0].url).toBe(`${ONE_PATH}/characters/c_01/ref/upload?size=3`);
    FakeXhr.sent[0].progress(1, 2);
    expect(within(tile).getByText("กำลังส่งไฟล์ 50%")).toBeInTheDocument();
    await FakeXhr.sent[0].respond(200, seriesOf({ characters: [{ ...peak, ref_rev: 1 }] }));

    expect(await within(tile).findByRole("img", { name: "ภาพอ้างอิง พีค" })).toHaveAttribute(
      "src",
      `${ONE_PATH}/characters/c_01/ref?rev=1`,
    );
  });

  it("a Ref job refused with gpu_busy names the running job from RUNNING_NAMES (e2e)", async () => {
    const busy = { code: "gpu_busy", message: "GPU busy", running: "describe" };
    const user = open(`#/toon/series/${SID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", "/api/toon/jobs", busy, 409)]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByText("ยังสร้างภาพอ้างอิงไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();
    expect(sent(fetchMock, "POST", "/api/toon/jobs")).toEqual([
      { kind: "ref", series_id: SID, item_kind: "characters", item_id: "c_01" },
    ]);
  });

  it("a started Ref job opens เลือกภาพอ้างอิง", async () => {
    const user = open(`#/toon/series/${SID}/cast`, [
      get(ONE_PATH, seriesOf()),
      send("POST", "/api/toon/jobs", jobOf({ state: "translating", done: null, total: null }), 202),
    ]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SID}/characters/c_01/pick`));
  });

  it("not_ready links to ติดตั้ง", async () => {
    const missing = { code: "not_ready", message: "ยังติดตั้ง FLUX.2 klein ไม่ครบ" };
    const user = open(`#/toon/series/${SID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", "/api/toon/jobs", missing, 503)]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByRole("link", { name: "ไปที่ ติดตั้ง" })).toHaveAttribute("href", "#/setup");
  });

  it("เพิ่มตัวละคร sends name, tag and description and shows the new tile", async () => {
    const mind: Item = { id: "c_02", name: "มายด์", tag: "ขี้กลัว", description: "", ref_rev: 0, pending: 0 };
    const user = open(`#/toon/series/${SID}/cast`, [
      get(ONE_PATH, seriesOf()),
      send("POST", `${ONE_PATH}/characters`, seriesOf({ characters: [peak, mind] }), 201),
    ]);

    await user.click(await screen.findByRole("button", { name: "เพิ่มตัวละคร" }));
    const form = screen.getByRole("form", { name: "ตัวละครใหม่" });
    await user.type(within(form).getByLabelText("ชื่อ"), "มายด์");
    await user.type(within(form).getByLabelText("คำสั้น (ไม่บังคับ)"), "ขี้กลัว");
    await user.click(within(form).getByRole("button", { name: "เพิ่ม" }));

    expect(await screen.findByRole("listitem", { name: "มายด์" })).toBeInTheDocument();
    expect(sent(fetchMock, "POST", `${ONE_PATH}/characters`)).toEqual([{ name: "มายด์", tag: "ขี้กลัว", description: "" }]);
  });
});

describe("เลือกภาพอ้างอิง", () => {
  const PICK_HASH = `#/toon/series/${SID}/characters/c_01/pick`;

  it("follows the job, then shows the three pictures; ใช้ภาพนี้ sends the chosen one", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const job = phased(JOB_PATH, jobOf({ done: 1 }), jobOf({ state: "done", done: 3 }));
    const user = open(PICK_HASH, [
      job.route,
      get(ONE_PATH, seriesOf()),
      get(ONE_PATH, seriesOf({ characters: [{ ...peak, pending: 3 }] })),
      send("POST", `${ONE_PATH}/characters/c_01/ref/pick`, seriesOf(), 200),
    ]);

    expect(await screen.findByText("กำลังสร้างภาพ 3 แบบ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ใช้ภาพนี้" })).toBeDisabled();
    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1000));

    expect(await screen.findByText("สร้างครบ 3 แบบแล้ว")).toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: "แบบ 2" }));
    expect(screen.getByRole("radio", { name: "แบบ 2" })).toHaveAttribute("aria-checked", "true");
    await user.click(screen.getByRole("button", { name: "ใช้ภาพนี้" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SID}/cast`));
    expect(sent(fetchMock, "POST", `${ONE_PATH}/characters/c_01/ref/pick`)).toEqual([{ n: 2 }]);
  });

  it("a failed job says why and offers ลองอีกครั้ง", async () => {
    const failed = jobOf({ state: "failed", error: { code: "model_failed", message: "หน่วยความจำการ์ดจอไม่พอ" } });
    open(PICK_HASH, [get(JOB_PATH, failed), get(ONE_PATH, seriesOf())]);

    expect(await screen.findByText("หน่วยความจำการ์ดจอไม่พอ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ลองอีกครั้ง" })).toBeInTheDocument();
  });
});
