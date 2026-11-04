import { useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import type { Sentence } from "../lib/draft";
import { ModalDialog } from "./ModalDialog";

type Props = {
  sentences: Sentence[];
  onPolish: (includeEdited: boolean) => void;
  onClose: () => void;
};

/**
 * The choice before เรียบเรียงใหม่ (spoil-maker D72, D74, D75): whether the sentences the
 * user edited are polished too, what that overwrites, and that changed sentences need
 * a new voice. Until Blocked 15 has its design, it is built from the Shot picker's parts.
 */
export function PolishDialog({ sentences, onPolish, onClose }: Props) {
  const [includeEdited, setIncludeEdited] = useState(false);
  const titleId = useId();
  const edited = sentences.filter((s) => s.edited).length;
  const voiced = sentences.some((s) => s.audio !== null);
  const nothingLeft = edited === sentences.length && !includeEdited;

  return (
    <ModalDialog titleId={titleId} onClose={onClose} size="gap-4 sm:max-w-[480px]">
      <h3 id={titleId} className="text-lg font-semibold text-foreground">
        เรียบเรียงใหม่
      </h3>
      <p className="text-sm text-mid">AI อ่านบททั้งบทแล้วเกลาข้อความให้ประโยคเล่าต่อกัน จำนวน ลำดับ และ Shot ของประโยคไม่เปลี่ยน</p>
      {edited > 0 && (
        <label className="flex items-center gap-2 text-sm font-medium text-foreground">
          <input
            type="checkbox"
            checked={includeEdited}
            onChange={(event) => setIncludeEdited(event.target.checked)}
            className="size-4 accent-brand"
          />
          เรียบเรียงประโยคที่แก้เองด้วย
        </label>
      )}
      {includeEdited && <Alert tone="warning">ข้อความที่แก้เอง {edited} ประโยคจะถูกเขียนทับ ย้อนกลับไม่ได้</Alert>}
      {voiced && <p className="text-sm text-mid">ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่</p>}
      {nothingLeft && <p className="text-sm font-medium text-warning">ทุกประโยคแก้เองแล้ว: ติ๊กเพื่อเรียบเรียงทับ</p>}
      <div className="flex gap-2 sm:justify-end">
        <button type="button" onClick={onClose} className={`h-11 flex-1 px-6 sm:flex-none ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
        <button
          type="button"
          autoFocus
          onClick={() => onPolish(includeEdited)}
          disabled={nothingLeft}
          className={`h-11 flex-1 px-6 sm:flex-none ${PRIMARY_BUTTON} disabled:opacity-50`}
        >
          เรียบเรียง
        </button>
      </div>
    </ModalDialog>
  );
}
