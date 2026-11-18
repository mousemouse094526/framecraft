import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { useLeaveGuard } from "./lib/useHash";
import { stubMatchMedia } from "./testing/fakeMatchMedia";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  // Neither page needs an answer to show which tab is open.
  fetchMock.mockReturnValue(new Promise(() => {}));
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.localStorage.clear();
  window.location.hash = "";
});

// The main menu replaced the 8-tab bar and its narrow menu (ui-nav D1, D4); these tests replaced
// the ones on "แถบ tab" and "เมนู tab" (ui-nav D8).
function menu() {
  return within(screen.getByRole("navigation", { name: "เมนูหลัก" }));
}

function item(name: string) {
  return menu().getByRole("link", { name });
}

function menuButton() {
  return screen.getByRole("button", { name: /^เมนู:/ });
}

describe("main menu (ui-nav D1–D3, D12)", () => {
  it("lists เล่าเรื่อง, ดนตรี, คลัง and ตั้งค่า with their topics and items, in that order (e2e)", () => {
    render(<App />);

    expect(menu().getAllByRole("link").map((link) => link.textContent)).toEqual([
      "1เลือกคลิป",
      "2ตรวจแก้บท",
      "3ผล render",
      "ชุดทั้งหมด",
      "สร้างชุดใหม่",
      "เพลงทั้งหมด",
      "reel ทั้งหมด",
      "คลังคลิปใช้กับ สปอย",
      "คลังความรู้ใช้กับ สปอย",
      "คลังเสียงใช้กับ สปอย, การ์ตูนเล่า",
      "เสียงที่บันทึกใช้กับ สปอย, การ์ตูนเล่า",
      "ติดตั้ง",
    ]);
    const sections = menu().getAllByRole("group").filter((group) => group.parentElement?.tagName === "NAV");
    const groupsOf = (section: HTMLElement) =>
      within(section).queryAllByRole("group").map((group) => group.firstElementChild?.textContent);
    expect(sections.map((section) => [section.firstElementChild?.textContent, groupsOf(section)])).toEqual([
      ["เล่าเรื่อง", ["สปอย", "การ์ตูนเล่า"]],
      ["ดนตรี", ["แกะเพลง", "reel กลอง"]],
      ["คลัง", []],
      ["ตั้งค่า", []],
    ]);
    expect(within(menu().getByRole("group", { name: "ตั้งค่า" })).getByRole("link", { name: "ติดตั้ง" })).toHaveAttribute("href", "#/setup");
    expect(within(menu().getByRole("group", { name: "สปอย" })).getAllByRole("link").map((l) => l.getAttribute("href"))).toEqual([
      "#/spoil",
      "#/spoil/review",
      "#/spoil/renders",
    ]);
  });

  it("never marks a section open, only the topic in it (D12)", () => {
    window.location.hash = "#/spoil/review";
    render(<App />);

    expect(menu().getByRole("group", { name: "เล่าเรื่อง" })).not.toHaveAttribute("aria-current");
    expect(menu().getByRole("group", { name: "สปอย" })).toHaveAttribute("aria-current", "true");
  });

  it("names each library by itself and says what it is used with (D2)", () => {
    render(<App />);

    expect(item("คลังคลิป")).toHaveAttribute("href", "#/clips");
    expect(item("คลังคลิป")).toHaveAccessibleDescription("ใช้กับ สปอย");
    expect(item("คลังความรู้")).toHaveAccessibleDescription("ใช้กับ สปอย");
    expect(item("คลังเสียง")).toHaveAccessibleDescription("ใช้กับ สปอย, การ์ตูนเล่า");
    expect(item("เสียงที่บันทึก")).toHaveAttribute("href", "#/spoil/voices");
    expect(item("เสียงที่บันทึก")).toHaveAccessibleDescription("ใช้กับ สปอย, การ์ตูนเล่า");
  });

  // spec › Implementation › Hash: the item open, the topic whose heading stands out, and the header's line (D6, D11).
  it.each([
    ["", "ติดตั้ง", null, "ติดตั้ง"],
    ["#/nope", "ติดตั้ง", null, "ติดตั้ง"],
    ["#/setup", "ติดตั้ง", null, "ติดตั้ง"],
    ["#/spoil", "เลือกคลิป", "สปอย", "สปอย / เลือกคลิป"],
    ["#/spoil/xyz", "เลือกคลิป", "สปอย", "สปอย / เลือกคลิป"],
    ["#/spoil/review", "ตรวจแก้บท", "สปอย", "สปอย / ตรวจแก้บท"],
    ["#/spoil/renders", "ผล render", "สปอย", "สปอย / ผล render"],
    ["#/spoil/voices", "เสียงที่บันทึก", "สปอย", "คลัง / เสียงที่บันทึก"],
    ["#/toon", "ชุดทั้งหมด", "การ์ตูนเล่า", "การ์ตูนเล่า / ชุดทั้งหมด"],
    ["#/toon/new", "สร้างชุดใหม่", "การ์ตูนเล่า", "การ์ตูนเล่า / สร้างชุดใหม่"],
    ["#/toon/series/s_1/cast", null, "การ์ตูนเล่า", "การ์ตูนเล่า"],
    ["#/toon/eps/e_1/render", null, "การ์ตูนเล่า", "การ์ตูนเล่า"],
    ["#/toon/sounds", "คลังเสียง", null, "คลัง / คลังเสียง"],
    ["#/drums", "reel ทั้งหมด", "reel กลอง", "reel กลอง / reel ทั้งหมด"],
    ["#/drums/a1b2c3d4e5f6", null, "reel กลอง", "reel กลอง"],
    ["#/songs", "เพลงทั้งหมด", "แกะเพลง", "แกะเพลง / เพลงทั้งหมด"],
    ["#/songs/s_1", null, "แกะเพลง", "แกะเพลง"],
    ["#/songs/s_1/cover", null, "แกะเพลง", "แกะเพลง"],
    ["#/clips", "คลังคลิป", null, "คลัง / คลังคลิป"],
    ["#/stories", "คลังความรู้", null, "คลัง / คลังความรู้"],
    ["#/stories/new", "คลังความรู้", null, "คลัง / คลังความรู้"],
    ["#/stories/st_3fa91c07", "คลังความรู้", null, "คลัง / คลังความรู้"],
    ["#/sounds", "คลังเสียง", null, "คลัง / คลังเสียง"],
    ["#/sounds?back=#/toon", "คลังเสียง", null, "คลัง / คลังเสียง"],
  ])("at %j marks %s open, %s's heading, and says %s (e2e)", (hash, open, topic, line) => {
    window.location.hash = hash;
    render(<App />);

    expect(menu().queryAllByRole("link", { current: "page" }).length).toBe(open ? 1 : 0);
    if (open) expect(menu().getByRole("link", { name: open })).toHaveAttribute("aria-current", "page");
    const current = menu().getAllByRole("group").filter((group) => group.getAttribute("aria-current") === "true");
    expect(current.map((group) => group.firstElementChild?.textContent)).toEqual(topic ? [topic] : []);
    expect(menuButton()).toHaveAccessibleName(`เมนู: ${line}`);
    expect(screen.getByRole("banner")).toHaveTextContent(line);
  });

  it("still opens each page from its hash (D6)", () => {
    window.location.hash = "#/spoil/review";
    render(<App />);
    expect(screen.getByRole("navigation", { name: "ขั้นของสปอย" })).toBeInTheDocument();
  });

  it("writes an item's hash when it is picked, and the back button goes back (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(item("คลังคลิป"));
    expect(window.location.hash).toBe("#/clips");
    expect(await screen.findByText("กำลังโหลด…")).toBeInTheDocument();
    expect(item("คลังคลิป")).toHaveAttribute("aria-current", "page");

    await user.click(item("ติดตั้ง"));
    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(item("คลังคลิป")).toHaveAttribute("aria-current", "page"));
    expect(window.location.hash).toBe("#/clips");
  });
});

