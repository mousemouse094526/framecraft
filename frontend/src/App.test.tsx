import { render, screen, waitFor } from "@testing-library/react";
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
  return screen.getByRole("link", { name });
}

describe("tab bar", () => {
  it("opens Setup status, highlighted, when the hash is empty", () => {
    render(<App />);

    expect(screen.getByText("กำลังเช็ค…")).toBeInTheDocument();
    expect(tab("Setup status")).toHaveAttribute("aria-current", "page");
    expect(tab("สปอย")).not.toHaveAttribute("aria-current");
  });

  it("opens Setup status when the hash is unknown", () => {
    window.location.hash = "#/nope";
    render(<App />);

    expect(tab("Setup status")).toHaveAttribute("aria-current", "page");
  });

  // สปอย comes first in the bar even though Setup status is the default tab (D10).
  it("lists สปอย before Setup status", () => {
    render(<App />);

    expect(screen.getAllByRole("link").map((link) => link.textContent)).toEqual(["สปอย", "Setup status"]);
  });

  it("switches to สปอย and writes #/spoil to the hash", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(tab("สปอย"));

    expect(window.location.hash).toBe("#/spoil");
    expect(await screen.findByText("กำลังโหลด…")).toBeInTheDocument();
    expect(tab("สปอย")).toHaveAttribute("aria-current", "page");
  });

  it("opens สปอย from the hash, so a refresh stays on that tab", () => {
    window.location.hash = "#/spoil";
    render(<App />);

    expect(tab("สปอย")).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("กำลังโหลด…")).toBeInTheDocument();
  });

  it("goes back to the previous tab with the browser back button", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(tab("สปอย"));
    await user.click(tab("Setup status"));

    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(tab("สปอย")).toHaveAttribute("aria-current", "page"));
    expect(window.location.hash).toBe("#/spoil");
  });
});
