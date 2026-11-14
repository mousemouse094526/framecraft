import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT, type BlobReply } from "./api";
import { useListen } from "./useListen";

const WAV = new Blob([new Uint8Array(4)], { type: "audio/wav" });

function stubAudio() {
  const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  const pause = vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  let made = 0;
  const createObjectURL = vi.fn(() => `blob:wav-${++made}`);
  const revokeObjectURL = vi.fn();
  vi.stubGlobal("URL", Object.assign(URL, { createObjectURL, revokeObjectURL }));
  return { play, pause, revokeObjectURL };
}

function hookOf(reply: () => Promise<BlobReply | null>) {
  const request = vi.fn(reply);
  const hook = renderHook(() => useListen(request));
  return { request, state: () => hook.result.current.state, listen: () => act(() => hook.result.current.listen()), unmount: hook.unmount };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test("a wav plays from a blob URL and the state is idle again", async () => {
  const { play } = stubAudio();
  const { state, listen } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();

  await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
  expect((play.mock.contexts[0] as HTMLAudioElement).src).toBe("blob:wav-1");
  expect(state()).toEqual({ kind: "idle" });
});

test("pressing again stops the wav playing and frees its URL before the next request; unmounting stops it too", async () => {
  const { play, pause, revokeObjectURL } = stubAudio();
  const { request, listen, unmount } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();
  await listen();

  expect(pause).toHaveBeenCalledTimes(1);
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-1");
  expect(request).toHaveBeenCalledTimes(2);
  expect((play.mock.contexts[1] as HTMLAudioElement).src).toBe("blob:wav-2");

  unmount();
  expect(pause).toHaveBeenCalledTimes(2);
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-2");
});

test("a request that answers null plays nothing and leaves the state idle: the caller says why", async () => {
  const { play } = stubAudio();
  const { state, listen } = hookOf(() => Promise.resolve(null));

  await listen();

  expect(play).not.toHaveBeenCalled();
  expect(state()).toEqual({ kind: "idle" });
});

test("a refusal shows its message; not_ready adds the fix commands of the rows it names", async () => {
  stubAudio();
  const fetchMock = vi.fn(async () => new Response(JSON.stringify({ items: [{ id: "drum_kit", fix: "./setup.sh", fix_kind: "command" }, { id: "ffmpeg", fix: "brew install ffmpeg", fix_kind: "command" }] }), { headers: { "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchMock);
  const refused = hookOf(() => Promise.resolve({ status: 422, blob: null, body: { code: "too_long", message: "คลิปยาวเกิน 90 วินาที" } }));
  await refused.listen();
  expect(refused.state()).toEqual({ kind: "refused", text: "คลิปยาวเกิน 90 วินาที", fixes: [] });

  const notReady = hookOf(() => Promise.resolve({ status: 503, blob: null, body: { code: "not_ready", message: "ยังไม่พร้อม", rows: ["drum_kit"] } }));
  await notReady.listen();
  await waitFor(() => expect(notReady.state()).toEqual({ kind: "refused", text: "ยังไม่พร้อม", fixes: ["./setup.sh"] }));
});

test("a reply with no refusal in it, or a request that throws, reads as offline", async () => {
  stubAudio();
  const empty = hookOf(() => Promise.resolve({ status: 500, blob: null, body: null }));
  await empty.listen();
  expect(empty.state()).toEqual({ kind: "refused", text: OFFLINE_TEXT, fixes: [] });

  const thrown = hookOf(() => Promise.reject(new Error("network")));
  await thrown.listen();
  expect(thrown.state()).toEqual({ kind: "refused", text: OFFLINE_TEXT, fixes: [] });
});
