import { useCallback, useEffect } from "react";
import { getJson, getReply, sendJson } from "../../../lib/api";
import { CLIPS_PATH, type TempClip } from "../../../lib/clips";
import { gpuBusyText } from "../../../lib/gpu";
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
  REVIEW_HASH,
  SETTINGS_PATH,
  tokensPath,
  VOICES_PATH,
  type DraftJob,
  type Layout,
  type Style,
} from "../lib/draft";
import type { Voice } from "./useVoices";

/** What ร่างบท sends with `kind: "draft"` (spoil-maker spec › Draft job). */
export type Order = { clip_ids: string[]; style: Style; layout: Layout; target_s: number; voice_id: string };

/**
 * A page-level message (Figma `Setup banner`): a failed draft with ลองอีกครั้ง, the GPU
 * held by another job, an install missing a row with a link to ติดตั้ง, or the API's message.
 */
export type Banner =
  | { kind: "failed"; text: string }
  | { kind: "gpu_busy"; text: string }
  | { kind: "not_ready"; text: string }
  | { kind: "refused"; text: string };

export type SetupState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      clips: TempClip[];
      voices: Voice[];
      /** The voice of the last draft, the one ร่างบท starts with (spec › ค่าที่จำไว้). */
      lastVoiceId: string | null;
      /** ร่างบท asks before replacing it (D28). */
      draftExists: boolean;
      /** An unfinished Draft job, followed until it ends. */
      job: DraftJob | null;
      banner: Banner | null;
      /** The API answered `draft_exists`, or the user pressed ร่างบท with a draft there: ร่างทับ waits. */
      confirmingReplace: boolean;
    };

type Loaded = Extract<SetupState, { kind: "loaded" }>;

const whenLoaded = (change: (state: Loaded) => SetupState) => onlyWhen<SetupState, "loaded">("loaded", change);

/** The refusals of `POST /draft-jobs` the page shows as a banner; null for one it handles otherwise. */
function bannerOf(status: number, refusal: Refusal | null): Banner | null {
  if (refusal === null) return null;
  if (status === 409 && refusal.code === "gpu_busy") return { kind: "gpu_busy", text: gpuBusyText(refusal.running ?? "") };
  if (status === 503 && refusal.code === "not_ready") return { kind: "not_ready", text: refusal.message };
  return { kind: "refused", text: refusal.message };
}

/**
 * Step 1 of the สปอย tab, ตั้งค่าคลิปสปอย: the clips to pick from, the Saved voices, the
 * remembered voice, whether a Spoil draft is there, and the one Draft job behind ร่างบท
 * (spoil-maker D5, D25, D28). Polls the job every second while it runs and opens
 * ตรวจแก้บท when it is done. Any failure on load or poll is offline.
 */
export function useSpoilerSetup() {
  const [state, setState, setIfMounted] = useMountedState<SetupState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [{ clips }, voices, settings, draft, job] = await Promise.all([
        getJson<{ clips: TempClip[] }>(CLIPS_PATH),
        getJson<Voice[]>(VOICES_PATH),
        getJson<{ last_voice_id: string | null }>(SETTINGS_PATH),
        getJson<unknown>(DRAFT_PATH),
        getJson<DraftJob | null>(DRAFT_JOB_PATH),
      ]);
      setIfMounted({
        kind: "loaded",
        clips,
        voices,
        lastVoiceId: settings.last_voice_id,
        draftExists: draft !== null,
        // A `pick` belongs to ตรวจแก้บท; this page follows a whole draft only.
        job: isDrafting(job) && job?.kind === "draft" ? job : null,
        banner: null,
        confirmingReplace: false,
      });
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
      // Polls run only while a job is followed, so any other answer is its end.
      setIfMounted(
        whenLoaded((s) => ({
          ...s,
          job: null,
          banner: job?.state === "failed" ? { kind: "failed", text: jobFailureText(job) } : null,
        })),
      );
      if (job?.state === "done") window.location.hash = REVIEW_HASH;
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** ร่างบท, or ร่างทับ with `replace` once the user agreed to lose the draft there (D28). */
  const draft = useCallback(
    async (order: Order, replace: boolean) => {
      setIfMounted(whenLoaded((s) => ({ ...s, banner: null, confirmingReplace: false })));
      try {
        const reply = await sendJson<DraftJob | Refusal>("POST", DRAFT_JOBS_PATH, { kind: "draft", ...order, replace });
        if (reply.status === 202) {
          const job = reply.body as DraftJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        const refusal = refusalOf(reply.body);
        if (reply.status === 409 && refusal?.code === "draft_exists") {
          setIfMounted(whenLoaded((s) => ({ ...s, draftExists: true, confirmingReplace: true })));
          return;
        }
        if (reply.status === 409 && refusal?.code === "busy") {
          const job = await getJson<DraftJob | null>(DRAFT_JOB_PATH);
          if (job !== null && isDrafting(job)) setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        const banner = bannerOf(reply.status, refusal);
        if (banner) {
          setIfMounted(whenLoaded((s) => ({ ...s, banner })));
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [setIfMounted],
  );

  /** ร่างบท with a Spoil draft there asks first (Figma Draft action › replace confirm). */
  const askReplace = useCallback(
    (asking: boolean) => setIfMounted(whenLoaded((s) => ({ ...s, confirmingReplace: asking }))),
    [setIfMounted],
  );

  const cancel = useCallback(async () => {
    const reply = await cancelCurrent<DraftJob>(DRAFT_JOB_PATH);
    if (reply.kind === "cancelling") {
      setIfMounted(whenLoaded((s) => (s.job ? { ...s, job: reply.job } : s)));
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, draft, askReplace, cancel, reload };
}

/** Shown before any count; each count answers with the limit the backend checks (D46). */
export const TOKEN_LIMIT = 32_000;

export type TokensState =
  | { kind: "none" }
  | { kind: "counting" }
  | { kind: "counted"; total: number; limit: number }
  /** The count was refused (Qwen not installed, a clip not transcribed any more): the reason, as a banner. */
  | { kind: "refused"; banner: Banner };

/**
 * The token count of the picked clips' Transcripts, in their order (D46), asked again
 * whenever the pick changes; an answer about an older pick is dropped.
 */
export function useTokens(clipIds: string[]): TokensState {
  const key = clipIds.join(",");
  const [state, , setIfMounted] = useMountedState<TokensState>({ kind: "none" });

  useEffect(() => {
    if (key === "") {
      setIfMounted({ kind: "none" });
      return;
    }
    let current = true;
    setIfMounted({ kind: "counting" });
    void (async () => {
      try {
        const reply = await getReply<{ total: number; limit: number } | Refusal>(tokensPath(key.split(",")));
        if (!current) return;
        if (reply.status === 200) {
          const { total, limit } = reply.body as { total: number; limit: number };
          setIfMounted({ kind: "counted", total, limit });
          return;
        }
        const banner = bannerOf(reply.status, refusalOf(reply.body));
        setIfMounted(banner ? { kind: "refused", banner } : { kind: "none" });
      } catch {
        if (current) setIfMounted({ kind: "none" });
      }
    })();
    return () => {
      current = false;
    };
  }, [key, setIfMounted]);

  return state;
}
