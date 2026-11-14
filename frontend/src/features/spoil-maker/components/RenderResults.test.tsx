import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import type { RenderJob, RenderResult } from "../lib/render";
import { get, phased, type Route, send, serve } from "../../../testing/testBackend";

const RENDERS = "/api/spoil-maker/renders";
const CURRENT = "/api/spoil-maker/renders/current";

const RESULT: RenderResult = {
  name: "20261103-143200",
  created_at: "2026-11-03T14:32:00+07:00",
  duration_s: 58.2,
  size_bytes: 1234,
  sources: ["Night of the Living Dead (1968)"],
  clip_id: "aaaaaaaaaaa",
  ep: 2,
  sound_name: null,
};
const OLDER: RenderResult = { ...RESULT, name: "20261101-110500", created_at: "2026-11-01T11:05:00+07:00" };
const VOICING: RenderJob = {
  kind: "render",
  state: "voicing",
  percent: null,
  done: 1,
  total: 3,
  error: null,
  cancel_requested: false,
  started_at: "2026-11-03T14:30:00+07:00",
};

/** Answers each route once in order when it repeats; the last of a path keeps answering. */
function backend(routes: Route[]) {
  serve(fetchMock, routes);
}

async function openRenders() {
  window.location.hash = "#/spoil/renders";
  render(<App />);
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

const tick = () =>
  act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
});

afterEach(() => {
  fetchMock.mockReset();
  window.location.hash = "";
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("ผล render", () => {
  it("with nothing rendered says so", async () => {
    backend([get(RENDERS, []), get(CURRENT, null)]);
    await openRenders();

    expect(await screen.findByText("ยังไม่มีผล render")).toBeInTheDocument();
  });

  it("a render running shows สร้างเสียง then render % then the new render with its files and source", async () => {
    const current = phased(
      CURRENT,
      VOICING,
      { ...VOICING, state: "rendering", percent: 50, done: null, total: null },
      { ...VOICING, state: "done", percent: 100 },
    );
    const renders = phased(RENDERS, [], [], [RESULT]);
    backend([renders.route, current.route]);
    await openRenders();

    const running = await screen.findByRole("region", { name: "กำลัง render" });
    expect(within(running).getByText("สร้างเสียง 1/3")).toBeInTheDocument();
    current.phases.at = renders.phases.at = 1;
    await tick();
    expect(within(running).getByText("render 50%")).toBeInTheDocument();
    current.phases.at = renders.phases.at = 2;
    await tick();

    const row = await screen.findByRole("listitem", { name: /^render / });
    expect(within(row).getByRole("link", { name: "mp4" })).toHaveAttribute("href", `${RENDERS}/${RESULT.name}.mp4`);
    expect(within(row).getByRole("link", { name: ".srt" })).toHaveAttribute("href", `${RENDERS}/${RESULT.name}.srt`);
    expect(within(row).getByText("ต้นฉบับ: Night of the Living Dead (1968)")).toBeInTheDocument();
    expect(within(row).getByText("ความยาว 0:58")).toBeInTheDocument();
    expect(screen.queryByText("render 50%")).not.toBeInTheDocument();
  });

  it("a render of an EP says which; one from before EPs says none", async () => {
    backend([get(RENDERS, [RESULT, { ...OLDER, clip_id: null, ep: null }]), get(CURRENT, null)]);
    await openRenders();

    const [newer, older] = await screen.findAllByRole("listitem", { name: /^render / });
    expect(within(newer).getByText("EP 2")).toBeInTheDocument();
    expect(within(older).queryByText(/^EP /)).not.toBeInTheDocument();
  });

  it("a render with a background sound names it under the source; one without has no such line", async () => {
    backend([get(RENDERS, [{ ...RESULT, sound_name: "ฝนตก" }, OLDER]), get(CURRENT, null)]);
    await openRenders();

    const [withSound, without] = await screen.findAllByRole("listitem", { name: /^render / });
    const credit = within(withSound).getByText("ต้นฉบับ: Night of the Living Dead (1968)");
    expect(credit.compareDocumentPosition(within(withSound).getByText("เสียงพื้น: ฝนตก")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(without).queryByText(/^เสียงพื้น:/)).not.toBeInTheDocument();
  });

  it("copy puts the source line on the clipboard", async () => {
    backend([get(RENDERS, [RESULT]), get(CURRENT, null)]);
    const user = await openRenders();
    // user-event puts its own clipboard on `navigator` in setup.
    const writeText = vi.spyOn(navigator.clipboard, "writeText");

    await user.click(await screen.findByRole("button", { name: "copy ชื่อต้นฉบับ" }));

    expect(writeText).toHaveBeenCalledWith("ต้นฉบับ: Night of the Living Dead (1968)");
    expect(await screen.findByRole("button", { name: "copy แล้ว" })).toBeInTheDocument();
  });

  it("a render that failed in ffmpeg says render ไม่สำเร็จ", async () => {
    const failed = { ...VOICING, state: "failed", error: { code: "ffmpeg_failed", message: "render ไม่สำเร็จ: x" } };
    backend([get(RENDERS, [RESULT]), get(CURRENT, { ...VOICING, state: "rendering", percent: 20 }), get(CURRENT, failed)]);
    await openRenders();
    await screen.findByText("render 20%");
    await tick();

    expect(await screen.findByText("render ไม่สำเร็จ")).toBeInTheDocument();
  });

  it("ลบ asks first, then deletes the row", async () => {
    backend([get(RENDERS, [RESULT, OLDER]), get(CURRENT, null), send("DELETE", `${RENDERS}/${RESULT.name}`, null, 204)]);
    const user = await openRenders();
    const rows = await screen.findAllByRole("listitem", { name: /^render / });

    await user.click(within(rows[0]).getByRole("button", { name: /^ลบ render/ }));
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(false);
    await user.click(within(rows[0]).getByRole("button", { name: "ลบ" }));

    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
    expect(screen.getAllByRole("listitem", { name: /^render / })).toHaveLength(1);
  });

  it("the thumbnail plays the render under its row on a phone", async () => {
    backend([get(RENDERS, [RESULT]), get(CURRENT, null)]);
    const user = await openRenders();
    const row = await screen.findByRole("listitem", { name: /^render / });

    await user.click(within(row).getByRole("button", { name: "เล่น" }));

    expect(within(row).getByText("กำลังเล่น")).toBeInTheDocument();
    expect(row.querySelector("video[controls]")).toHaveAttribute("src", `${RENDERS}/${RESULT.name}.mp4`);
    expect(within(row).getByRole("button", { name: "หยุด" })).toBeInTheDocument();
  });
});
