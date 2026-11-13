import { useCallback, useEffect, useRef } from "react";
import { useMountedState } from "../../../lib/useMountedState";
import { fetchSounds, type Sound } from "../../sound-library/lib/sounds";

/**
 * The sound library's sounds for ตรวจแก้บท's background sound: read when the page opens (coming
 * back from คลังเสียง opens it again) and when the browser tab comes back, since a sound may be
 * imported or deleted meanwhile (sound-library spec › Frontend). `sounds` is null until read, and
 * `unreadable` while the library can't be read: the picker then shows only the draft's choice.
 */
export function useLibrarySounds() {
  const [sounds, , setIfMounted] = useMountedState<Sound[] | null>(null);
  const [unreadable, , setUnreadableIfMounted] = useMountedState(false);
  const latest = useRef(0); // reads overlap: only the newest one's answer counts

  const reload = useCallback(async () => {
    const read = ++latest.current;
    const answer = await fetchSounds().catch(() => null);
    if (read !== latest.current) return;
    setIfMounted(answer);
    setUnreadableIfMounted(answer === null);
  }, [setIfMounted, setUnreadableIfMounted]);

  useEffect(() => {
    void reload();
    const onVisible = () => {
      if (document.visibilityState === "visible") void reload();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [reload]);

  return { sounds, unreadable, reload };
}
