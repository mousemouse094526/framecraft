import { useCallback, useEffect } from "react";
import { getReply } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { songPath, type Song } from "../lib/songs";

export type SongState = { kind: "loading" } | { kind: "offline" } | { kind: "not_found" } | { kind: "ready"; song: Song };

/** หน้าเพลง: one song as `GET /api/songs/{id}` answers it (spec › Frontend). */
export function useSong(id: string) {
  const [state, , setIfMounted] = useMountedState<SongState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const reply = await getReply<Song>(songPath(id));
      if (reply.status === 200 && reply.body) setIfMounted({ kind: "ready", song: reply.body });
      else if (reply.status === 404) setIfMounted({ kind: "not_found" });
      else setIfMounted({ kind: "offline" });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [id, setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  return { state, reload: load };
}
