import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import { cancelCurrent, isRunning } from "../../../lib/job";
import { useMountedState } from "../../../lib/useMountedState";
import { usePollWhile } from "../../../lib/usePollWhile";
import { RENDERS_HASH } from "../lib/draft";
import {
  failureOf,
  RENDER_JOB_PATH,
  RENDERS_PATH,
  startJob,
  VOICE_JOB_PATH,
  VOICE_JOBS_PATH,
  type Banner,
  type Refused,
  type RenderJob,
  type SentencesJob,
  type StartReply,
} from "../lib/render";

type Kind = "voice" | "render";

export type JobsState = {
  /** The Voice job `sentences` followed until it ends. */
  voice: SentencesJob | null;
  /** The Render job followed until it ends. */
  render: RenderJob | null;
  /** A job that ended badly, or too little disk (Figma `Review banner`); `kind` is what ลองอีกครั้ง starts. */
  banner: (Banner & { kind: Kind }) | null;
  /** Any other refusal of a start, to show the user. */
  refused: Refused | null;
};

const START: JobsState = { voice: null, render: null, banner: null, refused: null };
const CURRENT: Record<Kind, string> = { voice: VOICE_JOB_PATH, render: RENDER_JOB_PATH };

/**
 * The voice and the render of ตรวจแก้บท (spoil-maker D30, D42, D51): the Voice job
 * `sentences` (สร้างเสียงใหม่ of a sentence, สร้างเสียงทั้งหมด) and the Render job, each
 * polled every second while it runs. `onChange` reads the draft again: a sentence voiced,
 * a job ended. A render that ends `done` opens ผล render. `onOffline` takes over when
 * the backend stops answering.
 */
export function useReviewJobs(onChange: () => void, onOffline: () => void) {
  const [state, , setIfMounted] = useMountedState<JobsState>(START);

  useEffect(() => {
    void (async () => {
      try {
        const [voice, render] = await Promise.all([
          getJson<SentencesJob | { kind: string; state: string } | null>(VOICE_JOB_PATH),
          getJson<RenderJob | null>(RENDER_JOB_PATH),
        ]);
        setIfMounted((s) => ({
          ...s,
          // A Voice job of the Saved voice page (`design_preview`) isn't this page's.
          voice: voice?.kind === "sentences" && isRunning(voice) ? (voice as SentencesJob) : null,
          render: isRunning(render) ? render : null,
        }));
      } catch {
        onOffline();
      }
    })();
  }, [onOffline, setIfMounted]);

  /** One poll's answer: still running → follow it (and read the draft when it moved on); ended → read the draft. */
  const follow = (kind: Kind, job: SentencesJob | RenderJob | null) => {
    const before = state[kind];
    if (job !== null && isRunning(job)) {
      setIfMounted((s) => ({ ...s, [kind]: job }));
      if (job.done !== before?.done || job.state !== before?.state) onChange(); // a sentence voiced, or voicing over
      return;
    }
    setIfMounted((s) => ({ ...s, [kind]: null, banner: job?.state === "failed" ? { ...failureOf(job), kind } : null }));
    onChange();
    if (kind === "render" && job?.state === "done") window.location.hash = RENDERS_HASH;
  };

  usePollWhile<SentencesJob | null>(state.voice !== null, VOICE_JOB_PATH, (job) => follow("voice", job), onOffline);
  usePollWhile<RenderJob | null>(state.render !== null, RENDER_JOB_PATH, (job) => follow("render", job), onOffline);

  const start = useCallback(
    async (kind: Kind, reply: StartReply<SentencesJob | RenderJob>) => {
      if (reply.kind === "started") {
        setIfMounted((s) => ({ ...s, [kind]: reply.job, banner: null, refused: null }));
        onChange(); // the draft reads locked now
      } else if (reply.kind === "busy") {
        const job = await getJson<SentencesJob | RenderJob | null>(CURRENT[kind]).catch(() => null);
        if (isRunning(job)) setIfMounted((s) => ({ ...s, [kind]: job }));
      } else if (reply.kind === "banner") {
        setIfMounted((s) => ({ ...s, banner: { ...reply.banner, kind } }));
      } else if (reply.kind === "refused") {
        setIfMounted((s) => ({ ...s, refused: reply.refused }));
      } else {
        onOffline();
      }
    },
    [onChange, onOffline, setIfMounted],
  );

  /** สร้างเสียง of these sentences, ready or not (D30). */
  const voice = useCallback(
    async (sentenceIds: string[]) =>
      start("voice", await startJob<SentencesJob>(VOICE_JOBS_PATH, { kind: "sentences", sentence_ids: sentenceIds })),
    [start],
  );

  const render = useCallback(async () => start("render", await startJob<RenderJob>(RENDERS_PATH, {})), [start]);

  /** ยกเลิก of whichever runs: sentences already voiced stay (spec › Voice job). */
  const cancel = useCallback(async () => {
    const kind: Kind = state.render ? "render" : "voice";
    const reply = await cancelCurrent<SentencesJob & RenderJob>(CURRENT[kind]);
    if (reply.kind === "cancelling") setIfMounted((s) => (s[kind] ? { ...s, [kind]: reply.job } : s));
    else if (reply.kind === "offline") onOffline();
  }, [onOffline, setIfMounted, state.render]);

  return { jobs: state, voice, render, cancel };
}