describe("menu below 1280px: a drawer (ui-nav D4, D10)", () => {
  function content() {
    return screen.getByText("กำลังเช็ค…").closest("[inert]");
  }

  it("starts closed; the button opens it, takes the focus to the open item and makes the page inert (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).toHaveAttribute("aria-controls", screen.getByRole("navigation", { name: "เมนูหลัก" }).id);
    expect(content()).toBeNull();

    await user.click(menuButton());

    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
    expect(item("ติดตั้ง")).toHaveFocus();
    expect(content()).not.toBeNull();
  });

  it("closes when an item is picked, with the focus back on the menu button (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(menuButton());
    await user.click(item("ตรวจแก้บท"));

    expect(window.location.hash).toBe("#/spoil/review");
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: สปอย / ตรวจแก้บท"));
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    await waitFor(() => expect(menuButton()).toHaveFocus());
  });

  it("closes when the open item is picked again, though the hash stays the same", async () => {
    window.location.hash = "#/setup";
    const user = userEvent.setup();
    render(<App />);

    await user.click(menuButton());
    await user.click(item("ติดตั้ง"));

    expect(window.location.hash).toBe("#/setup");
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).toHaveFocus();
  });

  it("closes on Esc with the focus back on the button (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(menuButton());

    await user.keyboard("{Escape}");

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).toHaveFocus();
    expect(content()).toBeNull();
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

  it("closes on back or forward, with the page live again", async () => {
    const user = userEvent.setup();
    window.location.hash = "#/spoil";
    render(<App />);
    await user.click(item("ตรวจแก้บท"));
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: สปอย / ตรวจแก้บท"));
    await user.click(menuButton());

    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: สปอย / เลือกคลิป"));
    // The new hash renders first; the effect that closes the drawer runs after it.
    await waitFor(() => expect(menuButton()).toHaveAttribute("aria-expanded", "false"));
    expect(document.querySelector("[inert]")).toBeNull();
  });

  it("keeps the header's action out of reach behind an open drawer", async () => {
    const user = userEvent.setup();
    window.location.hash = "#/clips";
    render(<App />);
    await user.click(menuButton());

    expect(document.querySelectorAll("[inert]")).toHaveLength(2);
    expect(menuButton().closest("[inert]")).toBeNull();
  });

  it("closes, keeping the page, when the leave guard is declined (e2e)", async () => {
    // The hash the last test's cleanup reset is still on its way; let it land before the guard is up.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    function Unsaved() {
      useLeaveGuard(() => true);
      return null;
    }
    render(
      <>
        <Unsaved />
        <App />
      </>,
    );

    await user.click(menuButton());
    await user.click(item("เพลงทั้งหมด"));

    await waitFor(() => expect(window.confirm).toHaveBeenCalled());
    expect(window.location.hash).toBe("");
    expect(screen.getByText("กำลังเช็ค…")).toBeInTheDocument();
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
  });

  it("moves on when the leave guard is accepted", async () => {
    // The hash the last test's cleanup reset is still on its way; let it land before the guard is up.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    function Unsaved() {
      useLeaveGuard(() => true);
      return null;
    }
    render(
      <>
        <Unsaved />
        <App />
      </>,
    );

    await user.click(menuButton());
    await user.click(item("เพลงทั้งหมด"));

    expect(window.location.hash).toBe("#/songs");
  });
});

