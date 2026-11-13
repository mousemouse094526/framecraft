import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  // Neither page needs an answer to show which tab is open.
  fetchMock.mockReturnValue(new Promise(() => {}));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function tab(name: string) {
  return within(screen.getByRole("navigation", { name: "แถบ tab" })).getByRole("link", { name });
}

describe("tab bar", () => {
  it("opens ติดตั้ง, highlighted, when the hash is empty", () => {
    render(<App />);

    expect(screen.getByText("กำลังเช็ค…")).toBeInTheDocument();
    expect(tab("ติดตั้ง")).toHaveAttribute("aria-current", "page");
    expect(tab("คลิป")).not.toHaveAttribute("aria-current");
    expect(tab("สปอย")).not.toHaveAttribute("aria-current");
  });

  it("opens ติดตั้ง when the hash is unknown", () => {
    window.location.hash = "#/nope";
    render(<App />);

    expect(tab("ติดตั้ง")).toHaveAttribute("aria-current", "page");
  });

  it("lists ติดตั้ง, คลิป, คลังความรู้, สปอย, การ์ตูนเล่า, สอนกลอง, แกะเพลง in that order (spoil-maker D53, story-kb D9, toon, video-gen D9, drum-notes D2)", () => {
    render(<App />);

    expect(within(screen.getByRole("navigation", { name: "แถบ tab" })).getAllByRole("link").map((link) => link.textContent)).toEqual([
      "ติดตั้ง",
      "คลิป",
      "คลังความรู้",
      "สปอย",
      "การ์ตูนเล่า",
      "สอนกลอง",
      "แกะเพลง",
    ]);
  });

  it("switches to คลิป and writes #/clips to the hash", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(tab("คลิป"));

    expect(window.location.hash).toBe("#/clips");
    expect(await screen.findByText("กำลังโหลด…")).toBeInTheDocument();
    expect(tab("คลิป")).toHaveAttribute("aria-current", "page");
  });

  it("opens คลิป from the hash, so a refresh stays on that tab", () => {
    window.location.hash = "#/clips";
    render(<App />);

    expect(tab("คลิป")).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
  });

  it.each(["#/spoil", "#/spoil/review", "#/spoil/renders"])("opens สปอย from %s", (hash) => {
    window.location.hash = hash;
    render(<App />);

    expect(tab("สปอย")).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("navigation", { name: "ขั้นของสปอย" })).toBeInTheDocument();
  });

  it.each(["#/stories", "#/stories/new", "#/stories/st_3fa91c07"])("opens คลังความรู้ from %s (story-kb D9)", (hash) => {
    window.location.hash = hash;
    render(<App />);

    expect(tab("คลังความรู้")).toHaveAttribute("aria-current", "page");
  });

  it("goes back to the previous tab with the browser back button", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(tab("คลิป"));
    await user.click(tab("ติดตั้ง"));

    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(tab("คลิป")).toHaveAttribute("aria-current", "page"));
    expect(window.location.hash).toBe("#/clips");
  });
});
