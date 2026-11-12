import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";

/** Figma `Draft action › replace confirm`: the ask before a new draft replaces the Spoil draft (D28, D86). */
export function ReplaceConfirm({ onReplace, onKeep }: { onReplace: () => void; onKeep: () => void }) {
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
