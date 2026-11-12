import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT } from "../../../lib/api";
import { get, send, serve } from "../../../testing/testBackend";
import { JOB_PATH, type ToonJob } from "../lib/series";
import { cancelToonJob, useToonJobPoll } from "./useToonJobPoll";

const fetchMock = vi.fn<typeof fetch>();

function jobOf(change: Partial<ToonJob> = {}): ToonJob {
  return { kind: "ref", state: "drawing", series_id: "s_1", ep_id: null, item_id: "c_01", done: 0, total: 3, error: null, cancel_requested: false, ...change };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.useFakeTimers();
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function poll(job: ToonJob | null) {
  const calls = { running: vi.fn(), end: vi.fn(), fail: vi.fn() };
  renderHook(() => useToonJobPoll(job, calls.running, calls.end, calls.fail));
  return calls;
}

test("a running answer goes to onRunning, the job's end to onEnd", async () => {
  serve(fetchMock, [get(JOB_PATH, jobOf({ done: 1 })), get(JOB_PATH, jobOf({ state: "done", done: 3 }))]);
  const calls = poll(jobOf());

  await act(() => vi.advanceTimersByTimeAsync(1100));
  expect(calls.running).toHaveBeenCalledWith(jobOf({ done: 1 }));
  await act(() => vi.advanceTimersByTimeAsync(1100));

  expect(calls.end).toHaveBeenCalledWith(jobOf({ state: "done", done: 3 }));
  expect(calls.fail).not.toHaveBeenCalled();
});

test("no job at all is the end; a failed poll goes to onFail", async () => {
  serve(fetchMock, [get(JOB_PATH, null)]);
  const ended = poll(jobOf());
  await act(() => vi.advanceTimersByTimeAsync(1100));
  expect(ended.end).toHaveBeenCalledWith(null);

  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
  const failed = poll(jobOf());
  await act(() => vi.advanceTimersByTimeAsync(1100));
  expect(failed.fail).toHaveBeenCalled();
});

test("a job that isn't running is not polled", async () => {
  poll(jobOf({ state: "done" }));
  poll(null);

  await act(() => vi.advanceTimersByTimeAsync(3000));

  expect(fetchMock).not.toHaveBeenCalled();
});

test("หยุด gives the job asking to stop, or the notice of a stop that didn't happen", async () => {
  const stopping = jobOf({ cancel_requested: true });
  serve(fetchMock, [send("DELETE", JOB_PATH, stopping, 202), send("DELETE", JOB_PATH, { code: "busy", message: "หยุดไม่ได้แล้ว" }, 409)]);
  const onCancelling = vi.fn();
  const onRefused = vi.fn();

  await cancelToonJob(onCancelling, onRefused);
  expect(onCancelling).toHaveBeenCalledWith(stopping);
  await cancelToonJob(onCancelling, onRefused);
  expect(onRefused).toHaveBeenCalledWith({ tone: "error", title: "หยุดงานไม่ได้", text: "หยุดไม่ได้แล้ว", setupLink: false });

  // The job ended before the cancel came: the next poll shows how, nothing to say.
  serve(fetchMock, [send("DELETE", JOB_PATH, { code: "not_found", message: "ไม่มีงานที่ทำอยู่" }, 404)]);
  await cancelToonJob(onCancelling, onRefused);
  expect(onRefused).toHaveBeenCalledTimes(1);

  fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
  await cancelToonJob(onCancelling, onRefused);
  expect(onRefused).toHaveBeenLastCalledWith({ tone: "error", title: "หยุดงานไม่ได้", text: OFFLINE_TEXT, setupLink: false });
});
