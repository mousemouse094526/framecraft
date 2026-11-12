import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { OFFLINE_TEXT } from "../../../lib/api";
import { FakeXhr } from "../../../testing/fakeXhr";
import { findStatusWith } from "../../../testing/statusBox";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import { GENRE_DEFAULTS, type Item, type ListedSeries, type Series, type ToonJob } from "../lib/series";

const SERIES_ID = "s_1a2b3c4d";
const SERIES_PATH = "/api/toon/series";
const ONE_PATH = `${SERIES_PATH}/${SERIES_ID}`;
const JOB_PATH = "/api/toon/jobs/current";
const VOICES_PATH = "/api/spoil-maker/voices";

const fetchMock = vi.fn<typeof fetch>();

const listed: ListedSeries = { id: SERIES_ID, name: "รุ่นพี่เล่าว่า…", channel_name: "ช่อง เล่าก่อนนอน", layout: "frame", genre: "horror", ep_count: 12 };

const peak: Item = { id: "c_01", name: "พีค", tag: "สายแฟ", description: "ผู้ชายผมสั้น เสื้อฮาวาย", ref_rev: 0, pending: 0 };
const camp: Item = { id: "b_01", name: "กองไฟในป่า", description: "ลานโล่งกลางป่า", ref_rev: 1, pending: 0 };

function seriesOf(change: Partial<Series> = {}): Series {
  return {
    id: SERIES_ID,
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
    series_id: SERIES_ID,
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
    expect(within(row).getByRole("link")).toHaveAttribute("href", `#/toon/series/${SERIES_ID}`);
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

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SERIES_ID}`));
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
    const user = open(`#/toon/series/${SERIES_ID}/settings`, [
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
  it("a refused save says why in a line with no title, and the form stays to send again", async () => {
    const refused = { code: "invalid_series", message: "ต้องเลือกเสียงพากย์" };
    const user = open(`#/toon/series/${SERIES_ID}/settings`, [
      get(VOICES_PATH, [{ id: "v_01", name: "พี่โอ๊ต" }]),
      get(ONE_PATH, seriesOf()),
      send("PATCH", ONE_PATH, refused, 400),
    ]);

    await screen.findByLabelText("ชื่อชุด");
    await user.click(screen.getByRole("button", { name: "บันทึก" }));

    // the box holds the line alone: no title above it
    expect(await findStatusWith(refused.message)).toHaveTextContent(new RegExp(`^${refused.message}$`));
    expect(screen.getByRole("button", { name: "บันทึก" })).toBeEnabled();
    expect(window.location.hash).toBe(`#/toon/series/${SERIES_ID}/settings`);
  });
});

