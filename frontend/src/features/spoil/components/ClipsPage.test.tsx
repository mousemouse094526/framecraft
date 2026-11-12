import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChecklistItem, StatusResponse } from "../../../lib/statusTypes";
import type { DescribeJob } from "../hooks/useDescribe";
import type { DownloadJob } from "../hooks/useSpoilDownload";
import { LOCAL_SITE, type TempClip } from "../../../lib/clips";
import type { TranscribeJob, Transcript } from "../hooks/useTranscribe";
import type { TrimJob } from "../hooks/useTrim";
import { FakeXhr } from "../../../testing/fakeXhr";
import { sent } from "../../../testing/testBackend";
import { ClipsPage } from "./ClipsPage";

const SHORTS_URL = "https://www.youtube.com/shorts/f7jkZXvaB4g";

function okItem(id: string, label: string): ChecklistItem {
  return { id, label, status: "ok", detail: "", fix: null, fix_kind: null, license: null };
}

const ITEMS: ChecklistItem[] = [
  okItem("python", "Python venv"),
  okItem("ffmpeg", "ffmpeg"),
  okItem("yt_dlp", "yt-dlp"),
  okItem("deno", "Deno"),
  // A missing model does not stop a download (D9).
  { ...okItem("model_whisper", "Whisper model"), status: "missing", fix: "./setup.sh", fix_kind: "command" },
];

