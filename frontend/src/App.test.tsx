import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { rememberRecent } from "./lib/recent";
import { useLeaveGuard } from "./lib/useHash";
import { stubMatchMedia } from "./testing/fakeMatchMedia";
import { get, serve } from "./testing/testBackend";

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

function heading() {
  return within(screen.getByRole("banner")).getByRole("heading", { level: 1 });
}

/** Every group in the menu is one of these sections, in this order: a group inside one would be extra (D16). */
function expectSections(names: string[]) {
  expect(menu().getAllByRole("group")).toEqual(names.map((name) => menu().getByRole("group", { name })));
}

function recentGroup() {
  return within(menu().getByRole("group", { name: "ล่าสุด" }));
}

const RECENT_KEY = "framecraft.nav.recent";

describe("main menu: sections, then links (ui-nav D1–D3, nav-ia D16–D20)", () => {
  it("lists เล่าเรื่อง, ดนตรี, คลัง and ตั้งค่า with only links under them, in that order (e2e)", () => {
    render(<App />);

    expect(menu().getAllByRole("link").map((link) => link.textContent)).toEqual([
      "ทำสปอย",
      "คลิปทั้งหมด",
      "การ์ตูนเล่า",
      "reel cover",
      "reel กลอง",
      "คลังความรู้ใช้กับ สปอย",
      "คลังเสียงใช้กับ สปอย, การ์ตูนเล่า",
      "เสียงพากย์ใช้กับ สปอย, การ์ตูนเล่า",
      "ติดตั้ง",
    ]);
    expectSections(["เล่าเรื่อง", "ดนตรี", "คลัง", "ตั้งค่า"]);
    expect(within(menu().getByRole("group", { name: "ตั้งค่า" })).getByRole("link", { name: "ติดตั้ง" })).toHaveAttribute("href", "#/setup");
    expect(within(menu().getByRole("group", { name: "เล่าเรื่อง" })).getAllByRole("link").map((l) => l.getAttribute("href"))).toEqual([
      "#/spoil",
      "#/spoil/clips",
      "#/toon",
    ]);
    expect(within(menu().getByRole("group", { name: "ดนตรี" })).getAllByRole("link").map((l) => l.getAttribute("href"))).toEqual([
      "#/covers",
      "#/drums",
    ]);
  });

  it("has no line that is an action or the same page as another (D17)", () => {
    render(<App />);

    for (const name of ["สร้างชุดใหม่", "ชุดทั้งหมด", "เพลงทั้งหมด", "reel ทั้งหมด"]) expect(menu().queryByRole("link", { name })).toBeNull();
  });

  it("never marks a section open, only the link (D16)", () => {
    window.location.hash = "#/spoil/clips";
    render(<App />);

    expect(menu().getAllByRole("group").filter((group) => group.hasAttribute("aria-current"))).toEqual([]);
    expect(menu().getByRole("link", { current: "page" })).toHaveTextContent("คลิปทั้งหมด");
  });

  it("names each library by itself and says what it is used with (D2, nav-ia D2–D4)", () => {
    render(<App />);

    expect(item("คลังความรู้")).toHaveAccessibleDescription("ใช้กับ สปอย");
    expect(item("คลังเสียง")).toHaveAccessibleDescription("ใช้กับ สปอย, การ์ตูนเล่า");
    expect(item("เสียงพากย์")).toHaveAttribute("href", "#/voices");
    expect(item("เสียงพากย์")).toHaveAccessibleDescription("ใช้กับ สปอย, การ์ตูนเล่า");
    expect(within(menu().getByRole("group", { name: "คลัง" })).getAllByRole("link")).toHaveLength(3);
  });

  // spec › Design › หัวหน้าและลิงก์ที่เปิด: the link open is the header's line, with nothing in ล่าสุด (D19, D20).
  it.each([
    ["", "ติดตั้ง"],
    ["#/nope", "ติดตั้ง"],
    ["#/setup", "ติดตั้ง"],
    // Not a page of การ์ตูนเล่า (`tabOf`): it opens ติดตั้ง, and the การ์ตูนเล่า link stays closed.
    ["#/toon?x", "ติดตั้ง"],
    ["#/spoil", "ทำสปอย"],
    ["#/spoil/xyz", "ทำสปอย"],
    ["#/spoil/clips", "คลิปทั้งหมด"],
    ["#/voices", "เสียงพากย์"],
    ["#/toon", "การ์ตูนเล่า"],
    ["#/toon/new", "การ์ตูนเล่า"],
    ["#/toon/series/s_1/cast", "การ์ตูนเล่า"],
    ["#/toon/eps/e_1", "การ์ตูนเล่า"],
    ["#/toon/sounds", "คลังเสียง"],
    ["#/drums", "reel กลอง"],
    ["#/drums/a1b2c3d4e5f6", "reel กลอง"],
    ["#/covers", "reel cover"],
    ["#/covers/s_1", "reel cover"],
    ["#/covers/s_1/cover", "reel cover"],
    ["#/stories", "คลังความรู้"],
    ["#/stories/new", "คลังความรู้"],
    ["#/stories/st_3fa91c07", "คลังความรู้"],
    ["#/sounds", "คลังเสียง"],
    ["#/sounds?back=#/toon", "คลังเสียง"],
  ])("at %j marks %s open and says it (e2e)", (hash, open) => {
    window.location.hash = hash;
    render(<App />);

    expect(menu().getAllByRole("link", { current: "page" })).toEqual([item(open)]);
    expect(menuButton()).toHaveAccessibleName(`เมนู: ${open}`);
    expect(heading().textContent).toBe(open);
  });

  // The pages that open from ล่าสุด: the recent link is open, the header names its source (D20).
  it.each([
    ["#/toon/series/s_1", "toon", "รุ่นพี่เล่าว่า…", "การ์ตูนเล่า"],
    ["#/toon/series/s_1/cast", "toon", "รุ่นพี่เล่าว่า…", "การ์ตูนเล่า"],
    ["#/toon/eps/e_1", "toon", "รุ่นพี่เล่าว่า… · EP1", "การ์ตูนเล่า"],
    ["#/covers/s_1", "covers", "Smells Like Teen Spirit", "reel cover"],
    ["#/drums/a1b2c3d4e5f6", "drums", "ร็อกพื้นฐาน", "reel กลอง"],
  ])("at %j in ล่าสุด (%s) marks %j open, not its source, and says %s (e2e)", (hash, area, label, line) => {
    // ล่าสุด keeps the Series, not its cast page; the cast page opens the Series' link (prefix).
    const page = hash.replace(/\/cast$/, "");
    window.localStorage.setItem(RECENT_KEY, JSON.stringify({ [area]: [{ hash: page, label }] }));
    window.location.hash = hash;
    render(<App />);

    expect(recentGroup().getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
    expect(menu().getAllByRole("link", { current: "page" })).toHaveLength(1);
    expect(heading().textContent).toBe(line);
    expect(menuButton()).toHaveAccessibleName(`เมนู: ${line}`);
  });

  it("has a ล่าสุด section between ดนตรี and คลัง: การ์ตูนเล่า, reel cover, reel กลอง, each saying its source (D18)", () => {
    // Stored in another order than the menu's: the menu's order is its own.
    window.localStorage.setItem(
      RECENT_KEY,
      JSON.stringify({
        toon: [{ hash: "#/toon/eps/e_1", label: "EP 3: ไปทะเล" }],
        drums: [{ hash: "#/drums/a1b2c3d4e5f6", label: "ร็อกพื้นฐาน" }],
        covers: [{ hash: "#/covers/s_1", label: "Smells Like Teen Spirit" }],
      }),
    );
    render(<App />);

    expectSections(["เล่าเรื่อง", "ดนตรี", "ล่าสุด", "คลัง", "ตั้งค่า"]);
    const links = recentGroup().getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual(["#/toon/eps/e_1", "#/covers/s_1", "#/drums/a1b2c3d4e5f6"]);
    expect(links[0]).toHaveAccessibleName("EP 3: ไปทะเล");
    expect(links[1]).toHaveAccessibleName("Smells Like Teen Spirit");
    expect(links[2]).toHaveAccessibleName("ร็อกพื้นฐาน");
    expect(links[0]).toHaveAccessibleDescription("การ์ตูนเล่า");
    expect(links[1]).toHaveAccessibleDescription("reel cover");
    expect(links[2]).toHaveAccessibleDescription("reel กลอง");
  });

  it("reads a song kept under the old songs key as a reel cover link in ล่าสุด (nav-ia D9)", () => {
    window.localStorage.setItem(RECENT_KEY, JSON.stringify({ songs: [{ hash: "#/songs/x", label: "เพลงเก่า" }] }));
    render(<App />);

    const link = recentGroup().getByRole("link", { name: "เพลงเก่า" });
    expect(link).toHaveAttribute("href", "#/covers/x");
    expect(link).toHaveAccessibleDescription("reel cover");
  });

  it("keeps the header when a page puts itself in ล่าสุด after it loads; the open link moves there (D20)", async () => {
    window.location.hash = "#/covers/s_1";
    render(<App />);
    expect(item("reel cover")).toHaveAttribute("aria-current", "page");

    act(() => rememberRecent("covers", "#/covers/s_1", "Smells Like Teen Spirit"));

    await waitFor(() => expect(recentGroup().getByRole("link", { name: "Smells Like Teen Spirit" })).toHaveAttribute("aria-current", "page"));
    expect(item("reel cover")).not.toHaveAttribute("aria-current");
    expect(heading().textContent).toBe("reel cover");
  });

  it("opens การ์ตูนเล่า on #/toon/new, and สร้าง Series at #/toon still leads there (D17)", async () => {
    const user = userEvent.setup();
    serve(fetchMock, [get("/api/toon/series", [])]);
    window.location.hash = "#/toon";
    render(<App />);

    // The list offers it twice: in its header and in its empty state.
    await user.click((await screen.findAllByRole("link", { name: "สร้าง Series" }))[0]);

    expect(await screen.findByRole("heading", { level: 2, name: "สร้าง Series" })).toBeInTheDocument();
    expect(window.location.hash).toBe("#/toon/new");
    await waitFor(() => expect(item("การ์ตูนเล่า")).toHaveAttribute("aria-current", "page"));
    expect(heading().textContent).toBe("การ์ตูนเล่า");
  });

  it("still opens each page from its hash (D6)", () => {
    window.location.hash = "#/spoil";
    render(<App />);
    expect(screen.getByRole("navigation", { name: "ขั้นของสปอย" })).toBeInTheDocument();
  });

  it("writes an item's hash when it is picked, and the back button goes back (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(item("คลิปทั้งหมด"));
    expect(window.location.hash).toBe("#/spoil/clips");
    expect(await screen.findByText("กำลังโหลด…")).toBeInTheDocument();
    expect(item("คลิปทั้งหมด")).toHaveAttribute("aria-current", "page");

    await user.click(item("ติดตั้ง"));
    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(item("คลิปทั้งหมด")).toHaveAttribute("aria-current", "page"));
    expect(window.location.hash).toBe("#/spoil/clips");
  });
});

