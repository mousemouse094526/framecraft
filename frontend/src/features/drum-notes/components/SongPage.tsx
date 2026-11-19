import { useId, useRef, useState, type ReactNode, type RefObject } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, PRIMARY_BUTTON, SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import { RefusedAlert } from "../../../components/ui/RefusedAlert";
import { inputClass } from "../../../components/ui/inputStyles";
import { Labeled } from "../../../components/ui/Labeled";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { formatDuration } from "../../../lib/format";
import { useRecentPage } from "../../../lib/recent";
import { refusedLine, type Refused } from "../../../lib/refused";
import { mayLeave } from "../../../lib/useHash";
import { usePick } from "../hooks/usePick";
import { useSong } from "../hooks/useSong";
import {
  audioUrl,
  isPicking,
  lateStart,
  lateStartText,
  MELODY_HINT,
  MODE_LABELS,
  noHitsText,
  PICK_SECTION_ID,
  pickingOf,
  pickText,
  RANGE_MAX_S,
  RANGE_RULE,
  rangeFault,
  seconds,
  SONGS_HASH,
  SOURCE_LABELS,
  type Mode,
  type PickJob,
  type Range,
  type Song,
  songHash,
} from "../lib/songs";

/**
 * หน้าเพลง (`#/covers/{id}`): the song's head and player, the range and mode, the Pick job, and once
 * picked its reel, all one page (spec › Design, D5, D6, D18; ui-prompt.md screen 2, D28; nav-ia D6).
 * `reel` is drum-cover's part, put in by `App`, so this feature doesn't depend on that one (ADR 0052,
 * nav-ia D14). Nothing on it makes a lesson (reels-only D6).
 */
export function SongPage({ id, notice, reel }: { id: string; notice: string | null; reel?: (song: Song) => ReactNode }) {
  const { state, reload, replace } = useSong(id);
  useRecentPage("covers", songHash(id), state.kind === "ready" ? { label: state.song.title } : state.kind === "not_found" ? "gone" : null);
  const player = useRef<HTMLAudioElement>(null);
  const reelPart = useRef<HTMLDivElement>(null);
  // A new pick starts the reel over: an unsaved reel asks first, as leaving would (nav-ia D14).
  const startPick = (range: Range) => {
    if (mayLeave()) void pick.start(id, range);
  };
  const pick = usePick(replace, (job) => {
    if (job.song_id === id && job.state === "done") void reload();
  });

  return (
    <PageLayout tab="covers" wide>
      <div className="flex items-center gap-2">
        <a href={SONGS_HASH} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          รายการเพลง
        </a>
        {state.kind === "ready" && <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">{state.song.title}</h2>}
        {state.kind === "ready" && state.song.analysis && reel && (
          <button type="button" onClick={() => reelPart.current?.scrollIntoView({ behavior: "smooth", block: "start" })} className={`h-11 shrink-0 px-3 sm:h-8 ${GHOST_BUTTON}`}>
            ไปที่ reel
          </button>
        )}
      </div>
      {notice && <Alert tone="info">{notice}</Alert>}
      {state.kind === "loading" && <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && <OfflinePanel />}
      {state.kind === "not_found" && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card px-4 py-12">
          <p className="text-base leading-[1.5] font-medium text-foreground">ไม่พบเพลงนี้</p>
          <a href={SONGS_HASH} className={`h-11 px-4 sm:h-9 ${GHOST_BUTTON}`}>
            กลับไปรายการเพลง
          </a>
        </div>
      )}
      {state.kind === "ready" && (
        <>
          <Head song={state.song} player={player} />
          {state.song.source.kind !== "midi" && state.song.range && (
            <PickSection
              // A range saved elsewhere (เริ่มช่วงที่การตีแรก) shows in the fields.
              key={`${state.song.range.start_s}-${state.song.range.end_s}-${state.song.range.mode}`}
              song={state.song}
              range={state.song.range}
              job={pick.job}
              refused={pick.refused}
              player={player}
              onStart={startPick}
              onCancel={() => void pick.cancel()}
            />
          )}
          {state.song.analysis && <DrumsStart song={state.song} picking={pick.job !== null && isPicking(pick.job)} onRepick={startPick} />}
          {state.song.analysis ? reel && <div ref={reelPart} className="flex flex-col gap-4">{reel(state.song)}</div> : <EmptyNote text="ตั้งช่วงแล้วกด แกะโน้ต" />}
        </>
      )}
    </PageLayout>
  );
}