describe("ตัวละครและฉากหลัง", () => {
  it("shows ยังไม่มีภาพ, the reference image, and a set waiting to be picked", async () => {
    const mind: Item = { ...peak, id: "c_02", name: "มายด์", pending: 3 };
    open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf({ characters: [peak, mind] }))]);

    const characters = await screen.findByRole("region", { name: "ตัวละคร" });
    expect(within(characters).getByRole("listitem", { name: "พีค" })).toHaveTextContent("ยังไม่มีภาพ");
    const waiting = within(characters).getByRole("listitem", { name: "มายด์" });
    expect(within(waiting).getByRole("link", { name: "เลือกภาพ" })).toHaveAttribute(
      "href",
      `#/toon/series/${SERIES_ID}/characters/c_02/pick`,
    );
    expect(within(waiting).getByRole("button", { name: "สร้างภาพ 3 แบบ" })).toBeEnabled();
    const background = within(screen.getByRole("region", { name: "ฉากหลัง" })).getByRole("img", { name: "ภาพอ้างอิง กองไฟในป่า" });
    expect(background).toHaveAttribute("src", `${ONE_PATH}/backgrounds/b_01/ref?rev=1`);
  });

  it("เอาไฟล์เข้า of a character shows the legal notice before the file picker (e2e)", async () => {
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf())]);
    const tile = await screen.findByRole("listitem", { name: "พีค" });
    const picker = vi.spyOn(within(tile).getByLabelText<HTMLInputElement>("ไฟล์ภาพ พีค"), "click");

    await user.click(within(tile).getByRole("button", { name: "เอาไฟล์เข้า" }));

    const dialog = screen.getByRole("dialog", { name: "ก่อนเอาไฟล์ภาพตัวละครเข้า" });
    expect(dialog).toHaveTextContent(
      "ใช้ภาพหรือตัวละครที่คุณวาดเองหรือได้รับอนุญาต และอย่าใช้ภาพคนจริงในเรื่องที่ทำให้เขาเสียชื่อเสียง", // legal.md item 2
    );
    expect(picker).not.toHaveBeenCalled();
    await user.click(within(dialog).getByRole("button", { name: "เลือกไฟล์" }));
    expect(picker).toHaveBeenCalledOnce();
  });

  it("เอาไฟล์เข้า of a background opens the file picker at once", async () => {
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf())]);
    const tile = await screen.findByRole("listitem", { name: "กองไฟในป่า" });
    const picker = vi.spyOn(within(tile).getByLabelText<HTMLInputElement>("ไฟล์ภาพ กองไฟในป่า"), "click");

    await user.click(within(tile).getByRole("button", { name: "เอาไฟล์เข้า" }));

    expect(picker).toHaveBeenCalledOnce();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  // jsdom has no layout: the image's Tailwind classes are the one sign of its shape.
  it("a character's reference image is square, a background's 16:9", async () => {
    open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf({ characters: [{ ...peak, ref_rev: 1 }] }))]);

    expect(await screen.findByRole("img", { name: "ภาพอ้างอิง พีค" })).toHaveClass("size-[264px]");
    expect(screen.getByRole("img", { name: "ภาพอ้างอิง กองไฟในป่า" })).toHaveClass("h-[148px]", "w-[264px]");
  });

  it("a picked file is checked, then sent as the raw body; the answer's reference image shows", async () => {
    const check = `${ONE_PATH}/characters/c_01/ref/upload/check`;
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", check, { size: 3 }, 200)]);
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

  it("a picked file the check refuses is not sent and says why; a failed upload says why too", async () => {
    const check = `${ONE_PATH}/characters/c_01/ref/upload/check`;
    const tooBig = { code: "invalid_request", message: "ไฟล์ใหญ่เกิน 20 MB" };
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [
      get(ONE_PATH, seriesOf()),
      send("POST", check, tooBig, 400),
      send("POST", check, { size: 3 }, 200),
    ]);
    const tile = await screen.findByRole("listitem", { name: "พีค" });
    const png = new File(["png"], "peak.png", { type: "image/png" });

    await user.upload(within(tile).getByLabelText("ไฟล์ภาพ พีค"), png);

    expect(await screen.findByText("เอาไฟล์ peak.png เข้าไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("ไฟล์ใหญ่เกิน 20 MB")).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);

    await user.upload(within(tile).getByLabelText("ไฟล์ภาพ พีค"), png);
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(screen.queryByText("ไฟล์ใหญ่เกิน 20 MB")).not.toBeInTheDocument();
    await FakeXhr.sent[0].fail();

    expect(await screen.findByText("ติดต่อ backend ไม่ได้")).toBeInTheDocument();
    expect(within(tile).getByText("ยังไม่มีภาพ")).toBeInTheDocument();
  });

  it("a Ref job refused with gpu_busy names the running job from RUNNING_NAMES (e2e)", async () => {
    const busy = { code: "gpu_busy", message: "GPU busy", running: "describe" };
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", "/api/toon/jobs", busy, 409)]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByText("ยังสร้างภาพอ้างอิงไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();
    expect(sent(fetchMock, "POST", "/api/toon/jobs")).toEqual([
      { kind: "ref", series_id: SERIES_ID, item_kind: "characters", item_id: "c_01" },
    ]);
  });

  it("a started Ref job opens เลือกภาพอ้างอิง", async () => {
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [
      get(ONE_PATH, seriesOf()),
      send("POST", "/api/toon/jobs", jobOf({ state: "translating", done: null, total: null }), 202),
    ]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SERIES_ID}/characters/c_01/pick`));
  });

  it("not_ready links to ติดตั้ง", async () => {
    const missing = { code: "not_ready", message: "ยังติดตั้ง FLUX.2 klein ไม่ครบ" };
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [get(ONE_PATH, seriesOf()), send("POST", "/api/toon/jobs", missing, 503)]);

    await user.click(within(await screen.findByRole("listitem", { name: "พีค" })).getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByRole("link", { name: "ไปที่ ติดตั้ง" })).toHaveAttribute("href", "#/setup");
  });

  it("เพิ่มตัวละคร sends name, tag and description and shows the new tile", async () => {
    const mind: Item = { id: "c_02", name: "มายด์", tag: "ขี้กลัว", description: "", ref_rev: 0, pending: 0 };
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [
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

  it("a refused เพิ่ม says why and adds nothing; sent again and taken, the notice goes", async () => {
    const mind: Item = { id: "c_02", name: "มายด์", tag: "", description: "", ref_rev: 0, pending: 0 };
    const taken = { code: "invalid_request", message: "มีตัวละครชื่อนี้แล้ว" };
    const user = open(`#/toon/series/${SERIES_ID}/cast`, [
      get(ONE_PATH, seriesOf()),
      send("POST", `${ONE_PATH}/characters`, taken, 400),
      send("POST", `${ONE_PATH}/characters`, seriesOf({ characters: [peak, mind] }), 201),
    ]);

    await user.click(await screen.findByRole("button", { name: "เพิ่มตัวละคร" }));
    const form = screen.getByRole("form", { name: "ตัวละครใหม่" });
    await user.type(within(form).getByLabelText("ชื่อ"), "มายด์");
    await user.click(within(form).getByRole("button", { name: "เพิ่ม" }));

    expect(await screen.findByText("เพิ่ม มายด์ ไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("มีตัวละครชื่อนี้แล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("listitem", { name: "มายด์" })).not.toBeInTheDocument();

    // The form stays open with the name, so เพิ่ม sends it again.
    await user.click(within(form).getByRole("button", { name: "เพิ่ม" }));

    expect(await screen.findByRole("listitem", { name: "มายด์" })).toBeInTheDocument();
    expect(screen.queryByText("เพิ่ม มายด์ ไม่ได้")).not.toBeInTheDocument();
  });
});

