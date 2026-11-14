import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { OFFLINE_TEXT } from "../../../lib/api";
import { findStatusWith } from "../../../testing/statusBox";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Card, Ep, ListedEp } from "../lib/episodes";
import { GENRE_DEFAULTS, type Item, type Series, type ToonJob } from "../lib/series";

const SERIES_ID = "s_1a2b3c4d";
const EP_ID = "e_5e6f7a8b";
const EP_PATH = `/api/toon/eps/${EP_ID}`;
const SERIES_PATH = `/api/toon/series/${SERIES_ID}`;
const JOBS_PATH = "/api/toon/jobs";
const JOB_PATH = "/api/toon/jobs/current";
const SOUNDS_PATH = "/api/sounds";

const fetchMock = vi.fn<typeof fetch>();

const peak: Item = { id: "c_01", name: "พีค", tag: "สายแฟ", description: "", ref_rev: 1, pending: 0 };
const mind: Item = { id: "c_02", name: "มายด์", tag: "", description: "", ref_rev: 1, pending: 0 };
const camp: Item = { id: "b_01", name: "กองไฟในป่า", description: "", ref_rev: 1, pending: 0 };

const series: Series = {
  id: SERIES_ID,
  name: "รุ่นพี่เล่าว่า…",
  channel_name: "",
  layout: "frame",
  genre: "horror",
  voice_id: "v_01",
  name_tags: true,
  ...GENRE_DEFAULTS.horror,
  characters: [peak, mind],
  backgrounds: [camp],
};

function cardOf(change: Partial<Card> = {}): Card {
  return {
    id: "k_01",
    text: "คืนนั้นเราตั้งแคมป์กันสามคน",
    character_ids: ["c_01"],
    description: "พีคนั่งหน้ากองไฟ",
    motion: "zoom_in",
    flicker: false,
    hold_s: 0,
    edited: false,
    image_status: "no_image",
    audio_status: "no_audio",
    duration_s: 3.5,
    has_image: false,
    has_previous_image: false,
    ...change,
  };
}

function epOf(change: Partial<Ep> = {}): Ep {
  const act = (n: number, name: string) => ({
    id: `a_0${n}`,
    name,
    summary: `สรุปองก์ ${n}`,
    cards_from: `สรุปองก์ ${n}`,
    segments: [{ id: `g_0${n}`, background_id: "b_01", sound: null, cards: [cardOf({ id: `k_0${n}` })] }],
  });
  return {
    id: EP_ID,
    series_id: SERIES_ID,
    n: 4,
    idea: "ห้องน้ำชั้นสาม",
    title: "ห้องน้ำชั้นสาม",
    voice_id: "v_01",
    stage: "cards",
    plot: { characters: [{ id: "c_01", new: false, name: "", tag: "", description: "" }], backgrounds: [{ id: "b_01", new: false, name: "", tag: "", description: "" }] },
    acts: [act(1, "เปิด"), act(2, "ปม")],
    duration_s: 90,
    locked: false,
    ...change,
  };
}

function cardsJob(change: Partial<ToonJob> = {}): ToonJob {
  return { kind: "cards", state: "writing", series_id: SERIES_ID, ep_id: EP_ID, item_id: null, done: 0, total: 1, error: null, cancel_requested: false, ...change };
}

beforeEach(() => vi.stubGlobal("fetch", fetchMock));

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [
    [JOB_PATH, null],
    [SERIES_PATH, series],
    [SOUNDS_PATH, []],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup();
}

