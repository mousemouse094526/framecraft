import { SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import { isFoot, PIECES, type PieceId } from "../lib/kit";
import { BARS_MAX, countOf, HITS, noteFor, STEPS_PER_BAR, type Note } from "../lib/lesson";

type Props = {
  bars: number;
  notes: Note[];
  selected: Note | null;
  /** The notes an `invalid_request` names. */
  invalid: ReadonlySet<Note>;
  onCell: (piece: PieceId, step: number) => void;
  onBars: (bars: number) => void;
};

/**
 * ตาราง Groove: a row per piece in note-lane order, 16 steps a bar headed `1 e & a`. An empty cell
 * the hands can't take is disabled (D20); a note shows its stick, or ● for a foot.
 */
export function GrooveGrid({ bars, notes, selected, invalid, onCell, onBars }: Props) {
  const steps = Array.from({ length: bars * STEPS_PER_BAR }, (_, step) => step);
  const at = new Map(notes.map((note) => [`${note.piece}:${note.step}`, note]));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <button type="button" disabled={bars <= 1} onClick={() => onBars(bars - 1)} className={`h-9 px-3 ${SECONDARY_BUTTON}`}>
          ลดห้อง
        </button>
        <span className="text-sm leading-5 text-foreground">{bars} ห้อง</span>
        <button type="button" disabled={bars >= BARS_MAX} onClick={() => onBars(bars + 1)} className={`h-9 px-3 ${SECONDARY_BUTTON}`}>
          เพิ่มห้อง
        </button>
      </div>
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
                  const isSelected = note !== undefined && note === selected;
                  const isInvalid = note !== undefined && invalid.has(note);
                  const label = `${piece.name} ห้อง ${Math.floor(step / STEPS_PER_BAR) + 1} จังหวะ ${countOf(step)}`;
                  return (
                    <td key={step} className={step % STEPS_PER_BAR === 0 && step > 0 ? "border-l-2 border-border-strong pl-0.5" : ""}>
                      <button
                        type="button"
                        aria-label={label}
                        aria-pressed={isSelected}
                        aria-invalid={isInvalid || undefined}
                        title={note ? HITS.find((hit) => hit.id === note.hit)?.name : undefined}
                        disabled={!note && !noteFor(notes, piece.id, step)}
                        onClick={() => onCell(piece.id, step)}
                        className={cellClass(note, isSelected, isInvalid, step)}
                      >
                        {note && (isFoot(note.piece) ? "●" : note.hand)}
                        {note?.hit === "flam" && <sup>f</sup>}
                      </button>
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

function cellClass(note: Note | undefined, selected: boolean, invalid: boolean, step: number): string {
  const base = "size-7 rounded font-mono font-semibold disabled:cursor-not-allowed disabled:opacity-40";
  const ring = invalid ? "ring-2 ring-destructive" : selected ? "ring-2 ring-brand-accent" : "";
  if (!note) return `${base} ${step % 4 === 0 ? "bg-surface-strong" : "bg-muted"} hover:bg-accent-subtle`;
  // An accent is the full colour, a ghost the faint one.
  const look = note.hit === "ghost" ? "bg-accent-subtle text-brand" : note.hit === "accent" ? "bg-brand-accent text-card" : "bg-brand text-card";
  return `${base} ${look} ${ring}`;
}
