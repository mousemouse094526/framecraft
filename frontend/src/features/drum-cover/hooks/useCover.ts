import { useCallback, useEffect } from "react";
import { getJson, getReply, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { OFFLINE, refusedOf, type Refused } from "../../../lib/refused";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { reelRendersPath, type Song } from "../../drum-notes/lib/songs";
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

/**
 * ส่วน reel of a song: its cover and the cover's renders, newest first; the save and a render's delete
 * (spec › Frontend, D12). The song is the page's, read once there (nav-ia D14): a new pick gives a new
 * song, and the section starts over.
 */
export function useCover(song: Song) {
  const id = song.id;
  const [state, setState, setIfMounted] = useMountedState<CoverState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const cover = await getReply<Cover>(coverPath(id));
      if (cover.status === 404) return setIfMounted({ kind: "not_found" });
      if (cover.status === 409) return setIfMounted({ kind: "no_analysis", song });
      if (cover.status !== 200 || !cover.body) return setIfMounted({ kind: "offline" });
      const renders = await getJson<CoverRenderResult[]>(reelRendersPath(id));
      setIfMounted({ kind: "ready", song, cover: cover.body, renders, failure: null });
    } catch {
      setIfMounted({ kind: "offline" });
    }
    // Read once per song, not on every new copy of it: the section is keyed by its pick (nav-ia D14).
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

  /** The cover a picture's `PUT` or `DELETE` answered (the picture is saved at once, D8). */
  const applyCover = useCallback((cover: Cover) => setState((now) => (now.kind === "ready" ? { ...now, cover } : now)), [setState]);

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

  return { state, reload: load, reloadRenders, save, applyCover, removeRender, fileOf: (name: string, suffix: ".mp4" | ".srt") => coverRenderFile(id, name, suffix) };
}
