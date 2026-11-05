import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { get, serve } from "../../../testing/testBackend";
import type { StoryRow } from "../../../lib/stories";

const fetchMock = vi.fn<typeof fetch>();

function rowOf(change: Partial<StoryRow>): StoryRow {
  return {
    id: "st_3fa91c07",
    title: "ยอดนักสืบจิ๋วโคนัน",
    characters: 3,
    clips: 2,
    tokens: 812,
    updated_at: "2026-11-05T14:20:00+07:00",
    ...change,
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  window.location.hash = "#/stories";
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function list() {
  return screen.getByRole("region", { name: "เรื่องทั้งหมด" });
}

describe("คลังความรู้ list", () => {
  it("says the library is empty and offers เพิ่มเรื่อง", async () => {
    serve(fetchMock, [get("/api/stories", [])]);
    render(<App />);

    expect(await screen.findByText("ยังไม่มีเรื่องในคลังความรู้")).toBeInTheDocument();
    const adds = screen.getAllByRole("link", { name: "เพิ่มเรื่อง" });
    expect(adds).toHaveLength(2);
    for (const add of adds) expect(add).toHaveAttribute("href", "#/stories/new");
  });

  it("lists each Story as a link with its characters, clips and last edit", async () => {
    serve(fetchMock, [
      get("/api/stories", [
        rowOf({}),
        rowOf({ id: "st_00000001", title: "วันพีซ", characters: 4, clips: 0, updated_at: "2026-11-02T09:12:00+07:00" }),
      ]),
    ]);
    render(<App />);

    const conan = await screen.findByRole("link", { name: /ยอดนักสืบจิ๋วโคนัน/ });
    expect(conan).toHaveAttribute("href", "#/stories/st_3fa91c07");
    expect(within(conan).getByText("3 ตัวละคร")).toBeInTheDocument();
    expect(within(conan).getByText("แก้ล่าสุด 5 พ.ย. 14:20")).toBeInTheDocument();
    expect(within(conan).getByText("ใช้อยู่ 2 คลิป")).toBeInTheDocument();

    const onePiece = screen.getByRole("link", { name: /วันพีซ/ });
    expect(within(onePiece).getByText("แก้ล่าสุด 2 พ.ย. 09:12")).toBeInTheDocument();
    expect(within(onePiece).queryByText(/ใช้อยู่/)).not.toBeInTheDocument();
    expect(within(list()).getByText("2")).toBeInTheDocument();
  });

  it("is busy while the list loads", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    render(<App />);

    expect(list()).toHaveAttribute("aria-busy", "true");
  });

  it("shows OfflinePanel when the backend doesn't answer", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    render(<App />);

    expect(await screen.findByText("Backend offline")).toBeInTheDocument();
  });
});
