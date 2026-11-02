import { useCallback, useEffect, useRef, useState } from "react";

const IDLE_MS = 800; // spoil-maker spec › Frontend

/**
 * A text field that saves itself: 800 ms after the last key, or at once on blur
 * (`flush`), one request at a time; text typed while one is out goes in the next.
 * `saved` is the server's text: it replaces the field whenever nothing is unsaved.
 * `save` resolves to false when it was refused, and the field keeps what was typed.
 */
export function useAutoSave(saved: string, save: (text: string) => Promise<boolean>) {
  const [value, setValue] = useState(saved);
  const sent = useRef(saved); // the text the server has, or is being sent
  const busy = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const latest = useRef({ value, save });
  latest.current = { value, save };

  // A newer text from the server (a save's answer, a reload) shows unless the user is mid-edit.
  // `sent` follows the server even mid-edit, so the next flush compares against what it has.
  useEffect(() => {
    if (saved === sent.current) return; // nothing new: never undo a key typed before effects ran
    if (!busy.current && latest.current.value === sent.current) setValue(saved);
    sent.current = saved;
  }, [saved]);

  const flush = useCallback(async () => {
    clearTimeout(timer.current);
    if (busy.current) return;
    const text = latest.current.value;
    if (text === sent.current) return;
    busy.current = true;
    const previous = sent.current;
    sent.current = text;
    const ok = await latest.current.save(text);
    if (!ok) sent.current = previous;
    busy.current = false;
    // Typed while it was out: send that too.
    if (ok && latest.current.value !== sent.current) void flush();
  }, []);

  const change = useCallback(
    (text: string) => {
      setValue(text);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => void flush(), IDLE_MS);
    },
    [flush],
  );

  useEffect(() => () => clearTimeout(timer.current), []);

  return { value, change, flush };
}
