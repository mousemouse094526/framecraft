import { useState } from "react";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import circleAlertIcon from "../assets/circle-alert.svg";
import { sampleUrl, type RefusalText, type Voice } from "../hooks/useVoices";
import { playAudio } from "../lib/audio";
import { NameForm } from "./NameForm";

type Props = {
  voice: Voice;
  onRename: (name: string) => Promise<RefusalText>;
  onDelete: () => Promise<RefusalText>;
};

type Mode = "default" | "renaming" | "confirming";

// The Figma buttons: 36px on desktop, 44px and sharing the row on a phone.
const ROW_BUTTON = "h-11 min-w-0 flex-1 px-4 sm:h-9 sm:flex-none";
const RENAME_BUTTON = "h-11 min-w-0 flex-1 px-4 sm:h-10 sm:flex-none";

/** Figma component `Voice row`: default, renaming, delete confirm, and a refused delete (spoil-maker D43). */
export function VoiceRow({ voice, onRename, onDelete }: Props) {
  const [mode, setMode] = useState<Mode>("default");
  const [error, setError] = useState<string | null>(null);

  const remove = async () => {
    const refusal = await onDelete();
    // Done: the row leaves the list. Refused: back to the row with the reason under it.
    if (refusal !== null) {
      setMode("default");
      setError(refusal);
    }
  };

  return (
    <li aria-label={voice.name} className="flex flex-col gap-2 bg-card py-3 pr-3 pl-4">
      {mode === "renaming" && (
        <NameForm
          initial={voice.name}
          autoFocus
          buttonClass={RENAME_BUTTON}
          onSave={async (name) => {
            const refusal = await onRename(name);
            if (refusal === null) setMode("default");
            return refusal;
          }}
          onCancel={() => setMode("default")}
          extra={
            <button type="button" onClick={() => setMode("default")} className={`${RENAME_BUTTON} ${OUTLINE_BUTTON}`}>
              ยกเลิก
            </button>
          }
        />
      )}
      {mode === "confirming" && (
        <div className="flex flex-col gap-3 rounded-lg bg-muted p-3">
          <div className="flex flex-col gap-0.5">
            <p className="text-sm leading-[21px] font-medium text-foreground">ลบเสียง “{voice.name}”?</p>
            <p className="text-[13px] leading-5 text-mid">ลบแล้วกู้คืนไม่ได้</p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void remove()}
              className={`${ROW_BUTTON} rounded-lg bg-destructive font-button text-sm leading-5 font-medium text-card hover:opacity-90`}
            >
              ลบ
            </button>
            <button type="button" onClick={() => setMode("default")} className={`${ROW_BUTTON} ${OUTLINE_BUTTON}`}>
              ยกเลิก
            </button>
          </div>
        </div>
      )}
      {mode === "default" && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <p className="text-sm leading-[21px] font-medium break-words text-foreground sm:min-w-0 sm:flex-1">
            {voice.name}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => playAudio(sampleUrl(voice.id))}
              className={`${ROW_BUTTON} ${OUTLINE_BUTTON}`}
            >
              ฟัง
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                setMode("renaming");
              }}
              className={`${ROW_BUTTON} ${GHOST_BUTTON} hover:bg-muted`}
            >
              เปลี่ยนชื่อ
            </button>
            <button
              type="button"
              onClick={() => {
                setError(null);
                setMode("confirming");
              }}
              className={`${ROW_BUTTON} ${GHOST_BUTTON} hover:bg-muted`}
            >
              ลบ
            </button>
          </div>
        </div>
      )}
      {mode === "default" && error && (
        <p role="alert" className="flex items-center gap-1.5 text-[13px] leading-[1.5] text-destructive">
          <img src={circleAlertIcon} alt="" width={14} height={14} />
          {error}
        </p>
      )}
    </li>
  );
}
