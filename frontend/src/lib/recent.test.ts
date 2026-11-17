import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { forgetRecent, rememberRecent, useRecent } from "./recent";

const KEY = "framecraft.nav.recent";
const stored = () => JSON.parse(window.localStorage.getItem(KEY) ?? "null");

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("ล่าสุด (ui-nav D5, D10, D11)", () => {
  it("keeps the 3 newest per topic, newest first, with no repeats and the latest name", () => {
    for (const id of ["s_1", "s_2", "s_3", "s_4"]) rememberRecent("songs", `#/songs/${id}`, `เพลง ${id}`);
    expect(stored().songs.map((item: { hash: string }) => item.hash)).toEqual(["#/songs/s_4", "#/songs/s_3", "#/songs/s_2"]);

    rememberRecent("songs", "#/songs/s_2", "ชื่อใหม่");

    expect(stored().songs).toEqual([
      { hash: "#/songs/s_2", label: "ชื่อใหม่" },
      { hash: "#/songs/s_4", label: "เพลง s_4" },
      { hash: "#/songs/s_3", label: "เพลง s_3" },
    ]);
  });

  it("cuts a name at 80 characters and refuses a hash of the wrong shape or an empty name", () => {
    rememberRecent("drums", "#/drums/a1b2c3d4e5f6", "ก".repeat(200));
    rememberRecent("drums", "#/drums/../setup", "แปลก");
    rememberRecent("songs", "#/toon/series/s_1", "ผิดหัวข้อ");
    rememberRecent("songs", "#/songs/s_1", "   ");
    rememberRecent("songs", "#/songs/s_2", `${"ก".repeat(79)}🥁🥁`);

    expect(stored()).toEqual({ toon: [], drums: [{ hash: "#/drums/a1b2c3d4e5f6", label: "ก".repeat(80) }], songs: [{ hash: "#/songs/s_2", label: `${"ก".repeat(79)}🥁` }] });
  });

  it("forgets a Series together with its EPs, and leaves the rest", () => {
    rememberRecent("toon", "#/toon/series/s_2", "อีกชุด");
    rememberRecent("toon", "#/toon/series/s_1", "รุ่นพี่เล่าว่า…");
    rememberRecent("toon", "#/toon/eps/e_1", "รุ่นพี่เล่าว่า… · EP01", "#/toon/series/s_1");

    forgetRecent("#/toon/series/s_1");

    expect(stored().toon).toEqual([{ hash: "#/toon/series/s_2", label: "อีกชุด" }]);
  });

  it("reads broken or tampered storage as no recent items", () => {
    window.localStorage.setItem(KEY, "{not json");
    expect(renderHook(() => useRecent()).result.current).toEqual({ toon: [], drums: [], songs: [] });

    window.localStorage.setItem(
      KEY,
      JSON.stringify({ toon: [{ hash: "javascript:alert(1)", label: "x" }, { hash: "#/toon/eps/e_1", label: 5 }], songs: "nope", drums: [{ hash: "#/drums/a1b2c3d4e5f6", label: "ok", parent: "#/x" }] }),
    );
    expect(renderHook(() => useRecent()).result.current).toEqual({ toon: [], drums: [{ hash: "#/drums/a1b2c3d4e5f6", label: "ok" }], songs: [] });
  });

  it("does without storage that throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });

    expect(() => rememberRecent("songs", "#/songs/s_1", "เพลง")).not.toThrow();
    expect(renderHook(() => useRecent()).result.current.songs).toEqual([]);
  });

  it("follows a change from this tab and from another one", () => {
    const { result } = renderHook(() => useRecent());

    act(() => rememberRecent("songs", "#/songs/s_1", "เพลง"));
    expect(result.current.songs).toEqual([{ hash: "#/songs/s_1", label: "เพลง" }]);

    act(() => {
      window.localStorage.setItem(KEY, JSON.stringify({ songs: [{ hash: "#/songs/s_9", label: "จากอีกแท็บ" }] }));
      window.dispatchEvent(new StorageEvent("storage", { key: KEY }));
    });
    expect(result.current.songs).toEqual([{ hash: "#/songs/s_9", label: "จากอีกแท็บ" }]);
  });
});
