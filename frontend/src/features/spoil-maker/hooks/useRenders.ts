import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { cancelCurrent } from "../../../lib/job";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { isRunning } from "../../../lib/job";
import {
  failureOf,
  RENDER_JOB_PATH,
  RENDERS_PATH,
  startJob,
  type Banner,
  type RenderJob,
  type RenderResult,
} from "../lib/render";
import { useStepsRefresh } from "./useStepStatus";

export type RendersState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      /** Newest first (D42). */
      renders: RenderResult[];
      /** The Render job followed until it ends. */
      job: RenderJob | null;
      /** How the last render failed, a refused retry or delete. */
      error: Banner | null;
    };

/**
 * Step 3 of the สปอย tab, ผล render (spoil-maker D42): every finished render, and the
 * Render job still running, polled every second until it ends and then listed.
 */
export function useRenders() {
  const [state, , setIfMounted] = useMountedState<RendersState>({ kind: "loading" });
  const refreshSteps = useStepsRefresh();

  const load = useCallback(async () => {
    try {
      const [renders, job] = await Promise.all([
        getJson<RenderResult[]>(RENDERS_PATH),
        getJson<RenderJob | null>(RENDER_JOB_PATH),
      ]);
      setIfMounted((previous) => ({
        kind: "loaded",
        renders,
        job: isRunning(job) ? job : null,
        error: previous.kind === "loaded" ? previous.error : null,
      }));
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  usePollWhile<RenderJob | null>(
    state.kind === "loaded" && state.job !== null,
    RENDER_JOB_PATH,
    (job) => {
      if (job !== null && isRunning(job)) {
        setIfMounted((s) => (s.kind === "loaded" ? { ...s, job } : s));
        return;
      }
      setIfMounted((s) =>
        s.kind === "loaded" ? { ...s, job: null, error: job?.state === "failed" ? failureOf(job) : null } : s,
      );
      void load(); // a `done` render is in the list now
    },
    () => setIfMounted({ kind: "offline" }),
  );

  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<RenderJob>(RENDER_JOB_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted((s) => (s.kind === "loaded" && s.job ? { ...s, job: reply.job } : s));
      refreshSteps();
    } else if (reply.kind === "offline") setIfMounted({ kind: "offline" });
  }, [refreshSteps, setIfMounted]);

  /** ลบ after its confirm: mp4, `.srt` and `.json` go together. */
  const remove = useCallback(
    async (name: string) => {
      try {
        const reply = await sendJson<Refusal>("DELETE", `${RENDERS_PATH}/${name}`);
        if (reply.status === 204 || reply.status === 404) {
          setIfMounted((s) => (s.kind === "loaded" ? { ...s, renders: s.renders.filter((r) => r.name !== name) } : s));
          refreshSteps();
          return;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          // `in_use`: a player still holds the mp4.
          setIfMounted((s) =>
            s.kind === "loaded" ? { ...s, error: { tone: "error", title: "ลบไม่ได้", text: refusal.message, retry: false } } : s,
          );
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [refreshSteps, setIfMounted],
  );

  /** ลองอีกครั้ง of a failed render: the draft as it is now. */
  const retry = useCallback(async () => {
    const reply = await startJob<RenderJob>(RENDERS_PATH, {});
    if (reply.kind === "offline") {
      setIfMounted({ kind: "offline" });
      return;
    }
    refreshSteps();
    if (reply.kind === "busy") {
      void load(); // another render runs: follow it
      return;
    }
    const change = (s: RendersState): RendersState => {
      if (s.kind !== "loaded") return s;
      if (reply.kind === "started") return { ...s, job: reply.job, error: null };
      if (reply.kind === "banner") return { ...s, error: reply.banner };
      return { ...s, error: { tone: "error", title: "render ไม่ได้", text: reply.refused.text, retry: false } };
    };
    setIfMounted(change);
  }, [load, refreshSteps, setIfMounted]);

  return { state, cancel, remove, retry };
}