/** The subtitle, where the song came from and its length; the player for a song with audio (a MIDI file has none, D18). */
function Head({ song, player }: { song: Song; player: RefObject<HTMLAudioElement | null> }) {
  return (
    <section aria-label="เพลง" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
      {song.subtitle && <p className="text-sm leading-[1.5] text-mid">{song.subtitle}</p>}
      <p className="flex flex-wrap gap-x-1.5 text-[13px] text-mid">
        <span>{SOURCE_LABELS[song.source.kind]}</span>
        <span className="text-muted-foreground">·</span>
        <span>{formatDuration(Math.round(song.duration_s))}</span>
      </p>
      {song.source.kind !== "midi" && (
        <audio ref={player} controls preload="metadata" src={audioUrl(song.id)} aria-label="เสียงเพลง" className="w-full" />
      )}
    </section>
  );
}

type PickSectionProps = {
  song: Song;
  /** The saved range the fields start from. */
  range: Range;
  job: PickJob | null;
  refused: Refused | null;
  player: RefObject<HTMLAudioElement | null>;
  onStart: (range: Range) => void;
  onCancel: () => void;
};

/**
 * ช่วงแกะ, โหมด and แกะโน้ต: the fields start from the saved range; แกะโน้ต saves them and starts the
 * job, which shows its bar and ยกเลิก here while it runs, and its failure after (spec › Design, D5, D18, D20).
 */
function PickSection({ song, range, job, refused, player, onStart, onCancel }: PickSectionProps) {
  const [start, setStart] = useState(String(range.start_s));
  const [end, setEnd] = useState(String(range.end_s));
  const [mode, setMode] = useState<Mode>(range.mode);
  const [touched, setTouched] = useState(false);
  const id = useId();
  const start_s = Number(start);
  const end_s = Number(end);
  const fault = rangeFault(start_s, end_s, song.duration_s);
  const shown = touched ? fault : null;
  const field = shown ?? refused?.field ?? null;
  const running = job !== null && isPicking(job); // any song's: one Pick job at a time
  const picking = pickingOf(job, song.id);
  const failed = job !== null && job.song_id === song.id && job.state === "failed" ? job : null;

  const submit = () => {
    setTouched(true);
    if (fault) return;
    onStart({ start_s, end_s, mode });
  };

  const useCurrent = (set: (value: string) => void) => () => {
    const now = player.current?.currentTime ?? 0;
    set(now.toFixed(1));
    setTouched(true);
  };

  const length = end_s - start_s;
  return (
    <section id={PICK_SECTION_ID} aria-label="ช่วงแกะ" className="flex scroll-mt-4 flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <h3 className="text-base leading-[1.5] font-semibold text-foreground">ช่วงแกะ</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        <RangeField id={`${id}-start`} label="เริ่ม (วินาที)" value={start} error={field === "start_s" ? RANGE_RULE : undefined} disabled={running} onChange={(v) => (setStart(v), setTouched(true))} onUseCurrent={useCurrent(setStart)} />
        <RangeField id={`${id}-end`} label="จบ (วินาที)" value={end} error={field === "end_s" ? RANGE_RULE : undefined} disabled={running} onChange={(v) => (setEnd(v), setTouched(true))} onUseCurrent={useCurrent(setEnd)} />
      </div>
      <p className="text-[13px] leading-[1.5] text-mid">{Number.isNaN(length) ? `ไม่เกิน ${RANGE_MAX_S} วินาที` : `ยาว ${seconds(length)} (ไม่เกิน ${RANGE_MAX_S} วินาที)`}</p>
      <div className="flex flex-col gap-2">
        <p className="font-button text-sm leading-5 font-medium text-foreground">โหมด</p>
        <div role="radiogroup" aria-label="โหมด" className="flex gap-2">
          {(["drums", "melody"] as Mode[]).map((option) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={mode === option}
              disabled={running}
              onClick={() => setMode(option)}
              className={`h-11 rounded-lg border px-4 font-button text-sm font-medium sm:h-10 ${mode === option ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card text-mid hover:bg-muted"} disabled:opacity-60`}
            >
              {MODE_LABELS[option]}
            </button>
          ))}
        </div>
        {mode === "melody" && <p className="text-xs leading-4 text-muted-foreground">{MELODY_HINT}</p>}
      </div>
      {picking ? (
        <div role="group" aria-label="งานแกะโน้ต" className="flex flex-col gap-2 rounded-xl bg-muted px-4 py-3">
          <div className="flex items-center gap-3">
            <p className="min-w-0 flex-1 text-sm font-medium text-foreground">{pickText(picking)}</p>
            <button type="button" disabled={picking.cancel_requested} onClick={onCancel} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
              <img src={xIcon} alt="" width={16} height={16} />
              ยกเลิก
            </button>
          </div>
          <ProgressBar label="แกะโน้ต" percent={picking.state === "picking" ? picking.percent : "unknown"} cancelling={picking.cancel_requested} />
        </div>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <button type="button" disabled={running} onClick={submit} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
            แกะโน้ต
          </button>
          {running && <p className="text-[13px] leading-[1.5] text-mid">กำลังแกะเพลงอื่นอยู่ รอให้เสร็จก่อน</p>}
        </div>
      )}
      {refused && !refused.field && <RefusedAlert refused={refused} />}
      {failed && !refused && <RefusedAlert refused={refusedLine(failed.message ?? "", failed.fix ? [failed.fix] : [])} />}
    </section>
  );
}

