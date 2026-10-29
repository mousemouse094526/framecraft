import { useEffect, useRef } from "react";
import { CLIPS_PATH, type TempClip } from "../hooks/useTempClips";
import { formatDuration } from "./format";
import deleteErrorIcon from "../assets/delete-error.svg";
import playActiveIcon from "../assets/thumb-play-active.svg";
import playIcon from "../assets/thumb-play.svg";
import trashIcon from "../assets/trash.svg";

type Props = {
  clips: TempClip[];
  /** The clip in the transcript panel's player (D25). */
  selectedId: string | null;
  /** The clip the Transcribe job is on, while it is unfinished. */
  transcribingId: string | null;
  deleteErrors: Record<string, string>;
  /** The row the message above is about: a new clip or a duplicate link (D12). */
  highlightId: string | null;
  onSelect: (clip: TempClip) => void;
  /** Lets go of the selected clip's file and empties the panel (D15). */
  onClosePlayer: () => void;
  onDelete: (id: string) => void;
};

/** The Temp clip list, newest first; a row puts its clip in the transcript panel (D7, D18, D25). */
export function TempClipList(props: Props) {
  const { clips, selectedId, transcribingId, deleteErrors, highlightId, onSelect, onClosePlayer, onDelete } = props;
  const remove = (clip: TempClip) => {
    if (!window.confirm(`ลบ ${clip.title}?`)) return;
    // Windows can't delete a file the player still holds open (D15). The panel
    // stays empty even when the delete is refused, except for the clip being
    // transcribed: the API refuses that one, so its progress stays (D34).
    if (clip.id === selectedId && clip.id !== transcribingId) onClosePlayer();
    onDelete(clip.id);
  };

  return (
    <section className="overflow-hidden rounded-2xl border border-border bg-card">
      <h2 className="flex items-center gap-2 px-4 py-3 whitespace-nowrap">
        <span className="text-sm leading-[1.5] font-medium text-foreground">คลิปที่โหลดมา</span>{" "}
        <span className="font-mono text-[13px] leading-[1.5] font-normal text-muted-foreground">{clips.length}</span>
      </h2>
      {clips.length === 0 ? (
        <p className="border-t border-border pt-10 pb-11 text-center text-sm leading-[1.5] text-muted-foreground">
          ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน
        </p>
      ) : (
        <ul>
          {clips.map((clip) => (
            <ClipRow
              key={clip.id}
              clip={clip}
              selected={clip.id === selectedId}
              highlighted={clip.id === highlightId}
              deleteError={deleteErrors[clip.id] ?? null}
              onSelect={() => onSelect(clip)}
              onDelete={() => remove(clip)}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

type RowProps = {
  clip: TempClip;
  /** In the panel's player; the row says กำลังเล่น (D18). */
  selected: boolean;
  highlighted: boolean;
  deleteError: string | null;
  onSelect: () => void;
  onDelete: () => void;
};

/** Figma component `Clip row`: default, highlight, playing, ถอดแล้ว (D23), and a delete error under it. */
function ClipRow({ clip, selected, highlighted, deleteError, onSelect, onDelete }: RowProps) {
  const row = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (highlighted) row.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [highlighted]);

  const look = highlighted ? "border-l-3 border-l-brand-accent bg-accent-subtle" : selected ? "bg-muted" : "";

  return (
    <li
      ref={row}
      aria-label={clip.title}
      aria-current={highlighted ? "true" : undefined}
      className={`flex flex-col gap-2 border-t border-border py-3 pr-3 pl-4 ${look}`}
    >
      <div className="flex items-center gap-3">
        <button type="button" onClick={onSelect} className="flex min-w-0 flex-1 items-center gap-3 text-left">
          <span className="relative h-[54px] w-24 shrink-0 overflow-hidden rounded bg-surface-strong">
            {clip.thumbnail && (
              <img
                src={`${CLIPS_PATH}/${clip.id}/thumbnail`}
                alt=""
                className="absolute inset-0 h-full w-full object-cover"
              />
            )}
            <img
              src={selected ? playActiveIcon : playIcon}
              alt=""
              width={20}
              height={20}
              className="absolute top-[17px] left-[38px]"
            />
          </span>
          <span className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="min-w-[160px] flex-1 truncate text-sm leading-[1.5] font-medium text-foreground">
                {clip.title}
              </span>
              {selected && (
                <span className="shrink-0 rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
                  กำลังเล่น
                </span>
              )}
              {clip.transcribed && (
                <span className="shrink-0 rounded-full bg-success-surface px-2 py-0.5 font-button text-xs leading-4 font-medium text-success">
                  ถอดแล้ว
                </span>
              )}
            </span>
            <span className="text-[13px] leading-[1.5] text-mid">{sourceLine(clip)}</span>
            <span className="font-mono text-xs leading-[1.5] text-muted-foreground">{fileLine(clip)}</span>
          </span>
        </button>
        <button
          type="button"
          onClick={onDelete}
          aria-label={`ลบ ${clip.title}`}
          title="ลบ"
          className="flex size-9 shrink-0 items-center justify-center rounded-lg hover:bg-muted"
        >
          <img src={trashIcon} alt="" width={16} height={16} />
        </button>
      </div>
      {deleteError && (
        <p className="flex items-center gap-1.5 pl-[108px] text-[13px] leading-[1.5] text-destructive">
          <img src={deleteErrorIcon} alt="" width={14} height={14} className="shrink-0" />
          {deleteError}
        </p>
      )}
    </li>
  );
}

/** "ช่อง · 1:35:42" (spec › Frontend). */
function sourceLine(clip: TempClip): string {
  const duration = clip.duration_s === null ? null : formatDuration(clip.duration_s);
  return [clip.channel, duration].filter(Boolean).join(" · ");
}

/** "1920×1080 นอน · 1.6 GB · 29 ต.ค. 18:52" (spec › Frontend). */
function fileLine(clip: TempClip): string {
  const orientation = clip.orientation === "portrait" ? "ตั้ง" : "นอน";
  const frame = clip.width && clip.height ? `${clip.width}×${clip.height} ${orientation}` : orientation;
  return [frame, formatSize(clip.file_bytes), formatTime(clip.downloaded_at)].join(" · ");
}

/** MB or GB with one decimal, in powers of 1000 like the backend's disk message. */
function formatSize(bytes: number): string {
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(1)} GB` : `${(bytes / 1e6).toFixed(1)} MB`;
}

const TIME_FORMAT = new Intl.DateTimeFormat("th-TH", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/** Local time, "29 ต.ค. 18:52". */
function formatTime(iso: string): string {
  return TIME_FORMAT.format(new Date(iso));
}
