import { useCallback, useEffect } from "react";
import { getJson, sendJson } from "../../../lib/api";
import { useMountedState } from "../../../lib/useMountedState";
import { notice, type Notice } from "./notice";
import { refusalOf, type Refusal } from "./refusal";
import { usePollWhile } from "./usePollWhile";
import { CLIPS_PATH, type TempClip } from "./useTempClips";

// The shape of a Transcribe job (backend.spoil.transcribe.TranscribeJob, spec › API).
export type TranscribeJobState = "preparing" | "transcribing" | "done" | "failed" | "cancelled";

export type TranscribeJob = {
  clip_id: string;
  state: TranscribeJobState;
  percent: number | null;
  cancel_requested: boolean;
  error: { code: string; message: string } | null;
};

// `{id}.transcript.json` (spec › Transcribe).
export type TranscriptLine = { start_s: number; end_s: number; text: string };

export type Transcript = {
  clip_id: string;
  language: string | null;
  duration_s: number | null;
  model: string;
  revision: string;
  transcribed_at: string;
  lines: TranscriptLine[];
};

export type TranscribeState =
  | { kind: "loading" }
  | { kind: "offline" }
  | {
      kind: "loaded";
      /** The clip in the panel and its player, or null (D25). */
      selectedId: string | null;
      /** The user clicked the row, so the player starts; a clip selected for its running job waits. */
      autoPlay: boolean;
      /** Only ever an unfinished job, of any clip; a finished one becomes the notice. */
      job: TranscribeJob | null;
      /** The message under the selected clip's title (D33); it goes when another clip is selected. */
      notice: Notice | null;
      /** The selected clip's Transcript, once loaded. */
      transcript: Transcript | null;
    };

type Loaded = Extract<TranscribeState, { kind: "loaded" }>;

const TRANSCRIPTIONS_PATH = "/api/spoil/transcriptions";
const CURRENT_PATH = "/api/spoil/transcriptions/current";

const UNFINISHED: TranscribeJobState[] = ["preparing", "transcribing"];

function isUnfinished(job: TranscribeJob): boolean {
  return UNFINISHED.includes(job.state);
}

export function transcriptPath(clipId: string): string {
  return `${CLIPS_PATH}/${clipId}/transcript`;
}

/** What a finished job says in the panel (spec › Frontend, D33). */
function resultNotice(job: TranscribeJob): Notice {
  if (job.state === "done") return notice("success", "ถอดเสร็จ", job.clip_id);
  if (job.state === "cancelled") return notice("info", "ยกเลิกแล้ว", job.clip_id);
  return notice("error", job.error?.message ?? "ถอดไม่สำเร็จ", job.clip_id);
}

/** Applies `change` only once the panel is loaded. */
function whenLoaded(change: (state: Loaded) => TranscribeState) {
  return (previous: TranscribeState): TranscribeState => (previous.kind === "loaded" ? change(previous) : previous);
}

/**
 * The transcript panel: which clip is selected, its Transcript, and the one
 * Transcribe job (D24). Checks the current job on mount, selecting its clip
 * when unfinished; polls every second only while a job is unfinished, apart
 * from the download's poll. Any failure (no backend, a status the API never
 * sends, 30 s) is offline. `onClipsChanged` (stable) loads the list again:
 * when a followed job ends or is lost (ถอดแล้ว may change) and when a clip
 * turns out to be gone. `onNotReady` (stable) runs on a `503` POST, so the
 * status is checked again.
 */