type RangeFieldProps = { id: string; label: string; value: string; error?: string; disabled: boolean; onChange: (value: string) => void; onUseCurrent: () => void };

/** A number field in seconds with ใช้เวลาที่เล่นอยู่, which takes the player's time (spec › Design). */
function RangeField({ id, label, value, error, disabled, onChange, onUseCurrent }: RangeFieldProps) {
  return (
    <Labeled label={label} htmlFor={id} error={error}>
      <div className="flex gap-2">
        <input id={id} type="number" min={0} step={0.1} value={value} disabled={disabled} aria-invalid={error !== undefined} onChange={(e) => onChange(e.target.value)} className={inputClass(error !== undefined)} />
        <button type="button" disabled={disabled} onClick={onUseCurrent} aria-label={`ใช้เวลาที่เล่นอยู่เป็น${label}`} className={`h-11 shrink-0 px-3 sm:h-10 ${GHOST_BUTTON} border border-border`}>
          ใช้เวลาที่เล่นอยู่
        </button>
      </div>
    </Labeled>
  );
}

/** A card that says why a section has nothing to show. */
function EmptyNote({ text }: { text: string }) {
  return <p className="rounded-2xl border border-border bg-card px-4 py-6 text-center text-sm leading-[1.5] text-mid">{text}</p>;
}

/**
 * Above the reel cover: a pick that found no hit says so; one whose first bars are empty says where the
 * first hit is, with เริ่มช่วงที่การตีแรก, which saves the range from there and picks again at once
 * (drum-cover D9, D19). A blank strip read as a broken app.
 */
function DrumsStart({ song, picking, onRepick }: { song: Song; picking: boolean; onRepick: (range: Range) => void }) {
  if (!song.analysis) return null;
  if (song.analysis.hits.length === 0) return <Alert tone="warning">{noHitsText(song.analysis)}</Alert>;
  const late = lateStart(song);
  if (!late) return null;
  const range = late.range;
  return (
    <Alert
      tone="info"
      action={
        range && (
          <button type="button" disabled={picking} onClick={() => onRepick(range)} className={`h-11 px-4 sm:h-9 ${SECONDARY_BUTTON}`}>
            เริ่มช่วงที่การตีแรก
          </button>
        )
      }
    >
      {lateStartText(late)}
    </Alert>
  );
}
