import { useRef, type RefObject } from "react";
import { Alert } from "../../../components/ui/Alert";
import { GHOST_BUTTON } from "../../../components/ui/buttonStyles";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import arrowLeftIcon from "../../../components/ui/assets/arrow-left.svg";
import { formatDuration } from "../../../lib/format";
import { useSong } from "../hooks/useSong";
import { audioUrl, barsOf, bpmOf, seconds, SONGS_HASH, SOURCE_LABELS, type Analysis, type Song } from "../lib/songs";

/**
 * หน้าเพลง (`#/songs/{id}`): the song's head, its player, and the bars found (spec › Design). The
 * range, the Pick job and the lesson come with their tickets. The design is pending, so the app's own parts.
 */
export function SongPage({ id, notice }: { id: string; notice: string | null }) {
  const { state } = useSong(id);
  const player = useRef<HTMLAudioElement>(null);

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
          {state.song.analysis ? (
            <FoundBars analysis={state.song.analysis} onPick={(start) => seek(player.current, start)} />
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

/** The BPM and the bars found, in time order; a bar without four beats is dimmed and can't be picked (D6, D20). */
function FoundBars({ analysis, onPick }: { analysis: Analysis; onPick: (start_s: number) => void }) {
  const bars = barsOf(analysis);
  const bpm = bpmOf(bars);
  return (
    <section aria-label="ผลแกะ" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 sm:p-6">
      <p className="text-sm leading-[1.5] font-medium text-foreground">BPM ที่พบ {bpm ?? "—"}</p>
      <ol aria-label="ห้องที่พบ" className="flex flex-wrap gap-2">
        {bars.map((bar) => (
          <li key={bar.n}>
            <button
              type="button"
              disabled={!bar.fourFour}
              onClick={() => onPick(bar.start_s)}
              aria-label={`ห้อง ${bar.n}`}
              className={`flex flex-col items-start rounded-lg border border-border px-3 py-2 text-left leading-[1.5] ${
                bar.fourFour ? "bg-card hover:bg-muted" : "bg-muted text-muted-foreground opacity-50"
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
