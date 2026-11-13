import { useId } from "react";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import plusIcon from "../../../components/ui/assets/plus.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { PIECES, type PieceId } from "../lib/kit";
import { inputClass, Labeled } from "./Labeled";
import { CHAPTERS_MAX, NEW_CHAPTER, REPEATS_MAX, SPEEDS, type Chapter, type FieldErrors } from "../lib/lesson";

type Props = {
  chapters: Chapter[];
  errors: FieldErrors;
  onChange: (chapters: Chapter[]) => void;
};

/** ท่อนสอน 1–6: each plays the Groove `repeats` times at its own speed, with its label, text and focus (D4). */
export function ChapterList({ chapters, errors, onChange }: Props) {
  const set = (index: number, change: Partial<Chapter>) => onChange(chapters.map((c, i) => (i === index ? { ...c, ...change } : c)));
  const move = (index: number, by: number) => {
    const next = [...chapters];
    [next[index], next[index + by]] = [next[index + by], next[index]];
    onChange(next);
  };

  return (
    <section aria-label="ท่อนสอน" className="flex flex-col gap-3">
      <h3 className="text-sm leading-[1.5] font-medium text-foreground">
        ท่อนสอน <span className="font-mono text-xs text-muted-foreground">{chapters.length} / {CHAPTERS_MAX}</span>
      </h3>
      {chapters.map((chapter, index) => (
        <ChapterRow
          key={index}
          index={index}
          chapter={chapter}
          count={chapters.length}
          errors={errors}
          onChange={(change) => set(index, change)}
          onMove={(by) => move(index, by)}
          onRemove={() => onChange(chapters.filter((_, i) => i !== index))}
        />
      ))}
      <button
        type="button"
        disabled={chapters.length >= CHAPTERS_MAX}
        onClick={() => onChange([...chapters, NEW_CHAPTER])}
        className={`h-11 w-fit px-4 sm:h-9 ${OUTLINE_BUTTON}`}
      >
        <img src={plusIcon} alt="" width={16} height={16} />
        เพิ่มท่อน
      </button>
    </section>
  );
}

type RowProps = {
  index: number;
  chapter: Chapter;
  count: number;
  errors: FieldErrors;
  onChange: (change: Partial<Chapter>) => void;
  onMove: (by: number) => void;
  onRemove: () => void;
};

function ChapterRow({ index, chapter, count, errors, onChange, onMove, onRemove }: RowProps) {
  const id = useId();
  const n = index + 1;
  const labelError = errors[`chapters[${index}].label`];
  const textError = errors[`chapters[${index}].text`];
  const toggle = (piece: PieceId) =>
    onChange({ focus: chapter.focus.includes(piece) ? chapter.focus.filter((p) => p !== piece) : [...chapter.focus, piece] });

  return (
    <div role="group" aria-label={`ท่อน ${n}`} className="flex flex-col gap-3 rounded-xl border border-border p-3">
      <div className="flex items-center gap-1">
        <p className="flex-1 text-sm leading-5 font-medium text-foreground">ท่อน {n}</p>
        <button type="button" aria-label={`เลื่อนท่อน ${n} ขึ้น`} disabled={index === 0} onClick={() => onMove(-1)} className={`h-9 px-2 ${GHOST_BUTTON} hover:bg-muted`}>
          ขึ้น
        </button>
        <button type="button" aria-label={`เลื่อนท่อน ${n} ลง`} disabled={index === count - 1} onClick={() => onMove(1)} className={`h-9 px-2 ${GHOST_BUTTON} hover:bg-muted`}>
          ลง
        </button>
        <button type="button" aria-label={`ลบท่อน ${n}`} disabled={count <= 1} onClick={onRemove} className={`size-9 ${GHOST_BUTTON} hover:bg-muted`}>
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Labeled label="ป้าย" htmlFor={`${id}-label`} error={labelError} hint={index === 0 ? "ว่าง = แสดงหัวเรื่อง" : undefined}>
          <input
            id={`${id}-label`}
            value={chapter.label}
            aria-invalid={labelError !== undefined}
            onChange={(event) => onChange({ label: event.target.value })}
            className={inputClass(labelError !== undefined)}
          />
        </Labeled>
        <Labeled label="คำอธิบาย" htmlFor={`${id}-text`} error={textError}>
          <input
            id={`${id}-text`}
            value={chapter.text}
            aria-invalid={textError !== undefined}
            onChange={(event) => onChange({ text: event.target.value })}
            className={inputClass(textError !== undefined)}
          />
        </Labeled>
        <Labeled label="รอบ" htmlFor={`${id}-repeats`}>
          <select id={`${id}-repeats`} value={chapter.repeats} onChange={(event) => onChange({ repeats: Number(event.target.value) })} className={inputClass(false)}>
            {Array.from({ length: REPEATS_MAX }, (_, i) => i + 1).map((repeats) => (
              <option key={repeats} value={repeats}>
                {repeats}
              </option>
            ))}
          </select>
        </Labeled>
        <Labeled label="ความเร็ว" htmlFor={`${id}-speed`}>
          <select id={`${id}-speed`} value={chapter.speed} onChange={(event) => onChange({ speed: Number(event.target.value) })} className={inputClass(false)}>
            {SPEEDS.map((speed) => (
              <option key={speed} value={speed}>
                {speed}%
              </option>
            ))}
          </select>
        </Labeled>
      </div>
      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-sm leading-5 font-medium text-foreground">ชิ้นที่เน้น</legend>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          {PIECES.map((piece) => (
            <label key={piece.id} className="flex items-center gap-1.5 text-sm leading-5 text-foreground">
              <input type="checkbox" checked={chapter.focus.includes(piece.id)} onChange={() => toggle(piece.id)} className="accent-brand" />
              {piece.name}
            </label>
          ))}
        </div>
        <p className="text-xs leading-4 text-muted-foreground">ไม่เลือก = ทุกชิ้นสว่าง</p>
      </fieldset>
    </div>
  );
}