// Every item the Transcribe job needs is ok (D27).
const READY_ITEMS: ChecklistItem[] = [
  ...ITEMS.filter((i) => i.id !== "model_whisper"),
  okItem("torch", "torch"),
  okItem("transformers", "transformers"),
  okItem("model_whisper", "Whisper model"),
  okItem("device", "Device"),
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

/** `downloaded_at` at a local wall-clock time, so the shown time is the same in every time zone. */
function localIso(month: number, day: number, hour: number, minute: number): string {
  return new Date(2026, month - 1, day, hour, minute).toISOString();
}

function clipOf(change: Partial<TempClip>): TempClip {
  return {
    id: "dQw4w9WgXcQ",
    title: "Rick Astley - Never Gonna Give You Up (Official Video)",
    channel: "Rick Astley",
    source_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    duration_s: 213,
    width: 1920,
    height: 1080,
    orientation: "landscape",
    file_bytes: 84_400_000,
    thumbnail: "dQw4w9WgXcQ.webp",
    downloaded_at: localIso(10, 28, 21, 10),
    yt_dlp_version: "2026.10.26",
    site: "Youtube",
    transcribed: false,
    described: false,
    in_draft: false,
    trimmed: [],
    trimmed_at: null,
    ...change,
  };
}

const RICK = clipOf({});
const MOON = clipOf({
  id: "f7jkZXvaB4g",
  title: "From the Moon to the 50-Yard Line",
  channel: "NASA",
  duration_s: 39,
  width: 1080,
  height: 1920,
  orientation: "portrait",
  file_bytes: 16_700_000,
  thumbnail: "f7jkZXvaB4g.webp",
  downloaded_at: localIso(10, 29, 18, 34),
});
const NIGHT = clipOf({
  id: "H91BxkBXttE",
  title: "Night of the Living Dead (1968)",
  channel: "Public Domain Movies",
  duration_s: 5742,
  file_bytes: 1_600_000_000,
  thumbnail: null,
  downloaded_at: localIso(10, 29, 18, 52),
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

type Route = { method?: string; path: string; reply: () => Response | Promise<Response> };

/**
 * Fake backend: each request takes the first route that matches it. A route
 * answers once, so a list of routes for the same path plays out in order;
 * the last one for a path keeps answering. With no `/api/spoil/clips` route
 * the list is empty; with no `/api/spoil/transcriptions/current` or
 * `/api/spoil-maker/describes/current` or `/api/spoil/trims/current` route there is no such job; a clip's `/transcript` with no route is `404`, as for
 * a clip not yet transcribed.
 */
function backend(routes: Route[]) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  if (!has(CLIPS_PATH)) routes.push(clips([]));
  if (!has(TRANSCRIPTION_PATH)) routes.push(transcription(null));
  if (!has(DESCRIBE_PATH)) routes.push(describing(null));
  if (!has(TRIM_PATH)) routes.push(trimming(null));
  fetchMock.mockImplementation(async (input, init) => {
    const method = init?.method ?? "GET";
    const matches = routes.filter((r) => r.path === String(input) && (r.method ?? "GET") === method);
    if (matches.length === 0 && method === "GET" && String(input).endsWith("/transcript")) {
      return jsonResponse({ code: "not_found", message: "x" }, 404);
    }
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
const CLIPS_PATH = "/api/spoil/clips";
const clips = (list: TempClip[]): Route => ({ path: CLIPS_PATH, reply: () => jsonResponse({ clips: list }) });
const deleteClip = (id: string, reply: () => Response): Route => ({ method: "DELETE", path: `${CLIPS_PATH}/${id}`, reply });
const TRANSCRIPTION_PATH = "/api/spoil/transcriptions/current";
const transcription = (job: TranscribeJob | null): Route => ({ path: TRANSCRIPTION_PATH, reply: () => jsonResponse(job) });
const postTranscription = (body: unknown, code = 202): Route => ({
  method: "POST",
  path: "/api/spoil/transcriptions",
  reply: () => jsonResponse(body, code),
});
const DESCRIBE_PATH = "/api/spoil-maker/describes/current";
const describing = (job: DescribeJob | null): Route => ({ path: DESCRIBE_PATH, reply: () => jsonResponse(job) });
const postDescribe = (body: unknown, code = 202): Route => ({
  method: "POST",
  path: "/api/spoil-maker/describes",
  reply: () => jsonResponse(body, code),
});
const TRIM_PATH = "/api/spoil/trims/current";
const trimming = (job: TrimJob | null): Route => ({ path: TRIM_PATH, reply: () => jsonResponse(job) });
const postTrim = (body: unknown, code = 202): Route => ({ method: "POST", path: "/api/spoil/trims", reply: () => jsonResponse(body, code) });
const transcript = (value: Transcript): Route => ({
  path: `${CLIPS_PATH}/${value.clip_id}/transcript`,
  reply: () => jsonResponse(value),
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

/** The transcript panel, a region named for screen readers. */
function panel(): HTMLElement {
  return screen.getByRole("region", { name: "กล่องถอดบทพูด" });
}

async function startDownload() {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  await user.type(await screen.findByLabelText("ลิงก์คลิป"), SHORTS_URL);
  await user.click(screen.getByRole("button", { name: "โหลด" }));
  return user;
}

const fetchMock = vi.fn<typeof fetch>();

function clipListCalls(): number {
  return fetchMock.mock.calls.filter(([input, init]) => String(input) === CLIPS_PATH && !init?.method).length;
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.stubGlobal("fetch", fetchMock);
  // jsdom has no layout or media playback (docs/library-notes/vitest.md).
  Element.prototype.scrollIntoView = vi.fn();
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
});

afterEach(() => {
  fetchMock.mockReset();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("tab คลิป", () => {
  it("shows กำลังโหลด… until the status and the current job answer", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<ClipsPage />);

    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
  });

  it("keeps กำลังโหลด… until the clip list answers too", async () => {
    backend([status(), current(null), { path: CLIPS_PATH, reply: () => new Promise(() => {}) }]);
    render(<ClipsPage />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
    expect(screen.queryByLabelText("ลิงก์คลิป")).not.toBeInTheDocument();
  });

  it("names what is missing and links to the ติดตั้ง tab instead of the link field", async () => {
    backend([status(ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" } : i))), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ไปหน้าติดตั้ง" })).toHaveAttribute("href", "#/setup");
    expect(screen.queryByLabelText("ลิงก์คลิป")).not.toBeInTheDocument();
  });

  it("shows the link field when yt-dlp, Deno and ffmpeg are ok, even with a model missing", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByLabelText("ลิงก์คลิป")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
  });
});

describe("downloading", () => {
  it("posts the link, shows 40%, then โหลดเสร็จ with the title and the new row highlighted", async () => {
    backend([
      status(),
      current(null),
      current(DOWNLOADING_40),
      current(jobOf({ state: "done", title: "From the Moon", clip_id: "f7jkZXvaB4g" })),
      post(jobOf({})),
      clips([RICK]),
      clips([MOON, RICK]),
    ]);
    render(<ClipsPage />);
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
    expect(await screen.findByRole("listitem", { name: MOON.title })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("listitem", { name: RICK.title })).not.toHaveAttribute("aria-current");
    expect(clipListCalls()).toBe(2);

    await nextPoll();
    expect(clipListCalls()).toBe(2);
  });

  it("shows a bar with no number when the size is unknown", async () => {
    backend([status(), current(jobOf({ state: "downloading", title: "Me at the zoo", percent: null }))]);
    render(<ClipsPage />);

    expect(await screen.findByText("กำลังโหลด Me at the zoo")).toBeInTheDocument();
    expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
    expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");
  });

  it("disables โหลด while a job is unfinished and hides ยกเลิก while merging", async () => {
    backend([status(), current(jobOf({ state: "merging", title: "From the Moon" }))]);
    render(<ClipsPage />);

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
    render(<ClipsPage />);
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
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));

    expect(await screen.findByText("กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว")).toBeInTheDocument();
  });

  it("says ยกเลิกแล้ว when the job ends cancelled", async () => {
    backend([status(), current({ ...DOWNLOADING_40, cancel_requested: true }), current(jobOf({ state: "cancelled" }))]);
    render(<ClipsPage />);
    expect(await screen.findByText("กำลังยกเลิก…")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("says the job was lost when the poll answers null", async () => {
    backend([status(), current(DOWNLOADING_40), current(null)]);
    render(<ClipsPage />);
    expect(await screen.findByText("40%")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
    expect(clipListCalls()).toBe(2);
  });
});

describe("messages", () => {
  const youtubeError = jobOf({
    state: "failed",
    error: {
      code: "download_error",
      message: "โหลดไม่สำเร็จ (yt-dlp 2026.10.26). ถ้าเป็นทุกคลิป ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script",
      yt_dlp_version: "2026.10.26",
      fix: "uv lock --upgrade-package yt-dlp",
      clip_id: null,
    },
  });

  it("shows a failed job's message and its fix as a line with a copy button", async () => {
    backend([status(), current(null), current(youtubeError), post(jobOf({}))]);
    render(<ClipsPage />);
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
      error: {
        code: "live",
        message: "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้",
        yt_dlp_version: "2026.10.26",
        fix: null,
        clip_id: null,
      },
    });
    backend([status(), current(live)]);
    render(<ClipsPage />);

    expect(await screen.findByText("คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /คัดลอก/ })).not.toBeInTheDocument();
  });

  it.each([
    [400, "invalid_url", "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป"],
    [409, "busy", "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่"],
  ])("shows the Frontend table's text on %i %s", async (code, errorCode, text) => {
    backend([status(), current(null), post({ code: errorCode, message: "from the API" }, code)]);
    render(<ClipsPage />);
    await startDownload();

    expect(await screen.findByText(text)).toBeInTheDocument();
    expect(screen.queryByText("from the API")).not.toBeInTheDocument();
  });

  it("on 409 duplicate says so, highlights the old row and scrolls to it", async () => {
    backend([
      status(),
      current(null),
      clips([NIGHT, MOON, RICK]),
      post({ code: "duplicate", message: "from the API", clip_id: RICK.id }, 409),
    ]);
    render(<ClipsPage />);
    await startDownload();

    expect(await screen.findByText("คลิปนี้โหลดไว้แล้ว")).toBeInTheDocument();
    const row = screen.getByRole("listitem", { name: RICK.title });
    expect(row).toHaveAttribute("aria-current", "true");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledTimes(1);
    expect(vi.mocked(Element.prototype.scrollIntoView).mock.contexts[0]).toBe(row);
  });

  it("highlights the row a job that failed duplicate names (another site's link, D51)", async () => {
    const duplicate = jobOf({
      state: "failed",
      error: { code: "duplicate", message: "คลิปนี้โหลดไว้แล้ว", yt_dlp_version: "2026.10.26", fix: null, clip_id: MOON.id },
    });
    backend([status(), current(null), clips([NIGHT, MOON, RICK]), current(duplicate), post(jobOf({ id: null }))]);
    render(<ClipsPage />);
    await startDownload();

    await nextPoll();

    expect(screen.getByText("คลิปนี้โหลดไว้แล้ว")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: MOON.title })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("listitem", { name: RICK.title })).not.toHaveAttribute("aria-current");
  });

  it("shows the message of a link no extractor can load", async () => {
    const message = 'เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"';
    const unsupported = jobOf({
      state: "failed",
      error: { code: "unsupported", message, yt_dlp_version: "2026.10.26", fix: null, clip_id: null },
    });
    backend([status(), current(unsupported)]);
    render(<ClipsPage />);

    expect(await screen.findByText(message)).toBeInTheDocument();
  });

  it("clears the last message on the next โหลด", async () => {
    backend([
      status(),
      current(null),
      post({ code: "invalid_url", message: "x" }, 400),
      { method: "POST", path: "/api/spoil/downloads", reply: () => new Promise(() => {}) },
    ]);
    render(<ClipsPage />);
    const user = await startDownload();
    expect(await screen.findByText("ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "โหลด" }));

    expect(screen.queryByText("ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป")).not.toBeInTheDocument();
  });

  it("switches to not ready on 503 not_ready", async () => {
    const noDeno = ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" as const } : i));
    // The tab opens ready; after the 503 it asks for the status again and Deno is gone.
    backend([status(), status(noDeno), current(null), post({ code: "not_ready", message: "x" }, 503)]);
    render(<ClipsPage />);
    await startDownload();

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
  });
});

describe("offline", () => {
  it("shows the OfflinePanel when a fetch fails, and Refresh loads the tab again", async () => {
    backend([{ path: "/api/setup/status", reply: () => Promise.reject(new TypeError("Failed to fetch")) }, status(), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByLabelText("ลิงก์คลิป")).toBeInTheDocument();
  });

  it("shows the OfflinePanel when the backend gives no answer in 30 s", async () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<ClipsPage />);

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
    render(<ClipsPage />);
    expect(await screen.findByText("40%")).toBeInTheDocument();

    await nextPoll();

    expect(screen.getByText("Backend offline")).toBeInTheDocument();
  });
});

describe("Temp clip list", () => {
  it("says there is no clip yet when the list is empty", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "คลิปที่โหลดมา 0" })).toBeInTheDocument();
  });

  it("shows each clip newest first with what it is", async () => {
    backend([status(), current(null), clips([NIGHT, MOON, RICK])]);
    render(<ClipsPage />);

    const rows = await screen.findAllByRole("listitem");
    expect(rows.map((row) => row.getAttribute("aria-label"))).toEqual([NIGHT.title, MOON.title, RICK.title]);
    expect(screen.getByRole("heading", { name: "คลิปที่โหลดมา 3" })).toBeInTheDocument();

    const night = within(rows[0]);
    expect(night.getByText("Public Domain Movies · 1:35:42")).toBeInTheDocument();
    expect(night.getByText("1920×1080 นอน · 1.6 GB · 29 ต.ค. 18:52")).toBeInTheDocument();
    expect(rows[0].querySelector("img[src*='thumbnail']")).toBeNull();

    const moon = within(rows[1]);
    expect(moon.getByText("NASA · 0:39")).toBeInTheDocument();
    expect(moon.getByText("1080×1920 ตั้ง · 16.7 MB · 29 ต.ค. 18:34")).toBeInTheDocument();
    expect(rows[1].querySelector("img[src*='thumbnail']")).toHaveAttribute(
      "src",
      "/api/spoil/clips/f7jkZXvaB4g/thumbnail",
    );

    expect(within(rows[2]).getByText("Rick Astley · 3:33")).toBeInTheDocument();
  });

  it("names the site of a clip from another site after its channel (D52)", async () => {
    const page = clipOf({ id: "facebook-123", title: "From a page", channel: "เพจ", site: "Facebook", duration_s: 30 });
    const noChannel = clipOf({ id: "tiktok-7", title: "No channel", channel: null, site: "TikTok", duration_s: 9 });
    backend([status(), current(null), clips([page, noChannel])]);
    render(<ClipsPage />);

    expect(within(await screen.findByRole("listitem", { name: "From a page" })).getByText("เพจ · Facebook · 0:30")).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: "No channel" })).getByText("TikTok · 0:09")).toBeInTheDocument();
  });

  it("asks for a link of any site, not only YouTube", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByLabelText("ลิงก์คลิป")).toHaveAttribute("placeholder", "วางลิงก์คลิป (YouTube, Facebook, TikTok …)");
  });

  it("still shows the list when the tab is not ready", async () => {
    backend([status(ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" } : i))), current(null), clips([RICK])]);
    render(<ClipsPage />);

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: RICK.title })).toBeInTheDocument();
  });

  it("goes offline when the list can't be loaded", async () => {
    backend([status(), current(null), { path: CLIPS_PATH, reply: () => Promise.reject(new TypeError("Failed to fetch")) }]);
    render(<ClipsPage />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });

  it("plays a clicked row in the transcript panel and marks it กำลังเล่น", async () => {
    backend([status(), current(null), clips([MOON, RICK])]);
    const { container } = render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: /^From the Moon/ }));

    const video = panel().querySelector("video");
    // `?v=` keeps the browser off a cached file from before a trim (D41).
    expect(video).toHaveAttribute("src", `/api/spoil/clips/f7jkZXvaB4g/video?v=${encodeURIComponent(MOON.downloaded_at)}`);
    // The player moved into the panel: none above the list any more (D25).
    expect(container.querySelectorAll("video")).toHaveLength(1);
    expect(video).toHaveAttribute("controls");
    expect(within(screen.getByRole("listitem", { name: MOON.title })).getByText("กำลังเล่น")).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: RICK.title })).queryByText("กำลังเล่น")).not.toBeInTheDocument();
  });

  it("deletes a row after confirm", async () => {
    const confirm = vi.fn(() => true);
    vi.stubGlobal("confirm", confirm);
    backend([status(), current(null), clips([MOON, RICK]), deleteClip(RICK.id, () => new Response(null, { status: 204 }))]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${RICK.title}` }));

    expect(confirm).toHaveBeenCalledWith(`ลบ ${RICK.title}?`);
    expect(fetchMock).toHaveBeenCalledWith(`/api/spoil/clips/${RICK.id}`, expect.objectContaining({ method: "DELETE" }));
    await vi.waitFor(() => expect(screen.queryByRole("listitem", { name: RICK.title })).not.toBeInTheDocument());
    expect(screen.getByRole("heading", { name: "คลิปที่โหลดมา 1" })).toBeInTheDocument();
  });

  it("sends nothing when the confirm is cancelled", async () => {
    vi.stubGlobal("confirm", vi.fn(() => false));
    backend([status(), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${RICK.title}` }));

    expect(fetchMock).not.toHaveBeenCalledWith(expect.stringContaining(RICK.id), expect.anything());
    expect(screen.getByRole("listitem", { name: RICK.title })).toBeInTheDocument();
  });

  it("lets go of the playing clip before sending DELETE", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    const order: string[] = [];
    vi.mocked(HTMLMediaElement.prototype.load).mockImplementation(function (this: HTMLMediaElement) {
      order.push(`load src=${this.getAttribute("src") ?? ""}`);
    });
    backend([
      status(),
      current(null),
      clips([MOON]),
      deleteClip(MOON.id, () => {
        order.push("DELETE");
        return new Response(null, { status: 204 });
      }),
    ]);
    const { container } = render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.click(await screen.findByRole("button", { name: /^From the Moon/ }));

    await user.click(screen.getByRole("button", { name: `ลบ ${MOON.title}` }));

    expect(order).toEqual(["load src=", "DELETE"]);
    expect(container.querySelector("video")).toBeNull();
    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน")).toBeInTheDocument();
  });

  it("shows the API message under the row when the file is in use, and keeps the row", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    const inUse = "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง";
    backend([
      status(),
      current(null),
      clips([MOON, RICK]),
      deleteClip(RICK.id, () => jsonResponse({ code: "in_use", message: inUse }, 409)),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${RICK.title}` }));

    const row = screen.getByRole("listitem", { name: RICK.title });
    expect(await within(row).findByText(inUse)).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: MOON.title })).queryByText(inUse)).not.toBeInTheDocument();
  });
});

function transcribeJobOf(change: Partial<TranscribeJob>): TranscribeJob {
  return { clip_id: NIGHT.id, state: "preparing", percent: null, cancel_requested: false, error: null, ...change };
}

const NIGHT_TRANSCRIPT: Transcript = {
  clip_id: NIGHT.id,
  language: "en",
  duration_s: 5742,
  model: "openai/whisper-large-v3-turbo",
  revision: "41f01f3",
  transcribed_at: "2026-10-29T19:12:00+07:00",
  lines: [
    { start_s: 12.4, end_s: 15.0, text: "They're coming to get you, Barbara.", edited: false },
    { start_s: 3725.2, end_s: 3727.9, text: "Is anybody here?", edited: false },
  ],
};

const TRANSCRIBED_NIGHT = { ...NIGHT, transcribed: true };

async function selectRow(title: string | RegExp) {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  await user.click(await screen.findByRole("button", { name: title }));
  return user;
}

describe("transcript panel", () => {
  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
  });

  it("says เลือกคลิปจากรายการ until a row is clicked, then shows the clip and ถอดบทพูด", async () => {
    backend([status(READY_ITEMS), current(null), clips([NIGHT, MOON])]);
    render(<ClipsPage />);

    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("เลือกคลิปจากรายการ")).toBeInTheDocument();

    await selectRow(/^Night of the Living Dead/);

    expect(within(panel()).getByText(NIGHT.title)).toBeInTheDocument();
    expect(within(panel()).getByText("1:35:42")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ถอดบทพูด" })).toBeEnabled();
    expect(within(panel()).queryByText("เลือกคลิปจากรายการ")).not.toBeInTheDocument();
  });

  it("posts the clip, shows กำลังถอด 35%, then the transcript lines and ถอดแล้ว on the row", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT, MOON]),
      clips([TRANSCRIBED_NIGHT, MOON]),
      transcription(null),
      transcription(transcribeJobOf({ state: "transcribing", percent: 35 })),
      transcription(transcribeJobOf({ state: "done" })),
      postTranscription(transcribeJobOf({})),
      transcript(NIGHT_TRANSCRIPT),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/spoil/transcriptions",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ clip_id: NIGHT.id }) }),
    );
    expect(await within(panel()).findByText("กำลังเตรียมเสียง…")).toBeInTheDocument();
    expect(within(panel()).getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");

    await nextPoll();
    expect(within(panel()).getByText("กำลังถอด")).toBeInTheDocument();
    expect(within(panel()).getByText("35%")).toBeInTheDocument();
    expect(within(panel()).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "35");

    await nextPoll();
    expect(await within(panel()).findByRole("button", { name: /They're coming to get you, Barbara\./ })).toBeInTheDocument();
    expect(within(panel()).getByText("ถอดเสร็จ")).toBeInTheDocument();
    expect(within(panel()).getByText("คลิปนี้ถอดแล้ว")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ถอดใหม่" })).toBeInTheDocument();
    expect(within(panel()).getByText("ภาษา: en")).toBeInTheDocument();
    expect(within(panel()).getByText("[01:02:05]")).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: NIGHT.title })).getByText("ถอดแล้ว")).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: MOON.title })).queryByText("ถอดแล้ว")).not.toBeInTheDocument();
  });

  it("jumps the player to a line's start and plays it", async () => {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_NIGHT]), transcript(NIGHT_TRANSCRIPT)]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(await within(panel()).findByRole("button", { name: /They're coming to get you, Barbara\./ }));

    const video = panel().querySelector("video")!;
    expect(video.currentTime).toBe(12.4);
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
  });

  it("copies the transcript as the .txt text and links the files", async () => {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_NIGHT]), transcript(NIGHT_TRANSCRIPT)]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(await within(panel()).findByRole("button", { name: "Copy" }));

    expect(await navigator.clipboard.readText()).toBe(
      "[00:00:12] They're coming to get you, Barbara.\n[01:02:05] Is anybody here?\n",
    );
    expect(within(panel()).getByRole("link", { name: ".txt" })).toHaveAttribute(
      "href",
      `/api/spoil/clips/${NIGHT.id}/transcript.txt`,
    );
    expect(within(panel()).getByRole("link", { name: ".srt" })).toHaveAttribute(
      "href",
      `/api/spoil/clips/${NIGHT.id}/transcript.srt`,
    );
  });

  it("says ไม่พบคำพูดในคลิปนี้ and offers no Copy or files for a transcript with no lines", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_NIGHT]),
      transcript({ ...NIGHT_TRANSCRIPT, language: null, lines: [] }),
    ]);
    render(<ClipsPage />);
    await selectRow(/^Night of the Living Dead/);

    expect(await within(panel()).findByText("ไม่พบคำพูดในคลิปนี้")).toBeInTheDocument();
    expect(within(panel()).getByText("ภาษา: ไม่ทราบ")).toBeInTheDocument();
    expect(within(panel()).queryByRole("button", { name: "Copy" })).not.toBeInTheDocument();
    expect(within(panel()).queryByRole("link", { name: ".srt" })).not.toBeInTheDocument();
  });

  it("selects the clip being transcribed when the tab opens, and polls it beside a download", async () => {
    backend([
      status(READY_ITEMS),
      current(DOWNLOADING_40),
      clips([NIGHT, MOON]),
      transcription(transcribeJobOf({ state: "transcribing", percent: 35 })),
      transcription(transcribeJobOf({ state: "transcribing", percent: 40 })),
    ]);
    render(<ClipsPage />);

    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("35%")).toBeInTheDocument();
    expect(within(panel()).getByText(NIGHT.title)).toBeInTheDocument();
    expect(within(screen.getByRole("listitem", { name: NIGHT.title })).getByText("กำลังเล่น")).toBeInTheDocument();
    expect(screen.getByText("กำลังโหลด From the Moon")).toBeInTheDocument();

    await nextPoll();

    expect(within(panel()).getByText("40%")).toBeInTheDocument();
    // Both jobs were asked again: one poll each, side by side (D24).
    const polls = (path: string) => fetchMock.mock.calls.filter(([input]) => String(input) === path).length;
    expect(polls(TRANSCRIPTION_PATH)).toBeGreaterThanOrEqual(2);
    expect(polls("/api/spoil/downloads/current")).toBeGreaterThanOrEqual(2);
    // Selected for its job, not by a click: the player waits.
    expect(panel().querySelector("video")!.autoplay).toBe(false);
  });

  it("keeps the old transcript when a new job on a transcribed clip is cancelled", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_NIGHT]),
      transcription(transcribeJobOf({ state: "transcribing", percent: 35 })),
      transcription(transcribeJobOf({ state: "cancelled" })),
      transcript(NIGHT_TRANSCRIPT),
    ]);
    render(<ClipsPage />);
    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("35%")).toBeInTheDocument();
    expect(within(panel()).queryByRole("button", { name: /Barbara/ })).not.toBeInTheDocument();

    await nextPoll();

    expect(within(panel()).getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(await within(panel()).findByRole("button", { name: /They're coming to get you, Barbara\./ })).toBeInTheDocument();
  });

  it("links to the ติดตั้ง tab instead of ถอดบทพูด while the Whisper model is missing; the link field still works", async () => {
    backend([status(), current(null), clips([NIGHT])]);
    render(<ClipsPage />);
    await selectRow(/^Night of the Living Dead/);

    expect(within(panel()).getByText("ยังติดตั้งไม่ครบ: Whisper model")).toBeInTheDocument();
    expect(within(panel()).getByRole("link", { name: "ไปหน้าติดตั้ง" })).toHaveAttribute("href", "#/setup");
    expect(within(panel()).queryByRole("button", { name: "ถอดบทพูด" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeEnabled();
  });

  it("sends DELETE on ยกเลิก and shows กำลังยกเลิก…, then ยกเลิกแล้ว", async () => {
    const running = transcribeJobOf({ state: "transcribing", percent: 35 });
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT]),
      transcription(running),
      transcription({ ...running, cancel_requested: true }),
      transcription(transcribeJobOf({ state: "cancelled" })),
      { method: "DELETE", path: TRANSCRIPTION_PATH, reply: () => jsonResponse({ ...running, cancel_requested: true }, 202) },
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByRole("button", { name: "ยกเลิก" }));

    expect(fetchMock).toHaveBeenCalledWith(TRANSCRIPTION_PATH, expect.objectContaining({ method: "DELETE" }));
    expect(await within(panel()).findByText("กำลังยกเลิก…")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ยกเลิก" })).toBeDisabled();

    await nextPoll();
    await nextPoll();
    expect(within(panel()).getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ถอดบทพูด" })).toBeEnabled();
  });

  it.each([
    ["failed", transcribeJobOf({ state: "failed", error: { code: "no_audio", message: "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้" } }), "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้"],
    ["lost", null, "งานถอดหายเพราะ backend เริ่มใหม่ ลองถอดอีกครั้ง"],
  ])("shows how a %s job ended in the panel", async (_, ended, text) => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT]),
      transcription(transcribeJobOf({ state: "transcribing", percent: 5 })),
      transcription(ended),
    ]);
    render(<ClipsPage />);
    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("5%")).toBeInTheDocument();

    await nextPoll();

    expect(within(panel()).getByRole("status")).toHaveTextContent(text);
  });

  it("follows the job on 409 busy for this clip", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT]),
      transcription(null),
      transcription(transcribeJobOf({ state: "transcribing", percent: 12 })),
      postTranscription({ code: "busy", message: "กำลังถอดคลิปอื่นอยู่" }, 409),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("12%")).toBeInTheDocument();
  });

  it("disables ถอดบทพูด and names the other clip on 409 busy", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT, MOON]),
      transcription(null),
      transcription(transcribeJobOf({ clip_id: MOON.id, state: "transcribing", percent: 12 })),
      postTranscription({ code: "busy", message: "กำลังถอดคลิปอื่นอยู่" }, 409),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText(`กำลังถอด ${MOON.title}`)).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ถอดบทพูด" })).toBeDisabled();
  });

  it("says ไม่พบคลิปนี้ in the panel and loads the list again on 404", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT]),
      clips([]),
      postTranscription({ code: "not_found", message: "x" }, 404),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน")).toBeInTheDocument();
    expect(clipListCalls()).toBe(2);
    expect(within(panel()).getByText("ไม่พบคลิปนี้")).toBeInTheDocument();
    expect(within(panel()).getByText("เลือกคลิปจากรายการ")).toBeInTheDocument();
  });

  it("switches the panel to not ready on 503 not_ready", async () => {
    const noModel = READY_ITEMS.map((i) => (i.id === "model_whisper" ? { ...i, status: "missing" as const } : i));
    backend([
      status(READY_ITEMS),
      status(noModel),
      current(null),
      clips([NIGHT]),
      postTranscription({ code: "not_ready", message: "x" }, 503),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("ยังติดตั้งไม่ครบ: Whisper model")).toBeInTheDocument();
  });

  it("keeps following a running download when a 503 finds an item the download needs is gone", async () => {
    const noFfmpeg = READY_ITEMS.map((i) => (i.id === "ffmpeg" ? { ...i, status: "missing" as const } : i));
    backend([
      status(READY_ITEMS),
      status(noFfmpeg),
      current(DOWNLOADING_40),
      clips([NIGHT]),
      postTranscription({ code: "not_ready", message: "x" }, 503),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("ยังติดตั้งไม่ครบ: ffmpeg")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ยกเลิก" })).toBeInTheDocument();
    const polls = fetchMock.mock.calls.filter(([path]) => path === "/api/spoil/downloads/current").length;
    await nextPoll();
    expect(fetchMock.mock.calls.filter(([path]) => path === "/api/spoil/downloads/current").length).toBe(polls + 1);
  });

  it("goes offline on a POST answer the API never sends", async () => {
    backend([status(READY_ITEMS), current(null), clips([NIGHT]), postTranscription({ code: "x", message: "x" }, 500)]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });

  it("empties the panel when the selected clip is deleted", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    backend([status(READY_ITEMS), current(null), clips([NIGHT]), deleteClip(NIGHT.id, () => new Response(null, { status: 204 }))]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(screen.getByRole("button", { name: `ลบ ${NIGHT.title}` }));

    expect(await within(panel()).findByText("เลือกคลิปจากรายการ")).toBeInTheDocument();
    expect(panel().querySelector("video")).toBeNull();
  });

  it("keeps the clip being transcribed selected and shows the API message under its row when its delete is refused", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    const refused = "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ";
    backend([
      status(READY_ITEMS),
      current(null),
      clips([NIGHT]),
      transcription(transcribeJobOf({ state: "transcribing", percent: 5 })),
      deleteClip(NIGHT.id, () => jsonResponse({ code: "transcribing", message: refused }, 409)),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${NIGHT.title}` }));

    expect(await within(screen.getByRole("listitem", { name: NIGHT.title })).findByText(refused)).toBeInTheDocument();
    expect(within(panel()).getByText("5%")).toBeInTheDocument();
  });
});

