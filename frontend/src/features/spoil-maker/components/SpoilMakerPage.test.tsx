import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { Draft, DraftJob, Sentence } from "../lib/draft";
import type { RenderJob, RenderResult, SentencesJob } from "../lib/render";

const API = "/api/spoil-maker";
const DRAFT = `${API}/draft`;
const DRAFT_JOB = `${API}/draft-jobs/current`;
const VOICE_JOB = `${API}/voice-jobs/current`;
const RENDERS = `${API}/renders`;
const RENDER_JOB = `${API}/renders/current`;
const CLIP = "aaaaaaaaaaa";

function sentenceOf(id: string): Sentence {
  return {
    id,
    text: "ชายคนหนึ่งตื่นขึ้นมา",
    refs: [{ clip_id: CLIP, line: 4 }],
    shots: [
      { clip_id: CLIP, n: 20 },
      { clip_id: CLIP, n: 21 },
    ],
    audio: { tts_text: "x", voice_id: "v_0000abcd", duration_s: 2.5 },
    status: "ready",
    estimated_s: 2.5,
    ref_lines: [],
    window: null,
  };
}

const DRAFT_EP2: Draft = {
  clip_id: CLIP,
  ep: { n: 2, start_s: 1800, end_s: 3600 },
  clip_title: "Night of the Living Dead",
  style: "fast",
  layout: "B",
  target_s: 30,
  voice_id: "v_0000abcd",
  original_volume: 20,
  top_text: "",
  sentences: ["1", "2", "3", "4", "5", "6"].map((n) => sentenceOf(`s_0000000${n}`)),
  estimated_total_s: 15,
  locked: false,
};

const RESULT: RenderResult = {
  name: "20261103-143200",
  created_at: "2026-11-03T14:32:00+07:00",
  duration_s: 58.2,
  size_bytes: 1234,
  sources: ["Night of the Living Dead"],
  clip_id: CLIP,
  ep: 2,
};
const resultsOf = (count: number) => Array.from({ length: count }, (_, i) => ({ ...RESULT, name: `2026110${i}-143200` }));

const AT = (minute: number) => `2026-11-04T10:${String(minute).padStart(2, "0")}:00+07:00`;
const renderJob = (change: Partial<RenderJob>): RenderJob => ({
  kind: "render",
  state: "rendering",
  percent: 45,
  done: null,
  total: null,
  error: null,
  cancel_requested: false,
  started_at: AT(0),
  ...change,
});
const voiceJob = (change: Partial<SentencesJob>): SentencesJob => ({
  kind: "sentences",
  state: "voicing",
  done: 2,
  total: 5,
  error: null,
  cancel_requested: false,
  started_at: AT(0),
  ...change,
});
const draftJob = (change: Partial<DraftJob>): DraftJob => ({
  kind: "draft",
  state: "writing",
  done: null,
  total: null,
  error: null,
  cancel_requested: false,
  started_at: AT(0),
  ...change,
});
const FAILED = { code: "model_failed", message: "x" };

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** What each GET answers now; a test changes it and lets the next poll read it. */
let answers: Record<string, unknown>;
const fetchMock = vi.fn<typeof fetch>();

function backend(change: Record<string, unknown> = {}, posts: Record<string, () => Response> = {}) {
  answers = {
    [DRAFT]: null,
    [DRAFT_JOB]: null,
    [VOICE_JOB]: null,
    [RENDERS]: [],
    [RENDER_JOB]: null,
    "/api/spoil/clips": { clips: [] },
    [`${API}/voices`]: [],
    [`${API}/settings`]: { watermarks: [], original_volume: 20, last_voice_id: null, ep_minutes: 30 },
    [`${API}/clips/${CLIP}/shots`]: { clip_id: CLIP, shots: [] },
    ...change,
  };
  fetchMock.mockImplementation(async (input, init) => {
    const path = String(input);
    const method = init?.method ?? "GET";
    if (method === "GET" && path in answers) return jsonResponse(answers[path]);
    const post = posts[`${method} ${path}`];
    if (post) return post();
    throw new Error(`unexpected ${method} ${path}`);
  });
}

const reads = (path: string) => fetchMock.mock.calls.filter(([input, init]) => String(input) === path && !init?.method).length;

