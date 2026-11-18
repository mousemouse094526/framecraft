import { describe, expect, it } from "vitest";
import { lateStart, pickedText, pickingOf, pickText, rangeFault, type PickJob, type Song, type SongRow } from "./songs";

const job = (change: Partial<PickJob> = {}): PickJob => ({ song_id: "a", state: "picking", percent: 40, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "", ...change });
const row = (change: Partial<SongRow> = {}): SongRow => ({ id: "a", title: "A", subtitle: "", source_kind: "link", duration_s: 60, analysis: null, updated_at: "", ...change });

describe("rangeFault", () => {
  it("accepts 4 to 90 seconds inside the song", () => {
    expect(rangeFault(0, 4, 60)).toBeNull();
    expect(rangeFault(10, 100, 120)).toBeNull();
    expect(rangeFault(0, 60, 60)).toBeNull();
  });

  it("names start_s before the song, end_s past it or for a length off 4–90, and either when not a number", () => {
    expect(rangeFault(-0.1, 10, 60)).toBe("start_s");
    expect(rangeFault(0, 60.1, 60)).toBe("end_s");
    expect(rangeFault(0, 3.9, 60)).toBe("end_s");
    expect(rangeFault(0, 90.1, 120)).toBe("end_s");
    expect(rangeFault(NaN, 10, 60)).toBe("start_s");
    expect(rangeFault(0, NaN, 60)).toBe("end_s");
  });
});

describe("the Pick job", () => {
  it("is this song's while it runs, not another song's nor an ended one", () => {
    expect(pickingOf(job(), "a")).toEqual(job());
    expect(pickingOf(job({ state: "preparing" }), "a")).toEqual(job({ state: "preparing" }));
    expect(pickingOf(job({ song_id: "b" }), "a")).toBeNull();
    expect(pickingOf(job({ state: "done" }), "a")).toBeNull();
    expect(pickingOf(null, "a")).toBeNull();
  });

  it("reads as preparing the sound, then picking with its percent", () => {
    expect(pickText(job({ state: "preparing" }))).toBe("กำลังเตรียมเสียง…");
    expect(pickText(job({ percent: 35 }))).toBe("กำลังแกะโน้ต… 35%");
  });

  it("gives a row its percent while picked, its bars after, else not yet", () => {
    expect(pickedText(row(), job({ percent: 35 }))).toBe("กำลังแกะ 35%");
    expect(pickedText(row({ analysis: { mode: "drums", bars: 12 } }), job({ state: "done" }))).toBe("แกะแล้ว 12 ห้อง");
    expect(pickedText(row({ analysis: { mode: "drums", bars: 12 } }), job({ song_id: "b" }))).toBe("แกะแล้ว 12 ห้อง");
    expect(pickedText(row(), null)).toBe("ยังไม่แกะ");
  });
});

describe("lateStart (drum-cover D9, D19)", () => {
  const song = (hits: number[], duration_s = 60): Song => ({
    version: 1,
    id: "s",
    title: "t",
    subtitle: "",
    source: { kind: "file", url: null, name: "a.mp3", size: 1 },
    duration_s,
    range: { start_s: 0, end_s: 30, mode: "drums" },
    analysis: { mode: "drums", start_s: 0, end_s: 30, beats: [], downbeats: [0, 2, 4], hits: hits.map((t) => ({ t, piece: "snare", level: "normal" })), notes: null, picked_at: "" },
    bars: [
      { n: 1, start_s: 0, end_s: 2, beats: 4, hits: hits.filter((t) => t < 2).length, four_four: true },
      { n: 2, start_s: 2, end_s: 4, beats: 4, hits: hits.filter((t) => t >= 2 && t < 4).length, four_four: true },
    ],
    created_at: "",
    updated_at: "",
  });

  it("moves the range to the first bar with a hit, as long as before", () => {
    expect(lateStart(song([2.5]))).toEqual({ empty: 1, first_s: 2.5, range: { start_s: 2, end_s: 32, mode: "drums" } });
  });

  it("near the song's end keeps at least 4 s", () => {
    expect(lateStart(song([2.5], 5))?.range).toEqual({ start_s: 1, end_s: 5, mode: "drums" });
  });

  it("says nothing when bar 1 has a hit or none was found", () => {
    expect(lateStart(song([0.5, 2.5]))).toBeNull();
    expect(lateStart(song([]))).toBeNull();
  });
});
