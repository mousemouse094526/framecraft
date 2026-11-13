import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, postForBlob } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import type { StatusResponse } from "../../../lib/statusTypes";
import { useMountedState } from "../../../lib/useMountedState";
import { lessonPath } from "../lib/lesson";

export type ListenState =
  | { kind: "idle" }
  | { kind: "mixing" }
  /** `fixes`: the commands of the Status check rows a `not_ready` names (setup-status D26). */
  | { kind: "refused"; text: string; fixes: string[] };

/**
 * ฟังจังหวะ: saves first, then has the backend mix the whole clip and plays the wav from a blob
 * URL; pressing again stops the one playing before anything else (D8, spec › Frontend).
 */
export function useListen(id: string, saveFirst: () => Promise<boolean>) {
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
    if (!(await saveFirst())) {
      // The save says why under บันทึก.
      setIfMounted({ kind: "idle" });
      return;
    }
    try {
      const reply = await postForBlob(`${lessonPath(id)}/listen`, {});
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
  }, [id, saveFirst, stop, setIfMounted]);

  return { state, listen };
}

/** The fix command of each named row that has one, from the Status check; none when it can't be read. */
async function fixesOf(rows: string[]): Promise<string[]> {
  try {
    const status = await getJson<StatusResponse>("/api/setup/status");
    // A `hint` is advice, not a command to copy (setup-status D26).
    return status.items.filter((item) => rows.includes(item.id) && item.fix && item.fix_kind === "command").map((item) => item.fix as string);
  } catch {
    return [];
  }
}
