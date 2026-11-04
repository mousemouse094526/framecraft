import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { cancelCurrent, onlyWhen } from "../../../lib/job";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import {
  DRAFT_JOB_PATH,
  DRAFT_JOBS_PATH,
  DRAFT_PATH,
  isDrafting,
  jobFailureText,
  shotsPath,
  type Draft,
  type DraftJob,
  type Shot,
  type ShotRef,
} from "../lib/draft";
import { useStepsRefresh } from "./useStepStatus";

export type ReviewState =
  | { kind: "loading" }
  | { kind: "offline" }
  /** No Spoil draft: the page links to ตั้งค่าคลิปสปอย. */
  | { kind: "empty" }
  | {
      kind: "loaded";
      draft: Draft;
      /** Each draft clip's Shots, for the thumbnails' times and the Shot picker. */
      shots: Record<string, Shot[]>;
      /** The unfinished `pick`, followed until it ends. */
      job: DraftJob | null;
      /** The sentence that job picks for, when this page started it. */
      pickingId: string | null;
      /** The last refusal or failed pick, to show the user. */
      error: string | null;
    };

type Loaded = Extract<ReviewState, { kind: "loaded" }>;

const whenLoaded = (change: (state: Loaded) => ReviewState) => onlyWhen<ReviewState, "loaded">("loaded", change);

/** What a change answers: `saved` with the draft it made, or the refusal's message to show. */
export type ChangeResult = { kind: "saved"; draft: Draft } | { kind: "refused"; message: string };

/**
 * Step 2 of the สปอย tab, ตรวจแก้บท: the Spoil draft with each clip's Shots, every change
 * to it (D19, D25, D26, D27), and the Draft job `pick` (AI เลือก Shot ใหม่), polled every
 * second while it runs. Any failure on load or poll is offline.
 */
export function useScriptReview() {
  const [state, setState, setIfMounted] = useMountedState<ReviewState>({ kind: "loading" });
  const refreshSteps = useStepsRefresh();

  const load = useCallback(async () => {
    try {
      const [draft, job] = await Promise.all([getJson<Draft | null>(DRAFT_PATH), getJson<DraftJob | null>(DRAFT_JOB_PATH)]);
      if (draft === null) {
        setIfMounted({ kind: "empty" });
        return;
      }
      // Shots that can't be read show no pictures; the rest of the draft still opens.
      const list = await getJson<{ shots: Shot[] }>(shotsPath(draft.clip_id)).then((file) => file.shots, () => []);
      const shots = { [draft.clip_id]: list };
      setIfMounted((previous) => ({
        kind: "loaded",
        draft,
        shots,
        job: isDrafting(job) && job?.kind === "pick" ? job : null,
        pickingId: previous.kind === "loaded" ? previous.pickingId : null,
        error: previous.kind === "loaded" ? previous.error : null,
      }));
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  usePollWhile<DraftJob | null>(
    state.kind === "loaded" && state.job !== null,
    DRAFT_JOB_PATH,
    (job) => {
      if (job !== null && isDrafting(job)) {
        setIfMounted(whenLoaded((s) => ({ ...s, job })));
        return;
      }
      // Polls run only while a job is followed, so any other answer is its end: the draft has the new Shots.
      setIfMounted(
        whenLoaded((s) => ({
          ...s,
          job: null,
          pickingId: null,
          error: job?.state === "failed" ? jobFailureText(job) : null,
        })),
      );
      void load();
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** One change to the draft; the answer is the whole draft again. */
  const change = useCallback(
    async (method: string, path: string, body?: unknown): Promise<ChangeResult> => {
      try {
        const reply = await sendJson<Draft | Refusal>(method, path, body);
        if (reply.status === 200 || reply.status === 201) {
          const draft = reply.body as Draft;
          setIfMounted(whenLoaded((s) => ({ ...s, draft, error: null })));
          return { kind: "saved", draft };
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          // `draft_locked`, `no_draft`, a sentence gone: what the page shows is old, so read it again.
          if (reply.status !== 400) void load();
          setIfMounted(whenLoaded((s) => ({ ...s, error: refusal.message })));
          return { kind: "refused", message: refusal.message };
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
      return { kind: "refused", message: "ติดต่อ backend ไม่ได้" };
    },
    [load, setIfMounted],
  );

  const changeDraft = useCallback(
    (fields: { top_text?: string; original_volume?: number }) => change("PATCH", DRAFT_PATH, fields),
    [change],
  );

  const changeText = useCallback(
    (sentenceId: string, text: string) => change("PATCH", `${DRAFT_PATH}/sentences/${sentenceId}`, { text }),
    [change],
  );

  const changeShots = useCallback(
    (sentenceId: string, shots: (ShotRef | null)[]) => change("PATCH", `${DRAFT_PATH}/sentences/${sentenceId}`, { shots }),
    [change],
  );

  /** A change to how many sentences there are: the steps count them (D68). */
  const changeSentenceCount = useCallback(
    async (method: string, path: string, body?: unknown) => {
      const result = await change(method, path, body);
      if (result.kind === "saved") refreshSteps();
      return result;
    },
    [change, refreshSteps],
  );

  const insertAfter = useCallback(
    (afterId: string | null, text: string) => changeSentenceCount("POST", `${DRAFT_PATH}/sentences`, { after_id: afterId, text }),
    [changeSentenceCount],
  );

  const remove = useCallback((sentenceId: string) => changeSentenceCount("DELETE", `${DRAFT_PATH}/sentences/${sentenceId}`), [changeSentenceCount]);

  /** เลือก Shot ใหม่: the Draft job `pick` for one sentence (D25). */
  const pick = useCallback(
    async (sentenceId: string) => {
      try {
        const reply = await sendJson<DraftJob | Refusal>("POST", DRAFT_JOBS_PATH, { kind: "pick", sentence_id: sentenceId });
        if (reply.status === 202) {
          const job = reply.body as DraftJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job, pickingId: sentenceId, error: null, draft: { ...s.draft, locked: true } })));
          refreshSteps();
          return;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          // `gpu_busy` says which job holds the GPU (spec › Frontend); `no_refs` and the rest say why.
          setIfMounted(whenLoaded((s) => ({ ...s, error: refusal.message })));
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [refreshSteps, setIfMounted],
  );

  /** ยกเลิก of a running pick: the draft keeps its Shots. */
  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<DraftJob>(DRAFT_JOB_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenLoaded((s) => (s.job ? { ...s, job: reply.job } : s)));
      refreshSteps();
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [refreshSteps, setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  /** Reads the draft again in place: a voice or render job moved on. */
  const refresh = useCallback(() => void load(), [load]);
  const goOffline = useCallback(() => setIfMounted({ kind: "offline" }), [setIfMounted]);

  return { state, changeDraft, changeText, changeShots, insertAfter, remove, pick, cancel, reload, refresh, goOffline };
}
