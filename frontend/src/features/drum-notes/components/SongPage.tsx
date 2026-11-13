import { useId, useRef, useState, type RefObject } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { FixCommand } from "../../../components/ui/FixCommand";
import { inputClass } from "../../../components/ui/inputStyles";
import { Labeled } from "../../../components/ui/Labeled";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { formatDuration } from "../../../lib/format";
import { usePick, type Refused } from "../hooks/usePick";
import { useSong } from "../hooks/useSong";
import {
  audioUrl,
  bpmOf,
  MELODY_HINT,
  MODE_LABELS,
  pickingOf,
  pickText,
  RANGE_MAX_S,
  RANGE_RULE,
  rangeFault,
  seconds,
  SONGS_HASH,
  SOURCE_LABELS,
  type FoundBar,
  type Mode,
  type PickJob,
  type Range,
  type Song,
} from "../lib/songs";

/**
 * หน้าเพลง (`#/songs/{id}`): the song's head and player, the range and mode, the Pick job, and the
 * bars found (spec › Design, D5, D6, D18, D20). The lesson comes with ticket 03; the design is
 * pending, so the app's own parts.
 */
export function SongPage({ id, notice }: { id: string; notice: string | null }) {
  const { state, reload, replace } = useSong(id);
  const player = useRef<HTMLAudioElement>(null);
  const pick = usePick(replace, (job) => {
    if (job.song_id === id && job.state === "done") void reload();
  });

  return (
    <PageLayout tab="songs">
      <div className="flex items-center gap-2">
        <a href={SONGS_HASH} className={`h-11 px-3 sm:h-8 ${GHOST_BUTTON}`}>
          <img src={arrowLeftIcon} alt="" width={16} height={16} />
          กลับ
        </a>
        {state.kind === "ready" && <h2 className="min-w-0 flex-1 truncate text-xl leading-[1.5] font-semibold text-foreground">{state.song.title}</h2>}
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
              song={state.song}
              range={state.song.range}
              job={pick.job}
              refused={pick.refused}
              player={player}
              onStart={(range) => void pick.start(id, range)}
              onCancel={() => void pick.cancel()}
            />
          )}
          {state.song.analysis ? (
            <FoundBars bars={state.song.bars} onPick={(start) => seek(player.current, start)} />
          ) : (
            <p className="rounded-2xl border border-border bg-card px-4 py-6 text-center text-sm leading-[1.5] text-mid">ตั้งช่วงแล้วกด แกะโน้ต</p>
          )}
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
  const running = job !== null && (job.state === "preparing" || job.state === "picking");
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
    <section aria-label="ช่วงแกะ" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
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
              // ทำนอง opens with ticket 04 (D14): shown, not yet pressable.
              disabled={running || option === "melody"}
              onClick={() => setMode(option)}
              className={`h-10 rounded-lg border px-4 font-button text-sm font-medium ${mode === option ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card text-mid hover:bg-muted"} disabled:opacity-60`}
            >
              {MODE_LABELS[option]}
            </button>
          ))}
        </div>
        <p className="text-xs leading-4 text-muted-foreground">{MELODY_HINT} (เร็ว ๆ นี้)</p>
      </div>
      {picking ? (
        <div role="group" aria-label="งานแกะโน้ต" className="flex flex-col gap-2 rounded-xl bg-muted px-4 py-3">
          <div className="flex items-center gap-3">
            <p className="min-w-0 flex-1 text-sm font-medium text-foreground">{pickText(picking)}</p>
            <button type="button" disabled={picking.cancel_requested} onClick={onCancel} className={`h-8 px-3 ${GHOST_BUTTON}`}>
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
      {refused && !refused.field && <RefusedAlert text={refused.text} fixes={refused.fixes} />}
      {failed && !refused && <FailedAlert job={failed} />}
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
        <button type="button" disabled={disabled} onClick={onUseCurrent} aria-label={`ใช้เวลาที่เล่นอยู่เป็น${label}`} className={`h-10 shrink-0 px-3 ${GHOST_BUTTON} border border-border`}>
          ใช้เวลาที่เล่นอยู่
        </button>
      </div>
    </Labeled>
  );
}

/** A start the API refused: `busy` and `not_ready` as a warning with its fixes, anything else as an error. */
function RefusedAlert({ text, fixes }: { text: string; fixes: string[] }) {
  return (
    <Alert tone={fixes.length > 0 ? "warning" : "error"}>
      <div className="flex flex-col gap-2">
        <p>{text}</p>
        {fixes.map((fix) => (
          <FixCommand key={fix} command={fix} />
        ))}
      </div>
    </Alert>
  );
}

/** A job that failed: `no_beats`, `model_failed`, `internal` by their message; `model_broken` with the Setup script to run (D20). */
function FailedAlert({ job }: { job: PickJob }) {
  return (
    <Alert tone="error">
      <div className="flex flex-col gap-2">
        <p>{job.message}</p>
        {job.fix && <FixCommand command={job.fix} />}
      </div>
    </Alert>
  );
}

/** The BPM and the bars found, in time order; a bar without four beats is dimmed and can't be picked (D6, D20). */
function FoundBars({ bars, onPick }: { bars: FoundBar[]; onPick: (start_s: number) => void }) {
  const bpm = bpmOf(bars);
  return (
    <section aria-label="ผลแกะ" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <p className="text-sm leading-[1.5] font-medium text-foreground">BPM ที่พบ {bpm ?? "—"}</p>
      <ol aria-label="ห้องที่พบ" className="flex flex-wrap gap-2">
        {bars.map((bar) => (
          <li key={bar.n}>
            <button
              type="button"
              disabled={!bar.four_four}
              title={bar.four_four ? undefined : "ห้องนี้ไม่ใช่ 4/4"}
              onClick={() => onPick(bar.start_s)}
              aria-label={`ห้อง ${bar.n}`}
              className={`flex flex-col items-start rounded-lg border border-border px-3 py-2 text-left leading-[1.5] ${
                bar.four_four ? "bg-card hover:bg-muted" : "bg-muted text-muted-foreground opacity-50"
              }`}
            >
              <span className="font-button text-sm font-medium">ห้อง {bar.n}</span>
              <span className="font-mono text-xs">{seconds(bar.start_s)}</span>
              <span className="text-xs">{bar.hits} การตี</span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}

/** The player to the start of a bar (D20); nothing to do for a song with no player. */
function seek(player: HTMLAudioElement | null, start_s: number) {
  if (player) player.currentTime = start_s;
}