describe("menu from 1280px: a pinned sidebar (ui-nav D4, D10, D11)", () => {
  it("starts open; the button collapses it and the setting stays after a reload (e2e)", async () => {
    stubMatchMedia(true);
    const user = userEvent.setup();
    const { unmount } = render(<App />);

    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
    await user.click(menuButton());

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(window.localStorage.getItem("framecraft.nav.collapsed")).toBe("true");
    unmount();
    render(<App />);
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");

    await user.click(menuButton());
    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
    expect(window.localStorage.getItem("framecraft.nav.collapsed")).toBeNull();
  });

  it("is open when the stored setting is anything but true", () => {
    stubMatchMedia(true);
    window.localStorage.setItem("framecraft.nav.collapsed", "yes");
    render(<App />);

    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
  });

  it("stays open, and the page not inert, when an item is picked", async () => {
    stubMatchMedia(true);
    const user = userEvent.setup();
    render(<App />);

    await user.click(item("คลังคลิป"));

    expect(window.location.hash).toBe("#/clips");
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: คลัง / คลังคลิป"));
    expect(menuButton()).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("กำลังโหลด…").closest("[inert]")).toBeNull();
  });

  it("closes an open drawer when the window grows past 1280px, then follows the sidebar's setting", async () => {
    const media = stubMatchMedia(false);
    window.localStorage.setItem("framecraft.nav.collapsed", "true");
    const user = userEvent.setup();
    render(<App />);
    await user.click(menuButton());
    expect(menuButton()).toHaveAttribute("aria-expanded", "true");

    act(() => media.change(true));

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    act(() => media.change(false));
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
  });
});