export function useTranscribe(onClipsChanged: () => void, onNotReady: () => void) {
  const [state, setState, setIfMounted] = useMountedState<TranscribeState>({ kind: "loading" });

  /**
   * Loads a clip's Transcript into the panel if that clip is still selected.
   * A `404` for a clip the list calls ถอดแล้ว (`expected`) loads the list again;
   * otherwise it just means the clip has none yet.
   */
  const loadTranscript = useCallback(
    async (clipId: string, expected: boolean) => {
      try {
        const reply = await sendJson<Transcript>("GET", transcriptPath(clipId));
        if (reply.status === 200) {
          const transcript = reply.body as Transcript;
          setIfMounted(whenLoaded((s) => (s.selectedId === clipId ? { ...s, transcript } : s)));
        } else if (reply.status === 404) {
          // The file went some other way (deleted by hand): the list shows it isn't ถอดแล้ว.
          if (expected) onClipsChanged();
        } else {
          setIfMounted({ kind: "offline" });
        }
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [onClipsChanged, setIfMounted],
  );

  const load = useCallback(async () => {
    try {
      const job = await getJson<TranscribeJob | null>(CURRENT_PATH);
      // Opening the tab on an unfinished job selects its clip (spec › Frontend).
      const running = job !== null && isUnfinished(job) ? job : null;
      setIfMounted({
        kind: "loaded",
        selectedId: running?.clip_id ?? null,
        autoPlay: false,
        job: running,
        notice: null,
        transcript: null,
      });
      // A clip being transcribed again keeps its old Transcript if the job is cancelled or fails.
      if (running) void loadTranscript(running.clip_id, false);
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [loadTranscript, setIfMounted]);

  useEffect(() => {
    void load();
  }, [load]);

  const tracking = state.kind === "loaded" && state.job !== null;

  usePollWhile<TranscribeJob | null>(
    tracking,
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
          const shown = job === null ? notice("warning", "งานถอดหายเพราะ backend เริ่มใหม่ ลองถอดอีกครั้ง", clipId) : resultNotice(job);
          // The message is about the job's clip; another clip in the panel keeps its own.
          return { ...s, job: null, notice: clipId === s.selectedId ? shown : s.notice };
        }),
      );
      onClipsChanged();
      // `done` has a new Transcript; `cancelled` and `failed` leave the old one, if any, which may not be loaded.
      if (job !== null) void loadTranscript(job.clip_id, job.state === "done");
    },
    () => setIfMounted({ kind: "offline" }),
  );

  /** Puts a clip in the panel (`null` empties it); a clip ถอดแล้ว loads its Transcript. */
  const select = useCallback(
    (clip: TempClip | null) => {
      setState(whenLoaded((s) => ({ ...s, selectedId: clip?.id ?? null, autoPlay: true, notice: null, transcript: null })));
      if (clip?.transcribed) void loadTranscript(clip.id, true);
    },
    [loadTranscript, setState],
  );

  const start = useCallback(
    async (clipId: string) => {
      setIfMounted(whenLoaded((s) => ({ ...s, notice: null })));
      try {
        const reply = await sendJson<TranscribeJob | Refusal>("POST", TRANSCRIPTIONS_PATH, { clip_id: clipId });
        if (reply.status === 202) {
          const job = reply.body as TranscribeJob;
          setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        const code = refusalOf(reply.body)?.code;
        if (reply.status === 409 && code === "busy") {
          // Whichever clip it is, follow it: this clip shows its progress, another names it.
          const job = await getJson<TranscribeJob | null>(CURRENT_PATH);
          if (job !== null && isUnfinished(job)) setIfMounted(whenLoaded((s) => ({ ...s, job })));
          return;
        }
        if (reply.status === 404 && code === "not_found") {
          setIfMounted(whenLoaded((s) => ({ ...s, notice: notice("error", "ไม่พบคลิปนี้", clipId) })));
          onClipsChanged();
          return;
        }
        if (reply.status === 503 && code === "not_ready") {
          onNotReady();
          return;
        }
        setIfMounted({ kind: "offline" });
      } catch {
        setIfMounted({ kind: "offline" });
      }
    },
    [onClipsChanged, onNotReady, setIfMounted],
  );

  const cancel = useCallback(async () => {
    try {
      const reply = await sendJson<TranscribeJob | Refusal>("DELETE", CURRENT_PATH);
      if (reply.status === 202) {
        const job = reply.body as TranscribeJob;
        setIfMounted(whenLoaded((s) => (s.job ? { ...s, job } : s)));
      } else if (reply.status !== 404) {
        // 404: the job ended before the cancel arrived; the next poll shows how.
        setIfMounted({ kind: "offline" });
      }
    } catch {
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  const reload = useCallback(() => {
    setState({ kind: "loading" });
    void load();
  }, [load, setState]);

  return { state, select, start, cancel, reload };
}
