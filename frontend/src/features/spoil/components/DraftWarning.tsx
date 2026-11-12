import { Alert } from "../../../components/ui/Alert";
import { DESTRUCTIVE_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";

/** The `in_draft` message (spoil-maker spec › Frontend). */
export const IN_DRAFT_TEXT = "คลิปนี้อยู่ใน Spoil draft: ทำต่อจะลบ Spoil draft";

type Props = { onGo: () => void; onCancel: () => void };

/**
 * Figma `Clip row` state draft warning, shared by delete, transcribe again and describe
 * again of a clip the Spoil draft is made from (spoil-maker D29, D49). Opens with focus on ทำต่อ.
 */
export function DraftWarning({ onGo, onCancel }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <Alert tone="warning">{IN_DRAFT_TEXT}</Alert>
      <div className="flex gap-2">
        <button type="button" autoFocus onClick={onGo} className={`h-11 flex-1 px-4 lg:h-9 lg:flex-none ${DESTRUCTIVE_BUTTON}`}>
          ทำต่อ
        </button>
        <button type="button" onClick={onCancel} className={`h-11 flex-1 px-4 lg:h-9 lg:flex-none ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
      </div>
    </div>
  );
}
