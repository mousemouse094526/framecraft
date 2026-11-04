import { useEffect, useId, useRef, useState } from "react";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import { formatClock } from "../../../lib/format";
import pencilIcon from "../assets/pencil.svg";
import plusIcon from "../assets/plus.svg";
import refreshIcon from "../../../components/ui/assets/refresh-cw.svg";
import scanLineIcon from "../assets/scan-line.svg";
import trashRedIcon from "../assets/trash-red.svg";
import trashWhiteIcon from "../assets/trash-white.svg";
import { useAutoSave } from "../hooks/useAutoSave";
import { REVIEW_JOB_TEXT, shotImageUrl, type DraftJob, type Sentence, type SentenceStatus, type Shot } from "../lib/draft";
import { playAudio } from "../lib/audio";
import { sentenceAudioUrl } from "../lib/render";

// Figma component `Status badge` (spoil-maker D30).
const STATUS_LOOK: Record<SentenceStatus, { label: string; className: string }> = {
  no_shot: { label: "ไม่มี Shot", className: "bg-destructive text-card" },
  no_audio: { label: "ยังไม่มีเสียง", className: "bg-muted text-brand" },
  stale_audio: { label: "ต้องสร้างเสียงใหม่", className: "bg-warning-surface text-warning" },
  ready: { label: "พร้อม", className: "bg-success-surface text-success" },
};

type Props = {
  sentence: Sentence;
  number: number;
  /** "EP 2": the draft's EP, which every Shot and cited line is of. */
  episode: string;
  shots: Record<string, Shot[]>;
  /** A job changes the draft: every field and button waits (D51). */
  locked: boolean;
  /** The pick running for this sentence now, if any. */
  picking: DraftJob | null;
  /** Focus the text, with it selected: a sentence just inserted. */
  focus: boolean;
  onText: (text: string) => Promise<boolean>;
  onOpenPicker: (slot: number) => void;
  onPick: () => void;
  onCancelPick: () => void;
  /** สร้างเสียงใหม่: this sentence alone, even when it is `ready` (D30). */
  onVoice: () => void;
  onInsert: () => void;
  onDelete: () => void;
};

/**
 * Figma component `Sentence card`: two Shots, the text that saves itself, the lines it
 * cites, ฟัง, สร้างเสียงใหม่, AI เลือก Shot ใหม่, แทรกใต้ and ลบ with its confirm, and
 * แก้เอง on a sentence the user wrote (spoil-maker D19, D25, D26, D27, D30, D74).
 */
export function SentenceCard(props: Props) {
  const { sentence, number, episode, shots, locked, picking, focus } = props;
  const text = useAutoSave(sentence.text, props.onText);
  const [confirming, setConfirming] = useState(false);
  const textId = useId();
  const field = useRef<HTMLTextAreaElement>(null);
  const status = STATUS_LOOK[sentence.status];

  useEffect(() => {
    if (focus) field.current?.select();
  }, [focus]);

  return (
    <li aria-label={`ประโยค ${number}`} className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center gap-2">
        <label htmlFor={textId} className="text-sm font-semibold whitespace-nowrap text-foreground">
          ประโยค {number}
        </label>
        <span className={`rounded-full px-2 py-0.5 font-button text-xs leading-4 font-medium whitespace-nowrap ${status.className}`}>
          {status.label}
        </span>
        {/* The user's text: เรียบเรียงใหม่ keeps it unless told (D74, D75). */}
        {sentence.edited && (
          <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium whitespace-nowrap text-link">
            แก้เอง
          </span>
        )}
        <span className="flex-1" />
        {sentence.estimated_s !== null && (
          <span className="text-[13px] font-medium whitespace-nowrap text-mid">{sentence.estimated_s.toFixed(1)} วิ</span>
        )}
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
        <div className="flex gap-2">
          {sentence.shots.map((slot, index) => (
            <ShotThumb
              key={index}
              label={`เปลี่ยน Shot ${index + 1}`}
              shot={slot ? (shots[slot.clip_id]?.[slot.n] ?? null) : null}
              clipId={slot?.clip_id ?? null}
              episode={slot ? episode : null}
              loading={picking !== null}
              disabled={locked}
              onOpen={() => props.onOpenPicker(index)}
            />
          ))}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <textarea
            id={textId}
            ref={field}
            value={text.value}
            disabled={locked}
            onChange={(event) => text.change(event.target.value)}
            onBlur={() => void text.flush()}
            className="min-h-[90px] w-full resize-y rounded-lg border border-border bg-card px-3 py-2.5 text-[15px] leading-6 text-foreground disabled:bg-muted"
          />
          {sentence.ref_lines.length > 0 && (
            <p className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-[13px]">
              <span className="text-muted-foreground">อ้าง:</span>
              {sentence.ref_lines.map((line) => (
                <span key={`${line.clip_id}-${line.line}`} className="flex min-w-0 items-center gap-1.5">
                  <span className="font-mono whitespace-nowrap text-link">
                    {episode} {formatClock(line.start)}
                  </span>
                  <span className="min-w-0 truncate text-mid">"{line.text}"</span>
                </span>
              ))}
            </p>
          )}
        </div>
      </div>
      {picking && <ReviewJobProgress job={picking} onCancel={props.onCancelPick} />}
      {confirming ? (
        <div className="flex items-center gap-2 rounded-lg border border-error-border bg-error-surface py-2 pr-2 pl-3">
          <p className="min-w-0 flex-1 text-sm font-medium text-destructive">ลบประโยคนี้?</p>
          <button type="button" onClick={() => setConfirming(false)} className={`h-11 px-6 ${OUTLINE_BUTTON}`}>
            ยกเลิก
          </button>
          <button
            type="button"
            autoFocus
            onClick={() => {
              setConfirming(false);
              props.onDelete();
            }}
            className={`h-11 px-6 ${DESTRUCTIVE_BUTTON}`}
          >
            <img src={trashWhiteIcon} alt="" width={16} height={16} />
            ลบ
          </button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => listen(sentence)}
            disabled={sentence.audio === null}
            title={sentence.audio === null ? "ประโยคนี้ยังไม่มีเสียง" : undefined}
            className={`h-11 px-3 sm:px-6 ${OUTLINE_BUTTON}`}
          >
            ฟัง
          </button>
          <button type="button" onClick={props.onVoice} disabled={locked} className={`h-11 px-3 sm:px-6 ${OUTLINE_BUTTON}`}>
            <img src={refreshIcon} alt="" width={16} height={16} />
            สร้างเสียงใหม่
          </button>
          <button
            type="button"
            onClick={props.onPick}
            disabled={locked || sentence.refs.length === 0}
            title={sentence.refs.length === 0 ? "ประโยคนี้ไม่ได้อ้างบรรทัดไหน: เลือกภาพเอง" : undefined}
            className={`h-11 px-3 sm:px-6 ${OUTLINE_BUTTON}`}
          >
            <img src={refreshIcon} alt="" width={16} height={16} />
            เลือก Shot ใหม่
          </button>
          <span className="hidden flex-1 sm:block" />
          <button type="button" onClick={props.onInsert} disabled={locked} className={`h-11 px-3 sm:px-6 ${GHOST_BUTTON}`}>
            <img src={plusIcon} alt="" width={16} height={16} />
            แทรกใต้
          </button>
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={locked}
            aria-label={`ลบประโยค ${number}`}
            className={`h-11 px-3 sm:px-6 ${GHOST_BUTTON} text-destructive`}
          >
            <img src={trashRedIcon} alt="" width={16} height={16} />
            {/* A phone shows the icon only, on the same line (Figma mobile frame). */}
            <span aria-hidden className="hidden sm:inline">
              ลบ
            </span>
          </button>
        </div>
      )}
    </li>
  );
}

