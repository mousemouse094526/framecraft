import { useId } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import chevronDownIcon from "../assets/chevron-down.svg";
import radioSelectedIcon from "../assets/radio-selected.svg";
import radioIcon from "../assets/radio.svg";
import { VOICES_HASH, type DraftJob, type Layout, type Style } from "../lib/draft";
import type { Episode } from "../hooks/useEpisodes";
import type { RefusalLine } from "../../../lib/refusal";
import type { Voice } from "../hooks/useVoices";

// The styles and the layout each starts with (spoil-maker D7, D8).
export const STYLES: { id: Style; label: string; layout: Layout }[] = [
  { id: "fast", label: "ปั่นตัดเร็ว", layout: "A" },
  { id: "drama", label: "เล่าละครหักมุม", layout: "B" },
  { id: "chrono", label: "เล่าตามลำดับ", layout: "C" },
];
const LAYOUTS: Layout[] = ["A", "B", "C"];
export const TARGET_MIN = 30;
export const TARGET_MAX = 180;

export type Settings = { style: Style; layout: Layout; targetS: number; voiceId: string | null };

type Props = {
  settings: Settings;
  voices: Voice[];
  /** The picked EP, or null; `limit` is the token count the backend checks (D46), null until the EPs are read. */
  ep: Episode | null;
  limit: number | null;
  /** Why ร่างบท is off for the picked EP: no lines, or no token count (D71); null when it isn't. */
  epBlocked: RefusalLine | null;
  /** An EP to draft from, a voice, and its lines within 32,000 tokens (D46). */
  canDraft: boolean;
  job: DraftJob | null;
  confirmingReplace: boolean;
  onChange: (settings: Settings) => void;
  onDraft: () => void;
  onReplace: () => void;
  onKeep: () => void;
  onCancel: () => void;
};

const LABEL = "text-sm leading-[21px] font-medium text-foreground";

/** Figma `Settings card` of ตั้งค่าคลิปสปอย: style, layout, length, voice, the token meter and ร่างบท. */
export function SetupSettings(props: Props) {
  const { settings, voices, ep, limit, epBlocked, canDraft, job, onChange } = props;
  const drafting = job !== null;
  const lengthId = useId();
  const voiceId = useId();

  return (
    <section
      aria-label="ตั้งค่า"
      className="flex min-w-0 flex-1 flex-col gap-5 rounded-2xl border border-border bg-card p-4"
    >
      <fieldset disabled={drafting} className="flex flex-col gap-2">
        <legend className={`${LABEL} mb-2`}>สไตล์</legend>
        <div className="flex flex-col gap-2 sm:flex-row">
          {STYLES.map((style) => (
            <StyleOption
              key={style.id}
              label={style.label}
              selected={settings.style === style.id}
              // Picking a style picks its layout (D8); the layout can change after.
              onSelect={() => onChange({ ...settings, style: style.id, layout: style.layout })}
            />
          ))}
        </div>
      </fieldset>
      <fieldset disabled={drafting} className="flex flex-col gap-2">
        <legend className={`${LABEL} mb-2`}>Layout</legend>
        <div className="flex gap-2">
          {LAYOUTS.map((layout) => (
            <LayoutOption
              key={layout}
              layout={layout}
              selected={settings.layout === layout}
              onSelect={() => onChange({ ...settings, layout })}
            />
          ))}
        </div>
      </fieldset>
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-sm leading-5 font-medium text-foreground">
          <label htmlFor={lengthId} className="flex-1">
            ความยาว
          </label>
          <span className="font-mono whitespace-nowrap">{settings.targetS} วินาที</span>
        </div>
        <input
          id={lengthId}
          type="range"
          min={TARGET_MIN}
          max={TARGET_MAX}
          step={1}
          value={settings.targetS}
          disabled={drafting}
          onChange={(event) => onChange({ ...settings, targetS: Number(event.target.value) })}
          className="h-11 w-full accent-brand-accent"
        />
        <div className="flex justify-between font-mono text-xs leading-4 text-muted-foreground">
          <span>{TARGET_MIN}</span>
          <span>{TARGET_MAX}</span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <label htmlFor={voices.length > 0 ? voiceId : undefined} className={`${LABEL} flex-1`}>
            เสียงบรรยาย
          </label>
          {voices.length > 0 && (
            <a href={VOICES_HASH} className="font-button text-sm leading-5 font-medium text-link hover:underline">
              จัดการเสียง
            </a>
          )}
        </div>
        {voices.length === 0 ? (
          <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm leading-5">
            <span className="text-mid">ยังไม่มีเสียงบรรยาย</span>
            <a href={VOICES_HASH} className="flex h-11 items-center font-button font-medium text-brand hover:underline">
              สร้างเสียงบรรยาย
            </a>
          </p>
        ) : (
          <div className="relative">
            <select
              id={voiceId}
              value={settings.voiceId ?? ""}
              disabled={drafting}
              onChange={(event) => onChange({ ...settings, voiceId: event.target.value })}
              className="h-10 w-full appearance-none rounded-lg border border-border bg-card px-3 pr-9 font-button text-sm leading-5 text-foreground"
            >
              {voices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.name}
                </option>
              ))}
            </select>
            <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute top-3 right-3" />
          </div>
        )}
      </div>
      <TokenMeter tokens={ep?.tokens ?? null} limit={limit} />
      <div className="h-px bg-border" />
      <DraftAction {...props} canDraft={canDraft} />
      {epBlocked && job === null && (
        <p className="flex flex-wrap items-center gap-x-3 text-[13px] leading-5 text-mid">
          {epBlocked.text}
          {epBlocked.setupLink && (
            <a href="#/setup" className="flex h-11 items-center font-button font-medium text-brand hover:underline">
              ไปที่ Setup status
            </a>
          )}
        </p>
      )}
    </section>
  );
}

