import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChecklistItem, StatusResponse } from "../../../lib/statusTypes";
import type { DownloadJob } from "../hooks/useSpoilDownload";
import { SpoilPage } from "./SpoilPage";

const SHORTS_URL = "https://www.youtube.com/shorts/f7jkZXvaB4g";

function okItem(id: string, label: string): ChecklistItem {
  return { id, label, status: "ok", detail: "", fix: null, license: null };
}

const ITEMS: ChecklistItem[] = [
  okItem("python", "Python venv"),
  okItem("ffmpeg", "ffmpeg"),
  okItem("yt_dlp", "yt-dlp"),
  okItem("deno", "Deno"),
  // A missing model does not stop a download (D9).
  { ...okItem("model_whisper", "Whisper model"), status: "missing", fix: "./setup.sh" },
];

function statusOf(items: ChecklistItem[]): StatusResponse {
  const count = (status: ChecklistItem["status"]) => items.filter((i) => i.status === status).length;
  return {
    checked_at: "2026-10-29T17:42:10+07:00",
    ready: count("missing") === 0,
    ok_count: count("ok"),
    warning_count: count("warning"),
    missing_count: count("missing"),
    total: items.length,
    items,
  };
}

function jobOf(change: Partial<DownloadJob>): DownloadJob {
  return {
    url: SHORTS_URL,
    id: "f7jkZXvaB4g",
    state: "checking",
    title: null,
    percent: null,
    cancel_requested: false,
    error: null,
    clip_id: null,
    ...change,
  };
}

const DOWNLOADING_40 = jobOf({ state: "downloading", title: "From the Moon", percent: 40 });

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

type Route = { method?: string; path: string; reply: () => Response | Promise<Response> };

/**
 * Fake backend: each request takes the first route that matches it. A route
 * answers once, so a list of routes for the same path plays out in order;
 * the last one for a path keeps answering.
 */
function backend(routes: Route[]) {
  fetchMock.mockImplementation(async (input, init) => {
    const method = init?.method ?? "GET";
    const matches = routes.filter((r) => r.path === String(input) && (r.method ?? "GET") === method);
    if (matches.length === 0) throw new Error(`unexpected ${method} ${String(input)}`);
    const route = matches[0];
    if (matches.length > 1) routes.splice(routes.indexOf(route), 1);
    return route.reply();
  });
}

const status = (items = ITEMS): Route => ({ path: "/api/setup/status", reply: () => jsonResponse(statusOf(items)) });
const current = (job: DownloadJob | null): Route => ({
  path: "/api/spoil/downloads/current",
  reply: () => jsonResponse(job),
});
const post = (body: unknown, code = 202): Route => ({
  method: "POST",
  path: "/api/spoil/downloads",
  reply: () => jsonResponse(body, code),
});

/** Advances the 1-second poll and lets its answer render. */
async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
}

