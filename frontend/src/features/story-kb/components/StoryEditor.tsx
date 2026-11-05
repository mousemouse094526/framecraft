import { useId, useState, type FormEvent, type ReactNode } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import circleCheckIcon from "../assets/circle-check.svg";
import { useStoryEditor, type Editing } from "../hooks/useStoryEditor";
import {
  ARTICLE_MAX,
  articleLength,
  characterErrorKeys,
  characterKey,
  CHARACTERS_MAX,
  grouped,
  sameFields,
  STORIES_HASH,
  type Character,
} from "../lib/story";
import { DeleteStoryDialog } from "./DeleteStoryDialog";

// The Figma `Field` input; red while its field has an error.
const inputClass = (error: boolean) =>
  `h-10 w-full rounded-lg border bg-card px-3 text-sm leading-5 text-foreground outline-none focus:border-2 focus:border-brand-accent ${
    error ? "border-destructive" : "border-border"
  }`;

/** Figma `แก้ Story`: `#/stories/new` (id `null`) or `#/stories/{id}`. */
export function StoryEditor({ id }: { id: string | null }) {
  const { state, edit, save, remove } = useStoryEditor(id);

  return (
    <PageLayout tab="stories">
      <div className="flex items-center gap-2">
        <a href={STORIES_HASH} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับ
        </a>
        {state.kind === "ready" && (
          <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">
            {state.id === null ? "เพิ่มเรื่อง" : state.saved.title}
          </h2>
        )}
      </div>
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "not_found" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">ไม่พบเรื่องนี้</p>
          <a href={STORIES_HASH} className={`h-11 px-4 text-brand sm:h-9 ${GHOST_BUTTON} hover:bg-muted`}>
            กลับคลังความรู้
          </a>
        </div>
      )}
      {state.kind === "ready" && <StoryForm editing={state} edit={edit} onSave={save} onDelete={remove} />}
    </PageLayout>
  );
}

type FormProps = {
  editing: Editing;
  edit: ReturnType<typeof useStoryEditor>["edit"];
  onSave: () => Promise<void>;
  onDelete: () => Promise<void>;
};

function StoryForm({ editing, edit, onSave, onDelete }: FormProps) {
  const { form, errors, saving } = editing;
  const [asking, setAsking] = useState(false);
  const [added, setAdded] = useState<number | null>(null);
  const titleId = useId();
  const articleId = useId();
  const unsaved = !sameFields(form, editing.saved);
  const articleCount = articleLength(form.article);

  const characterErrors = characterErrorKeys(errors);

  const setCharacter = (index: number, change: Partial<Character>) =>
    edit(
      (fields) => ({ ...fields, characters: fields.characters.map((c, i) => (i === index ? { ...c, ...change } : c)) }),
      // A duplicate name's error may sit on another row; every name is checked again on save.
      "name" in change ? characterErrors : [characterKey(index, "description")],
    );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void onSave();
  };

  return (
    <form
      onSubmit={submit}
      aria-busy={saving}
      aria-label={editing.id === null ? "เพิ่มเรื่อง" : editing.saved.title}
      className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-4 sm:p-6"
    >
      <Field label="ชื่อเรื่อง" htmlFor={titleId} error={errors.title}>
        <input
          id={titleId}
          value={form.title}
          aria-invalid={errors.title !== undefined}
          onChange={(event) => edit((fields) => ({ ...fields, title: event.target.value }), ["title"])}
          className={inputClass(errors.title !== undefined)}
        />
      </Field>

      <div className="flex flex-col gap-2">
        <label htmlFor={articleId} className="text-sm leading-[1.5] font-medium text-foreground">
          บทความ
        </label>
        <textarea
          id={articleId}
          value={form.article}
          aria-invalid={errors.article !== undefined}
          aria-describedby={`${articleId}-count`}
          onChange={(event) => edit((fields) => ({ ...fields, article: event.target.value }), ["article"])}
          className={`h-[180px] w-full resize-y rounded-lg border bg-card px-3 py-2.5 text-sm leading-[1.5] text-foreground outline-none focus:border-2 focus:border-brand-accent ${
            // Figma `Article field` error: border/error, darker than the input's destructive red.
            errors.article !== undefined ? "border-error-border" : "border-border"
          }`}
        />
        {errors.article && <p className="text-xs leading-[1.5] text-destructive">{errors.article}</p>}
        <div className="flex gap-3 text-xs leading-[1.5]">
          <p className="min-w-0 flex-1 text-muted-foreground">เรื่องย่อ ปม และบทบาทตัวละคร ใช้เป็นพื้นหลังให้ AI</p>
          <p
            id={`${articleId}-count`}
            className={`shrink-0 font-mono font-medium whitespace-nowrap ${articleCount > ARTICLE_MAX ? "text-destructive" : "text-mid"}`}
          >
            {grouped(articleCount)} / {grouped(ARTICLE_MAX)}
          </p>
        </div>
      </div>

      <section aria-label="ตัวละคร" className="flex flex-col gap-3">
        <div className="flex items-center gap-2 leading-[1.5]">
          <h3 className="text-sm font-medium text-foreground">ตัวละคร</h3>
          <span className="font-mono text-xs font-medium text-muted-foreground">
            {form.characters.length} / {CHARACTERS_MAX}
          </span>
        </div>
        {errors.characters && <p className="text-xs leading-4 text-destructive">{errors.characters}</p>}
        {form.characters.map((character, index) => (
          <CharacterRow
            key={index}
            index={index}
            character={character}
            autoFocus={added === index}
            nameError={errors[characterKey(index, "name")]}
            descriptionError={errors[characterKey(index, "description")]}
            onChange={(change) => setCharacter(index, change)}
            onRemove={() => {
              setAdded(null);
              edit((fields) => ({ ...fields, characters: fields.characters.filter((_, i) => i !== index) }), characterErrors);
            }}
          />
        ))}
        {form.characters.length < CHARACTERS_MAX && (
          <button
            type="button"
            onClick={() => {
              setAdded(form.characters.length);
              edit((fields) => ({ ...fields, characters: [...fields.characters, { name: "", description: "" }] }), ["characters"]);
            }}
            className={`h-11 w-fit px-4 sm:h-9 ${OUTLINE_BUTTON}`}
          >
            <img src={plusIcon} alt="" width={16} height={16} />
            เพิ่มตัวละคร
          </button>
        )}
      </section>

      <div className="h-px bg-border" />

      {editing.failure && <Alert tone="error">{editing.failure}</Alert>}

      <div className="flex flex-wrap items-center gap-3">
        {editing.id !== null && (
          <button type="button" onClick={() => setAsking(true)} className={`h-11 px-4 sm:h-9 ${GHOST_BUTTON} hover:bg-muted`}>
            <img src={trashIcon} alt="" width={16} height={16} />
            ลบเรื่อง
          </button>
        )}
        <div className="flex-1" />
        {editing.justSaved && !unsaved && (
          <p role="status" className="flex items-center gap-1.5 text-[13px] leading-[1.5] text-success">
            <img src={circleCheckIcon} alt="" width={16} height={16} />
            บันทึกแล้ว
          </p>
        )}
        <button type="submit" disabled={!unsaved || saving} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
          บันทึก
        </button>
      </div>

      {asking && (
        <DeleteStoryDialog
          title={editing.saved.title}
          clips={editing.clips}
          onCancel={() => setAsking(false)}
          onDelete={async () => {
            setAsking(false);
            await onDelete();
          }}
        />
      )}
    </form>
  );
}