function open(hash: string) {
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const nav = () => screen.getByRole("navigation", { name: "ขั้นของสปอย" });
const step = (name: string) => within(nav()).getByRole("link", { name: new RegExp(name) });
const spinners = (element: HTMLElement) => within(element).queryAllByRole("img", { name: "กำลังทำงาน" });

const tick = () =>
  act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  window.location.hash = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("Spoil steps (spoil-maker D53, D68)", () => {
  it.each([
    ["#/spoil", "1", "เลือกคลิป"],
    ["#/spoil/review", "2", "ตรวจแก้บท"],
    ["#/spoil/renders", "3", "ผล render"],
  ])("%s highlights step %s %s", (hash, number, name) => {
    backend();
    open(hash);

    const current = within(nav()).getByRole("link", { current: "step" });
    expect(current).toHaveTextContent(`${number}${name}`);
  });

  it("opens step 1 on a #/spoil/ hash it doesn't know", () => {
    backend();
    open("#/spoil/nope");

    expect(within(nav()).getByRole("link", { current: "step" })).toHaveTextContent("เลือกคลิป");
  });

  it("every step is a numbered link, with no check for the steps before", () => {
    backend();
    open("#/spoil/renders");

    const links = within(nav()).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual(["#/spoil", "#/spoil/review", "#/spoil/renders"]);
    expect(links.map((link) => link.textContent?.[0])).toEqual(["1", "2", "3"]);
    expect(within(nav()).queryAllByRole("img")).toHaveLength(0);
  });

  it("moves to a step by its link, which changes the hash", async () => {
    backend();
    const user = open("#/spoil");

    await user.click(step("ตรวจแก้บท"));

    expect(window.location.hash).toBe("#/spoil/review");
    await waitFor(() => expect(within(nav()).getByRole("link", { current: "step" })).toHaveTextContent("ตรวจแก้บท"));
  });

  it("says the draft's clip and EP, its sentences and the renders", async () => {
    backend({ [DRAFT]: DRAFT_EP2, [RENDERS]: resultsOf(3) });
    open("#/spoil/renders");

    await waitFor(() => expect(step("เลือกคลิป")).toHaveTextContent("Night of the Living Dead · EP 2"));
    expect(step("ตรวจแก้บท")).toHaveTextContent("6 ประโยค");
    expect(step("ผล render")).toHaveTextContent("3 คลิป");
  });

  it("with nothing yet says so on every step", async () => {
    backend();
    open("#/spoil/renders");

    await waitFor(() => expect(step("เลือกคลิป")).toHaveTextContent("ยังไม่เลือก"));
    expect(step("ตรวจแก้บท")).toHaveTextContent("ยังไม่มีบท");
    expect(step("ผล render")).toHaveTextContent("ยังไม่มี");
    expect(spinners(nav())).toHaveLength(0);
  });

  it("a render running while step 1 is open shows its percent and a spinner on step 3, then the new count", async () => {
    backend({ [RENDER_JOB]: renderJob({}), [RENDERS]: resultsOf(1) });
    open("#/spoil");

    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 45%"));
    expect(spinners(step("ผล render"))).toHaveLength(1);
    expect(spinners(step("เลือกคลิป"))).toHaveLength(0);

    answers[RENDER_JOB] = renderJob({ state: "done", percent: 100 });
    answers[RENDERS] = resultsOf(2);
    const before = reads(RENDERS);
    await tick();

    await waitFor(() => expect(step("ผล render")).toHaveTextContent("2 คลิป"));
    expect(reads(RENDERS)).toBeGreaterThan(before);
    expect(spinners(nav())).toHaveLength(0);
  });

  it.each([
    [renderJob({ percent: null }), "render…"],
    [renderJob({ state: "voicing", percent: null, done: 1, total: 3 }), "render: สร้างเสียง 1/3"],
  ])("a render job %# says %s", async (job, line) => {
    backend({ [RENDER_JOB]: job });
    open("#/spoil");

    await waitFor(() => expect(step("ผล render")).toHaveTextContent(line));
  });

  it("a render that failed says so on step 3 until a render starts again", async () => {
    const started = renderJob({ percent: 0, started_at: AT(5) });
    backend(
      { [DRAFT]: DRAFT_EP2, [RENDER_JOB]: renderJob({ state: "failed", error: FAILED }), [RENDERS]: resultsOf(1) },
      { [`POST ${RENDERS}`]: () => jsonResponse(started, 202) },
    );
    const user = open("#/spoil/review");

    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render ไม่สำเร็จ"));
    expect(spinners(nav())).toHaveLength(0);

    answers[RENDER_JOB] = started;
    await user.click(await screen.findByRole("button", { name: "render" }));
    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 0%"));
  });

  it("cancel tells the steps, which then show the job ending", async () => {
    backend({ [RENDER_JOB]: renderJob({}) }, { [`DELETE ${RENDER_JOB}`]: () => jsonResponse(renderJob({ cancel_requested: true }), 202) });
    const user = open("#/spoil/renders");
    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 45%"));

    answers[RENDER_JOB] = renderJob({ state: "cancelled" });
    const before = reads(RENDER_JOB);
    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));

    await waitFor(() => expect(step("ผล render")).toHaveTextContent("ยังไม่มี"));
    expect(reads(RENDER_JOB)).toBeGreaterThan(before);
    expect(spinners(nav())).toHaveLength(0);
  });

  it("a Draft job that ends reads the draft again for step 2's count", async () => {
    backend({ [DRAFT_JOB]: draftJob({ state: "matching", done: 14, total: 15 }) });
    open("#/spoil/renders");
    await waitFor(() => expect(step("ตรวจแก้บท")).toHaveTextContent("กำลังเลือกภาพ 14/15"));

    answers[DRAFT_JOB] = draftJob({ state: "done", done: 15, total: 15 });
    answers[DRAFT] = DRAFT_EP2;
    await tick();

    await waitFor(() => expect(step("ตรวจแก้บท")).toHaveTextContent("6 ประโยค"));
    expect(step("เลือกคลิป")).toHaveTextContent("Night of the Living Dead · EP 2");
  });

  it("a poll that failed lets the next refresh follow the job again", async () => {
    backend({ [DRAFT]: DRAFT_EP2, [RENDER_JOB]: renderJob({}) }, { [`POST ${RENDERS}`]: () => jsonResponse(renderJob({ percent: 0 }), 202) });
    const user = open("#/spoil");
    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 45%"));

    delete answers[RENDER_JOB]; // the next poll fails
    await tick();
    await waitFor(() => expect(spinners(nav())).toHaveLength(0));

    answers[RENDER_JOB] = renderJob({ state: "cancelled" });
    await user.click(step("ตรวจแก้บท"));
    answers[RENDER_JOB] = renderJob({ percent: 10 });
    await user.click(await screen.findByRole("button", { name: "render" }));
    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 10%"));

    answers[RENDER_JOB] = renderJob({ percent: 20 });
    await tick();
    expect(step("ผล render")).toHaveTextContent("render 20%");
  });

  it.each([
    [{ [VOICE_JOB]: voiceJob({}) }, "สร้างเสียง 2/5", true],
    [{ [DRAFT_JOB]: draftJob({}) }, "กำลังร่าง", true],
    [{ [DRAFT_JOB]: draftJob({ state: "matching", done: 4, total: 15 }) }, "กำลังเลือกภาพ 4/15", true],
    [{ [DRAFT_JOB]: draftJob({ kind: "pick", state: "matching", done: 0, total: 1 }) }, "6 ประโยค", true],
    [{ [DRAFT_JOB]: draftJob({ state: "failed", error: FAILED }) }, "ร่างบทไม่สำเร็จ", false],
    [{ [VOICE_JOB]: voiceJob({ state: "failed", error: FAILED }) }, "สร้างเสียงไม่สำเร็จ", false],
    // A newer job than the failure says what step 2 does now.
    [{ [DRAFT_JOB]: draftJob({ state: "failed", error: FAILED }), [VOICE_JOB]: voiceJob({ started_at: AT(5) }) }, "สร้างเสียง 2/5", true],
  ])("step 2 with %o says %s", async (jobs, line, busy) => {
    backend({ [DRAFT]: DRAFT_EP2, ...jobs });
    open("#/spoil/renders");

    await waitFor(() => expect(step("ตรวจแก้บท")).toHaveTextContent(line));
    expect(spinners(step("ตรวจแก้บท"))).toHaveLength(busy ? 1 : 0);
  });

  it("a Voice job of the Saved voice page isn't step 2's", async () => {
    backend({ [DRAFT]: DRAFT_EP2, [VOICE_JOB]: { kind: "design_preview", state: "voicing", started_at: AT(1) } });
    open("#/spoil/renders");

    await waitFor(() => expect(step("ตรวจแก้บท")).toHaveTextContent("6 ประโยค"));
    expect(spinners(nav())).toHaveLength(0);
  });

  it("the spinner turns only without prefers-reduced-motion; the line stays", async () => {
    backend({ [RENDER_JOB]: renderJob({}) });
    open("#/spoil");

    await waitFor(() => expect(step("ผล render")).toHaveTextContent("render 45%"));
    const [spinner] = spinners(step("ผล render"));
    expect(spinner).toHaveClass("motion-safe:animate-spin");
    expect(spinner).not.toHaveClass("animate-spin");
  });

  it("a phone names only the open step, but every running step keeps its spinner", async () => {
    backend({ [RENDER_JOB]: renderJob({}) });
    open("#/spoil");

    await waitFor(() => expect(spinners(step("ผล render"))).toHaveLength(1));
    // jsdom has no CSS: the phone's view is the classes that hide the name below `sm`.
    const name = (label: string) => within(nav()).getByText(label).parentElement;
    expect(name("เลือกคลิป")).not.toHaveClass("sr-only");
    expect(name("ผล render")).toHaveClass("sr-only", "sm:not-sr-only");
    expect(name("ผล render")).not.toContainElement(spinners(step("ผล render"))[0]);
  });
});
