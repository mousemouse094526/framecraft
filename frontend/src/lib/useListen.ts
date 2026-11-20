import { useCallback, useEffect, useId, useRef } from "react";
import type { BlobReply } from "./api";
import { release, startCount, toggle, usePlayer, type PlayStatus } from "./player";
import { OFFLINE, refusedOf, type Refused } from "./refused";
import { useMountedState } from "./useMountedState";

export type ListenState =
  | { kind: "idle" }
  /** From the press until the wav plays: whatever comes before the request, then the backend's mix. */
  | { kind: "mixing" }
  /** The API refused the mix, or there is no backend. */
  | ({ kind: "refused" } & Refused);

type Inputs = {
  /** The form holds edits not saved yet: the wav stops, and the next press saves and mixes again. The
   * saved values change no other way while the form is open (a re-pick opens a new form), so the
   * wav is the saved reel's until then (audio-player D14). */
  unsaved: boolean;
  disabled?: boolean;
};

/**
 * A play button whose wav the backend mixes: `request` asks for it (ฟังจังหวะ saves the lesson
 * first and answers null when that failed, which plays nothing; reel cover's ฟัง reel saves the
 * cover first). The wav is kept, so pressing again with nothing changed pauses and plays on
 * through the one player; an edit stops it, and the next press mixes again (audio-player D7, D14,
 * ADR 0074). reel กลอง and the reel cover page share it.
 */
export function useListen(request: () => Promise<BlobReply | null>, { unsaved, disabled = false }: Inputs) {
  const owner = useId();
  const [state, , setIfMounted] = useMountedState<ListenState>({ kind: "idle" });
  const mixed = useRef<string | null>(null);
  const alive = useRef(false);
  const latestUnsaved = useRef(unsaved);
  useEffect(() => {
    latestUnsaved.current = unsaved;
  });
  const sound = usePlayer(owner);

  const drop = useCallback(() => {
    release(owner);
    if (mixed.current) URL.revokeObjectURL(mixed.current);
    mixed.current = null;
  }, [owner]);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      drop();
    };
  }, [drop]);

  const mixing = useRef(false);
  /** An edit came while the mix ran: what comes back is the old form's (D15). */
  const editedWhileMixing = useRef(false);

  // An edit or a button that can't be pressed: the wav is no longer this reel's.
  useEffect(() => {
    if (unsaved && mixing.current) editedWhileMixing.current = true;
    if (unsaved || disabled) drop();
  }, [unsaved, disabled, drop]);

  const press = useCallback(async () => {
    if (mixing.current) return;
    const wav = mixed.current;
    if (wav && !latestUnsaved.current) {
      toggle(owner, wav);
      return;
    }
    drop();
    mixing.current = true;
    editedWhileMixing.current = false;
    setIfMounted({ kind: "mixing" });
    const started = startCount();
    try {
      const reply = await request();
      if (reply === null) {
        // The caller says why (a save that failed shows under บันทึก).
        setIfMounted({ kind: "idle" });
        return;
      }
      if (reply.status === 200 && reply.blob) {
        setIfMounted({ kind: "idle" });
        // Gone, or edited while it mixed: the wav isn't the form's any more (D14, D15).
        if (!alive.current || editedWhileMixing.current) return;
        const url = URL.createObjectURL(reply.blob);
        mixed.current = url;
        // Another sound began while it mixed: that one is what the user wants now; this wav waits
        // for the next press (D15).
        if (startCount() === started) toggle(owner, url);
        return;
      }
      setIfMounted({ kind: "refused", ...(await refusedOf(reply.body)) });
    } catch {
      setIfMounted({ kind: "refused", ...OFFLINE });
    } finally {
      mixing.current = false;
    }
  }, [owner, request, drop, setIfMounted]);

  const mine = sound !== null && mixed.current !== null && sound.src === mixed.current ? sound : null;
  const status: PlayStatus = state.kind === "mixing" ? "mixing" : (mine?.status ?? "ready");
  return { state, status, position: mine?.position ?? 0, duration: mine?.duration ?? null, press };
}