describe("เลือกภาพอ้างอิง", () => {
  const PICK_HASH = `#/toon/series/${SERIES_ID}/characters/c_01/pick`;

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

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/series/${SERIES_ID}/cast`));
    expect(sent(fetchMock, "POST", `${ONE_PATH}/characters/c_01/ref/pick`)).toEqual([{ n: 2 }]);
  });

  it.each([
    ["characters", "c_01", "aspect-square"],
    ["backgrounds", "b_01", "aspect-video"],
  ])("the pictures of %s (%s) sit in an %s box", async (kind, id, aspect) => {
    const waiting = seriesOf({ characters: [{ ...peak, pending: 3 }], backgrounds: [{ ...camp, pending: 3 }] });
    open(`#/toon/series/${SERIES_ID}/${kind}/${id}/pick`, [get(ONE_PATH, waiting)]);

    const option = await screen.findByRole("radio", { name: "แบบ 1" });
    // jsdom has no layout: the box's Tailwind class is the one sign of its shape.
    const picture = option.querySelector(`img[src="${ONE_PATH}/${kind}/${id}/ref/pending/1"]`);
    expect(picture?.parentElement).toHaveClass(aspect);
  });

  it("a failed job says why and offers ลองอีกครั้ง", async () => {
    const failed = jobOf({ state: "failed", error: { code: "model_failed", message: "หน่วยความจำการ์ดจอไม่พอ" } });
    open(PICK_HASH, [get(JOB_PATH, failed), get(ONE_PATH, seriesOf())]);

    expect(await screen.findByText("หน่วยความจำการ์ดจอไม่พอ")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ลองอีกครั้ง" })).toBeInTheDocument();
  });
  it("a refused ใช้ภาพนี้ says why in a line with no title and stays on the page", async () => {
    const gone = { code: "no_pending", message: "ไม่มีภาพรอเลือกแล้ว" };
    const user = open(PICK_HASH, [
      get(ONE_PATH, seriesOf({ characters: [{ ...peak, pending: 3 }] })),
      send("POST", `${ONE_PATH}/characters/c_01/ref/pick`, gone, 409),
    ]);

    await user.click(await screen.findByRole("radio", { name: "แบบ 1" }));
    await user.click(screen.getByRole("button", { name: "ใช้ภาพนี้" }));

    // the box holds the line alone: no title above it
    expect(await findStatusWith(gone.message)).toHaveTextContent(new RegExp(`^${gone.message}$`));
    expect(window.location.hash).toBe(PICK_HASH);
    expect(screen.getByRole("button", { name: "ใช้ภาพนี้" })).toBeEnabled();
  });

  it("a refused สร้างภาพ 3 แบบ says why", async () => {
    const busy = { code: "busy", message: "มีงานอื่นทำอยู่" };
    const user = open(PICK_HASH, [get(ONE_PATH, seriesOf()), send("POST", "/api/toon/jobs", busy, 409)]);

    await user.click(await screen.findByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByText(busy.message)).toBeInTheDocument();
  });

  it("สร้างภาพ 3 แบบ with no backend says so", async () => {
    const user = open(PICK_HASH, [get(ONE_PATH, seriesOf())]);
    await screen.findByRole("button", { name: "สร้างภาพ 3 แบบ" });

    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await user.click(screen.getByRole("button", { name: "สร้างภาพ 3 แบบ" }));

    expect(await screen.findByText(OFFLINE_TEXT)).toBeInTheDocument();
  });
});
