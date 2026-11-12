import { useCallback, useEffect, useRef } from "react";
import { getJson, OFFLINE_TEXT, sendJson } from "../../../lib/api";
import { clipPath, videoPath, videoUrl, type TempClip } from "../../../lib/clips";
import { isRunning, onlyWhen } from "../../../lib/job";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import {
  DRAFT_JOB_PATH,
  DRAFT_JOBS_PATH,
  DRAFT_PATH,
  jobFailureText,
  shotsPath,
  type Draft,
  type DraftJob,
  type Shot,
  type ShotRef,
} from "../lib/draft";
import { useJobCalls } from "./useStepStatus";

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
      /** The Shot picker's player: the clip's mp4 with its `?v=` (spoil D41). */
      videoSrc: string;
      /** The unfinished `pick` or `polish`, followed until it ends. */
      job: DraftJob | null;
      /** The sentence that job picks for, when this page started it. */
      pickingId: string | null;
      /** The last refusal or failed job, or how the last `polish` went: "เรียบเรียง {n} ประโยค" (D76). */
      message: ReviewMessage | null;
    };

export type ReviewMessage = { tone: "error" | "success"; text: string };

type Loaded = Extract<ReviewState, { kind: "loaded" }>;

const whenLoaded = (change: (state: Loaded) => ReviewState) => onlyWhen<ReviewState, "loaded">("loaded", change);

/** What a change answers: `saved` with the draft it made, or the refusal's message to show. */
export type ChangeResult = { kind: "saved"; draft: Draft } | { kind: "refused"; message: string };

/** What a followed job says once it ends: why it failed, or how many sentences a `polish` changed (spec › Frontend, D76). */
function endMessage(job: DraftJob | null): ReviewMessage | null {
  if (job?.state === "failed") return { tone: "error", text: jobFailureText(job) };
  if (job?.kind !== "polish" || job.state !== "done") return null;
  return { tone: "success", text: job.done ? `เรียบเรียง ${job.done} ประโยค` : "ไม่มีประโยคที่เปลี่ยน" };
}

/**
 * Step 2 of the สปอย tab, ตรวจแก้บท: the Spoil draft with each clip's Shots, every change
 * to it (D19, D25, D26, D27), and the Draft jobs `pick` (AI เลือก Shot ใหม่) and `polish`
 * (เรียบเรียงใหม่, D72–D76), polled every second while they run. Any failure on load or
 * poll is offline.
 */