// nav-ia spec › Implementation › Redirect: an old hash is put back as its new one, on load and on a hash change (D9).
describe("pages that moved (nav-ia D9)", () => {
  it.each([
    ["#/toon/sounds", "#/sounds"],
    ["#/clips", "#/spoil/clips"],
    ["#/spoil/voices", "#/voices"],
    ["#/songs", "#/covers"],
    ["#/songs/s_1", "#/covers/s_1"],
    ["#/songs/s_1/cover", "#/covers/s_1"],
    ["#/covers/s_1/cover", "#/covers/s_1"],
    ["#/drums/a1b2c3d4e5f6/renders", "#/drums/a1b2c3d4e5f6"],
    ["#/toon/eps/e_1/plot", "#/toon/eps/e_1"],
    ["#/toon/eps/e_1/render", "#/toon/eps/e_1"],
    ["#/spoil/review", "#/spoil"],
    ["#/spoil/renders", "#/spoil"],
  ])("opens %s as %s", (old, now) => {
    window.location.hash = old;
    render(<App />);
    expect(window.location.hash).toBe(now);
  });

  it("follows an old hash that comes after the page is open", async () => {
    render(<App />);
    act(() => {
      window.location.hash = "#/clips";
    });
    await waitFor(() => expect(window.location.hash).toBe("#/spoil/clips"));
    expect(item("คลิปทั้งหมด")).toHaveAttribute("aria-current", "page");
  });

  it("leaves a hash that only looks like an old one", () => {
    window.location.hash = "#/songs/../setup";
    render(<App />);
    expect(window.location.hash).toBe("#/songs/../setup");
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
    await user.click(item("คลิปทั้งหมด"));

    expect(window.location.hash).toBe("#/spoil/clips");
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: คลิปทั้งหมด"));
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

  it("has the wordmark and ปิดเมนู in its head; ปิดเมนู closes it with the focus back on the button (e2e)", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(menuButton());

    expect(menu().getByText("craft")).toBeInTheDocument();
    const close = menu().getByRole("button", { name: "ปิดเมนู" });
    expect(close.closest("[inert]")).toBeNull();
    await user.click(close);

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).toHaveFocus();
    expect(content()).toBeNull();
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
    await user.click(item("คลิปทั้งหมด"));
    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: คลิปทั้งหมด"));
    await user.click(menuButton());

    act(() => {
      window.history.back();
    });

    await waitFor(() => expect(menuButton()).toHaveAccessibleName("เมนู: ทำสปอย"));
    // The new hash renders first; the effect that closes the drawer runs after it.
    await waitFor(() => expect(menuButton()).toHaveAttribute("aria-expanded", "false"));
    expect(document.querySelector("[inert]")).toBeNull();
  });

  it("keeps the header's action out of reach behind an open drawer", async () => {
    const user = userEvent.setup();
    window.location.hash = "#/spoil/clips";
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
    await user.click(item("reel cover"));

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
    await user.click(item("reel cover"));

    expect(window.location.hash).toBe("#/covers");
  });
});

