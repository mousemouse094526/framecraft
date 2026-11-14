import { useId, useState, type FormEvent } from "react";
import { Alert } from "../../../components/ui/Alert";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import copyIcon from "../../../components/ui/assets/copy.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import plusWhiteIcon from "../../../components/ui/assets/plus-white.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { editedAt, formatDuration } from "../../../lib/format";
import { useDrumRender } from "../hooks/useDrumRender";
import { useLessons } from "../hooks/useLessons";
import { lessonHash, TITLE_MAX, type LessonRow } from "../../../lib/lesson";
import { renderingOf } from "../lib/render";

/** รายการบทเรียนกลอง (`#/drums`): newest edit first; new, copy and delete (D10). The design is pending, so the app's own parts. */
export function LessonList() {
  const { state, reload, create, copy, remove } = useLessons();
  // A render that ends may add to its lesson's count.
  const { job } = useDrumRender(() => void reload());
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<LessonRow | null>(null);

  if (state.kind === "offline") {
    return (
      <PageLayout tab="drums" action={<RefreshButton onClick={() => void reload()} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  return (
    <PageLayout tab="drums">
      <div className="flex items-center gap-3">
        <h2 className="min-w-0 flex-1 text-xl leading-[1.5] font-semibold text-foreground">บทเรียนกลอง</h2>
        <button type="button" onClick={() => setCreating(true)} className={`flex h-11 items-center gap-2 px-4 sm:h-9 ${PRIMARY_BUTTON}`}>
          <img src={plusWhiteIcon} alt="" width={16} height={16} />
          บทเรียนใหม่
        </button>
      </div>
      {state.kind === "result" && state.failure && <Alert tone="error">{state.failure}</Alert>}
      <section aria-label="บทเรียนทั้งหมด" aria-busy={state.kind === "loading"} className="overflow-hidden rounded-2xl border border-border bg-card">
        {state.kind === "loading" ? (
          <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
        ) : state.lessons.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-4 py-12">
            <p className="text-sm leading-[1.5] text-mid">ยังไม่มีบทเรียนกลอง</p>
            <button type="button" onClick={() => setCreating(true)} className={`h-11 px-4 sm:h-9 ${OUTLINE_BUTTON}`}>
              <img src={plusIcon} alt="" width={16} height={16} />
              สร้างบทเรียนแรก
            </button>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {state.lessons.map((lesson) => (
              <Row
                key={lesson.id}
                lesson={lesson}
                renderingPercent={renderingOf(job, lesson.id)?.percent ?? null}
                onCopy={() => void copy(lesson.id)}
                onDelete={() => setDeleting(lesson)}
              />
            ))}
          </ul>
        )}
      </section>
      {creating && <NewLessonDialog create={create} onClose={() => setCreating(false)} />}
      {deleting && (
        <DeleteLessonDialog
          lesson={deleting}
          onCancel={() => setDeleting(null)}
          onDelete={() => {
            setDeleting(null);
            void remove(deleting.id);
          }}
        />
      )}
    </PageLayout>
  );
}

/** `renderingPercent`: how far the render running on this lesson is, or null (D22). */
function Row({ lesson, renderingPercent, onCopy, onDelete }: { lesson: LessonRow; renderingPercent: number | null; onCopy: () => void; onDelete: () => void }) {
  return (
    <li className="flex items-center gap-1 pr-2">
      <a href={lessonHash(lesson.id)} className="flex min-w-0 flex-1 flex-col gap-0.5 py-3 pl-4 leading-[1.5] hover:bg-muted">
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate text-sm font-medium text-foreground">{lesson.title}</span>
          {renderingPercent !== null && (
            <span className="shrink-0 rounded-full bg-accent-subtle px-2 font-button text-xs leading-5 font-medium text-link">กำลัง render {renderingPercent}%</span>
          )}
        </span>
        <span className="flex flex-wrap gap-x-1.5 text-[13px] text-mid">
          <span>{formatDuration(Math.round(lesson.length_s))}</span>
          <span className="text-muted-foreground">·</span>
          <span>render {lesson.renders} ครั้ง</span>
          <span className="text-muted-foreground">·</span>
          <span>แก้ล่าสุด {editedAt(lesson.updated_at)}</span>
        </span>
      </a>
      <button type="button" aria-label={`ทำซ้ำ ${lesson.title}`} onClick={onCopy} className={`size-10 ${GHOST_BUTTON} hover:bg-muted`}>
        <img src={copyIcon} alt="" width={16} height={16} />
      </button>
      <button type="button" aria-label={`ลบ ${lesson.title}`} onClick={onDelete} className={`size-10 ${GHOST_BUTTON} hover:bg-muted`}>
        <img src={trashIcon} alt="" width={16} height={16} />
      </button>
    </li>
  );
}

/** Asks the new lesson's title; the API's refusal stays in the dialog. */
function NewLessonDialog({ create, onClose }: { create: (title: string) => Promise<string | null>; onClose: () => void }) {
  const titleId = useId();
  const inputId = useId();
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    const refused = await create(title.trim());
    setBusy(false);
    if (refused) setError(refused);
    else onClose();
  };

  return (
    <ModalDialog titleId={titleId} onClose={onClose} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold text-foreground">
        บทเรียนใหม่
      </h3>
      <form onSubmit={(event) => void submit(event)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label htmlFor={inputId} className="font-button text-sm leading-5 font-medium text-foreground">
            หัวเรื่อง
          </label>
          <input
            id={inputId}
            autoFocus
            value={title}
            maxLength={TITLE_MAX}
            onChange={(event) => {
              setTitle(event.target.value);
              setError(null);
            }}
            className="h-10 w-full rounded-lg border border-border bg-card px-3 text-sm leading-5 text-foreground outline-none focus:border-2 focus:border-brand-accent"
          />
          {error && <p className="font-button text-xs leading-4 text-destructive">{error}</p>}
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className={`h-11 px-6 sm:h-10 ${OUTLINE_BUTTON}`}>
            ยกเลิก
          </button>
          <button type="submit" disabled={busy || !title.trim()} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
            สร้าง
          </button>
        </div>
      </form>
    </ModalDialog>
  );
}

/** Focus starts on ยกเลิก; says how many renders go with the lesson (D10). */
function DeleteLessonDialog({ lesson, onCancel, onDelete }: { lesson: LessonRow; onCancel: () => void; onDelete: () => void }) {
  const titleId = useId();
  return (
    <ModalDialog titleId={titleId} onClose={onCancel} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold break-words text-foreground">
        ลบ {lesson.title}?
      </h3>
      <p className="text-sm leading-[1.5] text-mid">
        {lesson.renders > 0 ? `ผล render ${lesson.renders} รายการจะหายไปด้วย` : "ยังไม่มีผล render"}
      </p>
      <div className="flex justify-end gap-2">
        <button type="button" autoFocus onClick={onCancel} className={`h-11 px-6 sm:h-10 ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
        <button type="button" onClick={onDelete} className={`h-11 px-6 sm:h-10 ${DESTRUCTIVE_BUTTON}`}>
          ลบ
        </button>
      </div>
    </ModalDialog>
  );
}
