import { useCallback, useEffect } from "react";
import { flushSync } from "react-dom";
import { getJson, sendJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { cancelCurrent, isUnfinishedIn, onlyWhen } from "../../../lib/job";
import { notice, type Notice } from "../lib/notice";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { usePollWhile } from "../../../lib/usePollWhile";
import type { Range } from "../../../lib/clips";
import { formatAxisTime, type RangeDraft } from "../lib/trim";
import { HANDLED, type StartResult } from "../lib/confirm";
import type { ClipsChanged } from "./useTempClips";

// The shape of a Trim job (backend.spoil.trim.TrimJob, spec › API).
export type TrimJobState = "trimming" | "replacing" | "done" | "failed" | "cancelled";

export type TrimJob = {
  clip_id: string;
  state: TrimJobState;
  /** `trimming` only. */
  percent: number | null;
  /** How long the clip will be once trimmed. */
  kept_s: number;
  cancel_requested: boolean;
  error: { code: string; message: string } | null;
};

/** `has_derived` waits for the user to confirm its `message`: the Transcript, Shots, EP cuts or draft go (D37). */
export type TrimStartResult = StartResult<"has_derived">;

export type TrimState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      /** Only ever an unfinished job; a finished one becomes the notice. */
      job: TrimJob | null;
      /** The message after a clip's last trim or refusal, shown in the panel while that clip is selected (D33). */
      notice: Notice | null;
      /** Each clip's open ตัดช่วง section and its ranges, kept while the page is open (D38). */
      drafts: Record<string, RangeDraft[]>;
      /**
       * A clip whose player stays let go outside its job's run (D41): its POST hasn't
       * answered, the user is asked about its `has_derived`, or its job is `done` and the
       * list with the new `?v=` hasn't come back.
       */
      releasedClipId: string | null;
    };

type Loaded = Extract<TrimState, { kind: "loaded" }>;

/** One clip's ตัดช่วง section: one state of the Frontend table (spec › Frontend). */
export type TrimView =
  | { kind: "running"; job: TrimJob }
  | { kind: "editing"; drafts: RangeDraft[] }
  /** Another clip's job runs: ตัดช่วง waits, naming it. */
  | { kind: "otherClip"; title: string }
  | { kind: "closed" };

/** The view of `clipId`'s section; `titleOf` names another clip being trimmed. */
export function trimViewOf(state: Loaded, clipId: string, titleOf: (clipId: string) => string): TrimView {
  if (state.job?.clip_id === clipId) return { kind: "running", job: state.job };
  if (state.job) return { kind: "otherClip", title: titleOf(state.job.clip_id) };
  const drafts = state.drafts[clipId];
  return drafts ? { kind: "editing", drafts } : { kind: "closed" };
}

/** The clip's player holds no file while its POST is out or its job runs: Windows can't replace an open file (D41). */
export function playerReleasedFor(state: Loaded, clipId: string): boolean {
  return state.releasedClipId === clipId || state.job?.clip_id === clipId;
}

const TRIMS_PATH = "/api/spoil/trims";
const CURRENT_PATH = "/api/spoil/trims/current";

const isUnfinished = isUnfinishedIn<TrimJobState>(["trimming", "replacing"]);

const whenLoaded = (change: (state: Loaded) => TrimState) => onlyWhen<TrimState, "loaded">("loaded", change);

/** The unfinished job, or null when there is none. */
async function runningJob(): Promise<TrimJob | null> {
  const job = await getJson<TrimJob | null>(CURRENT_PATH);
  return job !== null && isUnfinished(job) ? job : null;
}

/** A clip's section closed, its ranges forgotten. */
function withoutDraft(drafts: Record<string, RangeDraft[]>, clipId: string): Record<string, RangeDraft[]> {
  const rest = { ...drafts };
  delete rest[clipId];
  return rest;
}

/** What a finished job says in the panel (spec › Frontend, D33). */
function resultNotice(job: TrimJob): Notice {
  if (job.state === "done") return notice("success", `ตัดคลิปเสร็จ: เหลือ ${formatAxisTime(job.kept_s)}`, job.clip_id);
  if (job.state === "cancelled") return notice("info", "ยกเลิกแล้ว", job.clip_id);
  return notice("error", job.error?.message ?? "ตัดคลิปไม่สำเร็จ", job.clip_id);
}

/**
 * The ตัดช่วง section of the transcript panel (D38, D41): each clip's ranges, and the one
 * Trim job. Checks the current job on mount; polls every second only while a job is
 * unfinished, apart from the other jobs' polls. Any failure (no backend, a status the API
 * never sends, 30 s) is offline. `onClipsChanged` (stable) loads the list again when a
 * followed job ends (the new length, ตัดแล้ว and the new `?v=`) or a clip is gone, and
 * resolves once it has; `onNotReady` (stable) runs on a `503`, so the status is checked again.
 */
