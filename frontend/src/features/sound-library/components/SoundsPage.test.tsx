import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { FakeXhr } from "../../../testing/fakeXhr";
import { get, phased, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Sound } from "../lib/sounds";

const SOUNDS = "/api/sounds";
const IMPORT = "/api/sounds/import/current";
const LEGACY = "/api/sounds/legacy";

const fetchMock = vi.fn<typeof fetch>();

const rain: Sound = { id: "m_01", name: "ฝนตกในป่า", duration_s: 222, source: "file" };

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("XMLHttpRequest", FakeXhr);
  FakeXhr.sent = [];
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.location.hash = "";
});

function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [
    [SOUNDS, [rain]],
    [IMPORT, null],
    [LEGACY, { left_behind: null }],
    ["/api/toon/series", []],
    ["/api/toon/jobs/current", null],
  ]);
  window.location.hash = hash;
  render(<App />);
  return userEvent.setup({ advanceTimers: (ms) => vi.isFakeTimers() && vi.advanceTimersByTime(ms) });
}

function tabs() {
  return within(screen.getByRole("navigation", { name: "แถบ tab" }));
}

describe("คลังเสียง", () => {
  it("is a tab of its own after คลังความรู้: คลังเสียง opens #/sounds with the library and each sound's length (e2e)", async () => {
    const user = open("#/setup", [get("/api/status", new Promise(() => {}))]);

    await user.click(tabs().getByRole("link", { name: "คลังเสียง" }));

    expect(window.location.hash).toBe("#/sounds");
    const row = await screen.findByRole("listitem", { name: "ฝนตกในป่า" });
    expect(row).toHaveTextContent("3:42");
    expect(screen.getByRole("heading", { level: 2, name: "คลังเสียง" })).toBeInTheDocument();
    expect(screen.getByText("เสียงพื้น 1 เสียง")).toBeInTheDocument();
    expect(tabs().getByRole("link", { name: "คลังเสียง" })).toHaveAttribute("aria-current", "page");
  });

  it("#/toon/sounds opens the library as #/sounds, on load and on a hash change (e2e)", async () => {
    open("#/toon/sounds", []);
    expect(await screen.findByRole("listitem", { name: "ฝนตกในป่า" })).toBeInTheDocument();
    expect(window.location.hash).toBe("#/sounds");

    act(() => {
      window.location.hash = "#/toon";
    });
    expect(await screen.findByRole("heading", { level: 2, name: "การ์ตูนเล่า" })).toBeInTheDocument();
    act(() => {
      window.location.hash = "#/toon/sounds";
    });

    await waitFor(() => expect(window.location.hash).toBe("#/sounds"));
    expect(await screen.findByRole("listitem", { name: "ฝนตกในป่า" })).toBeInTheDocument();
  });

  it("the info button opens the three lines, and pressing it again, Esc or a click outside closes them (e2e)", async () => {
    const user = open("#/sounds", []);
    const info = await screen.findByRole("button", { name: "วิธีใช้คลังเสียง" });
    const box = () => screen.queryByRole("region", { name: "วิธีใช้คลังเสียง" });
    expect(info).toHaveAttribute("aria-expanded", "false");
    expect(box()).not.toBeInTheDocument();

    await user.click(info);
    expect(info).toHaveAttribute("aria-expanded", "true");
    expect(info).toHaveAttribute("aria-controls", box()!.id);
    expect(within(box()!).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "ใช้ร่วมกันทั้งการ์ตูนเล่าและสปอย: การ์ตูนเล่าเลือกเสียงพื้นต่อช่วง สปอยเลือกหนึ่งเสียงต่อคลิป",
      "เสียงพื้นคือเสียงบรรยากาศที่เล่นวนใต้เสียงเล่า เช่น เสียงจิ้งหรีด เสียงฝน เสียงห้องเรียน",
      "เอาเข้าได้จากไฟล์เสียงหรือวิดีโอในเครื่อง หรือวางลิงก์ แอปแปลงเป็นไฟล์เสียงให้เอง",
    ]);
    await user.click(info);
    expect(box()).not.toBeInTheDocument();

    await user.click(info);
    await user.keyboard("{Escape}");
    expect(box()).not.toBeInTheDocument();

    await user.click(info);
    await user.click(within(box()!).getAllByRole("listitem")[0]);
    expect(box()).toBeInTheDocument();
    await user.click(screen.getByRole("heading", { level: 2, name: "คลังเสียง" }));
    expect(box()).not.toBeInTheDocument();
    expect(info).toHaveAttribute("aria-expanded", "false");
  });

  it("ฟัง plays that sound of the library", async () => {
    const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
    const user = open("#/sounds", [get(SOUNDS, [rain, { ...rain, id: "m_02", name: "ลมพัด" }])]);

    await user.click(await screen.findByRole("button", { name: "ฟัง ลมพัด" }));

    expect(play).toHaveBeenCalledOnce();
    expect((play.mock.contexts[0] as HTMLAudioElement).src).toMatch(/\/api\/sounds\/m_02\/file$/);
  });

  it("shows the sound rights line before the file picker and the link field (e2e)", async () => {
    open("#/sounds", []);

    const rights = await screen.findByText(
      "ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด", // toon legal.md item 4
    );
    const picker = screen.getByLabelText("เลือกไฟล์เสียง");
    const link = screen.getByRole("textbox", { name: /ลิงก์เสียง/ });
    expect(rights.compareDocumentPosition(picker) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(rights.compareDocumentPosition(link) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("an empty library says so", async () => {
    open("#/sounds", [get(SOUNDS, [])]);

    expect(await screen.findByText("ยังไม่มีเสียงในคลัง")).toBeInTheDocument();
  });

  it("a file is checked, sent with its % out, and comes into the list", async () => {
    const user = open("#/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);

    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));

    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    expect(sent(fetchMock, "POST", `${SOUNDS}/imports/check`)).toEqual([{ name: "ลม.wav", size: 3 }]);
    expect(FakeXhr.sent[0].url).toBe(`${SOUNDS}/imports?name=${encodeURIComponent("ลม.wav")}&size=3`);
    FakeXhr.sent[0].progress(1, 2);
    expect(await screen.findByText("50%")).toBeInTheDocument();
    await FakeXhr.sent[0].respond(201, { id: "m_02", name: "ลม", duration_s: 61, source: "file" });
    expect(await screen.findByRole("listitem", { name: "ลม" })).toHaveTextContent("1:01");
  });

  it("ยกเลิก while a file is sent stops it: no notice, nothing comes in", async () => {
    const user = open("#/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);
    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));

    await user.click(screen.getByRole("button", { name: "ยกเลิก" }));

    expect(FakeXhr.sent[0].abort).toHaveBeenCalledOnce();
    await waitFor(() => expect(screen.queryByRole("button", { name: "ยกเลิก" })).not.toBeInTheDocument());
    expect(screen.queryByText("เอาไฟล์ ลม.wav เข้าไม่ได้")).not.toBeInTheDocument();
    expect(screen.queryByRole("listitem", { name: "ลม" })).not.toBeInTheDocument();
  });

  it("a file the check refuses is not sent and says why", async () => {
    const busy = { code: "busy", message: "มีงานเอาเสียงเข้าอยู่" };
    const user = open("#/sounds", [send("POST", `${SOUNDS}/imports/check`, busy, 409)]);

    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));

    expect(await screen.findByText("เอาไฟล์ ลม.wav เข้าไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("มีงานเอาเสียงเข้าอยู่")).toBeInTheDocument();
    expect(FakeXhr.sent).toHaveLength(0);
  });

  it("a link loads with its % and its sound comes in; a refused one says why", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const loading = { url: "https://youtu.be/x", state: "downloading", title: "ลม", percent: 63, error: null, cancel_requested: false, sound_id: null };
    const job = phased(IMPORT, loading, { ...loading, state: "done", percent: 100, sound_id: "m_02" });
    const user = open("#/sounds", [
      send("POST", `${SOUNDS}/downloads`, { code: "invalid_url", message: "ลิงก์นี้ใช้ไม่ได้" }, 400),
      send("POST", `${SOUNDS}/downloads`, loading, 202),
      get(IMPORT, null),
      job.route,
    ]);
    const field = await screen.findByRole("textbox", { name: /ลิงก์เสียง/ });

    await user.type(field, "ftp://x");
    await user.click(screen.getByRole("button", { name: "โหลด" }));
    expect(await screen.findByText("ลิงก์นี้ใช้ไม่ได้")).toBeInTheDocument();

    await user.clear(field);
    await user.type(field, "https://youtu.be/x");
    await user.click(screen.getByRole("button", { name: "โหลด" }));
    expect(await screen.findByText("กำลังโหลด 63%")).toBeInTheDocument();
    job.phases.at = 1;
    await act(() => vi.advanceTimersByTimeAsync(1100));
    await waitFor(() => expect(screen.queryByText("กำลังโหลด 63%")).not.toBeInTheDocument());
    expect(sent(fetchMock, "POST", `${SOUNDS}/downloads`)).toEqual([{ url: "ftp://x" }, { url: "https://youtu.be/x" }]);
  });

  it("a sound in use can't be deleted: a line per user under its tab's name (e2e)", async () => {
    const inUse = {
      code: "in_use",
      message: "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้",
      users: [
        { tab: "toon", label: "รุ่นพี่เล่าว่า… · EP 3 คืนที่ไฟดับ" },
        { tab: "spoil", label: "Spoil draft: ผีบ้านไม้ · EP 2" },
      ],
    };
    const user = open("#/sounds", [send("DELETE", `${SOUNDS}/m_01`, inUse, 409)]);

    await user.click(await screen.findByRole("button", { name: "ลบ ฝนตกในป่า" }));

    expect(await screen.findByText("ลบ ฝนตกในป่า ไม่ได้")).toBeInTheDocument();
    expect(screen.getByText("การ์ตูนเล่า · รุ่นพี่เล่าว่า… · EP 3 คืนที่ไฟดับ")).toBeInTheDocument();
    expect(screen.getByText("สปอย · Spoil draft: ผีบ้านไม้ · EP 2")).toBeInTheDocument();
    expect(screen.getByText("ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้")).toBeInTheDocument();
    expect(screen.getByRole("listitem", { name: "ฝนตกในป่า" })).toBeInTheDocument();
  });

  it("a refused rename says why and the name stays", async () => {
    const refused = { code: "invalid_name", message: "ชื่อยาวได้ไม่เกิน 60 ตัวอักษร" };
    const user = open("#/sounds", [send("PATCH", `${SOUNDS}/m_01`, refused, 400)]);
    const field = await screen.findByRole("textbox", { name: "ชื่อเสียง ฝนตกในป่า" });

    await user.tripleClick(field);
    await user.keyboard("ฝน");
    await user.tab();

    expect(await screen.findByText("เปลี่ยนชื่อ ฝนตกในป่า ไม่ได้")).toBeInTheDocument();
    expect(screen.getByText(refused.message)).toBeInTheDocument();
    expect(sent(fetchMock, "PATCH", `${SOUNDS}/m_01`)).toEqual([{ name: "ฝน" }]);
    expect(screen.getByRole("listitem", { name: "ฝนตกในป่า" })).toBeInTheDocument();
  });

  it("asks before leaving while a file is sent", async () => {
    const user = open("#/sounds", [send("POST", `${SOUNDS}/imports/check`, { size: 3 }, 200)]);
    await user.upload(await screen.findByLabelText("เลือกไฟล์เสียง"), new File(["wav"], "ลม.wav", { type: "audio/wav" }));
    await waitFor(() => expect(FakeXhr.sent).toHaveLength(1));
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);

    act(() => {
      window.location.hash = "#/toon";
    });

    await waitFor(() => expect(confirm).toHaveBeenCalled());
    expect(window.location.hash).toBe("#/sounds");
  });

  it("warns while the old library's folder still holds sounds start-up could not move (e2e)", async () => {
    open("#/sounds", [get(LEGACY, { left_behind: "media/toon/sounds" })]);

    expect(
      await screen.findByText("ยังย้ายเสียงเดิมจาก media/toon/sounds ไม่ครบ: เช็คที่ว่างดิสก์แล้วเปิดแอปใหม่"),
    ).toBeInTheDocument();
  });

  it("no warning once the old library is all moved", async () => {
    open("#/sounds", []);

    await screen.findByRole("listitem", { name: "ฝนตกในป่า" });
    expect(screen.queryByText(/ยังย้ายเสียงเดิม/)).not.toBeInTheDocument();
  });
});

describe("← กลับ", () => {
  it.each(["#/toon/eps/e_01", "#/spoil/review", "#/toon"])("goes back to %s, the page that opened the library (e2e)", async (back) => {
    open(`#/sounds?back=${back}`, []);

    expect(await screen.findByRole("link", { name: "กลับ" })).toHaveAttribute("href", back);
    expect(tabs().getByRole("link", { name: "คลังเสียง" })).toHaveAttribute("aria-current", "page");
  });

  it.each(["#/sounds", "#/sounds?back=#/setup", "#/sounds?back=https://example.com"])("is not there for %s (e2e)", async (hash) => {
    open(hash, []);

    await screen.findByRole("listitem", { name: "ฝนตกในป่า" });
    expect(screen.queryByRole("link", { name: "กลับ" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "การ์ตูนเล่า" })).toEqual([tabs().getByRole("link", { name: "การ์ตูนเล่า" })]); // the old "← การ์ตูนเล่า" is gone
  });
});
