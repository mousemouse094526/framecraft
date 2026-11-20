import { useEffect, useId, useSyncExternalStore } from "react";

/** The sound the app plays now: the one at a time (audio-player D1, ADR 0071). */
export type Sound = {
  /** The button that started it (its `useId`): two buttons on one file are two sounds. */
  owner: string;
  src: string;
  status: "playing" | "paused";
  /** Seconds played. */
  position: number;
  /** Seconds in all, or null until the file says (or when it can't: a stream). */
  duration: number | null;
};

let audio: HTMLAudioElement | null = null;
let current: Sound | null = null;
// Every start, pause and release takes a new round, so the answer of an older `play()` and the
// events of an older file can't change the sound that plays now (D13).
let round = 0;
const listeners = new Set<() => void>();

function set(next: Sound | null) {
  current = next;
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function snapshot() {
  return current;
}

function lengthOf(seconds: number): number | null {
  return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
}

function element(): HTMLAudioElement {
  if (audio) return audio;
  const made = new Audio();
  const update = () => {
    if (current && audio === made) set({ ...current, position: made.currentTime, duration: lengthOf(made.duration) ?? current.duration });
  };
  made.addEventListener("timeupdate", update);
  made.addEventListener("durationchange", update);
  made.addEventListener("loadedmetadata", update);
  // A file that ends or can't be read only means no sound: the button is ready again (D2, D9).
  const done = () => {
    if (audio === made) set(null);
  };
  made.addEventListener("ended", done);
  made.addEventListener("error", done);
  audio = made;
  return made;
}

function start(el: HTMLAudioElement, next: Sound) {
  const mine = ++round;
  set(next);
  const failed = (error: unknown) => {
    // A `pause()` or a new `src` before it began rejects with AbortError: the newer press wins (D13).
    if (round !== mine || (error instanceof DOMException && error.name === "AbortError")) return;
    set(null);
  };
  try {
    void el.play()?.catch(failed);
  } catch (error) {
    failed(error);
  }
}

/**
 * The press of a play button: its own sound playing pauses, paused plays on from there; any other
 * sound stops first and this one plays from the start (D1, D2).
 */
export function toggle(owner: string, src: string) {
  const el = element();
  if (current && current.owner === owner && current.src === src) {
    if (current.status === "playing") {
      round++;
      el.pause();
      set({ ...current, status: "paused" });
    } else {
      start(el, { ...current, status: "playing" });
    }
    return;
  }
  round++;
  if (current?.status === "playing") el.pause();
  el.src = src;
  el.currentTime = 0;
  start(el, { owner, src, status: "playing", position: 0, duration: null });
}

/** Stops the sound if it is `owner`'s: its button went away, changed file or can't be pressed (D6). */
export function release(owner: string) {
  if (current?.owner !== owner) return;
  round++;
  if (current.status === "playing") audio?.pause();
  set(null);
}

/** The sound when it is `owner`'s, else null. */
export function usePlayer(owner: string): Sound | null {
  const sound = useSyncExternalStore(subscribe, snapshot);
  return sound?.owner === owner ? sound : null;
}

export type PlayStatus = "ready" | "mixing" | Sound["status"];

/**
 * One play button's sound: `src` null means nothing to play yet. Stops when the button unmounts,
 * `src` changes, or `disabled` turns on (D6, D13).
 */
export function useSound(src: string | null, disabled = false) {
  const owner = useId();
  const sound = usePlayer(owner);
  const mine = sound !== null && sound.src === src ? sound : null;

  useEffect(() => () => release(owner), [owner, src]);
  useEffect(() => {
    if (disabled) release(owner);
  }, [owner, disabled]);

  return {
    status: (mine?.status ?? "ready") as PlayStatus,
    position: mine?.position ?? 0,
    duration: mine?.duration ?? null,
    toggle: () => {
      if (src !== null) toggle(owner, src);
    },
  };
}

/** Test only: no sound, no element, as when the app opens. */
export function resetPlayerForTests() {
  audio = null;
  current = null;
  round = 0;
}