describe("รายการ EP ใน Series", () => {
  const listed: ListedEp = { id: EP_ID, n: 4, title: "ห้องน้ำชั้นสาม", stage: "plot", cards: 0, images: 0, rendered_at: null };

  it("#/toon/series/{seriesId} lists the EPs with their number, title, stage and images", async () => {
    open(`#/toon/series/${SERIES_ID}`, [get(`${SERIES_PATH}/eps`, [listed])]);

    const row = await screen.findByRole("listitem");
    expect(row).toHaveTextContent("EP04");
    expect(row).toHaveTextContent("ห้องน้ำชั้นสาม");
    expect(row).toHaveTextContent("ภาพ 0/0");
    expect(row).toHaveTextContent("พล็อต");
    expect(within(row).getAllByRole("link")[0]).toHaveAttribute("href", `#/toon/eps/${EP_ID}`);
    expect(screen.getByRole("link", { name: "ตัวละครและฉากหลัง" })).toHaveAttribute("href", `#/toon/series/${SERIES_ID}/cast`);
  });

  it("a new EP sends its idea, starts its Plot job and opens its page", async () => {
    const user = open(`#/toon/series/${SERIES_ID}`, [
      get(`${SERIES_PATH}/eps`, []),
      send("POST", `${SERIES_PATH}/eps`, epOf({ stage: "plot" }), 201),
      send("POST", JOBS_PATH, { ...cardsJob(), kind: "plot" }, 202),
    ]);

    await user.click((await screen.findAllByRole("button", { name: "EP ใหม่" }))[0]);
    await user.type(screen.getByRole("textbox", { name: "ไอเดียของ EP ใหม่" }), "เสียงร้องไห้ในห้องน้ำ");
    await user.click(screen.getByRole("button", { name: "ให้ AI ร่างพล็อต" }));

    await waitFor(() => expect(window.location.hash).toBe(`#/toon/eps/${EP_ID}`));
    expect(sent(fetchMock, "POST", `${SERIES_PATH}/eps`)).toEqual([{ idea: "เสียงร้องไห้ในห้องน้ำ" }]);
    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([{ kind: "plot", ep_id: EP_ID }]);
  });

  it("a new EP whose Plot job is refused stays in the list with the reason as a warning", async () => {
    const busy = { code: "gpu_busy", message: "มีงานอื่นใช้การ์ดจออยู่", running: "spoil_voice" };
    const user = open(`#/toon/series/${SERIES_ID}`, [
      get(`${SERIES_PATH}/eps`, []),
      send("POST", `${SERIES_PATH}/eps`, epOf({ stage: "plot" }), 201),
      send("POST", JOBS_PATH, busy, 409),
      get(`${SERIES_PATH}/eps`, [listed]),
    ]);

    await user.click((await screen.findAllByRole("button", { name: "EP ใหม่" }))[0]);
    await user.type(screen.getByRole("textbox", { name: "ไอเดียของ EP ใหม่" }), "เสียงร้องไห้ในห้องน้ำ");
    await user.click(screen.getByRole("button", { name: "ให้ AI ร่างพล็อต" }));

    // jsdom has no colour: the Alert's Tailwind class is the one sign of its tone.
    expect(await findStatusWith("ยังร่างพล็อตไม่ได้")).toHaveClass("bg-warning-surface");
    expect(await screen.findByRole("listitem")).toHaveTextContent("ห้องน้ำชั้นสาม");
    expect(window.location.hash).toBe(`#/toon/series/${SERIES_ID}`);
  });

  it("a new EP whose Plot job gets no answer stays in the list with a warning", async () => {
    const user = open(`#/toon/series/${SERIES_ID}`, [
      get(`${SERIES_PATH}/eps`, []),
      send("POST", `${SERIES_PATH}/eps`, epOf({ stage: "plot" }), 201),
      { method: "POST", path: JOBS_PATH, reply: () => Promise.reject(new TypeError("Failed to fetch")) },
      get(`${SERIES_PATH}/eps`, [listed]),
    ]);

    await user.click((await screen.findAllByRole("button", { name: "EP ใหม่" }))[0]);
    await user.type(screen.getByRole("textbox", { name: "ไอเดียของ EP ใหม่" }), "เสียงร้องไห้ในห้องน้ำ");
    await user.click(screen.getByRole("button", { name: "ให้ AI ร่างพล็อต" }));

    expect(await findStatusWith(OFFLINE_TEXT)).toHaveClass("bg-warning-surface");
    expect(screen.getByText("ยังร่างพล็อตไม่ได้")).toBeInTheDocument();
    expect(await screen.findByRole("listitem")).toHaveTextContent("ห้องน้ำชั้นสาม");
    expect(screen.queryByRole("textbox", { name: "ไอเดียของ EP ใหม่" })).not.toBeInTheDocument();
  });

  it("a refused new EP says why and starts no job", async () => {
    const refused = { code: "invalid_idea", message: "ไอเดียยาวได้ไม่เกิน 500 ตัวอักษร" };
    const user = open(`#/toon/series/${SERIES_ID}`, [get(`${SERIES_PATH}/eps`, []), send("POST", `${SERIES_PATH}/eps`, refused, 400)]);

    await user.click((await screen.findAllByRole("button", { name: "EP ใหม่" }))[0]);
    await user.type(screen.getByRole("textbox", { name: "ไอเดียของ EP ใหม่" }), "เสียง");
    await user.click(screen.getByRole("button", { name: "ให้ AI ร่างพล็อต" }));

    expect(await findStatusWith("สร้าง EP ไม่ได้")).toHaveClass("bg-error-surface");
    expect(screen.getByText(refused.message)).toBeInTheDocument();
    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([]);
  });

  it("an EP whose job runs can't be deleted: the refusal shows", async () => {
    const busy = { code: "ep_busy", message: "EP นี้มีงานที่ยังไม่จบ" };
    const user = open(`#/toon/series/${SERIES_ID}`, [get(`${SERIES_PATH}/eps`, [listed]), send("DELETE", EP_PATH, busy, 409)]);

    await user.click(await screen.findByRole("button", { name: "ลบ EP04" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "ลบ EP" }));

    expect(await screen.findByText("EP นี้มีงานที่ยังไม่จบ")).toBeInTheDocument();
  });
});

