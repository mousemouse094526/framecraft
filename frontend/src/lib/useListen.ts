import { useCallback, useEffect, useRef } from "react";
import { OFFLINE_TEXT, type BlobReply } from "./api";
import { refusalOf } from "./refusal";
import { fixesOf } from "./setupFixes";
import { useMountedState } from "./useMountedState";

export type ListenState =
  | { kind: "idle" }
  /** From the press until the wav plays: whatever comes before the request, then the backend's mix. */
  | { kind: "mixing" }
  /** `fixes`: the commands of the Status check rows a `not_ready` names (setup-status D26). */
  | { kind: "refused"; text: string; fixes: string[] };

/**
 * A ฟัง button that plays a wav the backend mixes: `request` asks for it (ฟังจังหวะ saves the lesson
 * first and answers null when that failed, which plays nothing; the song page's ฟัง posts the bars
 * picked, drum-notes D21). The wav plays from a blob URL; pressing again stops the one playing
 * before anything else (video-gen D8). The สอนกลอง and แกะเพลง tabs share it.
 */
export function useListen(request: () => Promise<BlobReply | null>) {
  const [state, , setIfMounted] = useMountedState<ListenState>({ kind: "idle" });
  const playing = useRef<{ audio: HTMLAudioElement; url: string } | null>(null);

  const stop = useCallback(() => {
    if (!playing.current) return;
    playing.current.audio.pause();
    URL.revokeObjectURL(playing.current.url);
    playing.current = null;
  }, []);

  useEffect(() => stop, [stop]);

  const listen = useCallback(async () => {
    stop();
    setIfMounted({ kind: "mixing" });
    try {
      const reply = await request();
      if (reply === null) {
        // The caller says why (a save that failed shows under บันทึก).
        setIfMounted({ kind: "idle" });
        return;
      }
      if (reply.status === 200 && reply.blob) {
        const url = URL.createObjectURL(reply.blob);
        const audio = new Audio(url);
        playing.current = { audio, url };
        // A blocked autoplay only means no sound: nothing to show for it.
        void audio.play().catch(() => {});
        setIfMounted({ kind: "idle" });
        return;
      }
      const refusal = refusalOf(reply.body);
      if (!refusal) return setIfMounted({ kind: "refused", text: OFFLINE_TEXT, fixes: [] });
      setIfMounted({ kind: "refused", text: refusal.message, fixes: refusal.code === "not_ready" ? await fixesOf(refusal.rows ?? []) : [] });
    } catch {
      setIfMounted({ kind: "refused", text: OFFLINE_TEXT, fixes: [] });
    }
  }, [request, stop, setIfMounted]);

  return { state, listen };
}
