import { useEffect, useRef } from "react";
import { getJson } from "./api";

const POLL_MS = 1000;

/**
 * GETs `path` every second while `active` (spoil D6, D24); each answer goes to
 * `onAnswer`, a failure to `onFail` and the polling stops. Every job (a download,
 * a Transcribe job, a Voice job…) runs its own, apart from the others. The callbacks may
 * change between renders; the latest ones are called.
 */
export function usePollWhile<T>(active: boolean, path: string, onAnswer: (answer: T) => void, onFail: () => void) {
  const callbacks = useRef({ onAnswer, onFail });
  useEffect(() => {
    callbacks.current = { onAnswer, onFail };
  });

  useEffect(() => {
    if (!active) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const answer = await getJson<T>(path);
        if (stopped) return;
        callbacks.current.onAnswer(answer);
        // Once the job ends `active` flips and the cleanup clears this timer.
        timer = setTimeout(poll, POLL_MS);
      } catch {
        if (!stopped) callbacks.current.onFail();
      }
    };
    timer = setTimeout(poll, POLL_MS);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [active, path]);
}