describe("พล็อต", () => {
  const drafted = epOf({
    stage: "plot",
    acts: epOf().acts.map((act) => ({ ...act, cards_from: null, segments: [] })),
    plot: {
      characters: [
        { id: "c_01", new: false, name: "", tag: "", description: "" },
        { id: null, new: true, name: "ลุงยาม", tag: "", description: "ชายแก่" },
      ],
      backgrounds: [{ id: "b_01", new: false, name: "", tag: "", description: "" }],
    },
  });

  it("a new character shows ใหม่ and switches to one of the Series' (e2e)", async () => {
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, drafted), send("PATCH", EP_PATH, drafted, 200)]);

    expect(await screen.findByText("ใหม่")).toBeInTheDocument();
    expect(screen.getByText("ลุงยาม")).toBeInTheDocument();
    await user.selectOptions(screen.getByRole("combobox", { name: "ใช้ของในชุดแทน ลุงยาม" }), "c_02");

    expect(sent(fetchMock, "PATCH", EP_PATH)).toEqual([
      { plot: { characters: [{ id: "c_01" }, { id: "c_02" }], backgrounds: [{ id: "b_01" }] } },
    ]);
  });

  it("ยืนยันพล็อต starts the Cards job", async () => {
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, drafted), send("POST", JOBS_PATH, cardsJob(), 202)]);

    await user.click(await screen.findByRole("button", { name: "ยืนยันพล็อต" }));

    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([{ kind: "cards", ep_id: EP_ID, confirm_loss: false }]);
  });

  it("cards_will_be_lost shows what each act loses before the user confirms (e2e)", async () => {
    const changed = epOf({ acts: epOf().acts.map((act, i) => (i === 1 ? { ...act, summary: "สรุปใหม่" } : act)) });
    const lost = {
      code: "cards_will_be_lost",
      message: "การ์ดที่แก้เอง ภาพ หรือเสียงขององก์ที่แตกใหม่จะหาย",
      acts: [{ id: "a_02", name: "ปม", edited: 2, images: 7, audio: 7 }],
    };
    const user = open(`#/toon/eps/${EP_ID}/plot`, [
      get(EP_PATH, changed),
      send("POST", JOBS_PATH, lost, 409),
      send("POST", JOBS_PATH, cardsJob(), 202),
    ]);

    expect(await screen.findByText("• องก์ 2 ปม")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "แตกการ์ดใหม่" }));

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("องก์ 2 ปม: การ์ดแก้เอง 2 ใบ ภาพ 7 ภาพ เสียง 7 เสียง จะหาย");
    expect(dialog).toHaveTextContent("องก์ 1 ไม่เปลี่ยน");
    await user.click(within(dialog).getByRole("button", { name: "แตกการ์ดใหม่" }));

    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([
      { kind: "cards", ep_id: EP_ID, confirm_loss: false },
      { kind: "cards", ep_id: EP_ID, confirm_loss: true },
    ]);
  });
});