function StyleOption({ label, selected, onSelect }: { label: string; selected: boolean; onSelect: () => void }) {
  return (
    <label
      className={`flex h-12 cursor-pointer items-center gap-2.5 rounded-lg border px-3 has-disabled:cursor-default sm:flex-1 ${
        selected ? "border-brand-accent bg-accent-subtle" : "border-border bg-card"
      }`}
    >
      <input type="radio" name="style" checked={selected} onChange={onSelect} className="sr-only" />
      <img src={selected ? radioSelectedIcon : radioIcon} alt="" width={16} height={16} />
      <span className={`flex-1 text-sm leading-[21px] ${selected ? "font-semibold text-link" : "font-medium text-foreground"}`}>
        {label}
      </span>
    </label>
  );
}

/** Figma component `Layout option`: a drawing of the 1080×1920 video under each choice (D8). */
function LayoutOption({ layout, selected, onSelect }: { layout: Layout; selected: boolean; onSelect: () => void }) {
  return (
    <label
      className={`flex flex-1 cursor-pointer flex-col items-center gap-2 rounded-lg px-3 py-2.5 has-disabled:cursor-default sm:w-24 sm:flex-none ${
        selected ? "border-2 border-brand-accent bg-accent-subtle" : "border border-border bg-card"
      }`}
    >
      <input type="radio" name="layout" checked={selected} onChange={onSelect} aria-label={`Layout ${layout}`} className="sr-only" />
      <LayoutDrawing layout={layout} />
      <span className="flex items-center gap-1.5">
        <img src={selected ? radioSelectedIcon : radioIcon} alt="" width={16} height={16} />
        <span className={`text-sm leading-[21px] ${selected ? "font-semibold text-link" : "font-medium text-foreground"}`}>
          {layout}
        </span>
      </span>
    </label>
  );
}

function LayoutDrawing({ layout }: { layout: Layout }) {
  if (layout === "A") {
    // Blurred background, tall picture, a 2-line hook on top, big short subtitles in the middle.
    return (
      <span className="relative h-20 w-[45px] overflow-hidden rounded bg-border-strong">
        <span className="absolute -top-1.5 -left-1.5 h-[92px] w-[57px] bg-preview-blur blur-[2px]" />
        <span className="absolute top-4 left-[9px] h-12 w-[27px] rounded-[2px] bg-muted-foreground" />
        <span className="absolute top-[5px] left-1.5 h-[3px] w-[33px] rounded-[1px] bg-card" />
        <span className="absolute top-2.5 left-2.5 h-[3px] w-[25px] rounded-[1px] bg-card" />
        <span className="absolute top-[38px] left-2 h-[5px] w-[29px] rounded-[1px] bg-card" />
      </span>
    );
  }
  if (layout === "B") {
    // Black, a 16:9 picture in the middle, up to 2 lines of subtitles under it.
    return (
      <span className="relative h-20 w-[45px] overflow-hidden rounded bg-surface-inverse">
        <span className="absolute top-7 left-[3px] h-[22px] w-[39px] bg-border-strong" />
        <span className="absolute top-[54px] left-[7px] h-0.5 w-[31px] rounded-[1px] bg-card" />
        <span className="absolute top-[58px] left-[11px] h-0.5 w-[23px] rounded-[1px] bg-card" />
      </span>
    );
  }
  // Black, a 16:9 picture high up, a yellow episode title with a red outline on top.
  return (
    <span className="relative h-20 w-[45px] overflow-hidden rounded bg-surface-inverse">
      <span className="absolute top-[5px] left-1.5 h-[5px] w-[33px] rounded-[1px] border border-destructive bg-preview-title" />
      <span className="absolute top-4 left-[3px] h-[22px] w-[39px] bg-border-strong" />
    </span>
  );
}

