import { useId } from "react";
import { GHOST_BUTTON } from "../../../components/ui/buttonStyles";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { isFoot, pieceName } from "../../../lib/kit";
import { canTakeHand, canTakeHit, countOf, HITS, STEPS_PER_BAR, type Hand, type Note } from "../../../lib/lesson";

type Props = { notes: Note[]; note: Note; onChange: (note: Note) => void; onDelete: () => void };

/** The selected note's stick and hit, and its delete; a choice that would clash the hands is disabled (D20). */
export function NoteBox({ notes, note, onChange, onDelete }: Props) {
  const name = useId();
  const bar = Math.floor(note.step / STEPS_PER_BAR) + 1;
  return (
    <div role="group" aria-label="โน้ตที่เลือก" className="flex flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-border bg-muted px-4 py-3">
      <p className="text-sm leading-5 font-medium text-foreground">
        {pieceName(note.piece)} · ห้อง {bar} จังหวะ {countOf(note.step)}
      </p>
      {!isFoot(note.piece) && (
        <fieldset className="flex items-center gap-3">
          <legend className="sr-only">ไม้</legend>
          {(["R", "L"] as Hand[]).map((hand) => (
            <Choice
              key={hand}
              name={`${name}-hand`}
              label={hand}
              checked={note.hand === hand}
              disabled={note.hand !== hand && !canTakeHand(notes, note, hand)}
              onPick={() => onChange({ ...note, hand })}
            />
          ))}
        </fieldset>
      )}
      <fieldset className="flex flex-wrap items-center gap-3">
        <legend className="sr-only">ลักษณะตี</legend>
        {HITS.filter((hit) => hit.id !== "flam" || !isFoot(note.piece)).map((hit) => (
          <Choice
            key={hit.id}
            name={`${name}-hit`}
            label={hit.name}
            checked={note.hit === hit.id}
            disabled={note.hit !== hit.id && !canTakeHit(notes, note, hit.id)}
            onPick={() => onChange({ ...note, hit: hit.id })}
          />
        ))}
      </fieldset>
      <button type="button" onClick={onDelete} className={`h-9 px-3 ${GHOST_BUTTON} hover:bg-card`}>
        <img src={trashIcon} alt="" width={16} height={16} />
        ลบโน้ต
      </button>
    </div>
  );
}

type ChoiceProps = { name: string; label: string; checked: boolean; disabled: boolean; onPick: () => void };

function Choice({ name, label, checked, disabled, onPick }: ChoiceProps) {
  return (
    <label className={`flex items-center gap-1.5 text-sm leading-5 text-foreground ${disabled ? "opacity-40" : ""}`}>
      <input type="radio" name={name} checked={checked} disabled={disabled} onChange={onPick} className="accent-brand" />
      {label}
    </label>
  );
}
