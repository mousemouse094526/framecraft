import { useCallback, useEffect, useRef } from "react";
import { getReply, sendJson, type JsonReply } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import type { Ep } from "../lib/draft";

/** One EP of the clip's cut (spoil-maker spec › API, `GET /clips/{id}/episodes`). */
export type Episode = Ep & {
  /** The Shot that starts the EP: its thumbnail stands for the EP. */
  thumb_shot: number;
  lines: number;
  /** Null without Qwen's tokenizer (D71). */
  tokens: number | null;
  renders: number;
  in_draft: boolean;
};

export type Episodes = {
  clip_id: string;
  minutes: number;
  custom: boolean;
  episodes: Episode[];
  limit: number;
  /** The `not_ready` message when the EPs' `tokens` are null. */
  tokens_not_ready: string | null;
};

export type EpisodesState =
  | { kind: "none" }
  | { kind: "loading" }
  /** `error`: the last refusal of a change, or of the read, to show over the list. */
  | { kind: "loaded"; cut: Episodes; error: string | null }
  | { kind: "refused"; error: string }
  | { kind: "offline" };

export const MINUTES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]; // D69

export const episodesPath = (clipId: string) => `/api/spoil-maker/clips/${clipId}/episodes`;

/**
 * The picked clip's EP cut (spoil-maker D66, D69–D71): read on picking, changed with
 * `PUT` one change at a time. `settled` waits for the change in flight, so ร่างบท sends the
 * range the backend has; an answer about a clip no longer picked is dropped.
 */
export function useEpisodes(clipId: string | null) {
  const [state, , setIfMounted] = useMountedState<EpisodesState>({ kind: "none" });
  const picked = useRef(clipId);
  picked.current = clipId;
  // The `PUT` in flight, and the cut the backend has after it.
  const pending = useRef<Promise<void>>(Promise.resolve());
  const latest = useRef<Episodes | null>(null);

  /** Shows a cut the backend answered with and returns null; else the refusal's message, or "offline". */
  const answered = useCallback(
    (reply: JsonReply<Episodes>): string | "offline" | null => {
      if (reply.status === 200 && reply.body) {
        latest.current = reply.body;
        setIfMounted({ kind: "loaded", cut: reply.body, error: null });
        return null;
      }
      return refusalOf(reply.body)?.message ?? "offline";
    },
    [setIfMounted],
  );

  const read = useCallback(
    async (id: string) => {
      try {
        const reply = await getReply<Episodes>(episodesPath(id));
        if (picked.current !== id) return;
        const refusal = answered(reply);
        if (refusal !== null) setIfMounted(refusal === "offline" ? { kind: "offline" } : { kind: "refused", error: refusal });
      } catch {
        if (picked.current === id) setIfMounted({ kind: "offline" });
      }
    },
    [answered, setIfMounted],
  );

  // No ignore flag: `read` drops any answer about a clip no longer picked (the `picked` ref),
  // which also covers `put` and `reload` (react.md › fetching in an Effect).
  useEffect(() => {
    latest.current = null;
    if (clipId === null) {
      setIfMounted({ kind: "none" });
      return;
    }
    setIfMounted({ kind: "loading" });
    void read(clipId);
  }, [clipId, read, setIfMounted]);

  const put = useCallback(
    (body: { minutes: number; cuts?: number[] }) => {
      const id = picked.current;
      if (id === null) return;
      const send = async () => {
        try {
          const reply = await sendJson<Episodes>("PUT", episodesPath(id), body);
          if (picked.current !== id) return;
          const refusal = answered(reply);
          if (refusal === "offline") setIfMounted({ kind: "offline" });
          // The list stays as the backend has it; the field the user typed in shows it again.
          else if (refusal !== null) setIfMounted((s) => (s.kind === "loaded" ? { ...s, error: refusal } : s));
        } catch {
          if (picked.current === id) setIfMounted({ kind: "offline" });
        }
      };
      pending.current = pending.current.then(send);
    },
    [answered, setIfMounted],
  );

  /** The cut once every change sent so far is answered; null when there is none to draft from. */
  const settled = useCallback(async () => {
    await pending.current;
    return latest.current;
  }, []);

  const reload = useCallback(() => {
    if (picked.current !== null) void read(picked.current);
  }, [read]);

  return { state, put, settled, reload };
}
