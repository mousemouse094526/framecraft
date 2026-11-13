import { useId, useState, type FormEvent } from "react";
import { Alert } from "../../../components/ui/Alert";
import { FixCommand } from "../../../components/ui/FixCommand";
import { GHOST_BUTTON, PRIMARY_BUTTON, SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import { useDrumRender } from "../hooks/useDrumRender";
import { useLessonEditor, type Editing } from "../hooks/useLessonEditor";
import { useListen } from "../hooks/useListen";
import type { PieceId } from "../lib/kit";
import {
  BPM_MAX,
  BPM_MIN,
  DRUMS_HASH,
  lengthOf,
  MAX_SECONDS,
  noteFor,
  noteIndexOf,
  notesPast,
  rendersHash,
  sameFields,
  STEPS_PER_BAR,
  type LessonFields,
  type Note,
} from "../lib/lesson";
import { isRendering, jobOf } from "../lib/render";
import { ChapterList } from "./ChapterList";
import { GrooveGrid } from "./GrooveGrid";
import { inputClass, Labeled } from "./Labeled";
import { NoteBox } from "./NoteBox";
import { RenderProgress } from "./RenderProgress";

/** หน้าแก้บทเรียนกลอง (`#/drums/{id}`) without the background, which comes later. The design is pending, so the app's own parts. */
export function LessonEditor({ id }: { id: string }) {
  const { state, edit, save } = useLessonEditor(id);

  return (
    <PageLayout tab="drums" wide>
      <div className="flex items-center gap-2">
        <a href={DRUMS_HASH} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับ
        </a>
        {state.kind === "ready" && (
          <>
            <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">{state.saved.title}</h2>
            <a href={rendersHash(id)} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
              ผล render
            </a>
          </>
        )}
      </div>
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "not_found" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">ไม่พบบทเรียนนี้</p>
          <a href={DRUMS_HASH} className={`h-11 px-4 text-brand sm:h-9 ${GHOST_BUTTON} hover:bg-muted`}>
            กลับรายการบทเรียน
          </a>
        </div>
      )}
      {state.kind === "ready" && <LessonForm editing={state} edit={edit} save={save} />}
    </PageLayout>
  );
}

type FormProps = {
  editing: Editing;
  edit: ReturnType<typeof useLessonEditor>["edit"];
  save: () => Promise<boolean>;
};