describe("เส้นเรื่อง", () => {
  it("#/toon/eps/{epId} opens the storyline of a confirmed EP with its acts, segments and cards", async () => {
    open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf())]);

    expect(await screen.findByRole("heading", { name: "EP04 — เส้นเรื่อง" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "องก์ 1 เปิด" })).toBeInTheDocument();
    const card = screen.getByRole("article", { name: "การ์ด 2" });
    expect(within(card).getByRole("textbox", { name: "ข้อความเล่า" })).toHaveValue("คืนนั้นเราตั้งแคมป์กันสามคน");
    expect(within(card).getByText("พีค")).toBeInTheDocument();
    expect(screen.getAllByRole("combobox", { name: "ฉากหลังของช่วง 1" })[0]).toHaveValue("b_01");
  });

  it("closes every card field while a Cards job of this EP runs (e2e)", async () => {
    // The EP was read before the job started: the running job alone closes the fields.
    open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf({ locked: false })), get(JOB_PATH, cardsJob())]);

    const card = await screen.findByRole("article", { name: "การ์ด 1" });
    expect(within(card).getByRole("textbox", { name: "ข้อความเล่า" })).toBeDisabled();
    expect(within(card).getByRole("textbox", { name: "คำบรรยายภาพ" })).toBeDisabled();
    expect(within(card).getByRole("switch", { name: "ไฟกะพริบ" })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("AI กำลังเขียนการ์ด");
  });

  it("หยุด that the backend refuses says the job didn't stop", async () => {
    const user = open(`#/toon/eps/${EP_ID}`, [
      get(EP_PATH, epOf({ locked: false })),
      get(JOB_PATH, cardsJob()),
      send("DELETE", JOB_PATH, { code: "busy", message: "งานนี้หยุดไม่ได้แล้ว" }, 409),
    ]);

    await user.click(await screen.findByRole("button", { name: "หยุด" }));

    expect(await findStatusWith("หยุดงานไม่ได้")).toHaveClass("bg-error-surface");
    expect(screen.getByText("งานนี้หยุดไม่ได้แล้ว")).toBeInTheDocument();
  });

  it("a storyline of 130 s says it runs past the 60–120 s target (e2e)", async () => {
    open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf({ duration_s: 130 }))]);

    const meter = await screen.findByRole("meter", { name: "ความยาวรวม" });
    expect(meter).toHaveTextContent("130 วิ");
    expect(meter).toHaveTextContent("เป้า 60–120 วิ");
    expect(meter).toHaveTextContent("ยาวเกินเป้า 10 วิ");
  });

  it("an act's name is renamed in its header; left empty it goes back to its name", async () => {
    const renamed = epOf({ acts: epOf().acts.map((act, i) => (i === 0 ? { ...act, name: "เปิดเรื่อง" } : act)) });
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf()), send("PATCH", `${EP_PATH}/acts/a_01`, renamed, 200)]);

    const name = await screen.findByRole("textbox", { name: "ชื่อองก์ 2" });
    await user.clear(name);
    await user.tab();
    expect(name).toHaveValue("ปม");
    const first = screen.getByRole("textbox", { name: "ชื่อองก์ 1" });
    await user.clear(first);
    await user.type(first, "เปิดเรื่อง");
    await user.tab();

    expect(sent(fetchMock, "PATCH", `${EP_PATH}/acts/a_01`)).toEqual([{ name: "เปิดเรื่อง" }]);
    expect(sent(fetchMock, "PATCH", `${EP_PATH}/acts/a_02`)).toEqual([]);
  });

  it("a changed text is sent when the field is left; the answer shows the card as แก้เอง", async () => {
    const answer = epOf({ acts: epOf().acts.map((act, i) => (i === 0 ? { ...act, segments: [{ ...act.segments[0], cards: [cardOf({ text: "ข้อความใหม่", edited: true })] }] } : act)) });
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf()), send("PATCH", `${EP_PATH}/cards/k_01`, answer, 200)]);

    const field = within(await screen.findByRole("article", { name: "การ์ด 1" })).getByRole("textbox", { name: "ข้อความเล่า" });
    await user.clear(field);
    await user.type(field, "ข้อความใหม่");
    await user.tab();

    expect(sent(fetchMock, "PATCH", `${EP_PATH}/cards/k_01`)).toEqual([{ text: "ข้อความใหม่" }]);
    expect(await within(screen.getByRole("article", { name: "การ์ด 1" })).findByText("แก้เอง")).toBeInTheDocument();
  });

  it("a refused edit says บันทึกไม่ได้ and the card stays; sent again and taken, the notice goes", async () => {
    const answer = epOf({ acts: epOf().acts.map((act, i) => (i === 0 ? { ...act, segments: [{ ...act.segments[0], cards: [cardOf({ text: "ข้อความใหม่", edited: true })] }] } : act)) });
    const locked = { code: "ep_busy", message: "EP นี้มีงานทำอยู่" };
    const user = open(`#/toon/eps/${EP_ID}`, [
      get(EP_PATH, epOf()),
      send("PATCH", `${EP_PATH}/cards/k_01`, locked, 409),
      send("PATCH", `${EP_PATH}/cards/k_01`, answer, 200),
    ]);

    const field = within(await screen.findByRole("article", { name: "การ์ด 1" })).getByRole("textbox", { name: "ข้อความเล่า" });
    await user.clear(field);
    await user.type(field, "ข้อความใหม่");
    await user.tab();

    expect(await screen.findByText("บันทึกไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("EP นี้มีงานทำอยู่")).toBeInTheDocument();
    expect(within(screen.getByRole("article", { name: "การ์ด 1" })).queryByText("แก้เอง")).not.toBeInTheDocument();

    // The field still differs from the card, so leaving it again sends again; the second answer takes it.
    await user.type(field, "!");
    await user.tab();

    expect(await within(screen.getByRole("article", { name: "การ์ด 1" })).findByText("แก้เอง")).toBeInTheDocument();
    expect(screen.queryByText("บันทึกไม่ได้")).not.toBeInTheDocument();
  });
});

