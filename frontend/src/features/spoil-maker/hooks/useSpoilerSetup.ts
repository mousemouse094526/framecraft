import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { CLIPS_PATH, type TempClip } from "../../../lib/clips";
import { onlyWhen } from "../../../lib/job";
import { refusalLine, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { BUSY_TEXT, DRAFT_PATH, REVIEW_HASH, sendDraft, SETTINGS_PATH, VOICES_PATH, type Draft, type DraftAsk } from "../lib/draft";
import type { Voice } from "./useVoices";
import { useDraftRun, useJobCalls } from "./useStepStatus";

/**
 * A page-level message (Figma `Setup banner`): the GPU held by another job, an install
 * missing a row with a link to ติดตั้ง, or the API's message. A failed draft shows on
 * ตรวจแก้บท (D83).
 */
export type Banner =
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
 * remembered voice, and whether a Spoil draft is there and of which clip (spoil-maker D25,
 * D28, D66). ร่างบท puts its job in the steps' state and opens ตรวจแก้บท, which follows it
 * (D81). Any failure on load is offline.
 */
export function useSpoilerSetup() {
  const [state, setState, setIfMounted] = useMountedState<SetupState>({ kind: "loading" });
  const { refreshSteps } = useJobCalls();
  const run = useDraftRun();

  const load = useCallback(async () => {
    try {
      const [{ clips }, voices, settings, draft] = await Promise.all([
        getJson<{ clips: TempClip[] }>(CLIPS_PATH),
        getJson<Voice[]>(VOICES_PATH),
        getJson<{ last_voice_id: string | null }>(SETTINGS_PATH),
        getJson<Draft | null>(DRAFT_PATH),
      ]);
      setIfMounted({
        kind: "loaded",
        clips,
        voices,
        lastVoiceId: settings.last_voice_id,
        draftExists: draft !== null,
        draftClipId: draft?.clip_id ?? null,
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

  /**
   * ร่างบท, or ร่างทับ with `replace` once the user agreed to lose the draft there (D28).
   * Resolves to the refusal's code when the API refused, so the page can read the EPs again.
   */
  const draft = useCallback(
    async (order: DraftAsk, replace: boolean): Promise<string | null> => {
      setIfMounted(whenLoaded((s) => ({ ...s, banner: null, confirmingReplace: false })));
      const reply = await sendDraft(order, replace);
      if (reply.kind === "started") {
        // In the steps' state before the hash changes: ตรวจแก้บท opens on the job, not on no draft (D87).
        run.show(reply.job);
        refreshSteps();
        window.location.hash = REVIEW_HASH;
        return null;
      }
      if (reply.kind === "refused") {
        const { status, refusal } = reply;
        if (status === 409 && refusal?.code === "draft_exists") {
          setIfMounted(whenLoaded((s) => ({ ...s, draftExists: true, confirmingReplace: true })));
          return refusal.code;
        }
        if (status === 409 && refusal?.code === "busy") {
          // Another tab drafts: the steps read its job, which locks this page (D87).
          setIfMounted(whenLoaded((s) => ({ ...s, banner: { kind: "refused", text: BUSY_TEXT } })));
          refreshSteps();
          return refusal.code;
        }
        // `episodes_changed`, `ep_empty`, `transcript_too_long` and the rest say the API's message (spec › Frontend).
        const banner = bannerOf(status, refusal);
        if (banner && refusal) {
          setIfMounted(whenLoaded((s) => ({ ...s, banner })));
          return refusal.code;
        }
      }
      setIfMounted({ kind: "offline" });
      return null;
    },
    [refreshSteps, run, setIfMounted],
  );

  /** ร่างบท with a Spoil draft there asks first (Figma Draft action › replace confirm). */
  const askReplace = useCallback(
    (asking: boolean) => setIfMounted(whenLoaded((s) => ({ ...s, confirmingReplace: asking }))),
    [setIfMounted],
  );

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, draft, askReplace, reload };
}
