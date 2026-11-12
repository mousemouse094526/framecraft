import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../../../App";
import { get, jsonResponse, send, sent, serve, type Route } from "../../../testing/testBackend";
import type { Story } from "../lib/story";

const ID = "st_3fa91c07";
const PATH = `/api/stories/${ID}`;

const fetchMock = vi.fn<typeof fetch>();
const confirmMock = vi.fn<(message?: string) => boolean>();

function storyOf(change: Partial<Story>): Story {
  return {
    id: ID,
    title: "ยอดนักสืบจิ๋วโคนัน",
    article: "คุโด้ ชินอิจิ นักสืบมัธยมปลาย",
    characters: [
      { name: "โคนัน", description: "ชินอิจิในร่างเด็ก" },
      { name: "รัน", description: "" },
    ],
    clips: 0,
    created_at: "2026-11-05T14:00:00+07:00",
    updated_at: "2026-11-05T14:20:00+07:00",
    ...change,
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("confirm", confirmMock);
});

afterEach(() => {
  fetchMock.mockReset();
  confirmMock.mockReset();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

async function open(hash: string, routes: Route[]) {
  serve(fetchMock, routes, [["/api/stories", []]]);
  window.location.hash = hash;
  render(<App />);
  const user = userEvent.setup();
  if (hash !== "#/stories/new") await screen.findByRole("button", { name: "บันทึก" });
  return user;
}

const save = () => screen.getByRole("button", { name: "บันทึก" });
const title = () => screen.getByRole("textbox", { name: "ชื่อเรื่อง" });
const character = (n: number) => screen.getByRole("group", { name: `ตัวละคร ${n}` });
const nameOf = (n: number) => within(character(n)).getByRole("textbox", { name: "ชื่อ" });
const descriptionOf = (n: number) => within(character(n)).getByRole("textbox", { name: "คำอธิบายสั้น" });

async function hashSettles() {
  // `hashchange` is a task of its own; let it and React's answer to it run.
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("เพิ่มเรื่อง", () => {
  it("sends one POST with the typed fields, then opens the new Story without asking to leave", async () => {
    const created = storyOf({
      article: "",
      characters: [{ name: "โคนัน", description: "นักสืบ" }],
    });
    const user = await open("#/stories/new", [send("POST", "/api/stories", created, 201)]);

    expect(screen.getByRole("heading", { name: "เพิ่มเรื่อง" })).toBeInTheDocument();
    expect(save()).toBeDisabled();
    await user.type(title(), "ยอดนักสืบจิ๋วโคนัน");
    await user.click(screen.getByRole("button", { name: "เพิ่มตัวละคร" }));
    await user.type(nameOf(1), "รัน");
    await user.click(screen.getByRole("button", { name: "เพิ่มตัวละคร" }));
    await user.type(nameOf(2), "โคนัน");
    await user.type(descriptionOf(2), "นักสืบ");
    await user.click(screen.getByRole("button", { name: "ลบตัวละคร รัน" }));
    await user.click(save());

    await waitFor(() => expect(window.location.hash).toBe(`#/stories/${ID}`));
    await hashSettles();
    expect(sent(fetchMock, "POST", "/api/stories")).toEqual([
      { title: "ยอดนักสืบจิ๋วโคนัน", article: "", characters: [{ name: "โคนัน", description: "นักสืบ" }] },
    ]);
    expect(confirmMock).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("บันทึกแล้ว");
    expect(screen.getByRole("heading", { name: "ยอดนักสืบจิ๋วโคนัน" })).toBeInTheDocument();
    // The page already has the Story: no GET of it.
    expect(fetchMock.mock.calls.filter(([input]) => String(input) === PATH)).toHaveLength(0);
  });

  it("sends one POST however fast บันทึก is clicked twice", async () => {
    let answer: (response: Response) => void = () => {};
    const pending: Route = { method: "POST", path: "/api/stories", reply: () => new Promise((resolve) => (answer = resolve)) };
    const user = await open("#/stories/new", [pending]);

    await user.type(title(), "วันพีซ");
    await user.dblClick(save());
    // Enter in a field submits too, past the greyed button.
    fireEvent.submit(screen.getByRole("form", { name: "เพิ่มเรื่อง" }));

    expect(save()).toBeDisabled();
    expect(screen.getByRole("form", { name: "เพิ่มเรื่อง" })).toHaveAttribute("aria-busy", "true");
    await act(async () => answer(jsonResponse(storyOf({ title: "วันพีซ", article: "", characters: [] }), 201)));
    await waitFor(() => expect(window.location.hash).toBe(`#/stories/${ID}`));
    expect(sent(fetchMock, "POST", "/api/stories")).toHaveLength(1);
  });

  it("opens the new Story without asking even when typing went on during the POST, and keeps that typing unsaved", async () => {
    let answer: (response: Response) => void = () => {};
    const pending: Route = { method: "POST", path: "/api/stories", reply: () => new Promise((resolve) => (answer = resolve)) };
    const user = await open("#/stories/new", [pending]);

    await user.type(title(), "วันพีซ");
    await user.click(save());
    await user.type(title(), " ภาค 2");
    await act(async () => answer(jsonResponse(storyOf({ title: "วันพีซ", article: "", characters: [] }), 201)));

    await waitFor(() => expect(window.location.hash).toBe(`#/stories/${ID}`));
    await hashSettles();
    expect(confirmMock).not.toHaveBeenCalled();
    expect(title()).toHaveValue("วันพีซ ภาค 2");
    expect(save()).toBeEnabled();
  });

  it("says ใส่ชื่อเรื่อง and sends nothing when the title is empty", async () => {
    const user = await open("#/stories/new", []);

    await user.type(screen.getByRole("textbox", { name: "บทความ" }), "เรื่องย่อ");
    await user.click(save());

    expect(screen.getByText("ใส่ชื่อเรื่อง")).toBeInTheDocument();
    expect(title()).toHaveAttribute("aria-invalid", "true");
    expect(sent(fetchMock, "POST", "/api/stories")).toHaveLength(0);
  });

  it("counts the article in code points, so Thai vowels and tone marks count", async () => {
    const user = await open("#/stories/new", []);

    // ก + ี + ่ : three code points (spec › Data).
    await user.type(screen.getByRole("textbox", { name: "บทความ" }), "กี่");

    expect(screen.getByText("3 / 5,000")).toBeInTheDocument();
  });
});

describe("แก้ Story", () => {
  it("saves two edited fields in one PUT, says บันทึกแล้ว, and greys บันทึก until the next edit", async () => {
    const user = await open(`#/stories/${ID}`, [
      get(PATH, storyOf({})),
      send("PUT", PATH, storyOf({ title: "โคนัน", characters: [{ name: "โคนัน", description: "นักสืบจิ๋ว" }, { name: "รัน", description: "" }] }), 200),
    ]);

    expect(save()).toBeDisabled();
    await user.clear(title());
    await user.type(title(), "โคนัน");
    await user.clear(descriptionOf(1));
    await user.type(descriptionOf(1), "นักสืบจิ๋ว");
    await user.click(save());

    expect(await screen.findByRole("status")).toHaveTextContent("บันทึกแล้ว");
    expect(sent(fetchMock, "PUT", PATH)).toEqual([
      {
        title: "โคนัน",
        article: "คุโด้ ชินอิจิ นักสืบมัธยมปลาย",
        characters: [
          { name: "โคนัน", description: "นักสืบจิ๋ว" },
          { name: "รัน", description: "" },
        ],
      },
    ]);
    expect(save()).toBeDisabled();

    await user.type(title(), "!");
    expect(save()).toBeEnabled();
    expect(screen.queryByText("บันทึกแล้ว")).not.toBeInTheDocument();
  });

  it("shows the backend's invalid_story under the field it names", async () => {
    const user = await open(`#/stories/${ID}`, [
      get(PATH, storyOf({})),
      send("PUT", PATH, { code: "invalid_story", message: "ชื่อตัวละครซ้ำ", field: "characters.0.name" }, 400),
    ]);

    await user.type(descriptionOf(2), "เพื่อนสมัยเด็ก");
    await user.click(save());

    const first = character(1);
    expect(await within(first).findByText("ชื่อตัวละครซ้ำ")).toBeInTheDocument();
    expect(nameOf(1)).toHaveAttribute("aria-invalid", "true");
    expect(within(character(2)).queryByText("ชื่อตัวละครซ้ำ")).not.toBeInTheDocument();
  });

  it("has no เพิ่มตัวละคร at 30 characters", async () => {
    const thirty = Array.from({ length: 30 }, (_, i) => ({ name: `ตัว ${i + 1}`, description: "" }));
    await open(`#/stories/${ID}`, [get(PATH, storyOf({ characters: thirty }))]);

    expect(screen.getByText("30 / 30")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "เพิ่มตัวละคร" })).not.toBeInTheDocument();
  });

  it("asks ออกโดยไม่บันทึก? before another tab; no keeps the hash and the typing, and asks once", async () => {
    const user = await open(`#/stories/${ID}`, [get(PATH, storyOf({}))]);
    confirmMock.mockReturnValue(false);

    await user.type(title(), " ภาค 2");
    await user.click(within(screen.getByRole("navigation", { name: "แถบ tab" })).getByRole("link", { name: "สปอย" }));
    await hashSettles();

    expect(confirmMock).toHaveBeenCalledTimes(1);
    expect(confirmMock).toHaveBeenCalledWith("ออกโดยไม่บันทึก?");
    expect(window.location.hash).toBe(`#/stories/${ID}`);
    expect(title()).toHaveValue("ยอดนักสืบจิ๋วโคนัน ภาค 2");
  });

  it("leaves when ออกโดยไม่บันทึก? is answered yes", async () => {
    const user = await open(`#/stories/${ID}`, [get(PATH, storyOf({}))]);
    confirmMock.mockReturnValue(true);

    await user.type(title(), " ภาค 2");
    await user.click(screen.getByRole("link", { name: "กลับ" }));

    expect(await screen.findByText("ยังไม่มีเรื่องในคลังความรู้")).toBeInTheDocument();
    expect(window.location.hash).toBe("#/stories");
  });

  it("lets the browser ask before the tab closes with unsaved typing, and not without", async () => {
    const user = await open(`#/stories/${ID}`, [get(PATH, storyOf({}))]);
    const close = () => {
      const event = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(event);
      return event.defaultPrevented;
    };

    expect(close()).toBe(false);
    await user.type(title(), "!");
    expect(close()).toBe(true);
  });

  it("asks before deleting a Story two clips use, then deletes it and opens the list", async () => {
    const user = await open(`#/stories/${ID}`, [get(PATH, storyOf({ clips: 2 })), send("DELETE", PATH, null, 204)]);

    await user.click(screen.getByRole("button", { name: "ลบเรื่อง" }));
    const dialog = screen.getByRole("dialog", { name: "ลบ ยอดนักสืบจิ๋วโคนัน?" });
    expect(within(dialog).getByText("ใช้อยู่ 2 คลิป คลิปเหล่านั้นจะเป็น ไม่ใช้")).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "ยกเลิก" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "ลบ" }));

    await waitFor(() => expect(window.location.hash).toBe("#/stories"));
    expect(sent(fetchMock, "DELETE", PATH)).toHaveLength(1);
    expect(confirmMock).not.toHaveBeenCalled();
  });

  it("leaves the used line out of the ask when no clip uses the Story", async () => {
    const user = await open(`#/stories/${ID}`, [get(PATH, storyOf({}))]);

    await user.click(screen.getByRole("button", { name: "ลบเรื่อง" }));

    expect(within(screen.getByRole("dialog")).queryByText(/ใช้อยู่/)).not.toBeInTheDocument();
  });

  it("says ไม่พบเรื่องนี้ with a link back when the Story is gone", async () => {
    serve(fetchMock, [send("GET", PATH, { code: "not_found", message: "not found" }, 404)]);
    window.location.hash = `#/stories/${ID}`;
    render(<App />);

    expect(await screen.findByText("ไม่พบเรื่องนี้")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "กลับคลังความรู้" })).toHaveAttribute("href", "#/stories");
  });
});
