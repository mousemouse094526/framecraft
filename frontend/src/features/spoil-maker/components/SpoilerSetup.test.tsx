import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { get, jsonResponse, phased, type Route, send, sent as sentTo, serve } from "./testBackend";
import {
  CLIPS_PATH,
  CURRENT_PATH,
  cutOf,
  DRAFT_PATH,
  EMPTY_DRAFT,
  EPISODES,
  epOf,
  FILM,
  jobOf,
  JOBS_PATH,
  ORDER,
  OTHER,
  REVIEW_HASH,
  SETTINGS_PATH,
  setupDefaults,
  UNCLE,
  UNDESCRIBED,
  UNTRANSCRIBED,
  VOICES_PATH,
} from "./setupFixtures";

/** Fake backend: the first matching route answers; one of several for a path answers once, the last keeps answering. */
function backend(routes: Route[]) {
  serve(fetchMock, routes, setupDefaults());
}

const reads = (path: string) =>
  fetchMock.mock.calls.filter(([input, init]) => String(input) === path && (init?.method ?? "GET") === "GET").length;

async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
}

async function openSetup() {
  window.location.hash = "#/spoil";
  render(<App />);
  await screen.findByRole("region", { name: "เลือกคลิป" });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

/** Opens the setup and picks FILM; resolves once its EPs are listed. */
async function pickFilm() {
  const user = await openSetup();
  await user.click(screen.getByRole("radio", { name: `เลือก ${FILM.title}` }));
  await screen.findByRole("radio", { name: "เลือก EP 1" });
  return user;
}

const draftButton = () => screen.getByRole("button", { name: "ร่างบท" });
const epRow = (n: number) => screen.getByRole("radio", { name: `เลือก EP ${n}` }).closest("label") as HTMLElement;

const fetchMock = vi.fn<typeof fetch>();
const sent = (method: string, path: string) => sentTo(fetchMock, method, path);

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  window.location.hash = "";
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
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

  it("picking a clip lists its EPs with their range and renders, one clip and one EP at a time", async () => {
    backend([]);
    const user = await pickFilm();

    expect(within(epRow(1)).getByText("0:00–29:59")).toBeInTheDocument();
    expect(within(epRow(2)).getByText("29:59–1:00:00")).toBeInTheDocument();
    expect(within(epRow(2)).getByText("render แล้ว 2")).toBeInTheDocument();
    expect(epRow(2).querySelector("img[src*='/shots/']")).toHaveAttribute("src", `/api/spoil-maker/clips/${FILM.id}/shots/20.jpg`);
    expect(screen.getByRole("radio", { name: "เลือก EP 1" })).toBeChecked();
    await user.click(screen.getByRole("radio", { name: "เลือก EP 2" }));
    expect(screen.getByRole("radio", { name: "เลือก EP 2" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "เลือก EP 1" })).not.toBeChecked();

    await user.click(screen.getByRole("radio", { name: `เลือก ${OTHER.title}` }));
    expect(screen.getByRole("radio", { name: `เลือก ${FILM.title}` })).not.toBeChecked();
    expect(await screen.findByText("0:00–23:40")).toBeInTheDocument();
  });

  it("an EP over 32,000 tokens can't be drafted and the meter says so", async () => {
    backend([get(EPISODES, cutOf({ episodes: [epOf(1, 0, 3600, { tokens: 40_000 })] }))]);
    await pickFilm();

    expect(screen.getByText("40,000 / 32,000")).toBeInTheDocument();
    expect(screen.getByText("Transcript ของ EP นี้ 40,000 token เกิน 32,000")).toBeInTheDocument();
    expect(draftButton()).toBeDisabled();
  });

  it("an EP without lines, or without a token count, can't be drafted and says why", async () => {
    const episodes = [epOf(1, 0, 1799, { lines: 0 }), epOf(2, 1799, 3600, { tokens: null })];
    backend([get(EPISODES, cutOf({ episodes, tokens_not_ready: "ยังติดตั้งไม่ครบ: Qwen3.5 9B model" }))]);
    const user = await pickFilm();

    expect(screen.getByText("EP นี้ไม่มีบทพูด")).toBeInTheDocument();
    expect(draftButton()).toBeDisabled();
    await user.click(screen.getByRole("radio", { name: "เลือก EP 2" }));
    expect(screen.getByText(/^ยังติดตั้งไม่ครบ: Qwen3.5 9B model/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปที่ Setup status" })).toHaveAttribute("href", "#/setup");
    expect(draftButton()).toBeDisabled();
  });

  it("a new length per EP is sent; with cuts moved by hand it asks first", async () => {
    backend([send("PUT", EPISODES, cutOf({ minutes: 25 }), 200)]);
    const user = await pickFilm();

    await user.selectOptions(screen.getByRole("combobox", { name: "ความยาวต่อ EP" }), "25");

    expect(sent("PUT", EPISODES)).toEqual([{ minutes: 25 }]);
  });

  it("with cuts moved by hand, a new length asks first and ตัดใหม่ตามความยาว cuts again", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    backend([get(EPISODES, cutOf({ custom: true })), send("PUT", EPISODES, cutOf(), 200)]);
    const user = await pickFilm();

    await user.selectOptions(screen.getByRole("combobox", { name: "ความยาวต่อ EP" }), "25");
    expect(confirm).toHaveBeenCalledWith("จุดตัดที่เลื่อนเองจะหาย เปลี่ยนความยาวต่อ EP ไหม");
    expect(sent("PUT", EPISODES)).toEqual([]);

    await user.click(screen.getByRole("button", { name: "ตัดใหม่ตามความยาว" }));
    expect(sent("PUT", EPISODES)).toEqual([{ minutes: 30 }]);
  });

  it("a cut changed and left sends every cut; a refusal says why", async () => {
    backend([
      send("PUT", EPISODES, { code: "invalid_episodes", message: "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา" }, 400),
    ]);
    const user = await pickFilm();
    const field = screen.getByRole("textbox", { name: "จุดตัดระหว่าง EP 1 กับ EP 2" });

    await user.clear(field);
    await user.type(field, "1:59:00");
    await user.tab();

    expect(sent("PUT", EPISODES)).toEqual([{ minutes: 30, cuts: [7140] }]);
    expect(await screen.findByText("ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา")).toBeInTheDocument();
  });

  it("ร่างบท waits for a cut being saved and sends the clip and the EP's range from it", async () => {
    let answer: (response: Response) => void = () => {};
    const moved = cutOf({ custom: true, episodes: [epOf(1, 0, 1001), epOf(2, 1001, 3600)] });
    const current = phased(CURRENT_PATH, null, jobOf({}));
    backend([
      { method: "PUT", path: EPISODES, reply: () => new Promise<Response>((resolve) => (answer = resolve)) },
      send("POST", JOBS_PATH, jobOf({}), 202),
      current.route,
    ]);
    const user = await pickFilm();
    await user.click(screen.getByRole("radio", { name: "เลือก EP 2" }));
    const field = screen.getByRole("textbox", { name: "จุดตัดระหว่าง EP 1 กับ EP 2" });
    await user.clear(field);
    await user.type(field, "16:40");

    await user.click(draftButton()); // leaving the field saves the cut first
    expect(sent("POST", JOBS_PATH)).toEqual([]);
    current.phases.at = 1; // the job the POST starts
    await act(async () => answer(jsonResponse(moved)));

    await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });
    expect(window.location.hash).toBe(REVIEW_HASH);
    expect(sent("POST", JOBS_PATH)).toEqual([
      {
        kind: "draft",
        clip_id: FILM.id,
        ep: { n: 2, start_s: 1001, end_s: 3600 },
        style: "drama",
        layout: "B",
        target_s: 60,
        voice_id: UNCLE.id,
        replace: false,
      },
    ]);
  });

  it("episodes_changed says so and reads the EPs again", async () => {
    backend([
      send("POST", JOBS_PATH, { code: "episodes_changed", message: "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง" }, 409),
    ]);
    const user = await pickFilm();
    expect(reads(EPISODES)).toBe(1);

    await user.click(draftButton());

    expect(await screen.findByText("การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง")).toBeInTheDocument();
    expect(reads(EPISODES)).toBe(2);
  });

  it("with a Spoil draft of EP 2, its clip and EP are picked and marked", async () => {
    backend([
      get(DRAFT_PATH, { ...EMPTY_DRAFT, clip_id: FILM.id, clip_title: FILM.title, ep: { n: 2, start_s: 1799, end_s: 3600 } }),
      get(EPISODES, cutOf({ episodes: [epOf(1, 0, 1799), epOf(2, 1799, 3600, { in_draft: true })] })),
    ]);
    await openSetup();

    expect(screen.getByRole("radio", { name: `เลือก ${FILM.title}` })).toBeChecked();
    expect(await screen.findByRole("radio", { name: "เลือก EP 2" })).toBeChecked();
    expect(within(epRow(2)).getByText("อยู่ใน Spoil draft")).toBeInTheDocument();
  });

  it("a clip not described can't be picked and says why, with a way to the คลิป tab", async () => {
    backend([get(CLIPS_PATH, { clips: [FILM, UNDESCRIBED, UNTRANSCRIBED] })]);
    await openSetup();

    const undescribed = screen.getByRole("listitem", { name: "ไททัน ตอนที่ 3" });
    expect(within(undescribed).getByRole("radio")).toBeDisabled();
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
    backend([get(VOICES_PATH, [])]);
    await pickFilm();

    expect(screen.getByRole("link", { name: "สร้างเสียงบรรยาย" })).toHaveAttribute("href", "#/spoil/voices");
    expect(draftButton()).toBeDisabled();
  });

  it("starts from the voice of the last draft", async () => {
    const sister = { ...UNCLE, id: "v_1111abcd", name: "พี่สาว" };
    backend([
      get(VOICES_PATH, [UNCLE, sister]),
      get(SETTINGS_PATH, { watermarks: [], original_volume: 20, last_voice_id: sister.id, ep_minutes: 30 }),
    ]);
    await openSetup();

    expect(screen.getByRole("combobox", { name: "เสียงบรรยาย" })).toHaveValue(sister.id);
  });

  it("ร่างบท opens ตรวจแก้บท on the draft's progress card, then reads the draft once it is done (D81)", async () => {
    const current = phased(
      CURRENT_PATH,
      null,
      jobOf({}),
      jobOf({ state: "polishing" }),
      jobOf({ state: "matching", done: 4, total: 12 }),
      jobOf({ state: "done", done: 12, total: 12 }),
    );
    backend([send("POST", JOBS_PATH, jobOf({}), 202), current.route]);
    const user = await pickFilm();

    current.phases.at = 1;
    await user.click(draftButton());

    expect(window.location.hash).toBe(REVIEW_HASH);
    const card = await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });
    expect(screen.queryByRole("link", { name: "ไปที่ตั้งค่าคลิปสปอย" })).not.toBeInTheDocument();
    expect(within(card).getByText(`${FILM.title} · EP 1`)).toBeInTheDocument();
    expect(within(card).getByText("เล่าละครหักมุม · 60 วินาที")).toBeInTheDocument();
    expect(within(card).getByRole("listitem", { current: "step" })).toHaveTextContent("เขียนบท");
    current.phases.at = 2;
    await nextPoll();
    expect(within(card).getByRole("listitem", { current: "step" })).toHaveTextContent("เรียบเรียง");
    current.phases.at = 3;
    await nextPoll();
    expect(within(card).getByRole("listitem", { current: "step" })).toHaveTextContent("เลือกภาพ 4/12");
    const draftReads = reads(DRAFT_PATH);
    current.phases.at = 4;
    await nextPoll();
    expect(await screen.findByRole("link", { name: "ไปที่ตั้งค่าคลิปสปอย" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "ความคืบหน้าการร่างบท" })).not.toBeInTheDocument();
    expect(reads(DRAFT_PATH)).toBeGreaterThan(draftReads);
  });

  it("with a Spoil draft there, asks before sending replace: true", async () => {
    const current = phased(CURRENT_PATH, null, jobOf({}));
    backend([get(DRAFT_PATH, EMPTY_DRAFT), send("POST", JOBS_PATH, jobOf({}), 202), current.route]);
    const user = await pickFilm();

    await user.click(draftButton());

    expect(screen.getByText("มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม")).toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([]);
    current.phases.at = 1;
    await user.click(screen.getByRole("button", { name: "ร่างทับ" }));
    await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });
    expect(window.location.hash).toBe(REVIEW_HASH);
    expect(sent("POST", JOBS_PATH)).toEqual([expect.objectContaining({ replace: true })]);
  });

  it("while a draft runs, step 1 shows its order, every field locked and no ร่างบท (D82)", async () => {
    backend([get(CURRENT_PATH, jobOf({ order: { ...ORDER, style: "fast", layout: "A", target_s: 90 } }))]);
    await openSetup();

    expect(await screen.findByText(`กำลังร่างบท ${FILM.title} · EP 1: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้`)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปที่ตรวจแก้บท" })).toHaveAttribute("href", REVIEW_HASH);
    expect(screen.getByRole("radio", { name: `เลือก ${FILM.title}` })).toBeChecked();
    expect(screen.getByRole("radio", { name: `เลือก ${FILM.title}` })).toBeDisabled();
    expect(await screen.findByRole("radio", { name: "เลือก EP 1" })).toBeDisabled();
    expect(screen.getByRole("radio", { name: "ปั่นตัดเร็ว" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "ปั่นตัดเร็ว" })).toBeDisabled();
    expect(screen.getByRole("radio", { name: "Layout A" })).toBeChecked();
    expect(screen.getByRole("slider", { name: "ความยาว" })).toHaveValue("90");
    expect(screen.queryByRole("button", { name: "ร่างบท" })).not.toBeInTheDocument();
  });

  it("locked on an order whose clip and voice are gone: the clip's title, and เสียงถูกลบแล้ว (D87)", async () => {
    backend([get(CURRENT_PATH, jobOf({ order: { ...ORDER, clip_id: "zzzzzzzzzzz", clip_title: "คลิปที่ลบแล้ว", voice_id: "v_0000dead" } }))]);
    await openSetup();

    // Once in the form, once in the step bar's line for step 1 (D87).
    expect(await screen.findAllByText("คลิปที่ลบแล้ว · EP 1")).toHaveLength(2);
    expect(screen.queryByRole("region", { name: "เลือก EP" })).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "เสียงบรรยาย" })).toHaveDisplayValue("เสียงถูกลบแล้ว");
  });

  it("after a cancelled draft, its order is picked again and the fields can change (D87)", async () => {
    backend([get(CURRENT_PATH, jobOf({ state: "cancelled", order: { ...ORDER, ep: { n: 2, start_s: 1799, end_s: 3600 }, target_s: 120 } }))]);
    await openSetup();

    expect(await screen.findByRole("radio", { name: "เลือก EP 2" })).toBeChecked();
    expect(screen.getByRole("radio", { name: `เลือก ${FILM.title}` })).toBeEnabled();
    expect(screen.getByRole("slider", { name: "ความยาว" })).toHaveValue("120");
    expect(draftButton()).toBeEnabled();
  });

  it("after a cancelled draft whose EP the cut no longer has, the first EP is picked (spec › Frontend)", async () => {
    backend([get(CURRENT_PATH, jobOf({ state: "cancelled", order: { ...ORDER, ep: { n: 2, start_s: 1500, end_s: 3600 } } }))]);
    await openSetup();

    expect(await screen.findByRole("radio", { name: "เลือก EP 1" })).toBeChecked();
  });

  it("after a cancelled draft whose voice was deleted, the form starts from a voice still saved (D87)", async () => {
    backend([get(CURRENT_PATH, jobOf({ state: "cancelled", order: { ...ORDER, voice_id: "v_0000dead" } }))]);
    await openSetup();

    expect(await screen.findByRole("combobox", { name: "เสียงบรรยาย" })).toHaveDisplayValue(UNCLE.name);
  });

  it("busy from ร่างบท says มีงานร่างบทอยู่แล้ว and reads the steps again (D87)", async () => {
    backend([send("POST", JOBS_PATH, { code: "busy", message: "กำลังร่างบทอยู่" }, 409), get(CURRENT_PATH, null), get(CURRENT_PATH, jobOf({}))]);
    const user = await pickFilm();

    await user.click(draftButton());

    expect(await screen.findByText("มีงานร่างบทอยู่แล้ว")).toBeInTheDocument();
    expect(await screen.findByText(`กำลังร่างบท ${FILM.title} · EP 1: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้`)).toBeInTheDocument();
  });

  it("each style says how it tells the story (D84)", async () => {
    backend([]);
    await openSetup();

    expect(screen.getByRole("radio", { name: "ปั่นตัดเร็ว" })).toHaveAccessibleDescription("ประโยคสั้น ตลก เร็ว เล่าเหตุการณ์เด่น");
    expect(screen.getByRole("radio", { name: "เล่าละครหักมุม" })).toHaveAccessibleDescription(
      "hook เรื่อง หักมุม แรงจูงใจ คำถามชวนคอมเมนต์ท้ายคลิป",
    );
    expect(screen.getByRole("radio", { name: "เล่าตามลำดับ" })).toHaveAccessibleDescription("เล่าทีละฉากตามเวลา มีบทพูดตัวละครแทรกได้");
  });

  it("gpu_busy names the running job", async () => {
    backend([send("POST", JOBS_PATH, { code: "gpu_busy", message: "รอให้งานบรรยายฉากเสร็จก่อน", running: "describe" }, 409)]);
    const user = await pickFilm();

    await user.click(draftButton());

    expect(await screen.findByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();
  });
});
