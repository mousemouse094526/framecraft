import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChecklistItem, StatusResponse } from "../../../lib/statusTypes";
import type { DownloadJob } from "../hooks/useSpoilDownload";
import type { TempClip } from "../hooks/useTempClips";
import type { TranscribeJob, Transcript } from "../hooks/useTranscribe";
import { SpoilPage } from "./SpoilPage";

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
    transcribed: false,
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
 * the list is empty; with no `/api/spoil/transcriptions/current` route there
 * is no Transcribe job; a clip's `/transcript` with no route is `404`, as for
 * a clip not yet transcribed.
 */
function backend(routes: Route[]) {
  const has = (path: string) => routes.some((r) => r.path === path && (r.method ?? "GET") === "GET");
  if (!has(CLIPS_PATH)) routes.push(clips([]));
  if (!has(TRANSCRIPTION_PATH)) routes.push(transcription(null));
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
  await user.type(await screen.findByLabelText("ลิงก์ YouTube"), SHORTS_URL);
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

describe("tab สปอย", () => {
  it("shows กำลังโหลด… until the status and the current job answer", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<SpoilPage />);

    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
  });

  it("keeps กำลังโหลด… until the clip list answers too", async () => {
    backend([status(), current(null), { path: CLIPS_PATH, reply: () => new Promise(() => {}) }]);
    render(<SpoilPage />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
    expect(screen.queryByLabelText("ลิงก์ YouTube")).not.toBeInTheDocument();
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
    expect(await screen.findByRole("listitem", { name: MOON.title })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("listitem", { name: RICK.title })).not.toHaveAttribute("aria-current");
    expect(clipListCalls()).toBe(2);

    await nextPoll();
    expect(clipListCalls()).toBe(2);
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
    expect(clipListCalls()).toBe(2);
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
  ])("shows the Frontend table's text on %i %s", async (code, errorCode, text) => {
    backend([status(), current(null), post({ code: errorCode, message: "from the API" }, code)]);
    render(<SpoilPage />);
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
    render(<SpoilPage />);
    await startDownload();

    expect(await screen.findByText("คลิปนี้โหลดไว้แล้ว")).toBeInTheDocument();
    const row = screen.getByRole("listitem", { name: RICK.title });
    expect(row).toHaveAttribute("aria-current", "true");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledTimes(1);
    expect(vi.mocked(Element.prototype.scrollIntoView).mock.contexts[0]).toBe(row);
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

describe("Temp clip list", () => {
  it("says there is no clip yet when the list is empty", async () => {
    backend([status(), current(null)]);
    render(<SpoilPage />);

    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "คลิปที่โหลดมา 0" })).toBeInTheDocument();
  });

  it("shows each clip newest first with what it is", async () => {
    backend([status(), current(null), clips([NIGHT, MOON, RICK])]);
    render(<SpoilPage />);

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

  it("still shows the list when the tab is not ready", async () => {
    backend([status(ITEMS.map((i) => (i.id === "deno" ? { ...i, status: "missing" } : i))), current(null), clips([RICK])]);
    render(<SpoilPage />);

    expect(await screen.findByText("ยังติดตั้งไม่ครบ: Deno")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: RICK.title })).toBeInTheDocument();
  });

  it("goes offline when the list can't be loaded", async () => {
    backend([status(), current(null), { path: CLIPS_PATH, reply: () => Promise.reject(new TypeError("Failed to fetch")) }]);
    render(<SpoilPage />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });

  it("plays a clicked row in the transcript panel and marks it กำลังเล่น", async () => {
    backend([status(), current(null), clips([MOON, RICK])]);
    const { container } = render(<SpoilPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: /^From the Moon/ }));

    const video = panel().querySelector("video");
    expect(video).toHaveAttribute("src", "/api/spoil/clips/f7jkZXvaB4g/video");
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
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
    const { container } = render(<SpoilPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.click(await screen.findByRole("button", { name: /^From the Moon/ }));

    await user.click(screen.getByRole("button", { name: `ลบ ${MOON.title}` }));

    expect(order).toEqual(["load src=", "DELETE"]);
    expect(container.querySelector("video")).toBeNull();
    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน")).toBeInTheDocument();
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
    render(<SpoilPage />);
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
    { start_s: 12.4, end_s: 15.0, text: "They're coming to get you, Barbara." },
    { start_s: 3725.2, end_s: 3727.9, text: "Is anybody here?" },
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
    render(<SpoilPage />);

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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(await within(panel()).findByRole("button", { name: /They're coming to get you, Barbara\./ }));

    const video = panel().querySelector("video")!;
    expect(video.currentTime).toBe(12.4);
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
  });

  it("copies the transcript as the .txt text and links the files", async () => {
    backend([status(READY_ITEMS), current(null), clips([TRANSCRIBED_NIGHT]), transcript(NIGHT_TRANSCRIPT)]);
    render(<SpoilPage />);
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);

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
    render(<SpoilPage />);
    expect(await within(await screen.findByRole("region", { name: "กล่องถอดบทพูด" })).findByText("35%")).toBeInTheDocument();
    expect(within(panel()).queryByRole("button", { name: /Barbara/ })).not.toBeInTheDocument();

    await nextPoll();

    expect(within(panel()).getByText("ยกเลิกแล้ว")).toBeInTheDocument();
    expect(await within(panel()).findByRole("button", { name: /They're coming to get you, Barbara\./ })).toBeInTheDocument();
  });

  it("links to Setup status instead of ถอดบทพูด while the Whisper model is missing; the link field still works", async () => {
    backend([status(), current(null), clips([NIGHT])]);
    render(<SpoilPage />);
    await selectRow(/^Night of the Living Dead/);

    expect(within(panel()).getByText("ยังติดตั้งไม่ครบ: Whisper model")).toBeInTheDocument();
    expect(within(panel()).getByRole("link", { name: "ไปหน้า Setup status" })).toHaveAttribute("href", "#/setup");
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
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
    render(<SpoilPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await screen.findByText("ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน")).toBeInTheDocument();
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
    render(<SpoilPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await within(panel()).findByText("ยังติดตั้งไม่ครบ: Whisper model")).toBeInTheDocument();
  });

  it("goes offline on a POST answer the API never sends", async () => {
    backend([status(READY_ITEMS), current(null), clips([NIGHT]), postTranscription({ code: "x", message: "x" }, 500)]);
    render(<SpoilPage />);
    const user = await selectRow(/^Night of the Living Dead/);

    await user.click(within(panel()).getByRole("button", { name: "ถอดบทพูด" }));

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });

  it("empties the panel when the selected clip is deleted", async () => {
    vi.stubGlobal("confirm", vi.fn(() => true));
    backend([status(READY_ITEMS), current(null), clips([NIGHT]), deleteClip(NIGHT.id, () => new Response(null, { status: 204 }))]);
    render(<SpoilPage />);
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
    render(<SpoilPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    await user.click(await screen.findByRole("button", { name: `ลบ ${NIGHT.title}` }));

    expect(await within(screen.getByRole("listitem", { name: NIGHT.title })).findByText(refused)).toBeInTheDocument();
    expect(within(panel()).getByText("5%")).toBeInTheDocument();
  });
});
