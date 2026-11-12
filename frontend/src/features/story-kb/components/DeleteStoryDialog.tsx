import { useId } from "react";
import { DESTRUCTIVE_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { ModalDialog } from "../../../components/ui/ModalDialog";

type Props = {
  title: string;
  /** How many clips remember the Story: they become "ไม่ใช้" (D10). */
  clips: number;
  onCancel: () => void;
  onDelete: () => void;
};

/** Figma `Delete story dialog`: focus starts on ยกเลิก; the used line shows only when a clip remembers it. */
export function DeleteStoryDialog({ title, clips, onCancel, onDelete }: Props) {
  const titleId = useId();
  return (
    <ModalDialog titleId={titleId} onClose={onCancel} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg leading-[1.5] font-semibold break-words text-foreground">
        ลบ {title}?
      </h3>
      {clips > 0 && <p className="text-sm leading-[1.5] text-mid">ใช้อยู่ {clips} คลิป คลิปเหล่านั้นจะเป็น ไม่ใช้</p>}
      <div className="flex justify-end gap-2">
        <button type="button" autoFocus onClick={onCancel} className={`h-11 px-6 sm:h-10 ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
        <button type="button" onClick={onDelete} className={`h-11 px-6 sm:h-10 ${DESTRUCTIVE_BUTTON}`}>
          ลบ
        </button>
      </div>
    </ModalDialog>
  );
}