function listen(sentence: Sentence) {
  if (sentence.audio !== null) playAudio(sentenceAudioUrl(sentence.id, sentence.audio.duration_s));
}

/** A `pick` or `polish` running: "AI กำลังเลือก Shot ใหม่" or "กำลังเรียบเรียง", with ยกเลิก (spec › Design, หน้าตรวจแก้). */
export function ReviewJobProgress({ job, onCancel }: { job: DraftJob; onCancel: () => void }) {
  const text = REVIEW_JOB_TEXT[job.kind === "polish" ? "polish" : "pick"];
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <p className="text-[13px] font-semibold text-foreground">
          {job.cancel_requested ? "กำลังยกเลิก…" : text.doing}
        </p>
        <ProgressBar percent="unknown" label={text.label} cancelling={job.cancel_requested} />
      </div>
      <button type="button" onClick={onCancel} disabled={job.cancel_requested} className={`h-11 px-6 ${OUTLINE_BUTTON}`}>
        ยกเลิก
      </button>
    </div>
  );
}

type ThumbProps = {
  label: string;
  shot: Shot | null;
  clipId: string | null;
  episode: string | null;
  loading: boolean;
  disabled: boolean;
  onOpen: () => void;
};

/** Figma component `Shot thumb`: the picture is a button that opens the Shot picker; empty says เลือก Shot. */
function ShotThumb({ label, shot, clipId, episode, loading, disabled, onOpen }: ThumbProps) {
  const box = "relative flex h-[84px] w-[150px] flex-col items-center justify-center gap-1 overflow-hidden rounded-lg sm:h-[90px] sm:w-40";
  let picture;
  if (loading) {
    picture = (
      <span className={`${box} bg-muted`}>
        <span className="h-2 w-20 rounded-full bg-border" />
      </span>
    );
  } else if (shot && clipId) {
    picture = (
      <button type="button" aria-label={label} onClick={onOpen} disabled={disabled} className={`${box} bg-surface-inverse disabled:opacity-60`}>
        <img src={shotImageUrl(clipId, shot.n)} alt="" className="absolute inset-0 h-full w-full object-cover" />
        <span className="absolute top-1.5 right-1.5 flex rounded-full bg-card p-1.5">
          <img src={pencilIcon} alt="" width={24} height={24} />
        </span>
      </button>
    );
  } else {
    picture = (
      <button
        type="button"
        aria-label={label}
        onClick={onOpen}
        disabled={disabled}
        className={`${box} border border-dashed border-border-strong bg-muted disabled:opacity-60`}
      >
        <img src={scanLineIcon} alt="" width={24} height={24} />
        <span className="text-xs font-medium text-mid">เลือก Shot</span>
      </button>
    );
  }
  return (
    <div className="flex flex-col gap-1.5">
      {picture}
      <p className="font-mono text-xs text-mid">{shot && episode && !loading ? `${episode} · ${formatClock(shot.start)}` : "–"}</p>
    </div>
  );
}