describe("editing a Transcript line (spoil-maker D54)", () => {
  const LINE_0_PATH = `${CLIPS_PATH}/${NIGHT.id}/transcript/lines/0`;
  const patchLine = (reply: () => Response | Promise<Response>): Route => ({ method: "PATCH", path: LINE_0_PATH, reply });
  const FIXED = { start_s: 12.4, end_s: 15.0, text: "They're coming for you, Barbara.", edited: true };

  async function openEditor(routes: Route[] = []) {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_NIGHT]), transcript(NIGHT_TRANSCRIPT), ...routes]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);
    await user.click(await within(panel()).findByRole("button", { name: "แก้ [00:00:12]" }));
    return user;
  }

  function editor(): HTMLElement {
    return within(panel()).getByRole("textbox", { name: "แก้บรรทัด [00:00:12]" });
  }

  function patchCalls() {
    return fetchMock.mock.calls.filter(([, init]) => init?.method === "PATCH");
  }

  it("opens a field with the line's text, บันทึก and ยกเลิก", async () => {
    await openEditor();

    expect(editor()).toHaveValue("They're coming to get you, Barbara.");
    expect(within(panel()).getByRole("button", { name: "บันทึก" })).toBeEnabled();
    expect(within(panel()).getByRole("button", { name: "ยกเลิก" })).toBeEnabled();
  });

  it("can't save an empty line", async () => {
    const user = await openEditor();

    await user.clear(editor());
    await user.type(editor(), "   ");

    expect(within(panel()).getByRole("button", { name: "บันทึก" })).toBeDisabled();
  });

  it("saves the new text, then shows it with แก้แล้ว", async () => {
    const user = await openEditor([patchLine(() => jsonResponse(FIXED))]);

    await user.clear(editor());
    await user.type(editor(), "They're coming for you, Barbara.");
    await user.click(within(panel()).getByRole("button", { name: "บันทึก" }));

    expect(await within(panel()).findByRole("button", { name: /They're coming for you, Barbara\./ })).toBeInTheDocument();
    expect(within(panel()).getByText("แก้แล้ว")).toBeInTheDocument();
    expect(within(panel()).queryByRole("textbox")).not.toBeInTheDocument();
    expect(patchCalls()).toEqual([
      [LINE_0_PATH, expect.objectContaining({ body: JSON.stringify({ text: "They're coming for you, Barbara." }) })],
    ]);
  });

  it("saves on Enter, Shift+Enter too, so a line never breaks in two", async () => {
    const user = await openEditor([patchLine(() => jsonResponse(FIXED))]);

    await user.type(editor(), "{Shift>}{Enter}{/Shift}");

    expect(await within(panel()).findByText("แก้แล้ว")).toBeInTheDocument();
    expect(patchCalls()).toEqual([
      [LINE_0_PATH, expect.objectContaining({ body: JSON.stringify({ text: "They're coming to get you, Barbara." }) })],
    ]);
  });

  it("ยกเลิก puts the old text back and sends nothing", async () => {
    const user = await openEditor();

    await user.type(editor(), " typo");
    await user.click(within(panel()).getByRole("button", { name: "ยกเลิก" }));

    expect(within(panel()).getByRole("button", { name: /They're coming to get you, Barbara\.$/ })).toBeInTheDocument();
    expect(within(panel()).queryByText("แก้แล้ว")).not.toBeInTheDocument();
    expect(patchCalls()).toEqual([]);
  });

  it("shows a line edited earlier with แก้แล้ว", async () => {
    const edited = { ...NIGHT_TRANSCRIPT, lines: [FIXED, NIGHT_TRANSCRIPT.lines[1]] };
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_NIGHT]), transcript(edited)]);
    render(<ClipsPage />);
    await selectRow(/^Night of the Living Dead/);

    const line = await within(panel()).findByRole("listitem", { name: "[00:00:12]" });
    expect(within(line).getByText("แก้แล้ว")).toBeInTheDocument();
    expect(within(within(panel()).getByRole("listitem", { name: "[01:02:05]" })).queryByText("แก้แล้ว")).not.toBeInTheDocument();
  });

  it.each([
    ["clip_busy", "คลิปนี้กำลังถูกใช้ในงานอื่น"],
    ["transcribing", "กำลังถอดคลิปนี้อยู่ รอให้ถอดเสร็จก่อนแล้วแก้"],
  ])("keeps the field open and shows the API's message on 409 %s", async (code, message) => {
    const user = await openEditor([patchLine(() => jsonResponse({ code, message }, 409))]);

    await user.type(editor(), "!");
    await user.click(within(panel()).getByRole("button", { name: "บันทึก" }));

    expect(await within(panel()).findByText(message)).toBeInTheDocument();
    expect(editor()).toHaveValue("They're coming to get you, Barbara.!");
  });

  it("closes the field when another clip is selected", async () => {
    const transcribedMoon = { ...MOON, transcribed: true };
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_NIGHT, transcribedMoon]),
      transcript(NIGHT_TRANSCRIPT),
      transcript({ ...NIGHT_TRANSCRIPT, clip_id: MOON.id }),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);
    await user.click(await within(panel()).findByRole("button", { name: "แก้ [00:00:12]" }));

    await selectRow(/^From the Moon/);
    await selectRow(/^Night of the Living Dead/);

    expect(await within(panel()).findByRole("button", { name: "แก้ [00:00:12]" })).toBeInTheDocument();
    expect(within(panel()).queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("asks before transcribing a clip with edited lines again, then sends confirm_edit_loss", async () => {
    const confirm = vi.fn(() => true);
    vi.stubGlobal("confirm", confirm);
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_NIGHT]),
      transcript(NIGHT_TRANSCRIPT),
      postTranscription({ code: "has_edits", message: "ถอดใหม่จะลบบทพูดที่แก้ไว้" }, 409),
      postTranscription(transcribeJobOf({})),
      transcription(null),
      transcription(transcribeJobOf({ state: "transcribing", percent: 5 })),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(await within(panel()).findByRole("button", { name: "ถอดใหม่" }));

    expect(confirm).toHaveBeenCalledWith("ถอดใหม่จะลบบทพูดที่แก้ไว้");
    expect(await within(panel()).findByText("กำลังเตรียมเสียง…")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/spoil/transcriptions",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ clip_id: NIGHT.id, confirm_edit_loss: true }) }),
    );
  });

  it("sends nothing more when that confirm is cancelled", async () => {
    vi.stubGlobal("confirm", vi.fn(() => false));
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_NIGHT]),
      transcript(NIGHT_TRANSCRIPT),
      postTranscription({ code: "has_edits", message: "ถอดใหม่จะลบบทพูดที่แก้ไว้" }, 409),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(await within(panel()).findByRole("button", { name: "ถอดใหม่" }));

    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
    expect(within(panel()).getByText("คลิปนี้ถอดแล้ว")).toBeInTheDocument();
  });
});

