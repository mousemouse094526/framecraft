import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { CANCEL_PATH, isRendering, RENDER_PATH, type DrumRenderJob } from "../lib/render";
import { fixesOf } from "../../../lib/setupFixes";

const OFFLINE = { text: OFFLINE_TEXT, fixes: [] };

export type DrumRender = {
  /** The latest job, of any lesson: one renders at a time. Null: none since the backend started, or not read yet. */
  job: DrumRenderJob | null;
  /** A start the API refused; `fixes` for `not_ready` (setup-status D26). Cleared by the next start. */
  refused: { text: string; fixes: string[] } | null;
};

/**
 * The Render job as every page under `#/drums` sees it (D22): read on open, polled every second
 * while it renders. `onEnded` hears a job that ended while this page watched it; `startedHere`
 * says whether this page started it, so only that page moves on to the results.
 */
export function useDrumRender(onEnded?: (job: DrumRenderJob, startedHere: boolean) => void) {
  const [state, , setIfMounted] = useMountedState<DrumRender>({ job: null, refused: null });
  const startedHere = useRef(false);

  useEffect(() => {
    getJson<DrumRenderJob | null>(RENDER_PATH)
      .then((job) => setIfMounted((now) => ({ ...now, job })))
      // The page's own load says when the backend is gone.
      .catch(() => {});
  }, [setIfMounted]);

  usePollWhile<DrumRenderJob | null>(
    isRendering(state.job),
    RENDER_PATH,
    (job) => {
      setIfMounted((now) => ({ ...now, job }));
      if (job !== null && !isRendering(job)) {
        onEnded?.(job, startedHere.current);
        startedHere.current = false;
      }
    },
    () => {},
  );

  const start = useCallback(
    async (lessonId: string) => {
      setIfMounted((now) => ({ ...now, refused: null }));
      try {
        const reply = await sendJson<DrumRenderJob>("POST", RENDER_PATH, { lesson_id: lessonId });
        if (reply.status === 202 && reply.body) {
          startedHere.current = true;
          const job = reply.body;
          return setIfMounted({ job, refused: null });
        }
        const refusal = refusalOf(reply.body);
        if (!refusal) return setIfMounted((now) => ({ ...now, refused: OFFLINE }));
        const fixes = refusal.code === "not_ready" ? await fixesOf(refusal.rows ?? []) : [];
        setIfMounted((now) => ({ ...now, refused: { text: refusal.message, fixes } }));
      } catch {
        setIfMounted((now) => ({ ...now, refused: OFFLINE }));
      }
    },
    [setIfMounted],
  );

  const cancel = useCallback(async () => {
    try {
      const reply = await sendJson<DrumRenderJob>("POST", CANCEL_PATH, {});
      // `not_running`: it ended first, and the next poll says how.
      if (reply.status === 200 && reply.body) setIfMounted((now) => ({ ...now, job: reply.body }));
    } catch {
      setIfMounted((now) => ({ ...now, refused: OFFLINE }));
    }
  }, [setIfMounted]);

  return { ...state, start, cancel };
}
