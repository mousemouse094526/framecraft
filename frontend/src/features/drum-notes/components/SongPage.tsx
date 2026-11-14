import { useId, useRef, useState, type RefObject } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON, PRIMARY_BUTTON, SECONDARY_BUTTON } from "../../../components/ui/buttonStyles";
import { FixCommand } from "../../../components/ui/FixCommand";
import { GrooveGrid } from "../../../components/ui/GrooveGrid";
import { inputClass } from "../../../components/ui/inputStyles";
import { Labeled } from "../../../components/ui/Labeled";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { ProgressBar } from "../../../components/ui/ProgressBar";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import xIcon from "../../../components/ui/assets/x.svg";
import { formatDuration } from "../../../lib/format";
import { BAR_COUNTS, BPM_MAX, BPM_MIN, lessonHash } from "../../../lib/lesson";
import { useLessonPreview } from "../hooks/useLessonPreview";
import { usePick, type Refused } from "../hooks/usePick";
import { useSong } from "../hooks/useSong";
import {
  audioUrl,
  BPM_RULE,
  droppedText,
  firstPickable,
  MELODY_BASE,
  MELODY_HINT,
  MODE_LABELS,
  NO_FOUR_FOUR,
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
 * หน้าเพลง (`#/songs/{id}`): the song's head and player, the range and mode, the Pick job, the bars
 * found with the lesson made of the ones picked, and the lessons made before (spec › Design, D5, D6,
 * D11, D12, D18, D20, D21). The design is pending, so the app's own parts.
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
            // Keyed by `picked_at`, so a new analysis starts the lesson's pick over at its first 4/4 bar.
            <FoundSection key={state.song.analysis.picked_at} song={state.song} mode={state.song.analysis.mode} player={player} />
          ) : (
            <EmptyNote text="ตั้งช่วงแล้วกด แกะโน้ต" />
          )}
          <MadeLessons ids={state.song.lessons} />
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
              disabled={running}
              onClick={() => setMode(option)}
              className={`h-10 rounded-lg border px-4 font-button text-sm font-medium ${mode === option ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card text-mid hover:bg-muted"} disabled:opacity-60`}
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

type FoundSectionProps = { song: Song; mode: Mode; player: RefObject<HTMLAudioElement | null> };

/** The bars found in the analysis's `mode` and, when one is 4/4, the lesson made of the ones picked (spec › Design, D11, D14, D20). */
function FoundSection({ song, mode, player }: FoundSectionProps) {
  if (firstPickable(song.bars) < 0) {
    return (
      <>
        <FoundBars bars={song.bars} mode={mode} selected={null} onPick={(_, start) => seek(player.current, start)} />
        <EmptyNote text={NO_FOUR_FOUR} />
      </>
    );
  }
  return <LessonPick song={song} mode={mode} player={player} />;
}

/** A card that says why a section has nothing to show. */
function EmptyNote({ text }: { text: string }) {
  return <p className="rounded-2xl border border-border bg-card px-4 py-6 text-center text-sm leading-[1.5] text-mid">{text}</p>;
}

/** The strip and สร้างบทเรียน of a song with a 4/4 bar: pressing a bar seeks the player and makes it the lesson's first (D20). */
function LessonPick({ song, mode, player }: { song: Song; mode: Mode; player: RefObject<HTMLAudioElement | null> }) {
  const lesson = useLessonPreview(song.id, song.bars);
  return (
    <>
      <FoundBars
        bars={song.bars}
        mode={mode}
        selected={lesson.bar}
        onPick={(index, start) => {
          seek(player.current, start);
          lesson.pickBar(index);
        }}
      />
      <LessonSection lesson={lesson} mode={mode} />
    </>
  );
}

type FoundBarsProps = { bars: FoundBar[]; mode: Mode; selected: number | null; onPick: (index: number, start_s: number) => void };

