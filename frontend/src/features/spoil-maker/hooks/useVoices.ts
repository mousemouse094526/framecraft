import { useCallback, useEffect } from "react";
import { getJson, headStatus, sendJson } from "../../../lib/api";
import { GPU_JOB_PATHS, gpuBusyText } from "../../../lib/gpu";
import { isRunning, isUnfinishedIn, onlyWhen } from "../../../lib/job";
import { refusalOf, type Refusal } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";

// The shapes of GET /voices and the Voice job (backend.spoil_maker.voices, spoil-maker spec › API).
export type Voice = {
  id: string;
  name: string;
  speed: number;
  chars_per_s: number;
  created_at: string;
  in_use: boolean;
};

export type VoiceJobState = "voicing" | "done" | "failed" | "cancelled";

export type VoiceJob = {
  kind: "design_preview" | "sentences";
  state: VoiceJobState;
  error: { code: string; message: string } | null;
  cancel_requested: boolean;
  started_at: string;
};

/** What the user picks before สุ่ม (spoil-maker spec › Saved voice step 1). */
export type Choices = { gender: string; age: string; pitch: string; speed: number };

/** `setupLink` when the install is missing a row the job needs (`not_ready`, spec › Frontend). */
export type DesignError = { text: string; setupLink: boolean };

/** The GPU job that keeps สุ่ม disabled, and the `…/current` that says when it ends. */
export type GpuHolder = { running: string; path: string };

export type VoicesState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      voices: Voice[];
      /** An unfinished `design_preview`, followed until it ends. */
      job: VoiceJob | null;
      /** The `started_at` of the job whose preview is there to hear and save, or null: it tells
       * one preview from the next (the audio URL's `?v=`, a fresh name field). */
      previewVersion: string | null;
      gpu: GpuHolder | null;
      error: DesignError | null;
    };

type Loaded = Extract<VoicesState, { kind: "loaded" }>;

/** Why a save, rename or delete was refused, to show the user; null when it went through. */
export type RefusalText = string | null;

const VOICES_PATH = "/api/spoil-maker/voices";
const JOBS_PATH = "/api/spoil-maker/voice-jobs";
const CURRENT_PATH = "/api/spoil-maker/voice-jobs/current";
const PREVIEW_PATH = "/api/spoil-maker/voice-jobs/preview.wav";

/** The preview's audio; `version` skips the browser's copy of an older one (spoil-maker spec › Frontend). */
export function previewUrl(version: string): string {
  return `${PREVIEW_PATH}?v=${encodeURIComponent(version)}`;
}

export function sampleUrl(voiceId: string): string {
  return `${VOICES_PATH}/${voiceId}/sample.wav`;
}

const OFFLINE_TEXT = "ติดต่อ backend ไม่ได้";

const isUnfinished = isUnfinishedIn<VoiceJobState>(["voicing"]);

/** A model or a child that stopped says the same thing (spoil-maker spec › Frontend); the rest say the API's message. */
function failureText(job: VoiceJob): string {
  const code = job.error?.code;
  if (code === "crashed" || code === "model_failed") return "งานหยุดกลางทาง";
  return job.error?.message ?? "สร้างเสียงไม่สำเร็จ";
}

const whenLoaded = (change: (state: Loaded) => VoicesState) => onlyWhen<VoicesState, "loaded">("loaded", change);

/** The GPU job running now, if it is one the page can follow. */
async function gpuHolder(): Promise<GpuHolder | null> {
  for (const [running, path] of Object.entries(GPU_JOB_PATHS)) {
    if (isRunning(await getJson<{ state: string } | null>(path))) return { running, path };
  }
  return null;
}

/**
 * The Saved voice page (spoil-maker D32, D43): the list, and the one Voice job
 * `design_preview` behind สุ่ม. Checks the list, the current job and the other
 * GPU jobs on mount; polls the Voice job every second while it runs, and the
 * job holding the GPU until it ends. Any failure on load or poll is offline.
 */
