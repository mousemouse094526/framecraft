import { useCallback, useEffect } from "react";
import { getJson, getReply, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { OFFLINE, refusedOf, type Refused } from "../../../lib/refused";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { reelRendersPath, songPath, type Song } from "../../drum-notes/lib/songs";
import { coverPath, coverRenderFile, type Cover, type CoverFields, type CoverRenderResult } from "../lib/cover";

export type CoverState =
  | { kind: "loading" }
  | { kind: "offline" }
  | { kind: "not_found" }
  /** The song isn't picked yet: nothing to make a reel of. */
  | { kind: "no_analysis"; song: Song }
  /** `failure`: a delete the API refused (`in_use`), until the next one. */
  | { kind: "ready"; song: Song; cover: Cover; renders: CoverRenderResult[]; failure: string | null };

export type Saved = { kind: "saved"; cover: Cover } | ({ kind: "refused" } & Refused);

/** หน้า reel: the song, its cover and the cover's renders, newest first; the save and a render's delete (spec › Frontend, D12). */
export function useCover(id: string) {
  const [state, setState, setIfMounted] = useMountedState<CoverState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const song = await getReply<Song>(songPath(id));
      if (song.status === 404) return setIfMounted({ kind: "not_found" });
      if (song.status !== 200 || !song.body) return setIfMounted({ kind: "offline" });
      const cover = await getReply<Cover>(coverPath(id));
      if (cover.status === 409) return setIfMounted({ kind: "no_analysis", song: song.body });
      if (cover.status !== 200 || !cover.body) return setIfMounted({ kind: "offline" });
      const renders = await getJson<CoverRenderResult[]>(reelRendersPath(id));
      setIfMounted({ kind: "ready", song: song.body, cover: cover.body, renders, failure: null });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [id, setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  /** The renders again, after one ended or went. */
  const reloadRenders = useCallback(
    async (failure: string | null = null) => {
      try {
        const renders = await getJson<CoverRenderResult[]>(reelRendersPath(id));
        setIfMounted((now) => (now.kind === "ready" ? { ...now, renders, failure } : now));
      } catch {
        setIfMounted((now) => (now.kind === "ready" ? { ...now, failure: OFFLINE_TEXT } : now));
      }
    },
    [id, setIfMounted],
  );

  const save = useCallback(
    async (fields: CoverFields): Promise<Saved> => {
      try {
        const reply = await sendJson<Cover>("PUT", coverPath(id), fields);
        if (reply.status === 200 && reply.body) {
          const cover = reply.body;
          setState((now) => (now.kind === "ready" ? { ...now, cover } : now));
          return { kind: "saved", cover };
        }
        return { kind: "refused", ...(await refusedOf(reply.body)) };
      } catch {
        return { kind: "refused", ...OFFLINE };
      }
    },
    [id, setState],
  );

  const removeRender = useCallback(
    async (name: string) => {
      try {
        const reply = await sendJson("DELETE", `${reelRendersPath(id)}/${name}`);
        // Already gone is what was asked for.
        if (reply.status === 204 || reply.status === 404) await reloadRenders();
        else await reloadRenders(refusalOf(reply.body)?.message ?? OFFLINE_TEXT);
      } catch {
        setIfMounted((now) => (now.kind === "ready" ? { ...now, failure: OFFLINE_TEXT } : now));
      }
    },
    [id, reloadRenders, setIfMounted],
  );

  return { state, reload: load, reloadRenders, save, removeRender, fileOf: (name: string, suffix: ".mp4" | ".srt") => coverRenderFile(id, name, suffix) };
}
