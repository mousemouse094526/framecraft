import { useEffect, useId, useRef } from "react";
import { ModalDialog } from "../../../components/ui/ModalDialog";
import { OUTLINE_BUTTON, PRIMARY_BUTTON, DESTRUCTIVE_BUTTON } from "../../../components/ui/buttonStyles";

type Props = {
  title: string;
  message: string;
  confirmLabel: string;
  /** Red for a step that deletes (ลบชุด); dark otherwise (เลือกไฟล์). */
  destructive?: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

/** Figma `Toon/Dialog`: a title, one line, ยกเลิก and the confirm button; focus starts on ยกเลิก. */
export function ToonDialog({ title, message, confirmLabel, destructive = false, onConfirm, onClose }: Props) {
  const titleId = useId();
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => cancel.current?.focus(), []);

  return (
    <ModalDialog titleId={titleId} onClose={onClose} size="gap-4 sm:max-w-[480px]">
      <h2 id={titleId} className="text-lg leading-[1.5] font-semibold text-foreground">
        {title}
      </h2>
      <p className="text-sm leading-[1.5] text-mid">{message}</p>
      <div className="flex justify-end gap-2">
        <button ref={cancel} type="button" onClick={onClose} className={`h-9 px-4 ${OUTLINE_BUTTON}`}>
          ยกเลิก
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className={`h-9 px-4 ${destructive ? DESTRUCTIVE_BUTTON : PRIMARY_BUTTON}`}
        >
          {confirmLabel}
        </button>
      </div>
    </ModalDialog>
  );
}
