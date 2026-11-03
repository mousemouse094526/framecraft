import { useEffect, useId, useRef } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import plusIcon from "../assets/plus.svg";
import trashIcon from "../assets/trash.svg";
import { useAutoSave } from "../hooks/useAutoSave";
import type { SettingsState } from "../hooks/useVideoSettings";
import { WATERMARK_TEXT_MAX, WATERMARKS_MAX, type MarkSize, type Position, type Watermark } from "../lib/render";

const VOLUME_STEP = 5; // D40

// The picker is a 9:16 frame with three spots on top and three at the bottom (D41).
const ROWS: { position: Position; label: string }[][] = [
  [
    { position: "top_left", label: "บนซ้าย" },
    { position: "top_center", label: "บนกลาง" },
    { position: "top_right", label: "บนขวา" },
  ],
  [
    { position: "bottom_left", label: "ล่างซ้าย" },
    { position: "bottom_center", label: "ล่างกลาง" },
    { position: "bottom_right", label: "ล่างขวา" },
  ],
];
const SIZES: { size: MarkSize; label: string }[] = [
  { size: "small", label: "เล็ก" },
  { size: "medium", label: "กลาง" },
];

type Props = {
  volume: number;
  onVolume: (volume: number) => Promise<boolean>;
  settings: SettingsState;
  /** A job changes the draft or renders: every field waits (D51). */
  locked: boolean;
  onAdd: () => Promise<boolean>;
  onChange: (index: number, mark: Watermark) => Promise<boolean>;
  onRemove: (index: number) => Promise<boolean>;
};

/** Figma `Settings card` of ตรวจแก้บท: the original sound's level and the watermarks (D40, D41). */
export function VideoSettings(props: Props) {
  const { settings, locked } = props;
  // The slider saves itself like a text field: 800 ms after the last move, or on release.
  const volume = useAutoSave(String(props.volume), (value) => props.onVolume(Number(value)));
  const volumeId = useId();
  const added = useRef(false);
  const marks = settings.kind === "loaded" ? settings.watermarks : [];

  return (
    <section aria-label="ตั้งค่าวิดีโอ" className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-4">
      <h2 className="text-base font-semibold text-foreground">ตั้งค่าวิดีโอ</h2>
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-sm leading-5 text-foreground">
          <label htmlFor={volumeId} className="flex-1 font-medium">
            เสียงคลิปต้นฉบับ
          </label>
          <span className="font-mono font-medium">{volume.value}</span>
        </div>
        <input
          id={volumeId}
          type="range"
          min={0}
          max={100}
          step={VOLUME_STEP}
          value={volume.value}
          disabled={locked}
          onChange={(event) => volume.change(event.target.value)}
          onPointerUp={() => void volume.flush()}
          onBlur={() => void volume.flush()}
          className="h-11 w-full accent-brand-accent"
        />
        <div className="flex justify-between font-mono text-xs text-muted-foreground">
          <span>0</span>
          <span>100</span>
        </div>
      </div>
      <hr className="border-border" />
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <h3 className="flex-1 text-sm font-medium text-foreground">ลายน้ำ</h3>
          <span className="font-mono text-[13px] text-muted-foreground">
            {marks.length}/{WATERMARKS_MAX}
          </span>
        </div>
        {settings.kind === "loaded" && settings.error && <Alert tone="error">{settings.error}</Alert>}
        {marks.map((mark, index) => (
          <WatermarkRow
            // The list only grows at the end and shrinks by one: the index is the row.
            key={index}
            number={index + 1}
            mark={mark}
            locked={locked}
            focus={added.current && index === marks.length - 1}
            onChange={(changed) => props.onChange(index, changed)}
            onRemove={() => void props.onRemove(index)}
          />
        ))}
        {marks.length < WATERMARKS_MAX && (
          <button
            type="button"
            disabled={locked || settings.kind !== "loaded"}
            onClick={() => {
              added.current = true;
              void props.onAdd();
            }}
            className={`h-11 w-full px-6 ${OUTLINE_BUTTON}`}
          >
            <img src={plusIcon} alt="" width={16} height={16} />
            เพิ่มลายน้ำ
          </button>
        )}
      </div>
    </section>
  );
}