/** The bars found, in time order, under the mode they were picked in; the lesson's first bar is pressed; a bar without four beats is dimmed and can't be picked (D6, D14, D20). */
function FoundBars({ bars, mode, selected, onPick }: FoundBarsProps) {
  return (
    <section aria-label="ผลแกะ" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <p className="text-sm leading-[1.5] font-medium text-foreground">
        ห้องที่พบ {bars.length} ห้อง · โหมด{MODE_LABELS[mode]} · กดห้องเพื่อฟังและเลือกเป็นห้องแรกของบทเรียน
      </p>
      <ol aria-label="ห้องที่พบ" className="flex flex-wrap gap-2">
        {bars.map((bar, index) => (
          <li key={bar.n}>
            <button
              type="button"
              disabled={!bar.four_four}
              aria-pressed={index === selected}
              title={bar.four_four ? undefined : "ห้องนี้ไม่ใช่ 4/4"}
              onClick={() => onPick(index, bar.start_s)}
              aria-label={`ห้อง ${bar.n}`}
              className={`flex flex-col items-start rounded-lg border px-3 py-2 text-left leading-[1.5] ${
                !bar.four_four ? "border-border bg-muted text-muted-foreground opacity-50" : index === selected ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card hover:bg-muted"
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

/**
 * สร้างบทเรียน: the first bar (from the strip), how many, the BPM, the read-only grid of the preview
 * with its sticks and the notes dropped (in melody mode, which notes the app added), ฟัง, and
 * สร้างบทเรียนกลอง (spec › Design, D11, D13, D14, D20, D21).
 */
function LessonSection({ lesson, mode }: { lesson: ReturnType<typeof useLessonPreview>; mode: Mode }) {
  const id = useId();
  const { preview, creating, listen } = lesson;
  const mixing = listen.state.kind === "mixing";
  const bpmError = lesson.bpmFault ? BPM_RULE : preview.kind === "refused" && preview.field === "bpm" ? preview.text : undefined;
  const ready = preview.kind === "ready" && !lesson.bpmFault;
  return (
    <section aria-label="สร้างบทเรียน" className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <h3 className="text-base leading-[1.5] font-semibold text-foreground">สร้างบทเรียน</h3>
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="flex flex-col gap-2">
          <p className="font-button text-sm leading-5 font-medium text-foreground">ห้องแรก: ห้อง {lesson.bar + 1}</p>
          <p className="text-xs leading-4 text-muted-foreground">กดห้องบนแถบเพื่อเปลี่ยน</p>
        </div>
        <div className="flex flex-col gap-2">
          <p className="font-button text-sm leading-5 font-medium text-foreground">จำนวนห้อง</p>
          <div role="radiogroup" aria-label="จำนวนห้อง" className="flex gap-2">
            {BAR_COUNTS.map((count) => (
              <button
                key={count}
                type="button"
                role="radio"
                aria-checked={lesson.bars === count}
                disabled={count > lesson.pickable}
                onClick={() => lesson.setBars(count)}
                className={`h-10 w-10 rounded-lg border font-button text-sm font-medium ${lesson.bars === count ? "border-brand-accent bg-accent-subtle text-foreground" : "border-border bg-card text-mid hover:bg-muted"} disabled:opacity-40`}
              >
                {count}
              </button>
            ))}
          </div>
        </div>
        <Labeled label="BPM" htmlFor={`${id}-bpm`} error={bpmError} hint="ตั้งต้นจากความยาวห้องที่เลือก">
          <input id={`${id}-bpm`} type="number" min={BPM_MIN} max={BPM_MAX} value={lesson.bpmShown} aria-invalid={bpmError !== undefined} onChange={(e) => lesson.setBpmText(e.target.value)} className={inputClass(bpmError !== undefined)} />
        </Labeled>
      </div>
      {preview.kind === "loading" && <p className="text-sm leading-[1.5] text-mid">กำลังคำนวณโน้ต…</p>}
      {preview.kind === "refused" && preview.field !== "bpm" && <Alert tone="error">{preview.text}</Alert>}
      {preview.kind === "ready" && (
        <>
          <GrooveGrid bars={preview.groove.bars} notes={preview.groove.notes} />
          {mode === "melody" && <p className="text-[13px] leading-[1.5] text-mid">{MELODY_BASE}</p>}
          {preview.dropped.length > 0 && (
            <div className="flex flex-col gap-1">
              <p className="text-sm leading-[1.5] font-medium text-foreground">ตัดโน้ตที่มือตีไม่ได้</p>
              <ul aria-label="ตัดโน้ตที่มือตีไม่ได้" className="list-inside list-disc text-[13px] leading-[1.5] text-mid">
                {preview.dropped.map((dropped) => (
                  <li key={`${dropped.piece}:${dropped.step}`}>{droppedText(dropped)}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <button type="button" disabled={!ready || mixing || creating.kind === "creating"} onClick={() => void listen.listen()} className={`h-11 px-5 sm:h-10 ${SECONDARY_BUTTON}`}>
          {mixing ? "กำลังผสมเสียง…" : "ฟัง"}
        </button>
        <button type="button" disabled={!ready || creating.kind === "creating"} onClick={() => void lesson.create()} className={`h-11 px-6 sm:h-10 ${PRIMARY_BUTTON}`}>
          {creating.kind === "creating" ? "กำลังสร้าง…" : "สร้างบทเรียนกลอง"}
        </button>
      </div>
      {listen.state.kind === "refused" && <RefusedAlert text={listen.state.text} fixes={listen.state.fixes} />}
      {creating.kind === "refused" && <Alert tone="error">{creating.text}</Alert>}
    </section>
  );
}

/** The lessons made from this song that are still there, as links to their editors (D12, ADR 0044). */
function MadeLessons({ ids }: { ids: string[] }) {
  return (
    <section aria-label="บทเรียนจากเพลงนี้" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <h3 className="text-base leading-[1.5] font-semibold text-foreground">บทเรียนจากเพลงนี้</h3>
      {ids.length === 0 ? (
        <p className="text-sm leading-[1.5] text-mid">ยังไม่มี</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {ids.map((lessonId, index) => (
            <li key={lessonId}>
              <a href={lessonHash(lessonId)} className={`h-9 px-3 ${GHOST_BUTTON} border border-border`}>
                บทเรียน {index + 1}
                <span className="font-mono text-xs text-muted-foreground">{lessonId}</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** The player to the start of a bar (D20); nothing to do for a song with no player. */
function seek(player: HTMLAudioElement | null, start_s: number) {
  if (player) player.currentTime = start_s;
}
