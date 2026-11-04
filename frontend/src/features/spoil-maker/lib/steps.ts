// What each step of the สปอย tab says under its name (spoil-maker D68, D71).
import { isRunning } from "../../../lib/job";
import { epLabel, wholeDraft, type Draft, type DraftJob } from "./draft";
import type { RenderJob, RenderResult, SentencesJob } from "./render";

/** What the steps read; `undefined` is not read yet (no line), a job is the latest of its kind or null. */
export type StepStatus = {
  draft: Draft | null | undefined;
  renders: RenderResult[] | undefined;
  draftJob: DraftJob | null;
  /** The Voice job `sentences` only: a `design_preview` belongs to the Saved voice page. */
  voiceJob: SentencesJob | null;
  renderJob: RenderJob | null;
};

/** A step's status line (empty until read) and whether a job of that step runs. */
export type StepLine = { text: string; busy: boolean };

/** One line per step, in the steps' order. */
export type StepLines = [StepLine, StepLine, StepLine];

export function stepLines(status: StepStatus): StepLines {
  return [clipLine(status.draft, status.draftJob), reviewLine(status), renderLine(status.renderJob, status.renders)];
}

function clipLine(draft: Draft | null | undefined, job: DraftJob | null): StepLine {
  // While a whole new draft is written, step 1 names what it is written from (D87).
  const drafting = wholeDraft(job);
  if (drafting && isRunning(drafting)) return { text: `${drafting.order.clip_title} · ${epLabel(drafting.order.ep.n)}`, busy: false };
  if (draft === undefined) return { text: "", busy: false };
  return { text: draft ? `${draft.clip_title} · ${epLabel(draft.ep.n)}` : "ยังไม่เลือก", busy: false };
}

function reviewLine({ draft, draftJob, voiceJob }: StepStatus): StepLine {
  const count = draft === undefined ? "" : draft ? `${draft.sentences.length} ประโยค` : "ยังไม่มีบท";
  // The newer of the two says what step 2 does; a failure shows until a job starts again.
  const job = latest(draftJob, voiceJob);
  if (job === null) return { text: count, busy: false };
  const busy = isRunning(job);
  if (job.kind === "sentences") {
    if (busy) return { text: `สร้างเสียง ${countOf(job)}`, busy };
    return { text: job.state === "failed" ? "สร้างเสียงไม่สำเร็จ" : count, busy };
  }
  // A `pick` is one sentence's Shots: the count stays, with the spinner (spec › Frontend).
  if (job.kind === "pick") return { text: count, busy };
  if (job.state === "polishing") return { text: "กำลังเรียบเรียง", busy };
  if (job.kind === "polish") return { text: job.state === "failed" ? "เรียบเรียงไม่สำเร็จ" : count, busy };
  if (job.state === "writing") return { text: "กำลังร่าง", busy };
  if (job.state === "matching") return { text: `กำลังเลือกภาพ ${countOf(job)}`, busy };
  return { text: job.state === "failed" ? "ร่างบทไม่สำเร็จ" : count, busy };
}

function renderLine(job: RenderJob | null, renders: RenderResult[] | undefined): StepLine {
  if (job !== null && isRunning(job)) {
    if (job.state === "voicing") return { text: `render: สร้างเสียง ${countOf(job)}`, busy: true };
    return { text: job.percent === null ? "render…" : `render ${job.percent}%`, busy: true };
  }
  if (job?.state === "failed") return { text: "render ไม่สำเร็จ", busy: false };
  if (renders === undefined) return { text: "", busy: false };
  return { text: renders.length > 0 ? `${renders.length} คลิป` : "ยังไม่มี", busy: false };
}

/** "x/y" of a job that counts sentences. */
const countOf = (job: { done: number | null; total: number | null }) => `${job.done ?? 0}/${job.total ?? 0}`;

function latest(a: DraftJob | null, b: SentencesJob | null): DraftJob | SentencesJob | null {
  if (a === null || b === null) return a ?? b;
  return Date.parse(b.started_at) > Date.parse(a.started_at) ? b : a;
}