describe("ภาพการ์ดและเสียงเล่า", () => {
  function imageJob(change: Partial<ToonJob> = {}): ToonJob {
    return { ...cardsJob(), kind: "image", state: "drawing", card_ids: ["k_01", "k_02"], scope: "missing", done: 1, total: 2, skipped: 0, missing_refs: [], failed_cards: [], ...change };
  }
  const drawn = (...ids: string[]) =>
    epOf({
      acts: epOf().acts.map((act) => ({
        ...act,
        segments: act.segments.map((segment) => ({
          ...segment,
          cards: segment.cards.map((card) => (ids.includes(card.id) ? { ...card, image_status: "ready" as const, has_image: true } : card)),
        })),
      })),
    });

  afterEach(() => vi.useRealTimers());

  it("while an Image job draws, the second card's picture shows once done goes from 1 to 2 (e2e)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // A third card keeps the job drawing once the second picture is in.
    const job = phased(JOB_PATH, imageJob(), imageJob({ done: 2, total: 3, card_ids: ["k_01", "k_02", "k_03"] }));
    const ep = phased(EP_PATH, drawn("k_01"), drawn("k_01", "k_02"));
    open(`#/toon/eps/${EP_ID}`, [job.route, ep.route]);

    const second = await screen.findByRole("article", { name: "การ์ด 2" });
    expect(screen.getByRole("img", { name: "ภาพการ์ด 1" })).toBeInTheDocument();
    expect(within(second).getByText("กำลังวาด…")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("กำลังสร้างภาพ 1/2");
    job.phases.at = 1;
    ep.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1000));

    expect(await within(second).findByRole("img", { name: "ภาพการ์ด 2" })).toHaveAttribute(
      "src",
      expect.stringMatching(new RegExp(`^${EP_PATH}/cards/k_02/image\\?v=`)),
    );
  });

  it("drawing what is missing with cards skipped shows how many and what needs a reference image first (e2e)", async () => {
    const skipping = imageJob({
      state: "translating",
      done: 0,
      total: 1,
      card_ids: ["k_01"],
      skipped: 1,
      missing_refs: [{ item_kind: "characters", id: "c_03", name: "ลุงยาม", cards: 1 }],
    });
    const job = phased(JOB_PATH, null, skipping); // the page reads the job again once it started
    const user = open(`#/toon/eps/${EP_ID}`, [job.route, get(EP_PATH, epOf()), send("POST", JOBS_PATH, skipping, 202)]);

    const button = await screen.findByRole("button", { name: "สร้างภาพที่ขาดทั้งหมด" });
    job.phases.at = 1;
    await user.click(button);

    expect(await screen.findByRole("status")).toHaveTextContent("ข้าม 1");
    const needs = screen.getByRole("region", { name: "ต้องสร้างภาพอ้างอิงก่อน" });
    expect(needs).toHaveTextContent("การ์ด 1 ใบยังวาดไม่ได้");
    expect(needs).toHaveTextContent("ตัวละคร ลุงยาม");
    expect(within(needs).getByRole("link", { name: "ไปสร้างภาพอ้างอิง" })).toHaveAttribute("href", `#/toon/series/${SERIES_ID}/cast`);
    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([{ ep_id: EP_ID, kind: "image", scope: "missing" }]);
  });

  it("nothing_to_draw lists what needs a reference image first", async () => {
    const refusal = { code: "nothing_to_draw", message: "ไม่มีการ์ดให้สร้างภาพ", missing_refs: [{ item_kind: "backgrounds", id: "b_02", name: "ห้องน้ำ", cards: 2 }] };
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, epOf()), send("POST", JOBS_PATH, refusal, 400)]);

    await user.click(await screen.findByRole("button", { name: "สร้างภาพที่ขาดทั้งหมด" }));

    expect(await screen.findByRole("region", { name: "ต้องสร้างภาพอ้างอิงก่อน" })).toHaveTextContent("ฉากหลัง ห้องน้ำ");
  });

  it("สร้างเสียง starts a Voice job of the card; a card with narration offers ฟัง and สร้างใหม่", async () => {
    const voiced = epOf({
      acts: epOf().acts.map((act, i) => ({
        ...act,
        segments: act.segments.map((segment) => ({
          ...segment,
          cards: segment.cards.map((card) => (i === 1 ? { ...card, audio_status: "ready" as const } : card)),
        })),
      })),
    });
    const voicing: ToonJob = { ...imageJob(), kind: "voice", state: "voicing", scope: null, card_ids: ["k_01"], done: 0, total: 1 };
    const job = phased(JOB_PATH, null, voicing);
    const user = open(`#/toon/eps/${EP_ID}`, [job.route, get(EP_PATH, voiced), send("POST", JOBS_PATH, voicing, 202)]);

    const first = await screen.findByRole("article", { name: "การ์ด 1" });
    job.phases.at = 1;
    const second = screen.getByRole("article", { name: "การ์ด 2" });
    expect(within(second).getByRole("button", { name: "ฟัง" })).toBeInTheDocument();
    expect(within(second).getByRole("button", { name: "สร้างใหม่" })).toBeInTheDocument();
    await user.click(within(first).getByRole("button", { name: "สร้างเสียง" }));

    expect(sent(fetchMock, "POST", JOBS_PATH)).toEqual([{ ep_id: EP_ID, kind: "voice", card_id: "k_01" }]);
    expect(await within(first).findByText("กำลังสร้างเสียง…")).toBeInTheDocument();
  });

  it("ฟัง plays the card's own narration", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    const voiced = epOf({
      acts: epOf().acts.map((act, i) => ({
        ...act,
        segments: act.segments.map((segment) => ({
          ...segment,
          cards: segment.cards.map((card) => (i === 1 ? { ...card, audio_status: "ready" as const } : card)),
        })),
      })),
    });
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, voiced)]);

    const second = await screen.findByRole("article", { name: "การ์ด 2" });
    await user.click(within(second).getByRole("button", { name: "ฟัง" }));

    expect(play).toHaveBeenCalledOnce();
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toContain(`/api/toon/eps/${EP_ID}/cards/k_02/audio?v=`);
  });

  it("สลับภาพก่อนหน้า swaps the card's picture back", async () => {
    const withPrevious = drawn("k_01");
    withPrevious.acts[0].segments[0].cards[0].has_previous_image = true;
    const user = open(`#/toon/eps/${EP_ID}`, [get(EP_PATH, withPrevious), send("POST", `${EP_PATH}/cards/k_01/swap-image`, withPrevious, 200)]);

    const before = (await screen.findByRole("img", { name: "ภาพการ์ด 1" })).getAttribute("src");
    await user.click(screen.getByRole("button", { name: "สลับภาพก่อนหน้า" }));

    expect(sent(fetchMock, "POST", `${EP_PATH}/cards/k_01/swap-image`)).toEqual([{}]);
    // The card's picture loads again: it is the one it had before.
    await waitFor(() => expect(screen.getByRole("img", { name: "ภาพการ์ด 1" }).getAttribute("src")).not.toBe(before));
  });
});
