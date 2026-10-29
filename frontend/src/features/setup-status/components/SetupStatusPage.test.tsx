import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChecklistItem, StatusResponse } from "../../../lib/statusTypes";
import { SetupStatusPage } from "./SetupStatusPage";

const OMNIVOICE_LICENSE = {
  name: "CC BY-NC 4.0",
  url: "https://creativecommons.org/licenses/by-nc/4.0/",
  author: "k2-fsa",
  model_url: "https://huggingface.co/k2-fsa/OmniVoice",
};

const WHISPER_LICENSE = {
  name: "MIT",
  url: "https://opensource.org/license/mit",
  author: "OpenAI",
  model_url: "https://huggingface.co/openai/whisper-large-v3-turbo",
};

function okItem(id: string, label: string, detail: string): ChecklistItem {
  return { id, label, status: "ok", detail, fix: null, fix_kind: null, license: null };
}

const READY_ITEMS: ChecklistItem[] = [
  okItem("python", "Python venv", "3.12.11 (.venv)"),
  okItem("torch", "torch", "2.8.0"),
  okItem("transformers", "transformers", "5.3.0"),
  okItem("omnivoice", "omnivoice", "0.2.1"),
  okItem("fastapi", "fastapi", "0.162.0"),
  okItem("ffmpeg", "ffmpeg", "7.1 (imageio-ffmpeg)"),
  okItem("yt_dlp", "yt-dlp", "2026.10.26"),
  okItem("deno", "Deno", "2.9.8"),
  { ...okItem("model_omnivoice", "OmniVoice model", "k2-fsa/OmniVoice"), license: OMNIVOICE_LICENSE },
  { ...okItem("model_whisper", "Whisper model", "openai/whisper-large-v3-turbo"), license: WHISPER_LICENSE },
  okItem("device", "Device", "mps"),
];

function statusOf(items: ChecklistItem[], checkedAt = "2026-10-29T17:42:10+07:00"): StatusResponse {
  const count = (status: ChecklistItem["status"]) => items.filter((i) => i.status === status).length;
  return {
    checked_at: checkedAt,
    ready: count("missing") === 0,
    ok_count: count("ok"),
    warning_count: count("warning"),
    missing_count: count("missing"),
    total: items.length,
    items,
  };
}