describe("บรรยายฉาก on a clip row (spoil-maker D16, D45)", () => {
  const TRANSCRIBED = clipOf({ transcribed: true });

  function describeJobOf(change: Partial<DescribeJob>): DescribeJob {
    return {
      kind: "describe",
      state: "cutting",
      clip_id: TRANSCRIBED.id,
      percent: 0,
      done: null,
      total: null,
      error: null,
      cancel_requested: false,
      started_at: "2026-11-02T10:00:00+07:00",
      ...change,
    };
  }

  const row = () => screen.getByRole("listitem", { name: TRANSCRIBED.title });

  it("offers บรรยายฉาก only on a transcribed clip", async () => {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED, MOON])]);
    render(<ClipsPage />);

    expect(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" })).toBeEnabled();
    expect(within(screen.getByRole("listitem", { name: MOON.title })).queryByRole("button", { name: "บรรยายฉาก" })).toBeNull();
  });

  it("says under บรรยายฉาก what it does (spoil-maker D58)", async () => {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED])]);
    render(<ClipsPage />);

    const button = await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" });
    expect(button).toHaveAccessibleDescription("ให้ AI เขียนว่าแต่ละฉากมีภาพอะไร ใช้ตอนร่างบทสปอย");
  });

  it("posts the clip, shows 40%, then บรรยายฉากแล้ว", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      clips([{ ...TRANSCRIBED, described: true }]),
      describing(null),
      postDescribe(describeJobOf({})),
      describing(describeJobOf({ state: "describing", percent: null, done: 40, total: 100 })),
      describing(describeJobOf({ state: "done", percent: null, done: 100, total: 100 })),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" }));
    await nextPoll();

    expect(within(row()).getByText("40%")).toBeInTheDocument();
    expect(within(row()).getByText("กำลังบรรยายฉาก")).toBeInTheDocument();
    const posted = fetchMock.mock.calls.find(([input, init]) => String(input) === "/api/spoil-maker/describes" && init?.method === "POST");
    expect(JSON.parse(String(posted![1]!.body))).toEqual({ clip_id: TRANSCRIBED.id });

    await nextPoll();

    expect(await within(row()).findByText("บรรยายฉากแล้ว")).toBeInTheDocument();
    expect(within(row()).queryByText("กำลังบรรยายฉาก")).toBeNull();
  });

  it("sends DELETE on ยกเลิก", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      describing(describeJobOf({ state: "describing", percent: null, done: 3, total: 10 })),
      { method: "DELETE", path: DESCRIBE_PATH, reply: () => jsonResponse(describeJobOf({ state: "describing", cancel_requested: true })) },
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "ยกเลิก" }));

    expect(fetchMock.mock.calls.some(([input, init]) => String(input) === DESCRIBE_PATH && init?.method === "DELETE")).toBe(true);
  });

  it("names the running job from 409 gpu_busy: รอให้งานถอดบทพูดเสร็จก่อน", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      postDescribe({ code: "gpu_busy", message: "GPU busy", running: "transcribe" }, 409),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" }));

    expect(await within(row()).findByText("รอให้งานถอดบทพูดเสร็จก่อน")).toBeInTheDocument();
  });

  it("disables บรรยายฉาก with the reason while a transcription runs", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED, NIGHT]),
      transcription(transcribeJobOf({ clip_id: NIGHT.id, state: "transcribing", percent: 10 })),
    ]);
    render(<ClipsPage />);

    const button = await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" });

    expect(button).toBeDisabled();
    expect(button).toHaveAccessibleDescription("รอให้งานถอดบทพูดเสร็จก่อน");
  });

  it("disables บรรยายฉาก on other clips while one is described", async () => {
    const other = clipOf({ id: "aaaaaaaaaaa", title: "Another clip", transcribed: true });
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED, other]),
      describing(describeJobOf({ state: "describing", percent: null, done: 1, total: 10 })),
    ]);
    render(<ClipsPage />);

    const button = await within(await screen.findByRole("listitem", { name: "Another clip" })).findByRole("button", { name: "บรรยายฉาก" });

    expect(button).toBeDisabled();
    expect(button).toHaveAccessibleDescription("รอให้งานบรรยายฉากเสร็จก่อน");
  });

  it("asks before describing a described clip again, with focus on บรรยายฉากใหม่", async () => {
    const described = { ...TRANSCRIBED, described: true };
    backend([status(READY_ITEMS), current(null), clips([described]), postDescribe(describeJobOf({}))]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" }));

    expect(within(row()).getByText("บรรยายฉากคลิปนี้ใหม่?")).toBeInTheDocument();
    expect(within(row()).getByText("ผลเดิมจะถูกแทนที่เมื่อบรรยายฉากเสร็จ")).toBeInTheDocument();
    expect(within(row()).getByRole("button", { name: "บรรยายฉากใหม่" })).toHaveFocus();
    const posts = () => fetchMock.mock.calls.filter(([, init]) => init?.method === "POST").length;
    expect(posts()).toBe(0);

    await user.click(within(row()).getByRole("button", { name: "บรรยายฉากใหม่" }));

    expect(posts()).toBe(1);
  });

  it("sends nothing when that ask is cancelled", async () => {
    backend([status(READY_ITEMS), current(null), clips([{ ...TRANSCRIBED, described: true }])]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" }));
    await user.click(within(row()).getByRole("button", { name: "ยกเลิก" }));

    expect(within(row()).queryByText("บรรยายฉากคลิปนี้ใหม่?")).toBeNull();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("says งานหยุดกลางทาง when the job fails in the model, and offers บรรยายฉาก again", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      describing(describeJobOf({ state: "describing", percent: null, done: 1, total: 10 })),
      describing(describeJobOf({ state: "failed", error: { code: "model_failed", message: "บรรยายฉากไม่สำเร็จ: x" } })),
    ]);
    render(<ClipsPage />);

    await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByText("กำลังบรรยายฉาก");
    await nextPoll();

    expect(await within(row()).findByText("งานหยุดกลางทาง")).toBeInTheDocument();
    expect(within(row()).getByRole("button", { name: "บรรยายฉาก" })).toBeEnabled();
  });

  it("says what is missing and links to ติดตั้ง on 503 not_ready", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      postDescribe({ code: "not_ready", message: "ยังติดตั้งไม่ครบ: Qwen3.5 9B model", rows: ["model_qwen"] }, 503),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("listitem", { name: TRANSCRIBED.title })).findByRole("button", { name: "บรรยายฉาก" }));

    expect(await within(row()).findByText("ยังติดตั้งไม่ครบ: Qwen3.5 9B model")).toBeInTheDocument();
    expect(within(row()).getByRole("link", { name: "ไปหน้าติดตั้ง" })).toHaveAttribute("href", "#/setup");
  });

  it("shows clip_busy under the row when the clip being described is deleted", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED]),
      describing(describeJobOf({ state: "describing", percent: null, done: 1, total: 10 })),
      deleteClip(TRANSCRIBED.id, () => jsonResponse({ code: "clip_busy", message: "คลิปนี้กำลังถูกใช้ในงานอื่น" }, 409)),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${TRANSCRIBED.title}` }));

    expect(await within(row()).findByText("คลิปนี้กำลังถูกใช้ในงานอื่น")).toBeInTheDocument();
  });

  it("says รอให้งานบรรยายฉากเสร็จก่อน in the panel when ถอดบทพูด meets 409 gpu_busy", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([MOON]),
      postTranscription({ code: "gpu_busy", message: "GPU busy", running: "describe" }, 409),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByText(MOON.title));
    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("รอให้งานบรรยายฉากเสร็จก่อน")).toBeInTheDocument();
  });
});

describe("a clip in the Spoil draft (spoil-maker D29, D49)", () => {
  const IN_DRAFT = clipOf({ transcribed: true, described: true, in_draft: true });
  const WARNING = "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft";
  const row = () => screen.getByRole("listitem", { name: IN_DRAFT.title });
  const sentWith = (method: string) => fetchMock.mock.calls.filter(([, init]) => init?.method === method);

  async function openList() {
    render(<ClipsPage />);
    await screen.findByRole("listitem", { name: IN_DRAFT.title });
    return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  }

  it("ลบ warns in the row first, then ทำต่อ deletes it", async () => {
    const confirm = vi.fn(() => true);
    vi.stubGlobal("confirm", confirm);
    backend([status(READY_ITEMS), current(null), clips([IN_DRAFT]), deleteClip(IN_DRAFT.id, () => new Response(null, { status: 204 }))]);
    const user = await openList();

    await user.click(within(row()).getByRole("button", { name: `ลบ ${IN_DRAFT.title}` }));

    expect(within(row()).getByText(WARNING)).toBeInTheDocument();
    expect(within(row()).getByRole("button", { name: "ทำต่อ" })).toHaveFocus();
    expect(sentWith("DELETE")).toHaveLength(0);
    expect(confirm).not.toHaveBeenCalled();
    await user.click(within(row()).getByRole("button", { name: "ทำต่อ" }));

    expect(sentWith("DELETE")).toHaveLength(1);
  });

  it("ยกเลิก on that warning deletes nothing", async () => {
    backend([status(READY_ITEMS), current(null), clips([IN_DRAFT])]);
    const user = await openList();

    await user.click(within(row()).getByRole("button", { name: `ลบ ${IN_DRAFT.title}` }));
    await user.click(within(row()).getByRole("button", { name: "ยกเลิก" }));

    expect(within(row()).queryByText(WARNING)).toBeNull();
    expect(sentWith("DELETE")).toHaveLength(0);
  });

  it("บรรยายฉาก again warns, then ทำต่อ sends confirm_draft_loss", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([IN_DRAFT]),
      postDescribe({ kind: "describe", state: "cutting", clip_id: IN_DRAFT.id, percent: 0, done: null, total: null, error: null, cancel_requested: false, started_at: "2026-11-02T10:00:00+07:00" }),
    ]);
    const user = await openList();

    await user.click(within(row()).getByRole("button", { name: "บรรยายฉาก" }));

    expect(within(row()).getByText(WARNING)).toBeInTheDocument();
    expect(sentWith("POST")).toHaveLength(0);
    await user.click(within(row()).getByRole("button", { name: "ทำต่อ" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/spoil-maker/describes",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ clip_id: IN_DRAFT.id, confirm_draft_loss: true }) }),
    );
  });

  it("ถอดใหม่ warns in the panel before sending, then ทำต่อ sends confirm_draft_loss", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([IN_DRAFT]),
      transcript({ ...NIGHT_TRANSCRIPT, clip_id: IN_DRAFT.id }),
      postTranscription(transcribeJobOf({ clip_id: IN_DRAFT.id })),
      transcription(null),
      transcription(transcribeJobOf({ clip_id: IN_DRAFT.id, state: "transcribing", percent: 5 })),
    ]);
    const user = await openList();
    await user.click(within(row()).getAllByRole("button")[0]);

    await user.click(await within(panel()).findByRole("button", { name: "ถอดใหม่" }));

    expect(within(panel()).getByText(WARNING)).toBeInTheDocument();
    expect(sentWith("POST")).toHaveLength(0);
    await user.click(within(panel()).getByRole("button", { name: "ทำต่อ" }));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/spoil/transcriptions",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ clip_id: IN_DRAFT.id, confirm_draft_loss: true }) }),
    );
  });

  it("ถอดใหม่ sends nothing when the warning is cancelled", async () => {
    backend([status(READY_ITEMS), current(null), clips([IN_DRAFT]), transcript({ ...NIGHT_TRANSCRIPT, clip_id: IN_DRAFT.id })]);
    const user = await openList();
    await user.click(within(row()).getAllByRole("button")[0]);

    await user.click(await within(panel()).findByRole("button", { name: "ถอดใหม่" }));
    await user.click(within(panel()).getByRole("button", { name: "ยกเลิก" }));

    expect(sentWith("POST")).toHaveLength(0);
    expect(within(panel()).getByRole("button", { name: "ถอดใหม่" })).toBeInTheDocument();
  });
});

describe("ตัดช่วง (D36–D41)", () => {
  const TRANSCRIBED_RICK = { ...RICK, transcribed: true };
  const TRIMMED_AT = "2026-11-05T10:00:00+07:00";
  const TRIMMED_RICK = { ...RICK, duration_s: 183, trimmed: [{ start_s: 0, end_s: 30 }], trimmed_at: TRIMMED_AT };

  function trimJobOf(change: Partial<TrimJob>): TrimJob {
    return { clip_id: RICK.id, state: "trimming", percent: 0, kept_s: 183, cancel_requested: false, error: null, ...change };
  }

  beforeEach(() => {
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
  });

  const video = () => panel().querySelector("video")!;
  /** Moves the player as a seek would: jsdom fires no `timeupdate` of its own. */
  const seekTo = (seconds: number) => {
    video().currentTime = seconds;
    fireEvent(video(), new Event("timeupdate"));
  };
  const range = (n: number) => within(panel()).getByRole("group", { name: `ช่วง ${n}` });
  const slider = (name: string) => within(panel()).getByRole("slider", { name });

  /** Selects Rick, opens ตัดช่วง and adds a range at `at` seconds. */
  async function openWithRange(at = 0) {
    const user = await selectRow(/^Rick Astley/);
    await user.click(within(panel()).getByRole("button", { name: "ตัดช่วง" }));
    seekTo(at);
    await user.click(within(panel()).getByRole("button", { name: "เพิ่มช่วง" }));
    return user;
  }

  it("adds 30 s at the playhead, takes it off what is left, and disables ถอดบทพูด", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await selectRow(/^Rick Astley/);
    await user.click(within(panel()).getByRole("button", { name: "ตัดช่วง" }));
    expect(within(panel()).getByText("ตัดออก 0:00 · เหลือ 3:33")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ตัดคลิป" })).toBeDisabled();

    seekTo(0);
    await user.click(within(panel()).getByRole("button", { name: "เพิ่มช่วง" }));

    expect(within(range(1)).getByLabelText("เริ่ม")).toHaveValue("0:00:00.0");
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
    expect(within(panel()).getByText("ตัดออก 0:30 · เหลือ 3:03")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ตัดคลิป" })).toBeEnabled();
    expect(within(panel()).getByRole("button", { name: "ถอดบทพูด" })).toBeDisabled();
    expect(within(panel()).getByText("กดตัดคลิปหรือยกเลิกก่อน")).toBeInTheDocument();
  });

  it("reads a typed end of 1:30 as 90 s, and marks abc as an error that disables ตัดคลิป", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await openWithRange();
    const end = within(range(1)).getByLabelText("จบ");

    await user.clear(end);
    await user.type(end, "1:30");
    expect(within(panel()).getByText("ตัดออก 1:30 · เหลือ 2:03")).toBeInTheDocument();
    expect(slider("จุดจบช่วง 1")).toHaveAttribute("aria-valuenow", "90");

    await user.clear(end);
    await user.type(end, "abc");
    expect(end).toHaveAttribute("aria-invalid", "true");
    expect(within(range(1)).getByText("เวลาไม่ถูกต้อง")).toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ตัดคลิป" })).toBeDisabled();
  });

  it("moves an end handle 1 s per arrow, 10 s with Shift, never past the next range's start", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    seekTo(45);
    await user.click(within(panel()).getByRole("button", { name: "เพิ่มช่วง" }));
    const handle = slider("จุดจบช่วง 1");
    expect(handle).toHaveAttribute("aria-valuetext", "0:00:30.0");

    handle.focus();
    await user.keyboard("{ArrowRight}");
    expect(handle).toHaveAttribute("aria-valuenow", "31");
    await user.keyboard("{Shift>}{ArrowRight}{/Shift}");
    expect(handle).toHaveAttribute("aria-valuenow", "41");
    await user.keyboard("{Shift>}{ArrowRight}{/Shift}");
    expect(handle).toHaveAttribute("aria-valuenow", "45");
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:45.0");
  });

  it("ends a range near the end at the file's length floored to a tenth (213.47 → 213.4), not past it", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await selectRow(/^Rick Astley/);
    // The list's 213 is rounded; the file is 213.47 s, which a tenth would round up past.
    Object.defineProperty(video(), "duration", { value: 213.47, configurable: true });
    fireEvent(video(), new Event("durationchange"));
    await user.click(within(panel()).getByRole("button", { name: "ตัดช่วง" }));
    seekTo(200);

    await user.click(within(panel()).getByRole("button", { name: "เพิ่มช่วง" }));

    expect(within(range(1)).getByLabelText("เริ่ม")).toHaveValue("0:03:20.0");
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:03:33.4");
  });

  it("sets จบ from the player's time on จบ = ตอนนี้, to a tenth of a second", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    seekTo(95.34);

    await user.click(within(range(1)).getByRole("button", { name: "จบ = ตอนนี้" }));

    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:01:35.3");
  });

  it("removes a range on ✕, and ยกเลิก closes the section and forgets its ranges", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK])]);
    render(<ClipsPage />);
    const user = await openWithRange(0);

    await user.click(within(range(1)).getByRole("button", { name: "ลบช่วง 1" }));
    expect(within(panel()).queryByRole("group", { name: "ช่วง 1" })).not.toBeInTheDocument();

    await user.click(within(panel()).getByRole("button", { name: "เพิ่มช่วง" }));
    await user.click(within(panel()).getByRole("button", { name: "ยกเลิก" }));
    expect(within(panel()).queryByRole("button", { name: "ตัดคลิป" })).not.toBeInTheDocument();
    await user.click(within(panel()).getByRole("button", { name: "ตัดช่วง" }));
    expect(within(panel()).queryByRole("group", { name: "ช่วง 1" })).not.toBeInTheDocument();
  });

  it("keeps each clip's ranges while another clip is selected", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK, MOON])]);
    render(<ClipsPage />);
    await openWithRange(0);

    await selectRow(/^From the Moon/);
    expect(within(panel()).queryByRole("group", { name: "ช่วง 1" })).not.toBeInTheDocument();
    await selectRow(/^Rick Astley/);

    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
  });

  const DERIVED_QUESTION = "ตัดคลิปจะลบ Transcript (รวมบรรทัดที่แก้ไว้), ภาพฉากและการตัด EP ของคลิปนี้ ตัดต่อไหม?";
  const hasDerived = () => postTrim({ code: "has_derived", message: DERIVED_QUESTION, derived: ["transcript", "shots"] }, 409);
  const trimBodies = () =>
    fetchMock.mock.calls.filter(([input, init]) => String(input) === "/api/spoil/trims" && init?.method === "POST").map(([, init]) => init?.body);

  it("lets go of the player, asks the API's has_derived message, then posts confirm_derived_loss", async () => {
    const confirm = vi.fn(() => true);
    vi.stubGlobal("confirm", confirm);
    const srcAtPost: (string | null)[] = [];
    const answers = [() => jsonResponse({ code: "has_derived", message: DERIVED_QUESTION, derived: ["transcript"] }, 409), () => jsonResponse(trimJobOf({}), 202)];
    backend([
      status(READY_ITEMS),
      current(null),
      clips([TRANSCRIBED_RICK]),
      {
        method: "POST",
        path: "/api/spoil/trims",
        reply: () => {
          srcAtPost.push(video().getAttribute("src"));
          return answers.shift()!();
        },
      },
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);

    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    expect(confirm).toHaveBeenCalledWith(DERIVED_QUESTION);
    expect(srcAtPost).toEqual([null, null]);
    expect(trimBodies()).toEqual([
      JSON.stringify({ clip_id: RICK.id, ranges: [{ start_s: 0, end_s: 30 }] }),
      JSON.stringify({ clip_id: RICK.id, ranges: [{ start_s: 0, end_s: 30 }], confirm_derived_loss: true }),
    ]);
    expect(await within(panel()).findByText("กำลังตัดคลิป")).toBeInTheDocument();
  });

  it("posts once, and gives the player back, when that confirm is cancelled", async () => {
    vi.stubGlobal("confirm", vi.fn(() => false));
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_RICK]), hasDerived()]);
    render(<ClipsPage />);
    const user = await openWithRange(0);

    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    expect(trimBodies()).toHaveLength(1);
    expect(video()).toHaveAttribute("src", `/api/spoil/clips/${RICK.id}/video?v=${encodeURIComponent(RICK.downloaded_at)}`);
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
  });

  it("shows กำลังตัดคลิป 37%, then ตัดคลิปเสร็จ, the new ?v= and ตัดแล้ว on the row", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      clips([TRIMMED_RICK]),
      trimming(null),
      trimming(trimJobOf({ percent: 37 })),
      trimming(trimJobOf({ state: "done", percent: null })),
      postTrim(trimJobOf({})),
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));
    expect(video()).not.toHaveAttribute("src");

    await nextPoll();
    expect(within(panel()).getByText("กำลังตัดคลิป")).toBeInTheDocument();
    expect(within(panel()).getByText("37%")).toBeInTheDocument();
    expect(within(panel()).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "37");

    await nextPoll();
    expect(await within(panel()).findByText("ตัดคลิปเสร็จ: เหลือ 0:03:03")).toBeInTheDocument();
    expect(video()).toHaveAttribute("src", `/api/spoil/clips/${RICK.id}/video?v=${encodeURIComponent(TRIMMED_AT)}`);
    expect(within(screen.getByRole("listitem", { name: RICK.title })).getByText("ตัดแล้ว")).toBeInTheDocument();
    // done closes the section and drops its ranges.
    expect(within(panel()).queryByRole("group", { name: "ช่วง 1" })).not.toBeInTheDocument();
    expect(within(panel()).getByRole("button", { name: "ตัดช่วง" })).toBeEnabled();
  });

  it("keeps the player empty after done until the list brings the new ?v=", async () => {
    let listed: (response: Response) => void = () => {};
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      { path: CLIPS_PATH, reply: () => new Promise<Response>((resolve) => (listed = resolve)) },
      trimming(null),
      trimming(trimJobOf({ state: "done", percent: null })),
      postTrim(trimJobOf({})),
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    await nextPoll();
    expect(await within(panel()).findByText("ตัดคลิปเสร็จ: เหลือ 0:03:03")).toBeInTheDocument();
    // The old `?v=` would play the cached file from before the trim (D41).
    expect(video()).not.toHaveAttribute("src");

    await act(async () => listed(jsonResponse({ clips: [TRIMMED_RICK] })));
    expect(video()).toHaveAttribute("src", `/api/spoil/clips/${RICK.id}/video?v=${encodeURIComponent(TRIMMED_AT)}`);
  });

  it("says another clip is being trimmed on 409 busy, and names it on ตัดช่วง", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK, MOON]),
      trimming(null),
      trimming(trimJobOf({ clip_id: MOON.id, percent: 5 })),
      postTrim({ code: "busy", message: "กำลังตัดคลิปอื่นอยู่" }, 409),
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);

    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    expect(await within(panel()).findByText("กำลังตัดคลิปอื่นอยู่")).toBeInTheDocument();
    expect(within(panel()).getByText(`กำลังตัด ${MOON.title}`)).toBeInTheDocument();
    expect(video()).toHaveAttribute("src");
  });

  it("says the file is being replaced when ยกเลิก meets 409 replacing", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      trimming(trimJobOf({ percent: 99 })),
      { method: "DELETE", path: TRIM_PATH, reply: () => jsonResponse({ code: "replacing", message: "x" }, 409) },
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByRole("button", { name: "ยกเลิก" }));

    expect(await within(panel()).findByText("กำลังแทนไฟล์ ยกเลิกไม่ได้แล้ว")).toBeInTheDocument();
  });

  it("keeps the clip being trimmed in the panel when its delete is refused, though another clip is transcribed", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    backend([
      status(READY_ITEMS),
      current(null),
      clips([MOON, RICK]),
      transcription(transcribeJobOf({ clip_id: MOON.id, state: "transcribing", percent: 10 })),
      trimming(trimJobOf({ percent: 37 })),
      deleteClip(RICK.id, () => jsonResponse({ code: "trimming", message: "กำลังตัดคลิปนี้อยู่ รอให้จบหรือยกเลิกก่อน" }, 409)),
    ]);
    render(<ClipsPage />);
    await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("37%");
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(screen.getByRole("button", { name: `ลบ ${RICK.title}` }));

    expect(await within(screen.getByRole("listitem", { name: RICK.title })).findByText(/กำลังตัดคลิปนี้อยู่/)).toBeInTheDocument();
    expect(within(panel()).getByText("37%")).toBeInTheDocument();
  });

  it("shows a refused POST's message and loads the player back", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      postTrim({ code: "invalid_ranges", message: "ช่วงที่ตัดไม่ถูกต้อง: ต้องเหลือคลิปอย่างน้อย 10 วินาที" }, 400),
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);

    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    expect(await within(panel()).findByText("ช่วงที่ตัดไม่ถูกต้อง: ต้องเหลือคลิปอย่างน้อย 10 วินาที")).toBeInTheDocument();
    expect(video()).toHaveAttribute("src");
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
  });

  it("drops the last trim's message once another clip is selected, as for a transcription (D33)", async () => {
    const refused = "ช่วงที่ตัดไม่ถูกต้อง: ต้องเหลือคลิปอย่างน้อย 10 วินาที";
    backend([status(READY_ITEMS), current(null), clips([RICK, MOON]), postTrim({ code: "invalid_ranges", message: refused }, 400)]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));
    expect(await within(panel()).findByText(refused)).toBeInTheDocument();

    await selectRow(/^From the Moon/);
    await selectRow(/^Rick Astley/);

    expect(within(panel()).queryByText(refused)).not.toBeInTheDocument();
  });

  it("shows a failed job's message and keeps the ranges; replacing offers no ยกเลิก", async () => {
    const inUse = "แทนไฟล์ไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง";
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      trimming(null),
      trimming(trimJobOf({ state: "replacing", percent: null })),
      trimming(trimJobOf({ state: "failed", percent: null, error: { code: "in_use", message: inUse } })),
      postTrim(trimJobOf({})),
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    await nextPoll();
    expect(within(panel()).getByText("กำลังแทนไฟล์…")).toBeInTheDocument();
    expect(within(panel()).getByText("ยกเลิกไม่ได้ระหว่างแทนไฟล์")).toBeInTheDocument();
    expect(within(panel()).queryByRole("button", { name: "ยกเลิก" })).not.toBeInTheDocument();

    await nextPoll();
    expect(await within(panel()).findByText(inUse)).toBeInTheDocument();
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
    expect(video()).toHaveAttribute("src");
  });

  it("cancels: กำลังยกเลิก…, then ยกเลิกแล้ว with the ranges still there and the old file back", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      trimming(null),
      trimming(trimJobOf({ percent: 20, cancel_requested: true })),
      trimming(trimJobOf({ state: "cancelled", percent: null })),
      postTrim(trimJobOf({ percent: 10 })),
      { method: "DELETE", path: TRIM_PATH, reply: () => jsonResponse(trimJobOf({ percent: 10, cancel_requested: true }), 202) },
    ]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    await user.click(await within(panel()).findByRole("button", { name: "ยกเลิก" }));
    expect(fetchMock).toHaveBeenCalledWith(TRIM_PATH, expect.objectContaining({ method: "DELETE" }));
    expect(await within(panel()).findByText("กำลังยกเลิก…")).toBeInTheDocument();

    await nextPoll();
    await nextPoll();
    expect(await within(panel()).findByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(within(range(1)).getByLabelText("จบ")).toHaveValue("0:00:30.0");
    expect(video()).toHaveAttribute("src", `/api/spoil/clips/${RICK.id}/video?v=${encodeURIComponent(RICK.downloaded_at)}`);
  });

  it("says the job was lost when the poll answers null", async () => {
    backend([status(READY_ITEMS), current(null), clips([RICK]), trimming(null), trimming(null), postTrim(trimJobOf({}))]);
    render(<ClipsPage />);
    const user = await openWithRange(0);
    await user.click(within(panel()).getByRole("button", { name: "ตัดคลิป" }));

    await nextPoll();

    expect(await within(panel()).findByText("งานตัดหายเพราะ backend เริ่มใหม่ ลองตัดอีกครั้ง")).toBeInTheDocument();
  });

  it("selects the clip being trimmed when the tab opens, and shows its percent", async () => {
    backend([status(READY_ITEMS), current(null), clips([MOON, RICK]), trimming(trimJobOf({ percent: 37 }))]);
    render(<ClipsPage />);

    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("37%")).toBeInTheDocument();
    expect(within(panel()).getByText(RICK.title)).toBeInTheDocument();
    expect(within(panel()).getByText("กำลังตัดคลิป")).toBeInTheDocument();
    expect(video()).not.toHaveAttribute("src");
  });

  it("disables ตัดช่วง on other clips while one is trimmed, naming it", async () => {
    backend([status(READY_ITEMS), current(null), clips([MOON, RICK]), trimming(trimJobOf({ percent: 37 })), trimming(trimJobOf({ percent: 40 }))]);
    render(<ClipsPage />);
    await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("37%");

    await selectRow(/^From the Moon/);

    expect(within(panel()).getByRole("button", { name: "ตัดช่วง" })).toBeDisabled();
    expect(within(panel()).getByText(`กำลังตัด ${RICK.title}`)).toBeInTheDocument();
  });

  it("disables ตัดช่วง while ffmpeg is missing", async () => {
    const noFfmpeg = READY_ITEMS.map((item) => (item.id === "ffmpeg" ? { ...item, status: "missing" as const } : item));
    backend([status(noFfmpeg), current(null), clips([RICK])]);
    render(<ClipsPage />);

    await selectRow(/^Rick Astley/);

    expect(within(panel()).getByRole("button", { name: "ตัดช่วง" })).toBeDisabled();
  });

  it("shows ตัดแล้ว before ถอดแล้ว on a trimmed row", async () => {
    backend([status(READY_ITEMS), current(null), clips([{ ...TRIMMED_RICK, transcribed: true }])]);
    render(<ClipsPage />);

    const row = await screen.findByRole("listitem", { name: RICK.title });
    const badges = within(row).getAllByText(/^(ตัดแล้ว|ถอดแล้ว)$/).map((badge) => badge.textContent);
    expect(badges).toEqual(["ตัดแล้ว", "ถอดแล้ว"]);
  });

  it("says กำลังตัดคลิปนี้อยู่ when ถอดบทพูด meets 409 trimming", async () => {
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      postTranscription({ code: "trimming", message: "กำลังตัดคลิปนี้อยู่" }, 409),
    ]);
    render(<ClipsPage />);
    const user = await selectRow(/^Rick Astley/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("กำลังตัดคลิปนี้อยู่")).toBeInTheDocument();
  });

  it("shows the API message under the row when the clip being trimmed is deleted", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    const message = "กำลังตัดคลิปนี้อยู่ รอให้จบหรือยกเลิกก่อน";
    backend([
      status(READY_ITEMS),
      current(null),
      clips([RICK]),
      trimming(trimJobOf({ percent: 37 })),
      deleteClip(RICK.id, () => jsonResponse({ code: "trimming", message }, 409)),
    ]);
    render(<ClipsPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${RICK.title}` }));

    expect(await within(screen.getByRole("listitem", { name: RICK.title })).findByText(message)).toBeInTheDocument();
  });
});

