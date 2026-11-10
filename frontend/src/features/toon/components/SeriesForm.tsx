import { useId, useState, type ReactNode } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import radioSelectedIcon from "../../../components/ui/assets/radio-selected.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import chevronUpIcon from "../assets/chevron-up.svg";
import radio18Icon from "../assets/radio-18.svg";
import radioSelected18Icon from "../assets/radio-selected-18.svg";
import radioIcon from "../assets/radio.svg";
import { VOICES_HASH, type SavedVoice } from "../../../lib/voices";
import { useSeriesForm } from "../hooks/useSeriesForm";
import {
  ACT_NAME_MAX,
  ACTS_MAX,
  CHANNEL_MAX,
  GENRE_DEFAULTS,
  GENRE_LABELS,
  LAYOUT_LABELS,
  LIST_HASH,
  NAME_MAX,
  seriesHash,
  STYLE_MAX,
  TONE_MAX,
  type Genre,
  type Layout,
  type SeriesFields,
} from "../lib/series";

const INPUT =
  "h-10 w-full rounded-lg border border-border bg-card px-3 text-sm leading-[1.5] text-foreground disabled:opacity-60";
const LABEL = "text-sm leading-[1.5] font-medium text-foreground";
const HINT = "text-xs leading-[1.5] text-muted-foreground";