function replaceItem(id: string, change: Partial<ChecklistItem>): ChecklistItem[] {
  return READY_ITEMS.map((i) => (i.id === id ? { ...i, ...change } : i));
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

// Offline lines mix Thai text and <code>, so match a paragraph's whole text.
function paragraph(text: string) {
  return screen.getByText((_, element) => element?.tagName === "P" && element.textContent === text);
}

async function expectOffline() {
  expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  expect(paragraph("ยังไม่ได้ start: รัน npm run dev")).toBeInTheDocument();
  expect(
    paragraph("รันอยู่แล้ว: ดู error ในบรรทัด [api] ของ terminal ที่รัน npm run dev หรือรัน setup ใหม่"),
  ).toBeInTheDocument();
}

describe("SetupStatusPage", () => {
  it("shows every row, the ready verdict and the count when all items are ok", async () => {
    fetchMock.mockResolvedValue(jsonResponse(statusOf(READY_ITEMS)));

    render(<SetupStatusPage />);

    expect(await screen.findByText("พร้อมใช้งาน")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(11);
    expect(screen.getByText("11/11")).toBeInTheDocument();
    expect(screen.getByText("17:42:10")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/setup/status", expect.anything());
  });

  it("says ready with one warning when one row is a warning", async () => {
    const items = replaceItem("device", {
      status: "warning",
      detail: "cpu — ไม่พบ mps/cuda (ช้า)",
      fix: "ต้องเป็น Mac Apple Silicon",
      fix_kind: "hint",
    });
    fetchMock.mockResolvedValue(jsonResponse(statusOf(items)));

    render(<SetupStatusPage />);

    const verdict = await screen.findByText("พร้อมใช้งาน (มีคำเตือน 1 รายการ)");
    expect(within(verdict.parentElement!).getByText("Device")).toBeInTheDocument();
    expect(screen.getByText("10/11")).toBeInTheDocument();
  });

  it("says not ready and shows the fix as a copyable command when one row is missing", async () => {
    const user = userEvent.setup();
    const items = replaceItem("model_omnivoice", {
      status: "missing",
      detail: "ไม่พบ marker ใน models/.setup",
      fix: "./setup.sh",
      fix_kind: "command",
    });
    fetchMock.mockResolvedValue(jsonResponse(statusOf(items)));

    render(<SetupStatusPage />);

    expect(await screen.findByText("ยังไม่พร้อม: ขาด 1 รายการ")).toBeInTheDocument();
    const row = screen.getByRole("listitem", { name: "OmniVoice model" });
    expect(within(row).getByText("ไม่พบ marker ใน models/.setup")).toBeInTheDocument();
    expect(within(row).getByText("./setup.sh")).toBeInTheDocument();
    await user.click(within(row).getByRole("button", { name: "คัดลอก ./setup.sh" }));
    expect(await navigator.clipboard.readText()).toBe("./setup.sh");
  });

  it("shows a hint fix as plain text without a copy button", async () => {
    const items = replaceItem("device", {
      status: "warning",
      detail: "cpu",
      fix: "ต้องเป็น Mac Apple Silicon",
      fix_kind: "hint",
    });
    fetchMock.mockResolvedValue(jsonResponse(statusOf(items)));

    render(<SetupStatusPage />);

    const row = await screen.findByRole("listitem", { name: "Device" });
    expect(within(row).getByText("ต้องเป็น Mac Apple Silicon")).toBeInTheDocument();
    expect(within(row).queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows a command fix as a copy chip even when it has spaces", async () => {
    const items = replaceItem("torch", {
      status: "missing",
      detail: "ยังไม่ได้ติดตั้ง",
      fix: "uv sync",
      fix_kind: "command",
    });
    fetchMock.mockResolvedValue(jsonResponse(statusOf(items)));

    render(<SetupStatusPage />);

    const row = await screen.findByRole("listitem", { name: "torch" });
    expect(within(row).getByRole("button", { name: "คัดลอก uv sync" })).toBeInTheDocument();
  });

  it("shows license, author, license link and model link on model rows", async () => {
    fetchMock.mockResolvedValue(jsonResponse(statusOf(READY_ITEMS)));

    render(<SetupStatusPage />);

    const row = await screen.findByRole("listitem", { name: "OmniVoice model" });
    expect(within(row).getByText("CC BY-NC 4.0 · k2-fsa", { exact: false })).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "license" })).toHaveAttribute("href", OMNIVOICE_LICENSE.url);
    expect(within(row).getByRole("link", { name: "model" })).toHaveAttribute("href", OMNIVOICE_LICENSE.model_url);
  });

  it("shows the checking message before the first response arrives", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));

    render(<SetupStatusPage />);

    expect(screen.getByText("กำลังเช็ค…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeDisabled();
  });

  it("disables Refresh while checking again, then shows the new checked_at", async () => {
    const user = userEvent.setup();
    const second = deferred<Response>();
    fetchMock
      .mockResolvedValueOnce(jsonResponse(statusOf(READY_ITEMS)))
      .mockReturnValueOnce(second.promise);
    render(<SetupStatusPage />);
    const refresh = await screen.findByRole("button", { name: "Refresh" });
    await screen.findByText("17:42:10");

    await user.click(refresh);

    expect(refresh).toBeDisabled();
    expect(screen.getAllByRole("listitem")).toHaveLength(11);
    await act(async () => second.resolve(jsonResponse(statusOf(READY_ITEMS, "2026-10-29T17:45:03+07:00"))));
    expect(await screen.findByText("17:45:03")).toBeInTheDocument();
    expect(refresh).toBeEnabled();
  });

  it("shows the three offline lines when fetch fails", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    render(<SetupStatusPage />);

    await expectOffline();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeEnabled();
  });

  it("shows offline when the backend answers with something other than 200", async () => {
    fetchMock.mockResolvedValue(jsonResponse(statusOf(READY_ITEMS), 503));

    render(<SetupStatusPage />);

    await expectOffline();
  });

  it("shows offline when the backend does not answer within 30 seconds", async () => {
    vi.useFakeTimers();
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<SetupStatusPage />);
    expect(screen.getByText("กำลังเช็ค…")).toBeInTheDocument();

    await act(() => vi.advanceTimersByTimeAsync(29_999));
    expect(screen.queryByText("Backend offline")).not.toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(1));

    expect(screen.getByText("Backend offline")).toBeInTheDocument();
  });

  it("replaces the checklist with the offline message when Refresh fails after a result", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(jsonResponse(statusOf(READY_ITEMS)))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<SetupStatusPage />);
    await screen.findByText("พร้อมใช้งาน");

    await user.click(screen.getByRole("button", { name: "Refresh" }));

    await expectOffline();
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
    expect(screen.queryByText("พร้อมใช้งาน")).not.toBeInTheDocument();
  });

  it("gets the checklist after the backend comes back and Refresh is pressed", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(jsonResponse(statusOf(READY_ITEMS)));
    render(<SetupStatusPage />);
    await screen.findByText("Backend offline");

    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(await screen.findByText("พร้อมใช้งาน")).toBeInTheDocument();
    expect(screen.queryByText("Backend offline")).not.toBeInTheDocument();
  });
});