describe("file import (D49–D52)", () => {
  const IMPORTED = clipOf({
    id: "local-0123456789ab",
    title: "a",
    channel: null,
    site: LOCAL_SITE,
    source_url: null,
    yt_dlp_version: null,
    duration_s: 30,
    thumbnail: null,
  });
  const CHECK_PATH = "/api/spoil/imports/check";
  const check = (body: unknown, code = 200): Route => ({ method: "POST", path: CHECK_PATH, reply: () => jsonResponse(body, code) });
  const mp4 = (name = "a.mp4") => new File(["abcd"], name, { type: "video/mp4" });

  beforeEach(() => {
    FakeXhr.sent = [];
    vi.stubGlobal("XMLHttpRequest", FakeXhr);
  });

  /** The hidden `<input type="file">` behind เลือกไฟล์ในเครื่อง: it has no role (rules/testing.md). */
  function fileInput(): HTMLInputElement {
    const input = fileDrop().parentElement?.querySelector<HTMLInputElement>('input[type="file"]');
    if (!input) throw new Error("no file input");
    return input;
  }

  function fileDrop(): HTMLElement {
    return screen.getByRole("button", { name: "เลือกไฟล์ในเครื่อง" });
  }

  /** Picks `file` the way the dialog of เลือกไฟล์ในเครื่อง does; `accept` is only a hint there. */
  async function pick(file: File) {
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime, applyAccept: false });
    await user.upload(fileInput(), file);
    return user;
  }

  function drop(files: File[]) {
    fireEvent.drop(fileDrop(), { dataTransfer: { files, types: ["Files"] } });
  }

  it("shows where to pick or drop an mp4 and what it takes", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);

    expect(await screen.findByText("เลือกไฟล์ในเครื่อง")).toBeInTheDocument();
    expect(screen.getByText("หรือลากไฟล์ mp4 มาวาง · รับ mp4 (H.264, AAC) ไม่เกิน 1080p")).toBeInTheDocument();
    expect(fileDrop()).toBeEnabled();
    expect(fileInput()).toHaveAttribute("accept", "video/mp4,.mp4");
  });

  it("opens the file dialog from the keyboard", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);
    const click = vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(() => {});
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });

    fileDrop().focus();
    await user.keyboard("{Enter}");

    expect(click).toHaveBeenCalledTimes(1);
  });

  it("checks the file, sends it with its %, says กำลังตรวจไฟล์…, then เอาไฟล์เข้าเสร็จ with the new row", async () => {
    backend([status(), current(null), clips([RICK]), clips([IMPORTED, RICK]), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());

    expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([{ name: "a.mp4", size: 4 }]);
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    const xhr = FakeXhr.sent[0];
    expect(xhr.method).toBe("POST");
    expect(xhr.url).toBe("/api/spoil/imports?name=a.mp4&size=4");
    expect(xhr.headers).toEqual({ "Content-Type": "application/octet-stream" });
    expect(xhr.timeout).toBe(0);
    expect(xhr.body).toBeInstanceOf(File);

    xhr.progress(2, 4);
    expect(screen.getByText("กำลังเอาไฟล์เข้า a.mp4")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");
    expect(screen.getByLabelText("ลิงก์คลิป")).toBeDisabled();
    expect(screen.getByRole("button", { name: "โหลด" })).toBeDisabled();
    expect(fileDrop()).toBeDisabled();

    xhr.allSent();
    expect(screen.getByText("กำลังตรวจไฟล์…")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "ยกเลิก" })).not.toBeInTheDocument();

    await xhr.respond(201, IMPORTED);
    expect(screen.getByText("เอาไฟล์เข้าเสร็จ: a")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    const row = await screen.findByRole("listitem", { name: "a" });
    expect(row).toHaveAttribute("aria-current", "true");
    expect(within(row).getByText("ไฟล์ในเครื่อง · 0:30")).toBeInTheDocument();
    expect(fileDrop()).toBeEnabled();
    expect(screen.getByLabelText("ลิงก์คลิป")).toBeEnabled();
  });

  it("encodes the file name in the query", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4("หนัง ตอน 1&2.MP4"));

    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(FakeXhr.sent[0].url).toBe(`/api/spoil/imports?name=${encodeURIComponent("หนัง ตอน 1&2.MP4")}&size=4`);
  });

  it("aborts on ยกเลิก and says ยกเลิกแล้ว", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    const user = await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    FakeXhr.sent[0].progress(1, 4);

    await user.click(screen.getByRole("button", { name: "ยกเลิก" }));

    expect(FakeXhr.sent[0].abort).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(fileDrop()).toBeEnabled();
  });

  it("sends no file when ยกเลิก comes while the check is out", async () => {
    let answer: (response: Response) => void = () => {};
    backend([status(), current(null), { method: "POST", path: CHECK_PATH, reply: () => new Promise<Response>((r) => (answer = r)) }]);
    render(<ClipsPage />);
    const user = await pick(mp4());

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));
    await act(async () => answer(jsonResponse({ clip_id: IMPORTED.id })));

    expect(screen.getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("says ยกเลิกแล้ว, not offline, when the check fails after ยกเลิก", async () => {
    let fail: (error: Error) => void = () => {};
    backend([status(), current(null), { method: "POST", path: CHECK_PATH, reply: () => new Promise<Response>((_, f) => (fail = f)) }]);
    render(<ClipsPage />);
    const user = await pick(mp4());

    await user.click(await screen.findByRole("button", { name: "ยกเลิก" }));
    await act(async () => fail(new TypeError("Failed to fetch")));

    expect(screen.getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Refresh" })).not.toBeInTheDocument();
  });

  it("stops the upload when the tab goes offline for another reason, and Refresh starts idle", async () => {
    const transcribing: TranscribeJob = { clip_id: RICK.id, state: "transcribing", percent: 35, cancel_requested: false, error: null };
    backend([
      status(),
      current(null),
      clips([RICK]),
      transcription(transcribing),
      { path: TRANSCRIPTION_PATH, reply: () => Promise.reject(new TypeError("Failed to fetch")) },
      transcription(null),
      check({ clip_id: IMPORTED.id }),
    ]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await nextPoll();
    expect(await screen.findByRole("button", { name: "Refresh" })).toBeInTheDocument();
    expect(FakeXhr.sent[0].abort).toHaveBeenCalledTimes(1);

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" })).toBeEnabled();
    expect(screen.queryByText("ยกเลิกแล้ว")).not.toBeInTheDocument();
  });

  it("keeps the browser from opening a file dropped beside the box", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });

    const event = new Event("drop", { cancelable: true });
    Object.defineProperty(event, "dataTransfer", { value: { types: ["Files"], files: [] } });
    window.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
  });

  it("aborts the upload when the page goes away (the user leaves the คลิป tab)", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    const { unmount } = render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    unmount();

    expect(FakeXhr.sent[0].abort).toHaveBeenCalledTimes(1);
  });

  it("refuses a file that isn't .mp4 without sending anything", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);
    await pick(mp4("a.mkv"));

    expect(await screen.findByText("รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน")).toBeInTheDocument();
    expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([]);
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("sends a dropped file the same way as a picked one", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });

    drop([mp4()]);

    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([{ name: "a.mp4", size: 4 }]);
    expect(FakeXhr.sent[0].url).toBe("/api/spoil/imports?name=a.mp4&size=4");
  });

  it("takes a file dropped on the link field too", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);

    fireEvent.drop(await screen.findByLabelText("ลิงก์คลิป"), { dataTransfer: { files: [mp4()], types: ["Files"] } });

    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
  });

  it("shows the drop look while a file is dragged over", async () => {
    backend([status(), current(null)]);
    render(<ClipsPage />);
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });

    fireEvent.dragEnter(fileDrop(), { dataTransfer: { files: [], types: ["Files"] } });
    expect(screen.getByText("วางไฟล์ mp4 ที่นี่")).toBeInTheDocument();

    fireEvent.dragLeave(fileDrop(), { dataTransfer: { files: [], types: ["Files"] } });
    expect(screen.queryByText("วางไฟล์ mp4 ที่นี่")).not.toBeInTheDocument();
  });

  it("takes the first of several dropped files and says one at a time", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" });

    drop([mp4("a.mp4"), mp4("b.mp4")]);

    expect(await screen.findByText("เอาเข้าได้ทีละไฟล์")).toBeInTheDocument();
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(sent(fetchMock, "POST", CHECK_PATH)).toEqual([{ name: "a.mp4", size: 4 }]);
  });

  it("highlights the row on a duplicate from the check, sending no file", async () => {
    backend([
      status(),
      current(null),
      clips([IMPORTED, RICK]),
      check({ code: "duplicate", message: "ไฟล์นี้เอาเข้าไว้แล้ว", clip_id: IMPORTED.id }, 409),
    ]);
    render(<ClipsPage />);
    await pick(mp4());

    expect(await screen.findByText("ไฟล์นี้เอาเข้าไว้แล้ว")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: "a" })).toHaveAttribute("aria-current", "true");
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("shows the API message of another refusal from the check", async () => {
    const message = "ที่ว่างไม่พอ: ต้องการ 2.0 GB มี 1.0 GB";
    backend([status(), current(null), check({ code: "disk_full", message }, 409)]);
    render(<ClipsPage />);
    await pick(mp4());

    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("shows unsupported_file's message", async () => {
    const message = "ภาพเป็น hevc. แปลงเป็น mp4 (H.264, AAC) ไม่เกิน 1080p ด้วยโปรแกรมอื่นแล้วลองอีกครั้ง";
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await FakeXhr.sent[0].respond(400, { code: "unsupported_file", message });

    expect(screen.getByText(message)).toBeInTheDocument();
    expect(fileDrop()).toBeEnabled();
  });

  it("highlights the row on a duplicate from the upload", async () => {
    backend([status(), current(null), clips([IMPORTED, RICK]), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    // The page says it in its own words, as for a link (spec › Frontend), whatever the API's are.
    await FakeXhr.sent[0].respond(409, { code: "duplicate", message: "x", clip_id: IMPORTED.id });

    expect(screen.getByText("ไฟล์นี้เอาเข้าไว้แล้ว")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: "a" })).toHaveAttribute("aria-current", "true");
  });

  it("says stalled's message on 408", async () => {
    const message = "ไม่ได้รับข้อมูลไฟล์นาน 60 วินาที ลองอีกครั้ง";
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await FakeXhr.sent[0].respond(408, { code: "stalled", message });

    expect(screen.getByText(message)).toBeInTheDocument();
  });

  it("says try again, not offline, when the upload errors (the server answered early, D55)", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await FakeXhr.sent[0].fail();

    expect(screen.getByText("เอาไฟล์เข้าไม่สำเร็จ ลองอีกครั้ง")).toBeInTheDocument();
    expect(fileDrop()).toBeEnabled();
  });

  it("goes offline when the check gets no answer", async () => {
    backend([status(), current(null), { method: "POST", path: CHECK_PATH, reply: () => Promise.reject(new TypeError("Failed to fetch")) }]);
    render(<ClipsPage />);
    await pick(mp4());

    expect(await screen.findByRole("button", { name: "Refresh" })).toBeInTheDocument();
  });

  it("goes offline on an upload answer the API never sends", async () => {
    backend([status(), current(null), check({ clip_id: IMPORTED.id })]);
    render(<ClipsPage />);
    await pick(mp4());
    await vi.waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await FakeXhr.sent[0].respond(500, null);

    expect(await screen.findByRole("button", { name: "Refresh" })).toBeInTheDocument();
  });

  it("switches to not ready on 503 not_ready from the check", async () => {
    const noFfmpeg = ITEMS.map((i) => (i.id === "ffmpeg" ? { ...i, status: "missing" as const } : i));
    backend([status(), status(noFfmpeg), current(null), check({ code: "not_ready", message: "x" }, 503)]);
    render(<ClipsPage />);
    await pick(mp4());

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: ffmpeg")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "เลือกไฟล์ในเครื่อง" })).not.toBeInTheDocument();
  });

  it("disables เลือกไฟล์ในเครื่อง while a download runs", async () => {
    backend([status(), current(DOWNLOADING_40)]);
    render(<ClipsPage />);

    expect(await screen.findByRole("button", { name: "เลือกไฟล์ในเครื่อง" })).toBeDisabled();
  });

  it("clears the import's message on the next โหลด", async () => {
    backend([status(), current(null), post(jobOf({}))]);
    render(<ClipsPage />);
    await pick(mp4("a.mkv"));
    expect(await screen.findByText("รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน")).toBeInTheDocument();

    await startDownload();

    expect(screen.queryByText("รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน")).not.toBeInTheDocument();
  });

  it.each([
    ["unsupported", 'เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"'],
    ["login_required", 'เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด "เลือกไฟล์ในเครื่อง"'],
    ["unsupported_format", 'เว็บนี้ไม่มีไฟล์ H.264 ไม่เกิน 1080p ให้โหลด โหลดเองแล้วแปลง จากนั้นกด "เลือกไฟล์ในเครื่อง"'],
  ])("points at เลือกไฟล์ในเครื่อง after a link fails %s (D52)", async (code, message) => {
    const failed = jobOf({ state: "failed", error: { code, message, yt_dlp_version: "2026.10.26", fix: null, clip_id: null } });
    backend([status(), current(failed)]);
    render(<ClipsPage />);

    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(fileDrop()).toHaveAttribute("data-emphasis", "true");
  });

  it("doesn't point at the file button after another failure", async () => {
    const failed = jobOf({ state: "failed", error: { code: "live", message: "live", yt_dlp_version: "2026.10.26", fix: null, clip_id: null } });
    backend([status(), current(failed)]);
    render(<ClipsPage />);

    await screen.findByText("live");
    expect(fileDrop()).not.toHaveAttribute("data-emphasis");
  });
});
