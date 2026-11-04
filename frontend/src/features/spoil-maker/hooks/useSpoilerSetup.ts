import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { CLIPS_PATH, type TempClip } from "../../../lib/clips";
import { cancelCurrent, onlyWhen } from "../../../lib/job";
import { refusalLine, refusalOf, type Refusal } from "../../../lib/refusal";
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
  VOICES_PATH,
  type Draft,
  type DraftJob,
  type EpRange,
  type Layout,
  type Style,
} from "../lib/draft";
import type { Voice } from "./useVoices";
import { useStepsRefresh } from "./useStepStatus";

/** What ร่างบท sends with `kind: "draft"`: one EP of one clip, by its number and range (spoil-maker D66, D71). */
export type Order = { clip_id: string; ep: EpRange; style: Style; layout: Layout; target_s: number; voice_id: string };

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
      /** The clip of the Spoil draft: picked when the page opens (spec › Frontend). */
      draftClipId: string | null;
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
  if (status === 409 && refusal.code === "gpu_busy") return { kind: "gpu_busy", text: refusalLine(refusal).text };
  if (status === 503 && refusal.code === "not_ready") return { kind: "not_ready", text: refusal.message };
  return { kind: "refused", text: refusal.message };
}

/**
 * Step 1 of the สปอย tab, ตั้งค่าคลิปสปอย: the clips to pick from, the Saved voices, the
 * remembered voice, whether a Spoil draft is there and of which clip, and the one Draft
 * job behind ร่างบท (spoil-maker D25, D28, D66). Polls the job every second while it runs and opens
 * ตรวจแก้บท when it is done. Any failure on load or poll is offline.
 */
export function useSpoilerSetup() {
  const [state, setState, setIfMounted] = useMountedState<SetupState>({ kind: "loading" });
  const refreshSteps = useStepsRefresh();

  const load = useCallback(async () => {
    try {
      const [{ clips }, voices, settings, draft, job] = await Promise.all([
        getJson<{ clips: TempClip[] }>(CLIPS_PATH),
        getJson<Voice[]>(VOICES_PATH),
        getJson<{ last_voice_id: string | null }>(SETTINGS_PATH),
        getJson<Draft | null>(DRAFT_PATH),
        getJson<DraftJob | null>(DRAFT_JOB_PATH),
      ]);
      setIfMounted({
        kind: "loaded",
        clips,
        voices,
        lastVoiceId: settings.last_voice_id,
        draftExists: draft !== null,
        draftClipId: draft?.clip_id ?? null,
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

  /**
   * ร่างบท, or ร่างทับ with `replace` once the user agreed to lose the draft there (D28).
   * Resolves to the refusal's code when the API refused, so the page can read the EPs again.
   */
  const draft = useCallback(
    async (order: Order, replace: boolean): Promise<string | null> => {
      setIfMounted(whenLoaded((s) => ({ ...s, banner: null, confirmingReplace: false })));
      try {
        const reply = await sendJson<DraftJob | Refusal>("POST", DRAFT_JOBS_PATH, { kind: "draft", ...order, replace });
        if (reply.status === 202) {
          const job = reply.body as DraftJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job })));
          refreshSteps();
          return null;
        }
        const refusal = refusalOf(reply.body);
        if (reply.status === 409 && refusal?.code === "draft_exists") {
          setIfMounted(whenLoaded((s) => ({ ...s, draftExists: true, confirmingReplace: true })));
          return refusal.code;
        }
        if (reply.status === 409 && refusal?.code === "busy") {
          const job = await getJson<DraftJob | null>(DRAFT_JOB_PATH);
          if (job !== null && isDrafting(job)) setIfMounted(whenLoaded((s) => ({ ...s, job })));
          refreshSteps();
          return refusal.code;
        }
        // `episodes_changed`, `ep_empty`, `transcript_too_long` and the rest say the API's message (spec › Frontend).
        const banner = bannerOf(reply.status, refusal);
        if (banner && refusal) {
          setIfMounted(whenLoaded((s) => ({ ...s, banner })));
          return refusal.code;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
      return null;
    },
    [refreshSteps, setIfMounted],
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
      refreshSteps();
    } else if (reply.kind !== "ended") {
      setIfMounted({ kind: "offline" });
    }
  }, [refreshSteps, setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, draft, askReplace, cancel, reload };
}
