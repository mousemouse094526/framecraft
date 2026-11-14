import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { fixesFor } from "../../../lib/setupFixes";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { isPicking, PICK_PATH, pickPath, rangePath, type PickJob, type Range, type Song } from "../lib/songs";

/** Why a start was refused: the line, the fix commands a `not_ready` or `model_broken` names, and the field of an `invalid_request`. */
export type Refused = { text: string; fixes: string[]; field: string | null };

export type Pick = {
  /** The latest job, of any song: one picks at a time. Null: none since the backend started, or not read yet. */
  job: PickJob | null;
  /** The last start this page made that the API refused. Cleared by the next start. */
  refused: Refused | null;
};

const OFFLINE: Refused = { text: OFFLINE_TEXT, fixes: [], field: null };

async function refusedOf(body: unknown): Promise<Refused> {
  const refusal = refusalOf(body);
  if (!refusal) return OFFLINE;
  const fixes = await fixesFor(refusal);
  return { text: refusal.message, fixes, field: refusal.field ?? null };
}

/**
 * The Pick job as the song page sees it (spec › Frontend, D18): read on open, polled every second
 * while it runs. `start` saves the range first (`PUT /range`), then `POST /pick`; `onSaved` gets the
 * song the range was saved into, `onEnded` the job that ended while this page watched it.
 */
export function usePick(onSaved: (song: Song) => void, onEnded: (job: PickJob) => void) {
  const [state, , setIfMounted] = useMountedState<Pick>({ job: null, refused: null });
  const callbacks = useRef({ onSaved, onEnded });
  useEffect(() => {
    callbacks.current = { onSaved, onEnded };
  });

  useEffect(() => {
    getJson<PickJob | null>(PICK_PATH)
      .then((job) => setIfMounted((now) => ({ ...now, job })))
      // The page's own load says when the backend is gone.
      .catch(() => {});
  }, [setIfMounted]);

  usePollWhile<PickJob | null>(
    state.job !== null && isPicking(state.job),
    PICK_PATH,
    (job) => {
      setIfMounted((now) => ({ ...now, job }));
      if (job !== null && !isPicking(job)) callbacks.current.onEnded(job);
    },
    () => {},
  );

  const start = useCallback(
    async (songId: string, range: Range) => {
      setIfMounted((now) => ({ ...now, refused: null }));
      try {
        const saved = await sendJson<Song | Refusal>("PUT", rangePath(songId), range);
        if (saved.status !== 200 || !saved.body) {
          const refused = await refusedOf(saved.body);
          return setIfMounted((now) => ({ ...now, refused }));
        }
        callbacks.current.onSaved(saved.body as Song);
        const reply = await sendJson<PickJob | Refusal>("POST", pickPath(songId), {});
        if (reply.status === 202 && reply.body) return setIfMounted({ job: reply.body as PickJob, refused: null });
        const refused = await refusedOf(reply.body);
        setIfMounted((now) => ({ ...now, refused }));
      } catch {
        setIfMounted((now) => ({ ...now, refused: OFFLINE }));
      }
    },
    [setIfMounted],
  );

  const cancel = useCallback(async () => {
    try {
      const reply = await sendJson<PickJob>("POST", `${PICK_PATH}/cancel`, {});
      // `not_running`: it ended first, and the next poll says how.
      if (reply.status === 200 && reply.body) setIfMounted((now) => ({ ...now, job: reply.body }));
    } catch {
      setIfMounted((now) => ({ ...now, refused: OFFLINE }));
    }
  }, [setIfMounted]);

  return { ...state, start, cancel };
}