export function useVoices() {
  const [state, setState, setIfMounted] = useMountedState<VoicesState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const [voices, job, gpu] = await Promise.all([
        getJson<Voice[]>(VOICES_PATH),
        getJson<VoiceJob | null>(CURRENT_PATH),
        gpuHolder(),
      ]);
      const previewJob = job?.kind === "design_preview" ? job : null;
      // A done job's preview may be saved already (saving takes it away): ask whether it is still there.
      const previewThere = previewJob?.state === "done" && (await headStatus(PREVIEW_PATH)) === 200;
      setIfMounted({
        kind: "loaded",
        voices,
        job: previewJob && isUnfinished(previewJob) ? previewJob : null,
        previewVersion: previewThere ? previewJob.started_at : null,
        gpu,
        error: null,
      });
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const loaded = state.kind === "loaded" ? state : null;

  usePollWhile<VoiceJob | null>(
    loaded?.job != null,
    CURRENT_PATH,
    (job) => {
      if (job !== null && isUnfinished(job)) {
        setIfMounted(whenLoaded((s) => ({ ...s, job })));
        return;
      }
      // Polls run only while a job is followed, so any other answer is its end.
      setIfMounted(
        whenLoaded((s) => ({
          ...s,
          job: null,
          previewVersion: job?.state === "done" ? job.started_at : s.previewVersion,
          error: job?.state === "failed" ? { text: failureText(job), setupLink: false } : null,
        })),
      );
    },
    () => setIfMounted({ kind: "offline" }),
  );

  usePollWhile<{ state: string } | null>(
    loaded?.gpu != null,
    loaded?.gpu?.path ?? "",
    (job) => {
      if (!isRunning(job)) setIfMounted(whenLoaded((s) => ({ ...s, gpu: null })));
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** สุ่ม: a new `design_preview` replaces the preview once it is done. */
  const design = useCallback(
    async (choices: Choices) => {
      setIfMounted(whenLoaded((s) => ({ ...s, error: null })));
      try {
        const reply = await sendJson<VoiceJob | Refusal>("POST", JOBS_PATH, { kind: "design_preview", ...choices });
        const refusal = refusalOf(reply.body);
        if (reply.status === 202) {
          const job = reply.body as VoiceJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        if (reply.status === 409 && refusal?.code === "busy") {
          const job = await getJson<VoiceJob | null>(CURRENT_PATH);
          if (job !== null && isUnfinished(job)) setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        if (reply.status === 409 && refusal?.code === "gpu_busy") {
          const running = refusal.running ?? "";
          const path = GPU_JOB_PATHS[running];
          // A job the page can't follow names itself, but สุ่ม stays pressable to try again.
          setIfMounted(
            whenLoaded((s) =>
              path
                ? { ...s, gpu: { running, path } }
                : { ...s, error: { text: gpuBusyText(running), setupLink: false } },
            ),
          );
          return;
        }
        if (reply.status === 503 && refusal?.code === "not_ready") {
          setIfMounted(whenLoaded((s) => ({ ...s, error: { text: refusal.message, setupLink: true } })));
          return;
        }
        if (refusal) {
          setIfMounted(whenLoaded((s) => ({ ...s, error: { text: refusal.message, setupLink: false } })));
          return;
        }
      } catch {
        // offline, below
      }
      setIfMounted({ kind: "offline" });
    },
    [setIfMounted],
  );

  /** บันทึก: the preview becomes a Saved voice on top of the list. */
  const save = useCallback(
    async (name: string): Promise<RefusalText> => {
      try {
        const reply = await sendJson<Voice | Refusal>("POST", VOICES_PATH, { name });
        if (reply.status === 201) {
          const voice = reply.body as Voice;
          setIfMounted(whenLoaded((s) => ({ ...s, voices: [voice, ...s.voices], previewVersion: null })));
          return null;
        }
        const refusal = refusalOf(reply.body);
        if (reply.status === 409 && refusal?.code === "no_preview") {
          // Saved elsewhere, or the backend restarted: there is nothing left to save.
          setIfMounted(whenLoaded((s) => ({ ...s, previewVersion: null, error: { text: refusal.message, setupLink: false } })));
          return null;
        }
        if (refusal) return refusal.message;
      } catch {
        // below
      }
      return OFFLINE_TEXT;
    },
    [setIfMounted],
  );

  const rename = useCallback(
    async (id: string, name: string): Promise<RefusalText> => {
      try {
        const reply = await sendJson<Voice | Refusal>("PATCH", `${VOICES_PATH}/${id}`, { name });
        if (reply.status === 200) {
          const voice = reply.body as Voice;
          setIfMounted(whenLoaded((s) => ({ ...s, voices: s.voices.map((v) => (v.id === id ? voice : v)) })));
          return null;
        }
        if (reply.status === 404) {
          setIfMounted(whenLoaded((s) => ({ ...s, voices: s.voices.filter((v) => v.id !== id) })));
          return null;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) return refusal.message;
      } catch {
        // below
      }
      return OFFLINE_TEXT;
    },
    [setIfMounted],
  );

  /** ลบ, after the row's confirm. A voice already gone leaves the list too. */
  const remove = useCallback(
    async (id: string): Promise<RefusalText> => {
      try {
        const reply = await sendJson<Refusal>("DELETE", `${VOICES_PATH}/${id}`);
        if (reply.status === 204 || reply.status === 404) {
          setIfMounted(whenLoaded((s) => ({ ...s, voices: s.voices.filter((v) => v.id !== id) })));
          return null;
        }
        const refusal = refusalOf(reply.body);
        if (refusal) return refusal.message;
      } catch {
        // below
      }
      return OFFLINE_TEXT;
    },
    [setIfMounted],
  );

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, design, save, rename, remove, reload };
}
