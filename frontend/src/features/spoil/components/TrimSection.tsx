import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { GHOST_BUTTON, PRIMARY_BUTTON, SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import type { Range } from "../../../lib/clips";
import { formatDuration } from "../../../lib/format";
import type { TrimJob, TrimView } from "../hooks/useTrim";
import {
  cutSeconds,
  draftOf,
  formatTime,
  MAX_RANGES,
  MIN_KEPT_S,
  rangeAt,
  rangeErrors,
  rangeOf,
  SIDE_WORDS,
  toTenth,
  type RangeDraft,
  type Side,
} from "../lib/trim";
import clockIcon from "../assets/clock.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import scissorsIcon from "../assets/scissors.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { ProgressCard } from "./ProgressCard";
import { TrimTimeline } from "./TrimTimeline";

type Props = {
  videoRef: RefObject<HTMLVideoElement | null>;
  /** The clip's length from the list, until the player knows it to the frame. */
  durationS: number | null;
  view: TrimView;
  /** ffmpeg isn't ok, or this clip is being transcribed: ตัดช่วง stays disabled. */
  blocked: boolean;
  onOpen: () => void;
  onEdit: (drafts: RangeDraft[]) => void;
  onClose: () => void;
  onTrim: (ranges: Range[]) => void;
  onCancel: () => void;
};

/** Figma component `Trim section` and the `Transcript panel` trim states (D38, D41, D44). */
export function TrimSection({ videoRef, durationS, view, blocked, onOpen, onEdit, onClose, onTrim, onCancel }: Props) {
  const length = useMediaLength(videoRef, durationS);

  switch (view.kind) {
    case "running":
      return (
        <SectionBox>
          <TrimProgress job={view.job} onCancel={onCancel} />
        </SectionBox>
      );
    case "editing":
      // No length (none in the list, and the player hasn't read the file): ตัดช่วง stays disabled below.
      if (length !== null) {
        return (
          <SectionBox>
            <RangeEditor videoRef={videoRef} length={length} drafts={view.drafts} onEdit={onEdit} onClose={onClose} onTrim={onTrim} />
          </SectionBox>
        );
      }
  }
  const otherTitle = view.kind === "otherClip" ? view.title : null;
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={onOpen}
        disabled={blocked || otherTitle !== null || length === null}
        className={`h-8 px-3 ${SECONDARY_BUTTON}`}
      >
        <img src={scissorsIcon} alt="" width={16} height={16} />
        ตัดช่วง
      </button>
      {otherTitle !== null && (
        <>
          <img src={clockIcon} alt="" width={16} height={16} className="shrink-0" />
          <p className="min-w-0 flex-1 text-sm leading-[1.5] text-mid">กำลังตัด {otherTitle}</p>
        </>
      )}
    </div>
  );
}

function SectionBox({ children }: { children: ReactNode }) {
  return (
    <section aria-label="ตัดช่วง" className="flex flex-col gap-4 rounded-xl border border-border bg-muted p-4">
      <h3 className="flex items-center gap-2 text-sm leading-[1.5] font-medium text-foreground">
        <img src={scissorsIcon} alt="" width={16} height={16} />
        ตัดช่วง
      </h3>
      {children}
    </section>
  );
}

/** A value read off the player, read again on each of `events`. */
function useVideoValue<T>(videoRef: RefObject<HTMLVideoElement | null>, events: string[], read: (video: HTMLVideoElement) => T, initial: T): T {
  const [value, setValue] = useState<T>(() => (videoRef.current ? read(videoRef.current) : initial));
  const reader = useRef(read);
  useEffect(() => {
    reader.current = read;
  });
  const eventList = events.join(" ");
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const update = () => setValue(reader.current(video));
    const names = eventList.split(" ");
    for (const name of names) video.addEventListener(name, update);
    return () => names.forEach((name) => video.removeEventListener(name, update));
  }, [videoRef, eventList]);
  return value;
}

/** Floored to a tenth: times move in tenths, and a range ending past the file's real length is refused (D41, D45). */
const mediaLengthOf = (video: HTMLVideoElement): number | null =>
  Number.isFinite(video.duration) && video.duration > 0 ? Math.floor(video.duration * 10) / 10 : null;

/**
 * The player's own length once it has read the file, else the list's (a whole number that
 * may round past the end). The player keeps it while its file is let go during a trim, and
 * reads the new one when the trimmed file loads.
 */
function useMediaLength(videoRef: RefObject<HTMLVideoElement | null>, durationS: number | null): number | null {
  const [mediaLength, setMediaLength] = useState<number | null>(null);
  const read = useVideoValue(videoRef, ["durationchange"], mediaLengthOf, null);
  useEffect(() => {
    if (read !== null) setMediaLength(read);
  }, [read]);
  return mediaLength ?? durationS;
}

/** The player's time, followed as it plays or seeks. */
const usePlayhead = (videoRef: RefObject<HTMLVideoElement | null>): number =>
  useVideoValue(videoRef, ["timeupdate", "seeked"], (video) => video.currentTime, 0);

type EditorProps = {
  videoRef: RefObject<HTMLVideoElement | null>;
  length: number;
  drafts: RangeDraft[];
  onEdit: (drafts: RangeDraft[]) => void;
  onClose: () => void;
  onTrim: (ranges: Range[]) => void;
};