export function useTrim(onClipsChanged: ClipsChanged, onNotReady: () => void) {
  const [state, setState, setIfMounted] = useMountedState<TrimState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      // The page selects the unfinished job's clip once the list is in (ClipsPage).
      setIfMounted({ kind: "loaded", job: await runningJob(), notice: null, drafts: {}, releasedClipId: null });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  usePollWhile<TrimJob | null>(
    state.kind === "loaded" && state.job !== null,
    CURRENT_PATH,
    (job) => {
      if (job !== null && isUnfinished(job)) {
        setIfMounted(whenLoaded((s) => ({ ...s, job })));
        return;
      }
      // Polls run only while a job is followed, so any other answer is its end.
      setIfMounted(
        whenLoaded((s) => {
          const clipId = job?.clip_id ?? s.job?.clip_id ?? null;
          const shown = job === null ? notice("warning", "งานตัดหายเพราะ backend เริ่มใหม่ ลองตัดอีกครั้ง", clipId) : resultNotice(job);
          const done = job?.state === "done";
          // `done` closes the section; any other end keeps the ranges to try again. The old
          // file's `?v=` would play from cache, so a done clip's player waits for the new list.
          const drafts = done ? withoutDraft(s.drafts, job.clip_id) : s.drafts;
          return { ...s, job: null, notice: shown, drafts, releasedClipId: done ? job.clip_id : s.releasedClipId };
        }),
      );
      void onClipsChanged().then(() => setIfMounted(whenLoaded((s) => ({ ...s, releasedClipId: null }))));
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** Opens a clip's section: with no range the first time, as it was left after that. */
  const open = useCallback(
    (clipId: string) => setState(whenLoaded((s) => (s.drafts[clipId] ? s : { ...s, drafts: { ...s.drafts, [clipId]: [] } }))),
    [setState],
  );

  /** ยกเลิก: closes the section and forgets its ranges (D38). */
  const close = useCallback(
    (clipId: string) => setState(whenLoaded((s) => ({ ...s, drafts: withoutDraft(s.drafts, clipId) }))),
    [setState],
  );

  const edit = useCallback(
    (clipId: string, ranges: RangeDraft[]) => setState(whenLoaded((s) => ({ ...s, drafts: { ...s.drafts, [clipId]: ranges } }))),
    [setState],
  );

  /** Another clip was selected: the last trim's message goes, as a Transcribe job's does (D33). */
  const clearNotice = useCallback(() => setState(whenLoaded((s) => (s.notice ? { ...s, notice: null } : s))), [setState]);

  /** The user said no to `has_derived`: the player gets its file back. */
  const returnPlayer = useCallback(() => setState(whenLoaded((s) => ({ ...s, releasedClipId: null }))), [setState]);

  /**
   * Lets go of the player, then posts the job (D41). Resolves to `has_derived` when the clip
   * has data the user didn't agree to lose, with the player still let go: the caller asks,
   * then calls again or `returnPlayer` (D37). Every other answer is handled here; a refusal
   * is an error Alert in the panel and the player comes back.
   */
  const start = useCallback(
    async (clipId: string, ranges: Range[], confirmDerivedLoss: boolean): Promise<TrimStartResult> => {
      // Rendered now, not after the POST: the panel lets go of the file as it renders (D41).
      flushSync(() => setIfMounted(whenLoaded((s) => ({ ...s, notice: null, releasedClipId: clipId }))));
      const settle = (change: Partial<Loaded>) => setIfMounted(whenLoaded((s) => ({ ...s, releasedClipId: null, ...change })));
      try {
        const body = { clip_id: clipId, ranges, ...(confirmDerivedLoss ? { confirm_derived_loss: true } : {}) };
        const reply = await sendJson<TrimJob | Refusal>("POST", TRIMS_PATH, body);
        if (reply.status === 202) {
          settle({ job: reply.body as TrimJob });
          return HANDLED;
        }
        const refusal = refusalOf(reply.body);
        if (reply.status === 409 && refusal?.code === "has_derived") {
          return { kind: "has_derived", message: refusal.message };
        }
        if (reply.status === 409 && refusal?.code === "busy") {
          // The running job is followed: this clip's (a second POST) shows its percent; another
          // clip's is named on ตัดช่วง, under the API's message.
          const running = await runningJob();
          settle({ job: running, notice: running?.clip_id === clipId ? null : notice("error", refusal.message, clipId) });
          return HANDLED;
        }
        if (refusal) {
          settle({ notice: notice("error", refusal.message, clipId) });
          if (reply.status === 404) void onClipsChanged();
          if (reply.status === 503) onNotReady();
          return HANDLED;
        }
        setIfMounted({ kind: "offline" });
      } catch {
        setIfMounted({ kind: "offline" });
      }
      return HANDLED;
    },
    [onClipsChanged, onNotReady, setIfMounted],
  );

  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<TrimJob>(CURRENT_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenLoaded((s) => (s.job ? { ...s, job: reply.job } : s)));
    } else if (reply.kind === "refused" && reply.code === "replacing") {
      setIfMounted(whenLoaded((s) => ({ ...s, notice: notice("warning", "กำลังแทนไฟล์ ยกเลิกไม่ได้แล้ว", s.job?.clip_id ?? null) })));
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, open, close, edit, clearNotice, returnPlayer, start, cancel, reload };
}
