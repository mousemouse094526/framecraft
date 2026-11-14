/** The drum kit's pieces in note-lane order, top to bottom, as the backend's `kit` names them (spec › Drum kit). */
export const PIECES = [
  { id: "hihat_closed", name: "ไฮแฮทปิด" },
  { id: "hihat_open", name: "ไฮแฮทเปิด" },
  { id: "crash", name: "แครช" },
  { id: "ride", name: "ไรด์" },
  { id: "snare", name: "สแนร์" },
  { id: "tom_high", name: "ทอมสูง" },
  { id: "tom_mid", name: "ทอมกลาง" },
  { id: "tom_floor", name: "ทอมต่ำ" },
  { id: "kick", name: "กระเดื่อง" },
  { id: "hihat_pedal", name: "ไฮแฮทเท้า" },
] as const;

export type PieceId = (typeof PIECES)[number]["id"];

/** Played with a foot: no stick (`hand` is null) and no flam (D20). */
const FEET: ReadonlySet<PieceId> = new Set(["kick", "hihat_pedal"]);

export const isFoot = (piece: PieceId) => FEET.has(piece);

export const pieceName = (piece: PieceId) => PIECES.find((p) => p.id === piece)?.name ?? piece;