function LessonForm({ editing, edit, save }: FormProps) {
  const { form, errors } = editing;
  const id = useId();
  const listen = useListen(editing.id, save);
  // Only this page moves on to the results, and only for the render it started (D22).
  const render = useDrumRender((job, startedHere) => {
    if (startedHere && job.state === "done") window.location.hash = rendersHash(job.lesson_id);
  });
  /** The selected note's place, `piece:step`: its object changes with every edit. */
  const [selectedAt, setSelectedAt] = useState<string | null>(null);
  const unsaved = !sameFields(form, editing.saved);
  const notes = form.groove.notes;
  const selected = notes.find((note) => `${note.piece}:${note.step}` === selectedAt) ?? null;
  const invalid = new Set(
    Object.keys(errors)
      .map(noteIndexOf)
      .flatMap((index) => (index !== null && notes[index] ? [notes[index]] : [])),
  );
  const grooveErrors = Object.entries(errors).filter(([key]) => key.startsWith("groove"));
  // A refusal whose `field` has no input of its own (`chapters[0].speed`, `background`) still says why.
  const otherErrors = Object.entries(errors).filter(([key]) => !SHOWN_AT_INPUT.test(key));

  const setText = (key: "title" | "subtitle" | "caption") => (value: string) => edit((fields) => ({ ...fields, [key]: value }), (k) => k === key);
  const setGroove = (change: (groove: LessonFields["groove"]) => LessonFields["groove"]) =>
    edit((fields) => ({ ...fields, groove: change(fields.groove) }), (key) => key.startsWith("groove"));
  const setNotes = (change: (notes: Note[]) => Note[]) => setGroove((groove) => ({ ...groove, notes: change(groove.notes) }));

  const onCell = (piece: PieceId, step: number) => {
    const at = `${piece}:${step}`;
    if (notes.some((note) => `${note.piece}:${note.step}` === at)) {
      setSelectedAt(at === selectedAt ? null : at);
      return;
    }
    const note = noteFor(notes, piece, step);
    if (note) setNotes((now) => [...now, note]);
  };

  const onBars = (bars: number) => {
    const past = notesPast(notes, bars);
    if (past.length > 0 && !window.confirm(`ลดเหลือ ${bars} ห้อง โน้ต ${past.length} ตัวที่เลยห้องสุดท้ายจะถูกลบ`)) return;
    setGroove((groove) => ({ bars, notes: groove.notes.filter((note) => note.step < bars * STEPS_PER_BAR) }));
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void save();
  };

  return (
    <form onSubmit={submit} aria-busy={editing.saving} aria-label={editing.saved.title} className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Labeled label="หัวเรื่อง" htmlFor={`${id}-title`} error={errors.title}>
          <input id={`${id}-title`} value={form.title} aria-invalid={errors.title !== undefined} onChange={(e) => setText("title")(e.target.value)} className={inputClass(errors.title !== undefined)} />
        </Labeled>
        <Labeled label="BPM" htmlFor={`${id}-bpm`} error={errors.bpm}>
          <input
            id={`${id}-bpm`}
            type="number"
            min={BPM_MIN}
            max={BPM_MAX}
            value={Number.isNaN(form.bpm) ? "" : form.bpm}
            aria-invalid={errors.bpm !== undefined}
            onChange={(e) => edit((fields) => ({ ...fields, bpm: e.target.value === "" ? NaN : Number(e.target.value) }), (k) => k === "bpm")}
            className={inputClass(errors.bpm !== undefined)}
          />
        </Labeled>
        <Labeled label="บรรทัดรอง" htmlFor={`${id}-subtitle`} error={errors.subtitle}>
          <input id={`${id}-subtitle`} value={form.subtitle} aria-invalid={errors.subtitle !== undefined} onChange={(e) => setText("subtitle")(e.target.value)} className={inputClass(errors.subtitle !== undefined)} />
        </Labeled>
        <Labeled label="คำบรรยาย" htmlFor={`${id}-caption`} error={errors.caption}>
          <input id={`${id}-caption`} value={form.caption} aria-invalid={errors.caption !== undefined} onChange={(e) => setText("caption")(e.target.value)} className={inputClass(errors.caption !== undefined)} />
        </Labeled>
      </div>

      <section aria-label="Groove" className="flex flex-col gap-3">
        <h3 className="text-sm leading-[1.5] font-medium text-foreground">Groove</h3>
        <GrooveGrid bars={form.groove.bars} notes={notes} selected={selected} invalid={invalid} onCell={onCell} onBars={onBars} />
        {grooveErrors.map(([key, message]) => (
          <p key={key} className="font-button text-xs leading-4 text-destructive">
            {message}
          </p>
        ))}
        {selected && (
          <NoteBox
            notes={notes}
            note={selected}
            onChange={(next) => setNotes((now) => now.map((note) => (note === selected ? next : note)))}
            onDelete={() => {
              setNotes((now) => now.filter((note) => note !== selected));
              setSelectedAt(null);
            }}
          />
        )}
      </section>

      <ChapterList chapters={form.chapters} errors={errors} onChange={(chapters) => edit((fields) => ({ ...fields, chapters }), (key) => key.startsWith("chapters"))} />

      <div className="h-px bg-border" />

      <LengthLine fields={form} />
      {editing.failure && <Alert tone="error">{editing.failure}</Alert>}
      {otherErrors.map(([key, message]) => (
        <Alert key={key} tone="error">
          {message}
        </Alert>
      ))}

      <div className="flex flex-wrap items-start gap-3">
        <ListenControl fields={form} listen={listen} />
        <RenderControl id={editing.id} fields={form} render={render} save={save} />
        <div className="flex-1" />
        {editing.justSaved && !unsaved && (
          <p role="status" className="self-center text-[13px] leading-[1.5] text-success">
            บันทึกแล้ว
          </p>
        )}
        <button type="submit" disabled={!unsaved || editing.saving} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
          บันทึก
        </button>
      </div>
    </form>
  );
}

