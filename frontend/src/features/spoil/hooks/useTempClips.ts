import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { refusalOf, type Refusal } from "./refusal";

// The shape of a Temp clip (backend.spoil.clips.TempClip, spec › Temp clip).
export type TempClip = {
  id: string;
  title: string;
  channel: string | null;
  source_url: string;
  duration_s: number | null;
  width: number | null;
  height: number | null;
  orientation: "portrait" | "landscape";
  file_bytes: number;
  thumbnail: string | null;
  downloaded_at: string;
  yt_dlp_version: string;
};

export type ClipsState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      clips: TempClip[];
      /** The clip in the player, or null when none is (D7). */
      playingId: string | null;
      /** A delete's refusal from the API, by clip id, shown under that row (D15). */
      deleteErrors: Record<string, string>;
    };

export const CLIPS_PATH = "/api/spoil/clips";

/**
 * The Temp clip list of the สปอย tab: loads it, plays one clip, deletes.
 * Any failure (no backend, a status the API never sends, 30 s) is offline.
 */
export function useTempClips() {
  const [state, setState, setIfMounted] = useMountedState<ClipsState>({ kind: "loading" });

  /**
   * Fetches the list without the loading screen; the clip playing keeps
   * playing if it is still there. Delete errors go: they were about the old list.
   */
  const refetch = useCallback(async () => {
    try {
      const { clips } = await getJson<{ clips: TempClip[] }>(CLIPS_PATH);
      setIfMounted((previous) => {
        const playing = previous.kind === "loaded" ? previous.playingId : null;
        return {
          kind: "loaded",
          clips,
          playingId: clips.some((clip) => clip.id === playing) ? playing : null,
          deleteErrors: {},
        };
      });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  /** `null` closes the player. */
  const play = useCallback(
    (playingId: string | null) => {
      setState((previous) => (previous.kind === "loaded" ? { ...previous, playingId } : previous));
    },
    [setState],
  );

  /** Sends DELETE; the caller lets go of the player first (D15). */
  const remove = useCallback(
    async (id: string) => {
      try {
        const reply = await sendJson<Refusal>("DELETE", `${CLIPS_PATH}/${id}`);
        const refusal = refusalOf(reply.body);
        if (reply.status === 204 || reply.status === 404) {
          // 404: the files went some other way (deleted by hand); the row goes either way.
          setIfMounted((previous) => {
            if (previous.kind !== "loaded") return previous;
            const deleteErrors = { ...previous.deleteErrors };
            delete deleteErrors[id];
            return {
              ...previous,
              clips: previous.clips.filter((clip) => clip.id !== id),
              playingId: previous.playingId === id ? null : previous.playingId,
              deleteErrors,
            };
          });
        } else if (reply.status === 409 && refusal?.code === "in_use") {
          const message = refusal.message;
          setIfMounted((previous) =>
            previous.kind === "loaded" ? { ...previous, deleteErrors: { ...previous.deleteErrors, [id]: message } } : previous,
          );
        } else {
          setIfMounted({ kind: "offline" });
        }
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [setIfMounted],
  );

  /** Back to the loading screen, then fetch (the Refresh button). */
  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void refetch();
  }, [refetch, setState]);

  return { state, refetch, reload, play, remove };
}