/** `#/toon/new` and `#/toon/series/{sid}/settings`: ตั้งค่า Series (Figma toon / 2). */
export function SeriesForm({ sid }: { sid: string | null }) {
  const { state, save } = useSeriesForm(sid);
  const back = sid === null ? LIST_HASH : seriesHash(sid);

  return (
    <PageLayout tab="toon" wide>
      <div className="flex items-center gap-2">
        <a href={back} className={`h-8 px-3 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับ
        </a>
        <h2 className="text-xl leading-[1.5] font-semibold text-foreground">{sid === null ? "สร้าง Series" : "ตั้งค่า Series"}</h2>
      </div>
      {state.kind === "offline" ? (
        <OfflinePanel />
      ) : state.kind === "loading" ? (
        <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>
      ) : (
        <Form
          creating={sid === null}
          initial={state.initial}
          voices={state.voices}
          saving={state.saving}
          error={state.error}
          back={back}
          onSave={(fields) => void save(fields)}
        />
      )}
    </PageLayout>
  );
}

type FormProps = {
  creating: boolean;
  initial: SeriesFields;
  voices: SavedVoice[];
  saving: boolean;
  error: string | null;
  back: string;
  onSave: (fields: SeriesFields) => void;
};

function Form({ creating, initial, voices, saving, error, back, onSave }: FormProps) {
  const [fields, setFields] = useState<SeriesFields>(() => ({
    name: initial.name,
    channel_name: initial.channel_name,
    layout: initial.layout,
    genre: initial.genre,
    style: initial.style,
    tone: initial.tone,
    acts: initial.acts,
    voice_id: initial.voice_id,
    name_tags: initial.name_tags,
  }));
  const change = (patch: Partial<SeriesFields>) => setFields((f) => ({ ...f, ...patch }));
  // A genre sets style, tone and acts; the user edits them from there (D10, D11, D28, D41).
  const pickGenre = (genre: Genre) => change({ genre, ...GENRE_DEFAULTS[genre] });
  const ready = fields.name.trim() !== "" && fields.voice_id !== "" && fields.acts.every((act) => act.trim() !== "");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (ready) onSave(fields);
      }}
      className="flex w-full max-w-[720px] flex-col gap-5 rounded-2xl border border-border bg-card p-4 sm:p-6"
    >
      {error && <Alert tone="error">{error}</Alert>}
      <TextField
        label="ชื่อชุด"
        hint={`จำเป็น 1–${NAME_MAX} ตัวอักษร`}
        value={fields.name}
        max={NAME_MAX}
        onChange={(name) => change({ name })}
      />
      <TextField
        label="ชื่อช่อง (ไม่บังคับ)"
        hint={`ขึ้นด้านล่างของจอแบบกรอบดำ 0–${CHANNEL_MAX} ตัวอักษร`}
        value={fields.channel_name}
        max={CHANNEL_MAX}
        onChange={(channel_name) => change({ channel_name })}
      />
      <Group label="แบบจอ" hint={creating ? "เลือกได้ตอนสร้างเท่านั้น" : "แบบจอแก้ไม่ได้หลังสร้างชุด"}>
        <div role="radiogroup" aria-label="แบบจอ" className="flex flex-col gap-3 sm:flex-row">
          {(creating ? (["frame", "full"] as Layout[]) : [fields.layout]).map((layout) => (
            <LayoutOption
              key={layout}
              layout={layout}
              selected={fields.layout === layout}
              locked={!creating}
              onPick={() => change({ layout })}
            />
          ))}
        </div>
      </Group>
      {creating && (
        <Group label="แนว" hint="เลือกแล้วจะเติมสไตล์ภาพ น้ำเสียงเล่า และโครงองก์ให้ แก้ต่อได้">
          <div role="radiogroup" aria-label="แนว" className="flex gap-2">
            {(["horror", "comedy"] as Genre[]).map((genre) => (
              <GenreOption key={genre} genre={genre} selected={fields.genre === genre} onPick={() => pickGenre(genre)} />
            ))}
          </div>
        </Group>
      )}
      <TextArea
        label="สไตล์ภาพ (ภาษาอังกฤษ)"
        hint="ใช้กับทุกภาพในชุด"
        value={fields.style}
        max={STYLE_MAX}
        onChange={(style) => change({ style })}
      />
      <TextArea
        label="น้ำเสียงเล่า"
        hint="AI ใช้เขียนคำบรรยายทุก EP"
        value={fields.tone}
        max={TONE_MAX}
        onChange={(tone) => change({ tone })}
      />
      <Acts
        acts={fields.acts}
        hint={creating ? "แต่ละ EP แบ่งเป็นองก์ตามนี้" : "แก้แล้วมีผลกับ EP ใหม่เท่านั้น"}
        onChange={(acts) => change({ acts })}
      />
      <Group label="เสียงเล่าหลัก">
        {voices.length === 0 ? (
          <>
            <Alert tone="warning" title="ยังไม่มี Saved voice">
              สร้างเสียงที่ tab สปอยก่อน แล้วกลับมาเลือกที่นี่
            </Alert>
            <a href={VOICES_HASH} className={`h-8 w-fit px-3 ${OUTLINE_BUTTON}`}>
              ไปสร้างเสียงที่ tab สปอย
            </a>
          </>
        ) : (
          <VoiceSelect voices={voices} value={fields.voice_id} onChange={(voice_id) => change({ voice_id })} />
        )}
      </Group>
      <label className="flex items-center gap-3">
        <span className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <span className="text-sm font-medium text-foreground">ป้ายชื่อตัวละคร</span>
          <span className="text-xs text-muted-foreground">ขึ้นชื่อตัวละครบนภาพตลอดการ์ดแรกที่ตัวละครออก</span>
        </span>
        <Switch checked={fields.name_tags} onChange={(name_tags) => change({ name_tags })} />
      </label>
      <div className="h-px bg-border" />
      <div className="flex justify-end gap-3">
        <a href={back} className={`h-9 px-4 ${GHOST_BUTTON}`}>
          ยกเลิก
        </a>
        <button type="submit" disabled={!ready || saving} className={`h-9 px-4 ${PRIMARY_BUTTON}`}>
          บันทึก
        </button>
      </div>
    </form>
  );
}

function Group({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className={`${LABEL} mb-2`}>{label}</legend>
      {hint && <p className={`-mt-2 ${HINT}`}>{hint}</p>}
      {children}
    </fieldset>
  );
}

type TextProps = { label: string; hint: string; value: string; max: number; onChange: (value: string) => void };

function TextField({ label, hint, value, max, onChange }: TextProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className={LABEL}>
        {label}
      </label>
      <input id={id} value={value} maxLength={max} onChange={(e) => onChange(e.target.value)} className={INPUT} />
      <p className={HINT}>{hint}</p>
    </div>
  );
}

function TextArea({ label, hint, value, max, onChange }: TextProps) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className={LABEL}>
        {label}
      </label>
      <textarea
        id={id}
        value={value}
        maxLength={max}
        onChange={(e) => onChange(e.target.value)}
        className="h-24 w-full resize-none rounded-lg border border-border bg-card px-3 py-2.5 text-sm leading-[1.5] text-foreground"
      />
      <div className="flex gap-3 text-xs leading-[1.5]">
        <p className="min-w-0 flex-1 text-muted-foreground">{hint}</p>
        <p className="shrink-0 font-mono font-medium text-mid">
          {value.length} / {max}
        </p>
      </div>
    </div>
  );
}

type LayoutProps = { layout: Layout; selected: boolean; locked: boolean; onPick: () => void };

const LAYOUT_TEXT: Record<Layout, string> = {
  frame: "ภาพแนวนอนกลางจอ ชื่อเรื่องและป้าย EP ด้านบน ชื่อช่องด้านล่าง",
  full: "ภาพ 9:16 เต็มจอ ซับไตเติลสีขาวบนภาพ",
};

/** Figma `Toon/LayoutOption`: a radio card with a small 9:16 sketch of the layout. */
function LayoutOption({ layout, selected, locked, onPick }: LayoutProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      aria-disabled={locked}
      onClick={locked ? undefined : onPick}
      className={`flex flex-1 items-start gap-4 rounded-2xl p-4 text-left ${
        selected ? "border-2 border-brand-accent bg-accent-subtle" : "border border-border bg-card hover:bg-muted"
      } ${locked ? "cursor-default sm:max-w-[336px]" : ""}`}
    >
      <LayoutSketch layout={layout} />
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="flex items-center gap-2">
          <img src={selected ? radioSelected18Icon : radio18Icon} alt="" width={18} height={18} />
          <span className="text-sm leading-[1.5] font-semibold text-foreground">{LAYOUT_LABELS[layout]}</span>
        </span>
        <span className="text-[13px] leading-[1.5] text-mid">{LAYOUT_TEXT[layout]}</span>
      </span>
    </button>
  );
}

function LayoutSketch({ layout }: { layout: Layout }) {
  // Black frame: title bars on top, the picture in the middle, the channel at the bottom;
  // full: the picture fills the frame, white subtitle over it.
  return layout === "frame" ? (
    <span className="relative h-24 w-[54px] shrink-0 overflow-hidden rounded-lg bg-black">
      <span className="absolute top-2.5 left-1.5 h-1 w-[30px] bg-white" />
      <span className="absolute top-[9px] left-9 h-1.5 w-3 bg-brand" />
      <span className="absolute top-[33px] left-0 h-[30px] w-[54px] bg-accent-subtle" />
      <span className="absolute top-[84px] left-[15px] h-[3px] w-6 bg-white" />
    </span>
  ) : (
    <span className="relative h-24 w-[54px] shrink-0 overflow-hidden rounded-lg bg-accent-subtle">
      <span className="absolute top-[58px] left-[5px] h-[18px] w-11 bg-black" />
      <span className="absolute top-[62px] left-2 h-1 w-[38px] bg-white" />
      <span className="absolute top-[69px] left-3.5 h-1 w-[26px] bg-white" />
    </span>
  );
}


function GenreOption({ genre, selected, onPick }: { genre: Genre; selected: boolean; onPick: () => void }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onPick}
      className={`flex items-center gap-2 rounded-full px-4 py-2 ${
        selected ? "border-2 border-brand-accent bg-accent-subtle" : "border border-border bg-card hover:bg-muted"
      }`}
    >
      <img src={selected ? radioSelectedIcon : radioIcon} alt="" width={16} height={16} />
      <span className="text-sm leading-[1.5] font-medium text-foreground">{GENRE_LABELS[genre]}</span>
    </button>
  );
}

function Acts({ acts, hint, onChange }: { acts: string[]; hint: string; onChange: (acts: string[]) => void }) {
  const set = (i: number, name: string) => onChange(acts.map((act, j) => (j === i ? name : act)));
  const moveUp = (i: number) => onChange([...acts.slice(0, i - 1), acts[i], acts[i - 1], ...acts.slice(i + 1)]);
  const remove = (i: number) => onChange(acts.filter((_, j) => j !== i));

  return (
    <Group label="โครงองก์" hint={hint}>
      {acts.map((act, i) => (
        <div key={i} className="flex h-11 items-center gap-2">
          <span className="w-5 shrink-0 font-mono text-sm font-medium text-muted-foreground">{i + 1}</span>
          <input
            aria-label={`ชื่อองก์ ${i + 1}`}
            value={act}
            maxLength={ACT_NAME_MAX}
            onChange={(e) => set(i, e.target.value)}
            className={`min-w-0 flex-1 ${INPUT}`}
          />
          <IconButton label={`เลื่อนองก์ ${i + 1} ขึ้น`} icon={chevronUpIcon} disabled={i === 0} onClick={() => moveUp(i)} />
          <IconButton label={`ลบองก์ ${i + 1}`} icon={trashIcon} disabled={acts.length === 1} onClick={() => remove(i)} />
        </div>
      ))}
      {acts.some((act) => act.trim() === "") && <p className="text-xs leading-[1.5] text-destructive">ชื่อองก์ว่างไม่ได้</p>}
      {acts.length < ACTS_MAX && (
        <button type="button" onClick={() => onChange([...acts, ""])} className={`h-8 w-fit px-3 ${OUTLINE_BUTTON}`}>
          <img src={plusIcon} alt="" width={16} height={16} />
          เพิ่มองก์
        </button>
      )}
    </Group>
  );
}

function IconButton({ label, icon, disabled, onClick }: { label: string; icon: string; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex size-9 shrink-0 items-center justify-center rounded-lg hover:bg-muted disabled:opacity-40 disabled:hover:bg-transparent"
    >
      <img src={icon} alt="" width={16} height={16} />
    </button>
  );
}

function VoiceSelect({ voices, value, onChange }: { voices: SavedVoice[]; value: string; onChange: (id: string) => void }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="font-button text-sm leading-5 font-medium text-foreground">
        Saved voice
      </label>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`appearance-none pr-9 ${INPUT}`}
        >
          {voices.map((voice) => (
            <option key={voice.id} value={voice.id}>
              {voice.name}
            </option>
          ))}
        </select>
        <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute top-3 right-3" />
      </div>
    </div>
  );
}

function Switch({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full ${checked ? "bg-brand-accent" : "bg-border-disabled"}`}
    >
      <span
        className={`absolute top-0.5 size-4 rounded-full bg-white shadow-[0_1px_2px_rgba(0,0,0,0.15)] ${
          checked ? "left-[18px]" : "left-0.5"
        }`}
      />
    </button>
  );
}
