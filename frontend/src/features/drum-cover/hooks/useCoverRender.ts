import { useCallback, useEffect, useRef } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { NOT_NOW, OFFLINE, refusedOf, type Refused } from "../../../lib/refused";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { COVER_CANCEL_PATH, COVER_RENDER_PATH, coverRenderPath, isCoverRendering, type CoverRenderJob } from "../lib/cover";

export type CoverRender = {
  /** The latest job, of any song: one reel renders at a time. Null: none since the backend started, or not read yet. */
  job: CoverRenderJob | null;
  /** A start the API refused; `fixes` for `not_ready` (setup-status D26). Cleared by the next start. */
  refused: Refused | null;
};

/**
 * The reel's Render job (D12): read on open, polled every second while it renders. `onEnded`
 * hears a job that ended while the page watched it, so the page reads the renders again.
 */
export function useCoverRender(onEnded?: (job: CoverRenderJob) => void) {
  const [state, , setIfMounted] = useMountedState<CoverRender>({ job: null, refused: null });
  const ended = useRef(onEnded);
  useEffect(() => {
    ended.current = onEnded;
  });

  useEffect(() => {
    getJson<CoverRenderJob | null>(COVER_RENDER_PATH)
      .then((job) => setIfMounted((now) => ({ ...now, job })))
      // The page's own load says when the backend is gone.
      .catch(() => {});
  }, [setIfMounted]);

  usePollWhile<CoverRenderJob | null>(
    isCoverRendering(state.job),
    COVER_RENDER_PATH,
    (job) => {
      setIfMounted((now) => ({ ...now, job }));
      if (job !== null && !isCoverRendering(job)) ended.current?.(job);
    },
    () => {},
  );

  const start = useCallback(
    async (songId: string) => {
      setIfMounted((now) => ({ ...now, refused: null }));
      try {
        const reply = await sendJson<CoverRenderJob>("POST", coverRenderPath(songId), {});
        if (reply.status === 202 && reply.body) return setIfMounted({ job: reply.body, refused: null });
        const refused = await refusedOf(reply.body, NOT_NOW);
        setIfMounted((now) => ({ ...now, refused }));
      } catch {
        setIfMounted((now) => ({ ...now, refused: OFFLINE }));
      }
    },
    [setIfMounted],
  );

  const cancel = useCallback(async () => {
    try {
      const reply = await sendJson<CoverRenderJob>("POST", COVER_CANCEL_PATH, {});
      // `not_running`: it ended first, and the next poll says how.
      if (reply.status === 200 && reply.body) setIfMounted((now) => ({ ...now, job: reply.body }));
    } catch {
      setIfMounted((now) => ({ ...now, refused: OFFLINE }));
    }
  }, [setIfMounted]);

  return { ...state, start, cancel };
}
