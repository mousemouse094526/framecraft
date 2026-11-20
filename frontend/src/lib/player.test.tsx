import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { SoundButton } from "../components/ui/PlayButton";

function stubAudio(play: () => Promise<void> = () => Promise.resolve()) {
  const calls: string[] = [];
  const playSpy = vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(function (this: HTMLMediaElement) {
    calls.push(`play ${this.getAttribute("src")}`);
    return play();
  });
  const pause = vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(function (this: HTMLMediaElement) {
    calls.push(`pause ${this.getAttribute("src")}`);
  });
  return { calls, play: playSpy, pause };
}

function twoSounds() {
  return render(
    <>
      <SoundButton src="/a.wav" label="A" className="" />
      <SoundButton src="/b.wav" label="B" className="" />
    </>,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

test("starting B pauses A before B plays: one sound at a time", async () => {
  const { calls } = stubAudio();
  const user = userEvent.setup();
  twoSounds();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  await user.click(screen.getByRole("button", { name: "ฟัง B" }));

  expect(calls).toEqual(["play /a.wav", "pause /a.wav", "play /b.wav"]);
  expect(screen.getByRole("button", { name: "ฟัง A" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว B" })).toBeInTheDocument();
});

test("pressing the same button pauses, and again plays on from where it was", async () => {
  const { play, pause } = stubAudio();
  const user = userEvent.setup();
  twoSounds();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  const element = play.mock.contexts[0] as HTMLAudioElement;
  element.currentTime = 4;
  await user.click(screen.getByRole("button", { name: "หยุดชั่วคราว A" }));
  expect(pause).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "ฟัง A" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  expect(play).toHaveBeenCalledTimes(2);
  expect(element.currentTime).toBe(4);
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).toBeInTheDocument();
});

test("A again after B starts from the beginning", async () => {
  const { play } = stubAudio();
  const user = userEvent.setup();
  twoSounds();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  const element = play.mock.contexts[0] as HTMLAudioElement;
  element.currentTime = 4;
  await user.click(screen.getByRole("button", { name: "ฟัง B" }));
  element.currentTime = 2;
  await user.click(screen.getByRole("button", { name: "ฟัง A" }));

  expect(element.getAttribute("src")).toBe("/a.wav");
  expect(element.currentTime).toBe(0);
});

test("the end of the file, or a play() refused, makes the button ready again with no message", async () => {
  const refuse = { now: false };
  const { play } = stubAudio(() => (refuse.now ? Promise.reject(new DOMException("blocked", "NotAllowedError")) : Promise.resolve()));
  const user = userEvent.setup();
  twoSounds();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  (play.mock.contexts[0] as HTMLAudioElement).dispatchEvent(new Event("ended"));
  expect(await screen.findByRole("button", { name: "ฟัง A" })).toBeInTheDocument();

  refuse.now = true;
  await user.click(screen.getByRole("button", { name: "ฟัง B" }));
  expect(await screen.findByRole("button", { name: "ฟัง B" })).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("A's play() aborted by the press on B leaves B playing", async () => {
  let rejectA: (error: unknown) => void = () => {};
  let first = true;
  stubAudio(() => {
    if (!first) return Promise.resolve();
    first = false;
    return new Promise((_, reject) => (rejectA = reject));
  });
  const user = userEvent.setup();
  twoSounds();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  await user.click(screen.getByRole("button", { name: "ฟัง B" }));
  rejectA(new DOMException("interrupted", "AbortError"));
  await Promise.resolve();

  expect(screen.getByRole("button", { name: "หยุดชั่วคราว B" })).toBeInTheDocument();
});

test("the sound stops when its button goes, gets another file, or can't be pressed", async () => {
  const { calls } = stubAudio();
  const user = userEvent.setup();
  const view = render(<SoundButton src="/a.wav" label="A" className="" />);

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  view.rerender(<SoundButton src="/a2.wav" label="A" className="" />);
  expect(calls.at(-1)).toBe("pause /a.wav");
  expect(screen.getByRole("button", { name: "ฟัง A" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  view.rerender(<SoundButton src="/a2.wav" label="A" disabled className="" />);
  expect(calls.at(-1)).toBe("pause /a2.wav");
  expect(calls.filter((call) => call.startsWith("pause"))).toHaveLength(2);

  view.rerender(<SoundButton src="/a2.wav" label="A" className="" />);
  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  view.unmount();
  expect(calls.at(-1)).toBe("pause /a2.wav");
});

test("the button is named by what a press does, with a visible word when it has one", async () => {
  stubAudio();
  const user = userEvent.setup();
  render(<SoundButton src="/a.wav" label="จังหวะ" text="ฟังจังหวะ" className="" />);

  expect(screen.getByRole("button", { name: "ฟังจังหวะ" })).toHaveTextContent("ฟังจังหวะ");
  await user.click(screen.getByRole("button", { name: "ฟังจังหวะ" }));
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว ฟังจังหวะ" })).not.toHaveAttribute("aria-pressed");
});

function stubDuration(element: HTMLMediaElement, seconds: number) {
  Object.defineProperty(element, "duration", { configurable: true, value: seconds });
}

test("the button shows the time played and the length; the length waits until it is known", async () => {
  const { play } = stubAudio();
  const user = userEvent.setup();
  render(<SoundButton src="/a.wav" label="A" className="" />);
  expect(screen.getByRole("button", { name: "ฟัง A" })).toHaveTextContent(/^$/);

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  const element = play.mock.contexts[0] as HTMLAudioElement;
  element.currentTime = 3.7;
  act(() => void element.dispatchEvent(new Event("timeupdate")));
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).toHaveTextContent("0:03");
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).not.toHaveTextContent("/");

  stubDuration(element, 12);
  act(() => void element.dispatchEvent(new Event("durationchange")));
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).toHaveTextContent("0:03 / 0:12");

  await user.click(screen.getByRole("button", { name: "หยุดชั่วคราว A" }));
  expect(screen.getByRole("button", { name: "ฟัง A" })).toHaveTextContent("0:03 / 0:12");
});

test("a stream with no length (Infinity) shows the time played alone", async () => {
  const { play } = stubAudio();
  const user = userEvent.setup();
  render(<SoundButton src="/a.wav" label="A" className="" />);

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  const element = play.mock.contexts[0] as HTMLAudioElement;
  stubDuration(element, Infinity);
  element.currentTime = 65;
  act(() => void element.dispatchEvent(new Event("timeupdate")));

  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).toHaveTextContent(/^1:05$/);
});

test("a video in the page that starts with sound pauses the player; a muted one doesn't", async () => {
  stubAudio();
  const user = userEvent.setup();
  const { container } = render(
    <>
      <SoundButton src="/a.wav" label="A" className="" />
      <video data-testid="muted" muted />
      <video data-testid="loud" />
    </>,
  );
  const [muted, loud] = container.querySelectorAll("video");

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  act(() => void muted.dispatchEvent(new Event("play")));
  expect(screen.getByRole("button", { name: "หยุดชั่วคราว A" })).toBeInTheDocument();

  act(() => void loud.dispatchEvent(new Event("play")));
  expect(screen.getByRole("button", { name: "ฟัง A" })).toBeInTheDocument();
});

test("the player starting pauses a video playing with sound; one video starting pauses another", async () => {
  const { calls } = stubAudio();
  const user = userEvent.setup();
  const { container } = render(
    <>
      <SoundButton src="/a.wav" label="A" className="" />
      <video src="/one.mp4" />
      <video src="/two.mp4" />
    </>,
  );
  const [one, two] = container.querySelectorAll("video");
  Object.defineProperty(one, "paused", { configurable: true, value: false });

  await user.click(screen.getByRole("button", { name: "ฟัง A" }));
  expect(calls).toEqual(["pause /one.mp4", "play /a.wav"]);

  Object.defineProperty(two, "paused", { configurable: true, value: false });
  act(() => void one.dispatchEvent(new Event("play")));
  expect(calls.slice(2)).toEqual(["pause /two.mp4", "pause /a.wav"]);
});