export function useScriptReview() {
  const [state, setState, setIfMounted] = useMountedState<ReviewState>({ kind: "loading" });
  const { refreshSteps, cancelCurrent } = useJobCalls();
  const saving = useRef(new Set<Promise<ChangeResult>>()); // changes not answered yet

  const load = useCallback(async () => {
    try {
      const [draft, job] = await Promise.all([getJson<Draft | null>(DRAFT_PATH), getJson<DraftJob | null>(DRAFT_JOB_PATH)]);
      if (draft === null) {
        setIfMounted({ kind: "empty" });
        return;
      }
      // Shots that can't be read show no pictures; the rest of the draft still opens.
      const [list, clip] = await Promise.all([
        getJson<{ shots: Shot[] }>(shotsPath(draft.clip_id)).then((file) => file.shots, () => []),
        // The clip's `trimmed_at` gives the player's `?v=`; a clip that can't be read plays the bare path.
        getJson<TempClip>(clipPath(draft.clip_id)).then((clip) => clip, () => undefined),
      ]);
      const shots = { [draft.clip_id]: list };
      const videoSrc = clip ? videoUrl(clip) : videoPath(draft.clip_id);
      setIfMounted((previous) => ({
        kind: "loaded",
        draft,
        shots,
        videoSrc,
        // A whole new draft is step 1's; this page follows the jobs that change the draft it shows.
        job: isRunning(job) && job?.kind !== "draft" ? job : null,
        pickingId: previous.kind === "loaded" ? previous.pickingId : null,
        message: previous.kind === "loaded" ? previous.message : null,
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
      if (job !== null && isRunning(job)) {
        setIfMounted(whenLoaded((s) => ({ ...s, job })));
        return;
      }
      // Polls run only while a job is followed, so any other answer is its end: the draft has the new Shots or text.
      setIfMounted(
        whenLoaded((s) => ({
          ...s,
          job: null,
          pickingId: null,
          message: endMessage(job),
        })),
      );
      void load();
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** One change to the draft, untracked; the answer is the whole draft again. */
  const sendChange = useCallback(
    async (method: string, path: string, body?: unknown): Promise<ChangeResult> => {
      try {
        const reply = await sendJson<Draft | Refusal>(method, path, body);
        if (reply.status === 200 || reply.status === 201) {
          const draft = reply.body as Draft;
          setIfMounted(whenLoaded((s) => ({ ...s, draft, message: null })));
          return { kind: "saved", draft };
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          // `draft_locked`, `no_draft`, a sentence gone: what the page shows is old, so read it again.
          if (reply.status !== 400) void load();
          setIfMounted(whenLoaded((s) => ({ ...s, message: { tone: "error", text: refusal.message } })));
          return { kind: "refused", message: refusal.message };
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
      return { kind: "refused", message: OFFLINE_TEXT };
    },
    [load, setIfMounted],
  );

  /** Every change goes through here: it is remembered until answered, so เรียบเรียงใหม่ can wait for it (D76). */
  const change = useCallback(
    (method: string, path: string, body?: unknown) => {
      const sending = sendChange(method, path, body);
      saving.current.add(sending);
      void sending.finally(() => saving.current.delete(sending));
      return sending;
    },
    [sendChange],
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

  /** Starts a Draft job that changes the draft: it reads locked until the job ends (D51). */
  const startJob = useCallback(
    async (body: object, pickingId: string | null) => {
      try {
        const reply = await sendJson<DraftJob | Refusal>("POST", DRAFT_JOBS_PATH, body);
        if (reply.status === 202) {
          const job = reply.body as DraftJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job, pickingId, message: null, draft: { ...s.draft, locked: true } })));
          refreshSteps();
          return;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) {
          // `gpu_busy` says which job holds the GPU (spec › Frontend); `no_refs`, `nothing_to_polish` and the rest say why.
          setIfMounted(whenLoaded((s) => ({ ...s, message: { tone: "error", text: refusal.message } })));
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [refreshSteps, setIfMounted],
  );

  /** เลือก Shot ใหม่: the Draft job `pick` for one sentence (D25). */
  const pick = useCallback(
    (sentenceId: string) => startJob({ kind: "pick", sentence_id: sentenceId }, sentenceId),
    [startJob],
  );

  /**
   * เรียบเรียงใหม่ (D72, D75): once every change still out is answered, the draft is read
   * again, so the job polishes the text the user sees (D76).
   */
  const polish = useCallback(
    async (includeEdited: boolean) => {
      // Loop, not one wait: a save's answer starts the next save when text was typed while it was out (useAutoSave).
      while (saving.current.size > 0) await Promise.all(saving.current);
      await load();
      await startJob({ kind: "polish", include_edited: includeEdited }, null);
    },
    [load, startJob],
  );

  /** ยกเลิก of a running pick or polish: the draft stays as it was. */
  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<DraftJob>(DRAFT_JOB_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenLoaded((s) => (s.job ? { ...s, job: reply.job } : s)));
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [cancelCurrent, setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  /** Reads the draft again in place: a voice or render job moved on. */
  const refresh = useCallback(() => void load(), [load]);
  const goOffline = useCallback(() => setIfMounted({ kind: "offline" }), [setIfMounted]);

  return { state, changeDraft, changeText, changeShots, insertAfter, remove, pick, polish, cancel, reload, refresh, goOffline };
}
