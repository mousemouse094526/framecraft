import { isFoot, PIECES, type PieceId } from "../../lib/kit";
import { BARS_MAX, countOf, hitName, noteFor, notePlace, STEPS_PER_BAR, type Note } from "../../lib/lesson";
import { SECONDARY_BUTTON } from "./buttonStyles";

/** What the lesson editor adds to the grid: a selected note, the notes an `invalid_request` names, and the clicks. */
export type Editing = {
  selected: Note | null;
  invalid: ReadonlySet<Note>;
  onCell: (piece: PieceId, step: number) => void;
  onBars: (bars: number) => void;
};

type Props = {
  bars: number;
  notes: Note[];
  /** Left out, the grid is read-only: the song page's preview of a lesson (drum-notes D11). */
  editing?: Editing;
};

/**
 * ตาราง Groove: a row per piece in note-lane order, 16 steps a bar headed `1 e & a`. A note shows
 * its stick, or ● for a foot. Editing, an empty cell the hands can't take is disabled (video-gen
 * D20) and ลดห้อง/เพิ่มห้อง change the bar count; read-only, the cells are plain.
 */
export function GrooveGrid({ bars, notes, editing }: Props) {
  const steps = Array.from({ length: bars * STEPS_PER_BAR }, (_, step) => step);
  const at = new Map(notes.map((note) => [`${note.piece}:${note.step}`, note]));

  return (
    <div className="flex flex-col gap-3">
      {editing && (
        <div className="flex items-center gap-2">
          <button type="button" disabled={bars <= 1} onClick={() => editing.onBars(bars - 1)} className={`h-9 px-3 ${SECONDARY_BUTTON}`}>
            ลดห้อง
          </button>
          <span className="text-sm leading-5 text-foreground">{bars} ห้อง</span>
          <button type="button" disabled={bars >= BARS_MAX} onClick={() => editing.onBars(bars + 1)} className={`h-9 px-3 ${SECONDARY_BUTTON}`}>
            เพิ่มห้อง
          </button>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="border-separate border-spacing-0.5 text-xs leading-4">
          <thead>
            <tr>
              <th className="sticky left-0 bg-card" />
              {steps.map((step) => (
                <th
                  key={step}
                  scope="col"
                  className={`w-7 font-mono font-medium ${step % 4 === 0 ? "text-foreground" : "text-muted-foreground"}`}
                >
                  {/* The beat reads "1", the 16ths after it only their "e", "&", "a". */}
                  {step % 4 === 0 ? countOf(step) : countOf(step).slice(-1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PIECES.map((piece) => (
              <tr key={piece.id}>
                <th scope="row" className="sticky left-0 bg-card pr-2 text-left font-medium whitespace-nowrap text-foreground">
                  {piece.name}
                </th>
                {steps.map((step) => {
                  const note = at.get(`${piece.id}:${step}`);
                  const label = notePlace(piece.id, step);
                  return (
                    <td key={step} className={step % STEPS_PER_BAR === 0 && step > 0 ? "border-l-2 border-border-strong pl-0.5" : ""}>
                      {editing ? (
                        <EditableCell note={note} notes={notes} piece={piece.id} step={step} label={label} editing={editing} />
                      ) : (
                        <span aria-label={label} title={note && hitName(note)} className={`flex items-center justify-center ${cellClass(note, false, false, step)}`}>
                          {note && <Mark note={note} />}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

type CellProps = { note: Note | undefined; notes: Note[]; piece: PieceId; step: number; label: string; editing: Editing };

function EditableCell({ note, notes, piece, step, label, editing }: CellProps) {
  const isSelected = note !== undefined && note === editing.selected;
  const isInvalid = note !== undefined && editing.invalid.has(note);
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={isSelected}
      aria-invalid={isInvalid || undefined}
      title={note && hitName(note)}
      disabled={!note && !noteFor(notes, piece, step)}
      onClick={() => editing.onCell(piece, step)}
      className={cellClass(note, isSelected, isInvalid, step)}
    >
      {note && <Mark note={note} />}
    </button>
  );
}

/** What a note shows in its cell: its stick, or ● for a foot, and `f` for a flam. */
function Mark({ note }: { note: Note }) {
  return (
    <>
      {isFoot(note.piece) ? "●" : note.hand}
      {note.hit === "flam" && <sup>f</sup>}
    </>
  );
}

function cellClass(note: Note | undefined, selected: boolean, invalid: boolean, step: number): string {
  const base = "size-7 rounded font-mono font-semibold disabled:cursor-not-allowed disabled:opacity-40";
  const ring = invalid ? "ring-2 ring-destructive" : selected ? "ring-2 ring-brand-accent" : "";
  if (!note) return `${base} ${step % 4 === 0 ? "bg-surface-strong" : "bg-muted"} hover:bg-accent-subtle`;
  // An accent is the full colour, a ghost the faint one.
  const look = note.hit === "ghost" ? "bg-accent-subtle text-brand" : note.hit === "accent" ? "bg-brand-accent text-card" : "bg-brand text-card";
  return `${base} ${look} ${ring}`;
}