function Field({ label, htmlFor, error, children }: { label: string; htmlFor: string; error?: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <label htmlFor={htmlFor} className="font-button text-sm leading-5 font-medium text-foreground">
        {label}
      </label>
      {children}
      {error && <p className="font-button text-xs leading-4 text-destructive">{error}</p>}
    </div>
  );
}

type RowProps = {
  index: number;
  character: Character;
  autoFocus: boolean;
  nameError?: string;
  descriptionError?: string;
  onChange: (change: Partial<Character>) => void;
  onRemove: () => void;
};

/** Figma `Character row`: ชื่อ, คำอธิบายสั้น, then the trash; on a phone the description goes under the name. */
function CharacterRow({ index, character, autoFocus, nameError, descriptionError, onChange, onRemove }: RowProps) {
  const nameId = useId();
  const descriptionId = useId();
  const who = character.name.trim() || `ตัวที่ ${index + 1}`;
  return (
    <div role="group" aria-label={`ตัวละคร ${index + 1}`} className="flex flex-wrap items-start gap-2">
      <div className="min-w-0 flex-1 sm:w-[180px] sm:flex-none">
        <Field label="ชื่อ" htmlFor={nameId} error={nameError}>
          <input
            id={nameId}
            autoFocus={autoFocus}
            value={character.name}
            aria-invalid={nameError !== undefined}
            onChange={(event) => onChange({ name: event.target.value })}
            className={inputClass(nameError !== undefined)}
          />
        </Field>
      </div>
      <div className="order-last basis-full sm:order-none sm:min-w-0 sm:flex-1 sm:basis-0">
        <Field label="คำอธิบายสั้น" htmlFor={descriptionId} error={descriptionError}>
          <input
            id={descriptionId}
            value={character.description}
            aria-invalid={descriptionError !== undefined}
            onChange={(event) => onChange({ description: event.target.value })}
            className={inputClass(descriptionError !== undefined)}
          />
        </Field>
      </div>
      <div className="pt-7">
        <button
          type="button"
          aria-label={`ลบตัวละคร ${who}`}
          onClick={onRemove}
          className="flex size-10 items-center justify-center rounded-lg hover:bg-muted sm:size-9"
        >
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
    </div>
  );
}