/** Figma component `Token meter`: the picked EP's "{tokens} / 32,000"; over the limit it turns red with an alert (D46). */
function TokenMeter({ tokens, limit }: { tokens: number | null; limit: number | null }) {
  const total = tokens ?? 0;
  const over = limit !== null && total > limit;
  const percent = limit === null ? 0 : Math.min(100, Math.round((total * 100) / limit));
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2 text-sm leading-[21px] text-foreground">
        <span className="flex-1 font-button font-medium">Transcript</span>
        <span className={`font-mono font-medium whitespace-nowrap ${over ? "text-destructive" : ""}`}>
          {tokens === null ? "—" : total.toLocaleString("en-US")} / {limit?.toLocaleString("en-US") ?? "—"}
        </span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={`absolute inset-y-0 left-0 rounded-[4px] ${over ? "bg-destructive" : "bg-brand-accent"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      {over && (
        <Alert tone="error">
          <span className="block text-destructive">
            Transcript ของ EP นี้ {total.toLocaleString("en-US")} token เกิน {limit?.toLocaleString("en-US")}
          </span>
          <span className="block">ลดความยาวต่อ EP หรือเลื่อนจุดตัด</span>
        </Alert>
      )}
    </div>
  );
}

/** Figma component `Draft action`: ร่างบท, the ask before replacing a draft, and the drafting steps (D72). */
function DraftAction({ canDraft, job, confirmingReplace, onDraft, onReplace, onKeep, onCancel }: Props) {
  if (job) {
    // Only picking counts; writing and polishing don't (spec › Draft job).
    const counting = job.state === "matching";
    const done = job.done ?? 0;
    const total = job.total ?? 0;
    const step = counting ? "กำลังเลือกภาพ" : job.state === "polishing" ? "กำลังเรียบเรียง" : "กำลังเขียนบท";
    const headline = job.cancel_requested ? "กำลังยกเลิก…" : step;
    return (
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <div className="flex items-center gap-2 text-sm leading-[21px] text-foreground">
            <span className="flex-1 font-medium">{headline}</span>
            {counting && <span className="font-mono font-medium">{`${done}/${total}`}</span>}
          </div>
          <ProgressBar
            percent={counting ? (total ? Math.floor((done * 100) / total) : 0) : "unknown"}
            label="ความคืบหน้าการร่างบท"
            cancelling={job.cancel_requested}
          />
        </div>
        <button
          type="button"
          onClick={onCancel}
          disabled={job.cancel_requested}
          className={`h-11 w-full px-6 sm:h-10 sm:w-auto ${OUTLINE_BUTTON}`}
        >
          ยกเลิก
        </button>
      </div>
    );
  }
  if (confirmingReplace) {
    return (
      <div className="flex flex-col gap-2">
        <Alert tone="warning">มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม</Alert>
        <div className="flex gap-2">
          <button type="button" autoFocus onClick={onReplace} className={`h-11 flex-1 px-6 sm:h-10 sm:flex-none ${PRIMARY_BUTTON}`}>
            ร่างทับ
          </button>
          <button type="button" onClick={onKeep} className={`h-11 flex-1 px-6 sm:h-10 sm:flex-none ${OUTLINE_BUTTON}`}>
            ยกเลิก
          </button>
        </div>
      </div>
    );
  }
  return (
    <button type="button" onClick={onDraft} disabled={!canDraft} className={`h-11 w-full px-6 sm:h-10 ${PRIMARY_BUTTON} disabled:opacity-50`}>
      ร่างบท
    </button>
  );
}