/** The `field`s an input or the grid shows beside itself. */
const SHOWN_AT_INPUT = /^(title|bpm|subtitle|caption|groove.*|chapters\[\d+\]\.(label|text))$/;

/** The clip's length against the 90 s cap: over it says by how much (D16, D21). */
function LengthLine({ fields }: { fields: LessonFields }) {
  const seconds = lengthOf(fields);
  if (!Number.isFinite(seconds)) return <p className="text-sm leading-5 text-mid">ความยาวคลิป — / {MAX_SECONDS} วินาที</p>;
  if (seconds > MAX_SECONDS) {
    return <p className="text-sm leading-5 font-medium text-destructive">ยาวเกิน {MAX_SECONDS} วินาทีไป {(seconds - MAX_SECONDS).toFixed(1)} วินาที</p>;
  }
  return (
    <p className="text-sm leading-5 text-mid">
      ความยาวคลิป {seconds.toFixed(1)} / {MAX_SECONDS} วินาที
    </p>
  );
}

/** ฟังจังหวะ with its error under it; can't be pressed while the clip is over the cap (D16). */
function ListenControl({ fields, listen }: { fields: LessonFields; listen: ReturnType<typeof useListen> }) {
  const seconds = lengthOf(fields);
  const mixing = listen.state.kind === "mixing";
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <button
        type="button"
        disabled={mixing || !Number.isFinite(seconds) || seconds > MAX_SECONDS}
        onClick={() => void listen.listen()}
        className={`h-11 w-fit px-4 sm:h-10 ${SECONDARY_BUTTON}`}
      >
        {mixing ? "กำลังผสมเสียง…" : "ฟังจังหวะ"}
      </button>
      {listen.state.kind === "refused" && (
        <div className="flex flex-col gap-2">
          <Alert tone="error">{listen.state.text}</Alert>
          {listen.state.fixes.map((fix) => (
            <FixCommand key={fix} command={fix} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * render: saves first, then starts the job; its percent and ยกเลิก while it runs; a failed or
 * cancelled one says so with ลองอีกครั้ง; another lesson's render names that lesson (D14, D22).
 * Can't be pressed over the cap (D16) or while any render runs.
 */
function RenderControl({ id, fields, render, save }: { id: string; fields: LessonFields; render: ReturnType<typeof useDrumRender>; save: () => Promise<boolean> }) {
  const seconds = lengthOf(fields);
  const running = isRendering(render.job) ? render.job : null;
  const own = jobOf(render.job, id);
  const start = async () => {
    if (await save()) await render.start(id);
  };
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <button
        type="button"
        disabled={running !== null || !Number.isFinite(seconds) || seconds > MAX_SECONDS}
        onClick={() => void start()}
        className={`h-11 w-fit px-4 sm:h-10 ${SECONDARY_BUTTON}`}
      >
        render
      </button>
      {running && running.lesson_id === id && (
        <div className="flex w-64 max-w-full items-center gap-3">
          <RenderProgress percent={running.percent} />
          <button type="button" onClick={() => void render.cancel()} className={`h-9 px-3 ${GHOST_BUTTON}`}>
            ยกเลิก
          </button>
        </div>
      )}
      {running && running.lesson_id !== id && <Alert tone="warning">กำลัง render {running.title} อยู่ รอให้เสร็จก่อน</Alert>}
      {!running && own && own.state !== "done" && (
        <div className="flex flex-col gap-2">
          <Alert tone="error">{own.state === "cancelled" ? "ยกเลิก render แล้ว" : (own.message ?? "render ไม่สำเร็จ")}</Alert>
          <button type="button" onClick={() => void start()} className={`h-9 w-fit px-3 ${GHOST_BUTTON}`}>
            ลองอีกครั้ง
          </button>
        </div>
      )}
      {render.refused && (
        <div className="flex flex-col gap-2">
          <Alert tone="error">{render.refused.text}</Alert>
          {render.refused.fixes.map((fix) => (
            <FixCommand key={fix} command={fix} />
          ))}
        </div>
      )}
    </div>
  );
}
