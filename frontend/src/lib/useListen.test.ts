import { act, renderHook, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, expect, test, vi } from "vitest";
import { OFFLINE_TEXT, type BlobReply } from "./api";
import { toggle } from "./player";
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

function hookOf(reply: () => Promise<BlobReply | null>, inputs = { unsaved: false }, strict = false) {
  const request = vi.fn(reply);
  const hook = renderHook((props: { unsaved: boolean }) => useListen(request, props), { initialProps: inputs, wrapper: strict ? StrictMode : undefined });
  return {
    request,
    state: () => hook.result.current.state,
    status: () => hook.result.current.status,
    listen: () => act(() => hook.result.current.press()),
    press: () => hook.result.current.press(),
    rerender: hook.rerender,
    unmount: hook.unmount,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test("a wav plays from a blob URL through the one player and the state is idle again", async () => {
  const { play } = stubAudio();
  const { state, listen } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();

  await waitFor(() => expect(play).toHaveBeenCalledTimes(1));
  expect((play.mock.contexts[0] as HTMLAudioElement).getAttribute("src")).toBe("blob:wav-1");
  expect(state()).toEqual({ kind: "idle" });
});

test("pressing again with nothing changed pauses, then plays on: one mix", async () => {
  const { play, pause } = stubAudio();
  const { request, status, listen } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();
  expect(status()).toBe("playing");
  await listen();
  expect(status()).toBe("paused");
  expect(pause).toHaveBeenCalled();
  await listen();

  expect(request).toHaveBeenCalledTimes(1);
  expect(play).toHaveBeenCalledTimes(2);
  expect(status()).toBe("playing");
});

test("an edit while it plays stops it; once saved, the next press mixes again and frees the old URL", async () => {
  const { play, revokeObjectURL } = stubAudio();
  const { request, status, listen, rerender } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();
  rerender({ unsaved: true });
  expect(status()).toBe("ready");
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-1");

  rerender({ unsaved: false });
  await listen();
  expect(request).toHaveBeenCalledTimes(2);
  expect((play.mock.contexts[1] as HTMLAudioElement).getAttribute("src")).toBe("blob:wav-2");
});

test("unmounting stops the wav and frees its URL", async () => {
  const { pause, revokeObjectURL } = stubAudio();
  const { listen, unmount } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }));

  await listen();
  const pauses = pause.mock.calls.length;
  unmount();

  expect(pause.mock.calls.length).toBe(pauses + 1);
  expect(revokeObjectURL).toHaveBeenCalledWith("blob:wav-1");
});

test("under StrictMode's second mount the wav still plays", async () => {
  const { play } = stubAudio();
  const { status, listen } = hookOf(() => Promise.resolve({ status: 200, blob: WAV, body: null }), undefined, true);

  await listen();

  expect(play).toHaveBeenCalledTimes(1);
  expect(status()).toBe("playing");
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
  expect(refused.state()).toEqual({ kind: "refused", tone: "error", text: "คลิปยาวเกิน 90 วินาที", fixes: [], field: null });

  const notReady = hookOf(() => Promise.resolve({ status: 503, blob: null, body: { code: "not_ready", message: "ยังไม่พร้อม", rows: ["drum_kit"] } }));
  await notReady.listen();
  await waitFor(() => expect(notReady.state()).toEqual({ kind: "refused", tone: "error", text: "ยังไม่พร้อม", fixes: ["./setup.sh"], field: null }));
});

test("a reply with no refusal in it, or a request that throws, reads as offline", async () => {
  stubAudio();
  const empty = hookOf(() => Promise.resolve({ status: 500, blob: null, body: null }));
  await empty.listen();
  expect(empty.state()).toEqual({ kind: "refused", tone: "error", text: OFFLINE_TEXT, fixes: [], field: null });

  const thrown = hookOf(() => Promise.reject(new Error("network")));
  await thrown.listen();
  expect(thrown.state()).toEqual({ kind: "refused", tone: "error", text: OFFLINE_TEXT, fixes: [], field: null });
});

test("a mix that comes back after an edit, or after another sound began, doesn't play; a second press while mixing sends nothing", async () => {
  const { play } = stubAudio();
  let answer: (reply: BlobReply) => void = () => {};
  const edited = hookOf(() => new Promise((resolve) => (answer = resolve)));

  let first: Promise<void> = Promise.resolve();
  act(() => void (first = edited.press()));
  act(() => void edited.press());
  edited.rerender({ unsaved: true });
  await act(async () => answer({ status: 200, blob: WAV, body: null }));
  await act(() => first);
  expect(edited.request).toHaveBeenCalledTimes(1);
  expect(play).not.toHaveBeenCalled();
  expect(edited.status()).toBe("ready");

  const other = hookOf(() => new Promise((resolve) => (answer = resolve)));
  let pressed: Promise<void> = Promise.resolve();
  act(() => void (pressed = other.press()));
  act(() => toggle("someone-else", "/rain.mp3"));
  await act(async () => answer({ status: 200, blob: WAV, body: null }));
  await act(() => pressed);
  expect(play.mock.contexts.map((element) => (element as HTMLAudioElement).getAttribute("src"))).toEqual(["/rain.mp3"]);
  expect(other.status()).toBe("ready");
});
