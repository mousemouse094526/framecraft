import type { TempClip } from "../../../lib/clips";
import { CLIPS_PATH } from "../../../lib/clips";
import { formatDuration } from "../../../lib/format";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import radioSelectedIcon from "../assets/radio-selected.svg";
import radioIcon from "../assets/radio.svg";
import fileTextIcon from "../../../components/ui/assets/file-text-24.svg";
import playIcon from "../../../components/ui/assets/play.svg";

type Props = {
  clips: TempClip[];
  /** The picked clip's id, or null (D66). */
  picked: string | null;
  disabled: boolean;
  onChange: (picked: string) => void;
};

/** Ready to draft from: transcribed and described (D16). */
export const isReady = (clip: TempClip) => clip.transcribed && clip.described;

/**
 * Figma `Clips card` of ตั้งค่าคลิปสปอย: one clip is picked to cut into EPs (D66); a clip not
 * ready says why with a link to the คลิป tab (D16).
 */
export function ClipPicker({ clips, picked, disabled, onChange }: Props) {
  const ready = clips.filter(isReady);
  return (
    <section aria-label="เลือกคลิป" className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card lg:w-[560px] lg:shrink-0">
      <h3 className="flex items-center gap-2 px-4 py-3 leading-[1.5] whitespace-nowrap">
        <span className="text-sm font-medium text-foreground">เลือกคลิป</span>
      </h3>
      {ready.length === 0 ? (
        <div className="flex flex-col items-center gap-2 border-t border-border px-4 py-12">
          <img src={fileTextIcon} alt="" width={24} height={24} />
          <p className="text-center text-sm leading-[21px] text-mid">ยังไม่มีคลิปที่ถอดและบรรยายฉากแล้ว</p>
          <a href="#/clips" className="flex h-11 items-center rounded-lg px-4 font-button text-sm leading-5 font-medium text-brand hover:bg-muted">
            ไปที่รายการคลิป
          </a>
        </div>
      ) : (
        <ul>
          {clips.map((clip) => (
            <PickRow key={clip.id} clip={clip} picked={clip.id === picked} disabled={disabled} onPick={() => onChange(clip.id)} />
          ))}
        </ul>
      )}
    </section>
  );
}

type RowProps = { clip: TempClip; picked: boolean; disabled: boolean; onPick: () => void };

/** Figma component `Pick clip row`: the whole row is the radio's label (44 px and up). */
function PickRow({ clip, picked, disabled, onPick }: RowProps) {
  const reason = !clip.transcribed ? "ยังไม่ถอด" : !clip.described ? "ยังไม่บรรยายฉาก" : null;
  return (
    <li
      aria-label={clip.title}
      className={`flex items-center gap-3 border-t border-border py-2.5 pr-2 pl-4 ${picked ? "bg-accent-subtle" : ""}`}
    >
      <label className="flex min-w-0 flex-1 cursor-pointer items-center gap-3 has-disabled:cursor-default">
        <span className={`flex h-11 w-6 shrink-0 items-center justify-center ${reason ? "opacity-40" : ""}`}>
          <input
            type="radio"
            name="clip"
            checked={picked}
            disabled={reason !== null || disabled}
            onChange={onPick}
            aria-label={`เลือก ${clip.title}`}
            className="sr-only"
          />
          <img src={picked ? radioSelectedIcon : radioIcon} alt="" width={16} height={16} />
        </span>
        <span className="relative h-[45px] w-20 shrink-0 overflow-hidden rounded bg-surface-strong">
          {clip.thumbnail && (
            <img src={`${CLIPS_PATH}/${clip.id}/thumbnail`} alt="" className="absolute inset-0 h-full w-full object-cover" />
          )}
          <img src={playIcon} alt="" width={20} height={20} className="absolute top-[12.5px] left-[30px]" />
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="line-clamp-2 min-w-0 text-sm leading-[21px] font-medium text-foreground sm:truncate">{clip.title}</span>
          {clip.duration_s !== null && (
            <span className="font-mono text-xs leading-4 text-mid">{formatDuration(clip.duration_s)}</span>
          )}
          {reason && (
            <span className="flex flex-col items-start gap-2 sm:flex-row sm:items-center">
              <span className="text-[13px] leading-5 whitespace-nowrap text-mid">{reason}</span>
              <a href="#/clips" className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
                {clip.transcribed ? "ไปบรรยายฉาก" : "ไปถอด"}
              </a>
            </span>
          )}
        </span>
      </label>
    </li>
  );
}