async function startDownload() {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  await user.type(await screen.findByLabelText("ลิงก์ YouTube"), SHORTS_URL);
  await user.click(screen.getByRole("button", { name: "โหลด" }));
  return user;
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("tab สปอย", () => {
  it("shows กำลังโหลด… until the status and the current job answer", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<SpoilPage />);

    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
  });

  it("names what is missing and links to Setup status instead of the link field", async () => {
    backend([status(ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" } : i))), current(null)]);
    render(<SpoilPage />);

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปหน้า Setup status" })).toHaveAttribute("href", "#/setup");
    expect(screen.queryByLabelText("ลิงก์ YouTube")).not.toBeInTheDocument();
  });

  it("shows the link field when yt-dlp, Deno and ffmpeg are ok, even with a model missing", async () => {
    backend([status(), current(null)]);
    render(<SpoilPage />);

    expect(await screen.findByLabelText("ลิงก์ YouTube")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
  });
});

describe("downloading", () => {
  it("posts the link, shows 40%, then โหลดเสร็จ with the title", async () => {
    backend([
      status(),
      current(null),
      current(DOWNLOADING_40),
      current(jobOf({ state: "done", title: "From the Moon", clip_id: "f7jkZXvaB4g" })),
      post(jobOf({})),
    ]);
    render(<SpoilPage />);
    await startDownload();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/spoil/downloads",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ url: SHORTS_URL }) }),
    );
    expect(await screen.findByText("กำลังเช็คลิงก์…")).toBeInTheDocument();

    await nextPoll();
    expect(screen.getByText("กำลังโหลด From the Moon")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "40");

    await nextPoll();
    expect(screen.getByText("โหลดเสร็จ: From the Moon")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
  });

  it("shows a bar with no number when the size is unknown", async () => {
    backend([status(), current(jobOf({ state: "downloading", title: "Me at the zoo", percent: null }))]);
    render(<SpoilPage />);

    expect(await screen.findByText("กำลังโหลด Me at the zoo")).toBeInTheDocument();
    expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
    expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");
  });

  it("disables โหลด while a job is unfinished and hides ยกเลิก while merging", async () => {
    backend([status(), current(jobOf({ state: "merging", title: "From the Moon" }))]);
    render(<SpoilPage />);

    expect(await screen.findByText("กำลังรวมไฟล์…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "ยกเลิก" })).not.toBeInTheDocument();
    expect(screen.getByText("ยกเลิกไม่ได้ระหว่างรวมไฟล์")).toBeInTheDocument();
  });

  it("sends DELETE on ยกเลิก and shows กำลังยกเลิก… once the job says so", async () => {
    const cancelling = { ...DOWNLOADING_40, cancel_requested: true };
    backend([
      status(),
      current(DOWNLOADING_40),
      { method: "DELETE", path: "/api/spoil/downloads/current", reply: () => jsonResponse(cancelling, 202) },
    ]);
    render(<SpoilPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));

    expect(fetchMock).toHaveBeenCalledWith("/api/spoil/downloads/current", expect.objectContaining({ method: "DELETE" }));
    expect(await screen.findByText("กำลังยกเลิก…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ยกเลิก" })).toBeDisabled();
  });

  it("says the merge can't be cancelled on 409 merging", async () => {
    backend([
      status(),
      current(DOWNLOADING_40),
      {
        method: "DELETE",
        path: "/api/spoil/downloads/current",
        reply: () => jsonResponse({ code: "merging", message: "x" }, 409),
      },
    ]);
    render(<SpoilPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));

    expect(await screen.findByText("กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว")).toBeInTheDocument();
  });

  it("says ยกเลิกแล้ว when the job ends cancelled", async () => {
    backend([status(), current({ ...DOWNLOADING_40, cancel_requested: true }), current(jobOf({ state: "cancelled" }))]);
    render(<SpoilPage />);
    expect(await screen.findByText("กำลังยกเลิก…")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("says the job was lost when the poll answers null", async () => {
    backend([status(), current(DOWNLOADING_40), current(null)]);
    render(<SpoilPage />);
    expect(await screen.findByText("40%")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
  });
});

describe("messages", () => {
  const youtubeError = jobOf({
    state: "failed",
    error: {
      code: "youtube_error",
      message: "โหลดไม่สำเร็จ (yt-dlp 2026.10.26). ถ้าเป็นทุกคลิป ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script",
      yt_dlp_version: "2026.10.26",
      fix: "uv lock --upgrade-package yt-dlp",
    },
  });

  it("shows a failed job's message and its fix as a line with a copy button", async () => {
    backend([status(), current(null), current(youtubeError), post(jobOf({}))]);
    render(<SpoilPage />);
    const user = await startDownload();

    await nextPoll();

    expect(screen.getByText(youtubeError.error!.message)).toBeInTheDocument();
    expect(screen.getByText("uv lock --upgrade-package yt-dlp")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "คัดลอก uv lock --upgrade-package yt-dlp" }));
    expect(await navigator.clipboard.readText()).toBe("uv lock --upgrade-package yt-dlp");
  });

  it("shows how the last job ended when the tab opens on it", async () => {
    const live = jobOf({
      state: "failed",
      error: { code: "live", message: "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้", yt_dlp_version: "2026.10.26", fix: null },
    });
    backend([status(), current(live)]);
    render(<SpoilPage />);

    expect(await screen.findByText("คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /คัดลอก/ })).not.toBeInTheDocument();
  });

  it.each([
    [400, "invalid_url", "ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube"],
    [409, "busy", "กำลังโหลดคลิปอื่นอยู่"],
    [409, "duplicate", "คลิปนี้โหลดไว้แล้ว"],
  ])("shows the Frontend table's text on %i %s", async (code, errorCode, text) => {
    backend([status(), current(null), post({ code: errorCode, message: "from the API" }, code)]);
    render(<SpoilPage />);
    await startDownload();

    expect(await screen.findByText(text)).toBeInTheDocument();
    expect(screen.queryByText("from the API")).not.toBeInTheDocument();
  });

  it("clears the last message on the next โหลด", async () => {
    backend([
      status(),
      current(null),
      post({ code: "invalid_url", message: "x" }, 400),
      { method: "POST", path: "/api/spoil/downloads", reply: () => new Promise(() => {}) },
    ]);
    render(<SpoilPage />);
    const user = await startDownload();
    expect(await screen.findByText("ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "โหลด" }));

    expect(screen.queryByText("ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube")).not.toBeInTheDocument();
  });

  it("switches to not ready on 503 not_ready", async () => {
    const noDeno = ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" as const } : i));
    // The tab opens ready; after the 503 it asks for the status again and Deno is gone.
    backend([status(), status(noDeno), current(null), post({ code: "not_ready", message: "x" }, 503)]);
    render(<SpoilPage />);
    await startDownload();

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
  });
});

describe("offline", () => {
  it("shows the OfflinePanel when a fetch fails, and Refresh loads the tab again", async () => {
    backend([{ path: "/api/setup/status", reply: () => Promise.reject(new TypeError("Failed to fetch")) }, status(), current(null)]);
    render(<SpoilPage />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByLabelText("ลิงก์ YouTube")).toBeInTheDocument();
  });

  it("shows the OfflinePanel when the backend gives no answer in 30 s", async () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<SpoilPage />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(screen.getByText("Backend offline")).toBeInTheDocument();
  });

  it("goes offline when a poll fails", async () => {
    backend([
      status(),
      current(DOWNLOADING_40),
      { path: "/api/spoil/downloads/current", reply: () => Promise.reject(new TypeError("Failed to fetch")) },
    ]);
    render(<SpoilPage />);
    expect(await screen.findByText("40%")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("Backend offline")).toBeInTheDocument();
  });
});
