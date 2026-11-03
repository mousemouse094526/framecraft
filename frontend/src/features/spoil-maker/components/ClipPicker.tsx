import type { TempClip } from "../../../lib/clips";
import { CLIPS_PATH } from "../../../lib/clips";
import { formatDuration } from "../../../lib/format";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import checkWhiteIcon from "../assets/check-white.svg";
import chevronDownIcon from "../assets/chevron-down-dark.svg";
import chevronUpIcon from "../assets/chevron-up-dark.svg";
import fileTextIcon from "../../../components/ui/assets/file-text-24.svg";
import playIcon from "../../../components/ui/assets/play.svg";

type Props = {
  clips: TempClip[];
  /** The picked clips' ids, in episode order (D5). */
  picked: string[];
  disabled: boolean;
  onChange: (picked: string[]) => void;
};

/** Ready to draft from: transcribed and described (D16). */
export const isReady = (clip: TempClip) => clip.transcribed && clip.described;

/**
 * Figma `Clips card` of ตั้งค่าคลิปสปอย: picked clips first in episode order with ตอน N and
 * move up / down, then the rest; a clip not ready says why with a link to the คลิป tab (D5, D16).
 */
export function ClipPicker({ clips, picked, disabled, onChange }: Props) {
  const byId = new Map(clips.map((clip) => [clip.id, clip]));
  const pickedClips = picked.map((id) => byId.get(id)).filter((clip): clip is TempClip => clip !== undefined);
  const rest = clips.filter((clip) => !picked.includes(clip.id));
  const ready = clips.filter(isReady);

  const move = (index: number, by: number) => {
    const next = [...picked];
    [next[index], next[index + by]] = [next[index + by], next[index]];
    onChange(next);
  };

  return (
    <section aria-label="เลือกตอน" className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card lg:w-[560px] lg:shrink-0">
      <h3 className="flex items-center gap-2 px-4 py-3 leading-[1.5] whitespace-nowrap">
        <span className="text-sm font-medium text-foreground">เลือกตอน</span>
        <span className="font-mono text-[13px] text-muted-foreground">{picked.length}</span>
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
          {pickedClips.map((clip, index) => (
            <PickRow
              key={clip.id}
              clip={clip}
              episode={index + 1}
              disabled={disabled}
              onToggle={() => onChange(picked.filter((id) => id !== clip.id))}
              onUp={index > 0 ? () => move(index, -1) : null}
              onDown={index < pickedClips.length - 1 ? () => move(index, 1) : null}
            />
          ))}
          {rest.map((clip) => (
            <PickRow
              key={clip.id}
              clip={clip}
              episode={null}
              disabled={disabled}
              onToggle={() => onChange([...picked, clip.id])}
              onUp={null}
              onDown={null}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

type RowProps = {
  clip: TempClip;
  /** Its place among the picked clips, or null when not picked. */
  episode: number | null;
  disabled: boolean;
  onToggle: () => void;
  onUp: (() => void) | null;
  onDown: (() => void) | null;
};

/** Figma component `Pick clip row`: the whole row is the checkbox's label (44 px and up). */
function PickRow({ clip, episode, disabled, onToggle, onUp, onDown }: RowProps) {
  const reason = !clip.transcribed ? "ยังไม่ถอด" : !clip.described ? "ยังไม่บรรยายฉาก" : null;
  const picked = episode !== null;
  return (
    <li
      aria-label={clip.title}
      className={`flex items-center gap-3 border-t border-border py-2.5 pr-2 pl-4 ${picked ? "bg-accent-subtle" : ""}`}
    >
      <label className="flex min-w-0 flex-1 cursor-pointer items-center gap-3 has-disabled:cursor-default">
        <span className={`relative flex h-11 w-6 shrink-0 items-center justify-center ${reason ? "opacity-40" : ""}`}>
          <input
            type="checkbox"
            checked={picked}
            disabled={reason !== null || disabled}
            onChange={onToggle}
            aria-label={`เลือก ${clip.title}`}
            className="peer size-4 appearance-none rounded border border-border-strong bg-card checked:border-brand checked:bg-brand"
          />
          <img
            src={checkWhiteIcon}
            alt=""
            width={12}
            height={12}
            className="pointer-events-none absolute hidden peer-checked:block"
          />
        </span>
        <span className="relative h-[45px] w-20 shrink-0 overflow-hidden rounded bg-surface-strong">
          {clip.thumbnail && (
            <img src={`${CLIPS_PATH}/${clip.id}/thumbnail`} alt="" className="absolute inset-0 h-full w-full object-cover" />
          )}
          <img src={playIcon} alt="" width={20} height={20} className="absolute top-[12.5px] left-[30px]" />
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          {/* Desktop: ตอน N, the title, then the length under them. A phone wraps the title to two
              lines and puts ตอน N on the line under it, before the length (Figma mobile frame). */}
          <span className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
            <span className="line-clamp-2 min-w-0 basis-full text-sm leading-[21px] font-medium text-foreground sm:order-2 sm:flex-1 sm:basis-auto sm:truncate">
              {clip.title}
            </span>
            {picked && (
              <span className="shrink-0 rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link sm:order-1">
                ตอน {episode}
              </span>
            )}
            {clip.duration_s !== null && (
              <span className="font-mono text-xs leading-4 text-mid sm:order-3 sm:basis-full">
                {formatDuration(clip.duration_s)}
              </span>
            )}
          </span>
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
      {picked && (
        <span className="flex shrink-0 flex-col sm:flex-row sm:gap-1">
          <OrderButton label={`เลื่อน ${clip.title} ขึ้น`} icon={chevronUpIcon} onClick={onUp} disabled={disabled} />
          <OrderButton label={`เลื่อน ${clip.title} ลง`} icon={chevronDownIcon} onClick={onDown} disabled={disabled} />
        </span>
      )}
    </li>
  );
}

type OrderProps = { label: string; icon: string; onClick: (() => void) | null; disabled: boolean };

/** Up is off on the first picked clip, down on the last. */
function OrderButton({ label, icon, onClick, disabled }: OrderProps) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={onClick === null || disabled}
      onClick={onClick ?? undefined}
      className="flex size-11 items-center justify-center rounded-lg hover:bg-card disabled:opacity-40 disabled:hover:bg-transparent"
    >
      <img src={icon} alt="" width={16} height={16} />
    </button>
  );
}