type RowProps = {
  number: number;
  mark: Watermark;
  locked: boolean;
  /** Just added: its text is selected to type over. */
  focus: boolean;
  onChange: (mark: Watermark) => Promise<boolean>;
  onRemove: () => void;
};

/** Figma component `Watermark row`: text with its count, the 6-spot position picker, the size. */
function WatermarkRow({ number, mark, locked, focus, onChange, onRemove }: RowProps) {
  const text = useAutoSave(mark.text, (value) => onChange({ ...mark, text: value }));
  const textId = useId();
  const field = useRef<HTMLInputElement>(null);
  const title = `ลายน้ำ ${number}`;

  useEffect(() => {
    if (focus) field.current?.select();
  }, [focus]);

  return (
    <fieldset aria-label={title} disabled={locked} className="flex flex-col gap-3 rounded-xl border border-border bg-card pt-2 pr-1 pb-3 pl-3">
      <div className="flex items-center">
        <p className="flex-1 text-sm font-semibold text-foreground">{title}</p>
        <button type="button" aria-label={`ลบ${title}`} onClick={onRemove} className={`size-11 ${GHOST_BUTTON}`}>
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
      <div className="flex flex-col gap-3 pr-2">
        <div className="flex flex-col gap-2">
          <label htmlFor={textId} className="text-sm leading-5 font-medium text-foreground">
            ข้อความ
          </label>
          <input
            id={textId}
            ref={field}
            value={text.value}
            maxLength={WATERMARK_TEXT_MAX * 2}
            onChange={(event) => text.change(event.target.value)}
            onBlur={() => void text.flush()}
            className="h-10 rounded-lg border border-border bg-card px-3 text-sm text-foreground disabled:bg-muted"
          />
          <p className="text-right font-mono text-xs text-muted-foreground">
            {[...text.value].length}/{WATERMARK_TEXT_MAX}
          </p>
        </div>
        <div className="flex items-start gap-4">
          <div role="radiogroup" aria-label={`ตำแหน่ง${title}`} className="flex flex-col gap-2">
            <p className="text-sm font-medium text-foreground">ตำแหน่ง</p>
            <div className="flex h-[234px] w-[132px] flex-col justify-between rounded-xl border border-border-strong bg-muted">
              {ROWS.map((row) => (
                <div key={row[0].position} className="flex">
                  {row.map(({ position, label }) => (
                    <PositionCell
                      key={position}
                      label={label}
                      selected={mark.position === position}
                      onPick={() => void onChange({ ...mark, text: text.value, position })}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div role="radiogroup" aria-label={`ขนาด${title}`} className="flex min-w-0 flex-1 flex-col gap-2">
            <p className="text-sm font-medium text-foreground">ขนาด</p>
            {SIZES.map(({ size, label }) => {
              const selected = mark.size === size;
              return (
                <button
                  key={size}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => void onChange({ ...mark, text: text.value, size })}
                  className={`flex h-11 w-full items-center justify-center rounded-lg px-4 text-sm leading-5 ${
                    selected ? "border border-brand-accent bg-accent-subtle font-semibold text-link" : "font-medium text-mid"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </fieldset>
  );
}

/** Figma component `Position cell`: a 44 px radio with a text mark in its spot. */
function PositionCell({ label, selected, onPick }: { label: string; selected: boolean; onPick: () => void }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      aria-label={label}
      onClick={onPick}
      className="flex size-11 items-center justify-center"
    >
      <span
        className={`flex h-7 w-9 items-center justify-center rounded-lg ${selected ? "border-2 border-brand-accent bg-accent-subtle" : ""}`}
      >
        <span className={`h-1.5 rounded-full ${selected ? "w-[22px] bg-brand-accent" : "w-[18px] bg-border-strong"}`} />
      </span>
    </button>
  );
}
