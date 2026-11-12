import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { get, jsonResponse, phased, type Route, send, sent as sentTo, serve } from "../../../testing/testBackend";
import { CURRENT_PATH, DRAFT_PATH, EMPTY_DRAFT, FILM, jobOf, JOBS_PATH, ORDER, REVIEW_HASH, setupDefaults } from "./setupFixtures";

// ตรวจแก้บท while a whole new draft runs and after it ends (spoil-maker seam 2, D81, D83, D85–D88).

const fetchMock = vi.fn<typeof fetch>();
const sent = (method: string, path: string) => sentTo(fetchMock, method, path);

function backend(routes: Route[]) {
  serve(fetchMock, routes, setupDefaults());
}

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

describe("ร่างบทที่ขั้นตรวจแก้ (D81, D83, D85–D87)", () => {
  async function openReview() {
    window.location.hash = REVIEW_HASH;
    render(<App />);
    return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  }

  it("ยกเลิก says กำลังยกเลิก until the job stops, then opens step 1 with the order picked", async () => {
    const current = phased(CURRENT_PATH, jobOf({}), jobOf({ cancel_requested: true }), jobOf({ state: "cancelled", cancel_requested: true }));
    backend([current.route, send("DELETE", CURRENT_PATH, jobOf({ cancel_requested: true }), 202)]);
    const user = await openReview();
    const cancel = await screen.findByRole("button", { name: "ยกเลิก" });

    current.phases.at = 1; // what the backend says once the cancel is asked
    await user.click(cancel);

    expect(sent("DELETE", CURRENT_PATH)).toHaveLength(1);
    expect(screen.getByText("กำลังยกเลิก")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ยกเลิก" })).toBeDisabled();
    await nextPoll();
    expect(window.location.hash).toBe(REVIEW_HASH); // still cancelling: the job hasn't stopped (D85)
    current.phases.at = 2;
    await nextPoll();
    expect(await screen.findByRole("region", { name: "เลือกคลิป" })).toBeInTheDocument();
    expect(window.location.hash).toBe("#/spoil");
    expect(await screen.findByRole("radio", { name: "เลือก EP 1" })).toBeChecked();
  });

  it("a job that ends done after ยกเลิก shows the script with ยกเลิกไม่ทัน บทร่างเสร็จแล้ว", async () => {
    const current = phased(CURRENT_PATH, jobOf({}), jobOf({ state: "done", cancel_requested: true }));
    backend([current.route, send("DELETE", CURRENT_PATH, jobOf({ cancel_requested: true }), 202)]);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));
    current.phases.at = 1;
    await nextPoll();

    expect(await screen.findByText("ยกเลิกไม่ทัน บทร่างเสร็จแล้ว")).toBeInTheDocument();
    expect(window.location.hash).toBe(REVIEW_HASH);
  });

  it("a failed draft says why; ลองอีกครั้ง asks before replacing the draft there, then sends the order again", async () => {
    const failed = jobOf({ state: "failed", error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } });
    const current = phased(CURRENT_PATH, failed, jobOf({}));
    backend([current.route, get(DRAFT_PATH, EMPTY_DRAFT), send("POST", JOBS_PATH, jobOf({}), 202)]);
    const user = await openReview();

    expect(await screen.findByText("AI ร่างบทไม่สำเร็จ 3 ครั้ง")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับไปแก้ตั้งค่า" })).toHaveAttribute("href", "#/spoil");
    await user.click(screen.getByRole("button", { name: "ลองอีกครั้ง" }));
    expect(screen.getByText("มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม")).toBeInTheDocument();
    expect(sent("POST", JOBS_PATH)).toEqual([]);
    current.phases.at = 1;
    await user.click(screen.getByRole("button", { name: "ร่างทับ" }));

    const { clip_title: _title, story_title: _story, ...order } = ORDER;
    expect(sent("POST", JOBS_PATH)).toEqual([{ kind: "draft", ...order, replace: true }]);
    expect(await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" })).toBeInTheDocument();
  });

  it("ลองอีกครั้ง refused as episodes_changed says so and offers only กลับไปแก้ตั้งค่า", async () => {
    const failed = jobOf({ state: "failed", error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } });
    const changed = { code: "episodes_changed", message: "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง" };
    backend([get(CURRENT_PATH, failed), send("POST", JOBS_PATH, changed, 409)]);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "ลองอีกครั้ง" }));

    expect(await screen.findByText("การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "ลองอีกครั้ง" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับไปแก้ตั้งค่า" })).toBeInTheDocument();
  });

  it("ลองอีกครั้ง refused as story_not_found says so and offers only กลับไปแก้ตั้งค่า (story-kb spec › Frontend)", async () => {
    const failed = jobOf({ state: "failed", order: { ...ORDER, story_id: "st_000000ff", story_title: "เรื่องที่ลบแล้ว" }, error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } });
    const gone = { code: "story_not_found", message: "ไม่พบเรื่องนี้ในคลังความรู้แล้ว" };
    backend([get(CURRENT_PATH, failed), send("POST", JOBS_PATH, gone, 400)]);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "ลองอีกครั้ง" }));

    expect(await screen.findByText("ไม่พบเรื่องนี้ในคลังความรู้แล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "ลองอีกครั้ง" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับไปแก้ตั้งค่า" })).toBeInTheDocument();
  });

  it("กลับไปแก้ตั้งค่า after a failure opens step 1 with the order picked", async () => {
    const failed = jobOf({ state: "failed", order: { ...ORDER, ep: { n: 2, start_s: 1799, end_s: 3600 } }, error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } });
    backend([get(CURRENT_PATH, failed)]);
    const user = await openReview();

    await user.click(await screen.findByRole("link", { name: "กลับไปแก้ตั้งค่า" }));

    expect(await screen.findByRole("radio", { name: "เลือก EP 2" })).toBeChecked();
  });

  it("a job that goes away while its card shows says งานหยุดกลางทาง", async () => {
    const current = phased(CURRENT_PATH, jobOf({}), null);
    backend([current.route]);
    await openReview();
    await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });

    current.phases.at = 1;
    await nextPoll();

    expect(await screen.findByText("งานหยุดกลางทาง")).toBeInTheDocument();
  });

  it("a failed poll while the card shows says offline, then the card comes back once the backend answers", async () => {
    let down = false;
    backend([{ path: CURRENT_PATH, reply: () => (down ? Promise.reject(new TypeError("offline")) : jsonResponse(jobOf({}))) }]);
    await openReview();
    await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });

    down = true;
    await nextPoll();
    expect(await screen.findByRole("heading", { name: "Backend offline" })).toBeInTheDocument();
    down = false;
    await nextPoll();

    expect(await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" })).toBeInTheDocument();
  });

  it("a job of another kind in place of the card's says งานหยุดกลางทาง", async () => {
    const current = phased(CURRENT_PATH, jobOf({}), jobOf({ kind: "pick", state: "matching", done: 0, total: 1, order: null }));
    backend([current.route]);
    await openReview();
    await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });

    current.phases.at = 1;
    await nextPoll();

    expect(await screen.findByText("งานหยุดกลางทาง")).toBeInTheDocument();
  });

  it("a draft that ends done while step 1 is open stays on step 1", async () => {
    const current = phased(CURRENT_PATH, jobOf({}), jobOf({ state: "done", done: 12, total: 12 }));
    backend([current.route]);
    await openSetup();
    await screen.findByText(`กำลังร่างบท ${FILM.title} · EP 1: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้`);

    current.phases.at = 1;
    await nextPoll();

    expect(window.location.hash).toBe("#/spoil");
    expect(await screen.findByRole("button", { name: "ร่างบท" })).toBeInTheDocument();
  });

  it("the failure's Alert stays until a new Draft job starts, of any kind (D87)", async () => {
    const failed = jobOf({ state: "failed", error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" } });
    const pick = jobOf({ kind: "pick", state: "matching", done: 0, total: 1, order: null });
    const current = phased(CURRENT_PATH, failed, pick);
    const sentence = {
      id: "s_00000001",
      text: "ประโยคแรก",
      refs: [{ clip_id: EMPTY_DRAFT.clip_id, line: 0 }],
      shots: [null, null],
      edited: false,
      audio: null,
      status: "no_shot",
      estimated_s: 2,
      ref_lines: [],
      window: null,
    };
    backend([current.route, get(DRAFT_PATH, { ...EMPTY_DRAFT, sentences: [sentence] }), send("POST", JOBS_PATH, pick, 202)]);
    const user = await openReview();
    expect(await screen.findByText("AI ร่างบทไม่สำเร็จ 3 ครั้ง")).toBeInTheDocument();

    current.phases.at = 1;
    // ต้องให้ poll อ่านรอบใหม่ก่อน: ปุ่ม "เลือก Shot ใหม่" มีเฉพาะตอนที่ UI เห็น pick job แล้ว
    // (shouldAdvanceTime: true ทำให้บางรอบ poll ยังไม่ทันยิง → getByRole ไม่เจอปุ่ม)
    await nextPoll();
    await user.click(await screen.findByRole("button", { name: "เลือก Shot ใหม่" }));
    expect(sent("POST", JOBS_PATH)).toHaveLength(1);

    await nextPoll();
    // poll รอบใหม่ต้องมาถึงก่อน alert จึงหาย (shouldAdvanceTime ทำให้ลำดับ poll ไม่แน่นอน)
    await waitFor(() => expect(screen.queryByText("AI ร่างบทไม่สำเร็จ 3 ครั้ง")).not.toBeInTheDocument());
  });

  it("ยกเลิก with no answer from the backend says offline", async () => {
    backend([get(CURRENT_PATH, jobOf({})), { method: "DELETE", path: CURRENT_PATH, reply: () => Promise.reject(new TypeError("offline")) }]);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));

    expect(await screen.findByRole("heading", { name: "Backend offline" })).toBeInTheDocument();
  });

  it("step 1 open while another tab's draft fails starts again from that draft's order", async () => {
    const current = phased(
      CURRENT_PATH,
      jobOf({ order: { ...ORDER, target_s: 120 } }),
      jobOf({ state: "failed", order: { ...ORDER, target_s: 120 }, error: { code: "draft_failed", message: "x" } }),
    );
    backend([current.route]);
    window.location.hash = "#/spoil";
    render(<App />);
    expect(await screen.findByRole("slider", { name: "ความยาว" })).toBeDisabled();

    current.phases.at = 1;
    await nextPoll();

    const slider = await screen.findByRole("slider", { name: "ความยาว" });
    expect(slider).toBeEnabled();
    expect(slider).toHaveValue("120");
  });

  it("the card says เรื่อง: {story_title} of a draft with a Story, and nothing of one without", async () => {
    const withStory = jobOf({ order: { ...ORDER, story_id: "st_3fa91c07", story_title: "ยอดนักสืบจิ๋วโคนัน" } });
    backend([get(CURRENT_PATH, withStory)]);
    await openReview();

    const card = await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });
    expect(card).toHaveTextContent("เรื่อง: ยอดนักสืบจิ๋วโคนัน");
  });

  it("a card without a Story has no เรื่อง line", async () => {
    backend([get(CURRENT_PATH, jobOf({}))]);
    await openReview();

    const card = await screen.findByRole("region", { name: "ความคืบหน้าการร่างบท" });
    expect(card).not.toHaveTextContent("เรื่อง:");
  });

  it("ลองอีกครั้ง sends the order's Story again", async () => {
    const order = { ...ORDER, story_id: "st_3fa91c07", story_title: "ยอดนักสืบจิ๋วโคนัน" };
    const failed = jobOf({ state: "failed", error: { code: "draft_failed", message: "AI ร่างบทไม่สำเร็จ 3 ครั้ง" }, order });
    const current = phased(CURRENT_PATH, failed, jobOf({ order }));
    backend([current.route, send("POST", JOBS_PATH, jobOf({ order }), 202)]);
    const user = await openReview();

    await user.click(await screen.findByRole("button", { name: "ลองอีกครั้ง" }));

    expect(sent("POST", JOBS_PATH)).toEqual([expect.objectContaining({ story_id: "st_3fa91c07" })]);
    expect(sent("POST", JOBS_PATH)[0]).not.toHaveProperty("story_title");
  });
});
