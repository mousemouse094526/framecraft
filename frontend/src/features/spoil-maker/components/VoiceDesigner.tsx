import { useId, useState } from "react";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { gpuBusyText } from "../../../lib/gpu";
import type { RefusalLine } from "../../../lib/refusal";
import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import refreshIcon from "../../../components/ui/assets/refresh-cw.svg";
import refreshWhiteIcon from "../assets/refresh-cw-white.svg";
import { previewUrl, type Choices, type GpuHolder, type RefusalText } from "../hooks/useVoices";
import { playAudio } from "../lib/audio";
import { NameForm } from "./NameForm";

// OmniVoice's `instruct` values with the words the page shows (spoil-maker spec › Saved voice step 1).
const GENDERS = [
  { value: "male", label: "ชาย" },
  { value: "female", label: "หญิง" },
];
const AGES = [
  { value: "child", label: "เด็ก" },
  { value: "teenager", label: "วัยรุ่น" },
  { value: "young adult", label: "วัยหนุ่มสาว" },
  { value: "middle-aged", label: "วัยกลางคน" },
  { value: "elderly", label: "สูงอายุ" },
];
const PITCHES = [
  { value: "very low pitch", label: "ต่ำมาก" },
  { value: "low pitch", label: "ต่ำ" },
  { value: "moderate pitch", label: "กลาง" },
  { value: "high pitch", label: "สูง" },
  { value: "very high pitch", label: "สูงมาก" },
];

const FIRST_CHOICES: Choices = { gender: "male", age: "young adult", pitch: "moderate pitch", speed: 1 };

type Props = {
  /** A `design_preview` is running. */
  generating: boolean;
  /** Tells one preview from the next (`previewVersion` of the hook), or null when there is none. */
  previewVersion: string | null;
  gpu: GpuHolder | null;
  error: RefusalLine | null;
  onDesign: (choices: Choices) => void;
  onSave: (name: string) => Promise<RefusalText>;
};

/** Figma component `Voice designer`: no preview, generating, GPU busy, preview ready (spoil-maker D32, D35). */
export function VoiceDesigner({ generating, previewVersion, gpu, error, onDesign, onSave }: Props) {
  const [choices, setChoices] = useState<Choices>(FIRST_CHOICES);
  const reasonId = useId();
  const pick = (change: Partial<Choices>) => setChoices((c) => ({ ...c, ...change }));
  const ready = previewVersion !== null && !generating;
  const disabled = generating || gpu !== null;
  const reason = gpu ? gpuBusyText(gpu.running) : null;

  return (
    <section
      aria-label="ออกแบบเสียง"
      className="flex w-full shrink-0 flex-col gap-4 rounded-2xl border border-border bg-card p-4 lg:w-[520px]"
    >
      <h2 className="text-base leading-6 font-semibold text-foreground">ออกแบบเสียง</h2>
      <div className="flex flex-col gap-4">
        <GenderField value={choices.gender} onChange={(gender) => pick({ gender })} />
        <div className="flex flex-col gap-4 sm:flex-row sm:gap-3">
          <Select label="วัย" options={AGES} value={choices.age} onChange={(age) => pick({ age })} />
          <Select label="ระดับเสียง" options={PITCHES} value={choices.pitch} onChange={(pitch) => pick({ pitch })} />
        </div>
        <SpeedSlider value={choices.speed} onChange={(speed) => pick({ speed })} />
      </div>

      <div className={`flex w-full gap-2 sm:items-center sm:gap-3 ${ready ? "" : "flex-col items-start sm:flex-row"}`}>
        {generating && (
          <div className="flex w-full flex-col gap-1.5 sm:min-w-0 sm:flex-1">
            <p className="text-[13px] leading-5 text-mid">กำลังสุ่มเสียง…</p>
            <ProgressBar percent="unknown" label="กำลังสุ่มเสียง" />
          </div>
        )}
        {ready && (
          <button
            type="button"
            onClick={() => playAudio(previewUrl(previewVersion))}
            className={`h-11 min-w-0 flex-1 px-6 sm:h-10 sm:flex-none ${OUTLINE_BUTTON}`}
          >
            ฟัง
          </button>
        )}
        <button
          type="button"
          disabled={disabled}
          aria-describedby={reason ? reasonId : undefined}
          onClick={() => onDesign(choices)}
          className={`flex h-11 items-center justify-center gap-2 px-6 sm:h-10 ${
            ready ? `min-w-0 flex-1 sm:flex-none ${OUTLINE_BUTTON}` : `w-full sm:w-auto ${PRIMARY_BUTTON} disabled:opacity-50`
          }`}
        >
          <img src={ready ? refreshIcon : refreshWhiteIcon} alt="" width={16} height={16} />
          สุ่ม
        </button>
        {reason && (
          <p id={reasonId} className="text-[13px] leading-5 text-mid sm:min-w-0 sm:flex-1">
            {reason}
          </p>
        )}
      </div>
      {error && (
        <p role="alert" className="text-[13px] leading-5 text-destructive">
          {error.text}
          {error.setupLink && (
            <>
              {" "}
              <a href="#/setup" className="font-medium text-link underline">
                ไปหน้าติดตั้ง
              </a>
            </>
          )}
        </p>
      )}

      {ready && (
        <>
          <div className="h-px w-full bg-border" />
          {/* A new preview starts a new name: the key resets the field. */}
          <NameForm key={previewVersion} onSave={onSave} buttonClass="h-11 w-full px-6 sm:h-10 sm:w-auto" />
        </>
      )}
    </section>
  );
}

function GenderField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const labelId = useId();
  return (
    <div className="flex flex-col gap-2">
      <p id={labelId} className="font-button text-sm leading-5 font-medium text-foreground">
        เพศ
      </p>
      <div role="radiogroup" aria-labelledby={labelId} className="flex gap-1 rounded-[10px] border border-border bg-card p-0.5">
        {GENDERS.map((gender) => {
          const selected = gender.value === value;
          return (
            <button
              key={gender.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(gender.value)}
              className={`flex h-[38px] min-w-0 flex-1 items-center justify-center rounded-lg px-4 text-sm leading-5 ${
                selected
                  ? "border border-brand-accent bg-accent-subtle font-semibold text-link"
                  : "font-medium text-mid hover:bg-muted"
              }`}
            >
              {gender.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

type SelectProps = {
  label: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
};

function Select({ label, options, value, onChange }: SelectProps) {
  const id = useId();
  return (
    <div className="flex w-full flex-col gap-2 sm:min-w-0 sm:flex-1">
      <label htmlFor={id} className="font-button text-sm leading-5 font-medium text-foreground">
        {label}
      </label>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="h-10 w-full appearance-none rounded-lg border border-border bg-card pr-9 pl-3 text-sm leading-5 text-foreground"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <img
          src={chevronDownIcon}
          alt=""
          width={16}
          height={16}
          className="pointer-events-none absolute top-3 right-3"
        />
      </div>
    </div>
  );
}

function SpeedSlider({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2 text-sm leading-5 text-foreground">
        <label htmlFor={id} className="flex-1 font-button font-medium">
          ความเร็ว
        </label>
        <output htmlFor={id} className="font-mono font-medium">
          {value.toFixed(2)}×
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={0.8}
        max={1.2}
        step={0.05}
        value={value}
        onChange={(event) => onChange(Math.round(Number(event.target.value) * 100) / 100)}
        className="h-11 w-full cursor-pointer accent-brand-accent"
      />
      <div className="flex justify-between font-mono text-xs leading-4 text-muted-foreground">
        <span>0.8</span>
        <span>1.2</span>
      </div>
    </div>
  );
}
