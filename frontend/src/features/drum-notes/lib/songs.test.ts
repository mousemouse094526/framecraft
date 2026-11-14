import { describe, expect, it } from "vitest";
import { pickableFrom, pickedText, pickingOf, pickText, rangeFault, type FoundBar, type PickJob, type SongRow } from "./songs";

const job = (change: Partial<PickJob> = {}): PickJob => ({ song_id: "a", state: "picking", percent: 40, error: null, message: null, rows: null, fix: null, cancel_requested: false, started_at: "", ...change });
const row = (change: Partial<SongRow> = {}): SongRow => ({ id: "a", title: "A", subtitle: "", source_kind: "link", duration_s: 60, analysis: null, lessons: 0, updated_at: "", ...change });
const bar = (start_s: number, end_s: number, four_four = true): FoundBar => ({ n: 1, start_s, end_s, beats: four_four ? 4 : 3, hits: 0, four_four });

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

describe("pickableFrom", () => {
  it("counts the 4/4 bars in a row from the one picked, up to four", () => {
    const bars = [bar(0, 2), bar(2, 4), bar(4, 6), bar(6, 8), bar(8, 10), bar(10, 12, false), bar(12, 14)];
    expect(pickableFrom(bars, 0)).toBe(4);
    expect(pickableFrom(bars, 2)).toBe(3);
    expect(pickableFrom(bars, 5)).toBe(0);
    expect(pickableFrom(bars, 6)).toBe(1);
    expect(pickableFrom([], 0)).toBe(0);
  });
});