/** The timeline, the ranges' fields, เพิ่มช่วง, what is cut and left, then ตัดคลิป and ยกเลิก (spec › Frontend). */
function RangeEditor({ videoRef, length, drafts, onEdit, onClose, onTrim }: EditorProps) {
  const playhead = usePlayhead(videoRef);
  const ranges = drafts.map((draft) => rangeOf(draft, length));
  const valid = ranges.filter((range): range is Range => range !== null);
  const cut = cutSeconds(valid);
  const left = length - cut;
  const canTrim = drafts.length > 0 && valid.length === drafts.length && left >= MIN_KEPT_S;
  const canAdd = drafts.length < MAX_RANGES && rangeAt(playhead, valid, length) !== null;
  const now = () => toTenth(videoRef.current?.currentTime ?? 0);

  const change = (index: number, side: Side, text: string) =>
    onEdit(drafts.map((draft, i) => (i === index ? { ...draft, [side]: text } : draft)));

  const add = () => {
    const range = rangeAt(now(), valid, length);
    if (range) onEdit([...drafts, draftOf(range)]);
  };

  const seek = (seconds: number) => {
    if (videoRef.current) videoRef.current.currentTime = seconds;
  };

  return (
    <>
      <TrimTimeline
        length={length}
        ranges={ranges.flatMap((range, i) => (range ? [{ n: i + 1, range }] : []))}
        playhead={playhead}
        onSeek={seek}
        onMove={(n, side, seconds) => change(n - 1, side, formatTime(seconds))}
      />
      {drafts.length > 0 && (
        <div className="flex flex-col gap-3">
          {drafts.map((draft, i) => (
            // The fields are controlled, so an index key still shows each row's own times after a ✕.
            <RangeRow
              key={i}
              n={i + 1}
              draft={draft}
              length={length}
              onChange={(side, text) => change(i, side, text)}
              onNow={(side) => change(i, side, formatTime(now()))}
              onRemove={() => onEdit(drafts.filter((_, j) => j !== i))}
            />
          ))}
        </div>
      )}
      <button type="button" onClick={add} disabled={!canAdd} className={`h-8 w-fit px-3 ${SECONDARY_BUTTON}`}>
        <img src={plusIcon} alt="" width={16} height={16} />
        เพิ่มช่วง
      </button>
      <p className="font-mono text-[13px] leading-[1.5] text-mid">
        ตัดออก {formatDuration(Math.round(cut))} · เหลือ {formatDuration(Math.round(left))}
      </p>
      <div className="flex items-center gap-2">
        <button type="button" onClick={() => onTrim(valid)} disabled={!canTrim} className={`h-9 px-4 ${PRIMARY_BUTTON}`}>
          ตัดคลิป
        </button>
        <button type="button" onClick={onClose} className={`h-9 px-4 ${SECONDARY_BUTTON}`}>
          ยกเลิก
        </button>
      </div>
    </>
  );
}

type RowProps = {
  n: number;
  draft: RangeDraft;
  length: number;
  onChange: (side: Side, text: string) => void;
  onNow: (side: Side) => void;
  onRemove: () => void;
};

/** Figma component `Trim range row`: its number, เริ่ม and จบ each with "= ตอนนี้" under it, and ✕ (D44). */
function RangeRow({ n, draft, length, onChange, onNow, onRemove }: RowProps) {
  const errors = rangeErrors(draft, length);
  return (
    <div role="group" aria-label={`ช่วง ${n}`} className="flex items-start gap-2">
      <p className="pt-[30px] font-mono text-[13px] leading-[1.5] text-mid">{n}.</p>
      {(["start", "end"] as const).map((side) => (
        <div key={side} className="flex min-w-0 flex-1 flex-col gap-1">
          <label className="flex flex-col gap-2 font-button text-sm leading-5 font-medium text-foreground">
            {SIDE_WORDS[side].field}
            <input
              value={draft[side]}
              onChange={(event) => onChange(side, event.target.value)}
              aria-invalid={errors[side]}
              inputMode="decimal"
              className={`h-10 w-full rounded-lg border bg-card px-3 font-button text-sm leading-5 font-normal text-foreground ${
                errors[side] ? "border-destructive" : "border-border"
              }`}
            />
          </label>
          {errors[side] && <p className="font-button text-xs leading-4 text-destructive">เวลาไม่ถูกต้อง</p>}
          <button type="button" onClick={() => onNow(side)} className={`h-8 w-fit px-3 ${GHOST_BUTTON}`}>
            {SIDE_WORDS[side].now}
          </button>
        </div>
      ))}
      <div className="pt-[26px]">
        <button
          type="button"
          onClick={onRemove}
          aria-label={`ลบช่วง ${n}`}
          className="flex size-9 items-center justify-center rounded-lg hover:bg-card"
        >
          <img src={xIcon} alt="" width={16} height={16} />
        </button>
      </div>
    </div>
  );
}

/** "กำลังตัดคลิป" with its percent, then "กำลังแทนไฟล์…" with a full bar and no ยกเลิก (D44). */
function TrimProgress({ job, onCancel }: { job: TrimJob; onCancel: () => void }) {
  const replacing = job.state === "replacing";
  const headline = job.cancel_requested ? "กำลังยกเลิก…" : replacing ? "กำลังแทนไฟล์…" : "กำลังตัดคลิป";
  return (
    <ProgressCard
      headline={headline}
      percent={replacing ? null : job.percent}
      bar={replacing ? 100 : (job.percent ?? "unknown")}
      cancelling={job.cancel_requested}
      onCancel={onCancel}
      noCancelReason={replacing ? "ยกเลิกไม่ได้ระหว่างแทนไฟล์" : undefined}
    />
  );
}