describe("menu from 1280px: a pinned sidebar (ui-nav D4, D10, D11, D14)", () => {
  function collapseButton() {
    return menu().getByRole("button", { name: "ยุบเมนู" });
  }

  it("starts open with the wordmark and ยุบเมนู in its head, and no menu button in the header (e2e)", () => {
    stubMatchMedia(true);
    render(<App />);

    expect(menu().getByText("craft")).toBeInTheDocument();
    expect(collapseButton()).not.toHaveAttribute("aria-expanded");
    expect(screen.queryByRole("button", { name: /^เมนู:/ })).toBeNull();
  });

  it("collapses from its head, moving the focus to the header's button, and the setting stays after a reload (e2e)", async () => {
    stubMatchMedia(true);
    const user = userEvent.setup();
    const { unmount } = render(<App />);

    await user.click(collapseButton());

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menuButton()).toHaveFocus();
    expect(window.localStorage.getItem("framecraft.nav.collapsed")).toBe("true");
    unmount();
    render(<App />);
    expect(menuButton()).toHaveAttribute("aria-expanded", "false");

    await user.click(menuButton());
    expect(screen.queryByRole("button", { name: /^เมนู:/ })).toBeNull();
    expect(collapseButton()).toHaveFocus();
    expect(window.localStorage.getItem("framecraft.nav.collapsed")).toBeNull();
  });

  it("is open when the stored setting is anything but true", () => {
    stubMatchMedia(true);
    window.localStorage.setItem("framecraft.nav.collapsed", "yes");
    render(<App />);

    expect(screen.queryByRole("button", { name: /^เมนู:/ })).toBeNull();
    expect(collapseButton()).toBeInTheDocument();
  });

  it("stays open, and the page not inert, when an item is picked", async () => {
    stubMatchMedia(true);
    const user = userEvent.setup();
    render(<App />);

    await user.click(item("คลิปทั้งหมด"));

    expect(window.location.hash).toBe("#/spoil/clips");
    await waitFor(() => expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/^คลิปทั้งหมด$/));
    expect(screen.queryByRole("button", { name: /^เมนู:/ })).toBeNull();
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

  it("shows the header's button once the window narrows below 1280px with the sidebar open", () => {
    const media = stubMatchMedia(true);
    render(<App />);
    expect(screen.queryByRole("button", { name: /^เมนู:/ })).toBeNull();

    act(() => media.change(false));

    expect(menuButton()).toHaveAttribute("aria-expanded", "false");
    expect(menu().getByRole("button", { name: "ปิดเมนู" })).toBeInTheDocument();
  });

  it("hands the focus to the control that now shows or hides the menu when the window crosses 1280px", async () => {
    const media = stubMatchMedia(false);
    const user = userEvent.setup();
    render(<App />);
    await user.click(menuButton());
    await user.click(menuButton());
    expect(menuButton()).toHaveFocus();

    act(() => media.change(true));
    expect(collapseButton()).toHaveFocus();

    act(() => media.change(false));
    expect(menuButton()).toHaveFocus();
  });
});
