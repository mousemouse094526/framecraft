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

  it("lists ติดตั้ง, คลิป, คลังความรู้, คลังเสียง, สปอย, การ์ตูนเล่า, สอนกลอง in that order (sound-library D2, video-gen D9) (e2e)", () => {
    render(<App />);

    expect(within(screen.getByRole("navigation", { name: "แถบ tab" })).getAllByRole("link").map((link) => link.textContent)).toEqual([
      "ติดตั้ง",
      "คลิป",
      "คลังความรู้",
      "คลังเสียง",
      "สปอย",
      "การ์ตูนเล่า",
      "สอนกลอง",
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

describe("tab groups (sound-library D3)", () => {
  function bar() {
    return within(screen.getByRole("navigation", { name: "แถบ tab" }));
  }

  it("groups คลิป, คลังความรู้, คลังเสียง and สปอย, การ์ตูนเล่า, สอนกลอง by aria-label, with no heading text", () => {
    render(<App />);

    const prep = bar().getByRole("group", { name: "เตรียมของ" });
    const make = bar().getByRole("group", { name: "ทำคลิป" });
    expect(within(prep).getAllByRole("link").map((link) => link.textContent)).toEqual(["คลิป", "คลังความรู้", "คลังเสียง"]);
    expect(within(make).getAllByRole("link").map((link) => link.textContent)).toEqual(["สปอย", "การ์ตูนเล่า", "สอนกลอง"]);
    expect(prep).toHaveTextContent(/^คลิปคลังความรู้คลังเสียง$/);
    expect(make).toHaveTextContent(/^สปอยการ์ตูนเล่าสอนกลอง$/);
    expect(bar().getAllByRole("group")).toHaveLength(2);
  });

  it("shows the bar from 640px and the menu button below it (jsdom draws no layout: the classes)", () => {
    render(<App />);

    expect(screen.getByRole("navigation", { name: "แถบ tab" })).toHaveClass("hidden", "sm:flex");
    expect(screen.getByRole("button", { name: /^เมนู tab:/ }).parentElement).toHaveClass("sm:hidden");
  });
});

describe("tab menu on a narrow screen (sound-library D3)", () => {
  function menuButton() {
    return screen.getByRole("button", { name: /^เมนู tab:/ });
  }

  it("names the open page with a menu icon, closed at first", () => {
    window.location.hash = "#/sounds";
    render(<App />);

    expect(menuButton()).toHaveAccessibleName("เมนู tab: คลังเสียง");
    expect(menuButton()).toHaveTextContent(/^คลังเสียง$/);
    expect(menuButton().querySelector("img")).not.toBeNull();
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).not.toHaveAttribute("aria-controls");
    expect(screen.queryByRole("navigation", { name: "เมนู tab" })).toBeNull();
  });

  it("opens ติดตั้ง first, then the headings เตรียมของ and ทำคลิป with their tabs (e2e)", async () => {
    const user = userEvent.setup();
    window.location.hash = "#/clips";
    render(<App />);

    await user.click(menuButton());

    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
    const menu = screen.getByRole("navigation", { name: "เมนู tab" });
    expect(menuButton()).toHaveAttribute("aria-controls", menu.id);
    expect(menu).toHaveTextContent(/^ติดตั้งเตรียมของคลิปคลังความรู้คลังเสียงทำคลิปสปอยการ์ตูนเล่าสอนกลอง$/);
    expect(within(within(menu).getByRole("group", { name: "เตรียมของ" })).getAllByRole("link").map((l) => l.textContent)).toEqual([
      "คลิป",
      "คลังความรู้",
      "คลังเสียง",
    ]);
    expect(within(within(menu).getByRole("group", { name: "ทำคลิป" })).getAllByRole("link").map((l) => l.textContent)).toEqual([
      "สปอย",
      "การ์ตูนเล่า",
      "สอนกลอง",
    ]);
    expect(within(menu).getByRole("link", { name: "คลิป" })).toHaveAttribute("aria-current", "page");
    expect(within(menu).getByRole("link", { name: "ติดตั้ง" })).not.toHaveAttribute("aria-current");
  });

  it("opens the tab picked in the menu and closes the menu (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(menuButton());
    await user.click(within(screen.getByRole("navigation", { name: "เมนู tab" })).getByRole("link", { name: "สปอย" }));

    expect(window.location.hash).toBe("#/spoil");
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู tab: สปอย"));
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("navigation", { name: "เมนู tab" })).toBeNull();
  });

  it("closes when the open tab is picked again, though the hash stays the same", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(menuButton());
    await user.click(within(screen.getByRole("navigation", { name: "เมนู tab" })).getByRole("link", { name: "ติดตั้ง" }));

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on Esc with the focus back on the button (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(menuButton());
    within(screen.getByRole("navigation", { name: "เมนู tab" })).getByRole("link", { name: "คลิป" }).focus();

    await user.keyboard("{Escape}");

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("navigation", { name: "เมนู tab" })).toBeNull();
    expect(menuButton()).toHaveFocus();
  });

  it("closes on a click outside the menu, and on pressing the button again (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(menuButton());
    await user.click(document.body);
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");

    await user.click(menuButton());
    await user.click(menuButton());
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
  });
});
