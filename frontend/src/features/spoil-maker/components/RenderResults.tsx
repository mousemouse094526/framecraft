import { useState } from "react";
import { DESTRUCTIVE_BUTTON, GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { formatDuration } from "../../../lib/format";
import { useCopy } from "../../../lib/useCopy";
import checkIcon from "../assets/check-link.svg";
import copyIcon from "../../../components/ui/assets/copy.svg";
import downloadIcon from "../../../components/ui/assets/download.svg";
import pauseIcon from "../assets/pause-white-14.svg";
import playIcon from "../assets/play-white-14.svg";
import trashConfirmIcon from "../assets/trash-confirm.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { useIsDesktop } from "../hooks/useIsDesktop";
import { useRenders } from "../hooks/useRenders";
import { epLabel } from "../lib/draft";
import { renderFileUrl, renderTime, type RenderResult } from "../lib/render";
import { JobProgress } from "./ReviewFooter";
import { ReviewBanner } from "./ReviewBanner";

/**
 * Step 3 of the สปอย tab, ผล render (Figma `Render results`, spoil-maker D42, legal 1):
 * the running render with ยกเลิก, then every render newest first to play, download as
 * mp4 or `.srt`, delete, and copy its source line for the clip's description.
 */
export function RenderResults() {
  const { state, cancel, remove, retry } = useRenders();
  const desktop = useIsDesktop();
  const [playing, setPlaying] = useState<string | null>(null);

  if (state.kind === "offline") return <OfflinePanel />;
  if (state.kind === "loading") return <p className="flex justify-center py-6 text-sm text-muted-foreground">กำลังโหลด…</p>;

  const { renders, job, error } = state;
  const played = renders.find((r) => r.name === playing) ?? null;

  return (
    <div className="flex flex-col gap-4">
      {job && (
        <section aria-label="กำลัง render" className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 lg:flex-row lg:items-center">
          <JobProgress job={job} onCancel={() => void cancel()} />
        </section>
      )}
      {error && <ReviewBanner banner={error} onRetry={() => void retry()} />}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
        <section aria-label="ผล render" className="min-w-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card">
          <h2 className="flex items-center gap-2 px-4 py-3 leading-normal">
            <span className="text-sm font-medium text-foreground">ผล render</span>
            <span className="font-mono text-xs text-muted-foreground">{renders.length}</span>
          </h2>
          {renders.length === 0 ? (
            <p className="border-t border-border px-4 py-14 text-center text-sm text-mid">ยังไม่มีผล render</p>
          ) : (
            <ul>
              {renders.map((render) => (
                <RenderRow
                  key={render.name}
                  render={render}
                  playing={render.name === playing}
                  inlinePlayer={!desktop}
                  onPlay={() => setPlaying(render.name === playing ? null : render.name)}
                  onDelete={() => {
                    if (render.name === playing) setPlaying(null);
                    void remove(render.name);
                  }}
                />
              ))}
            </ul>
          )}
        </section>
        {desktop && played && <PlayerPanel render={played} />}
      </div>
    </div>
  );
}

type RowProps = {
  render: RenderResult;
  playing: boolean;
  /** A phone plays under the row, a desktop in the panel beside the list (Figma `Render row`). */
  inlinePlayer: boolean;
  onPlay: () => void;
  onDelete: () => void;
};

/** Figma component `Render row`: default, playing and delete confirm. */
function RenderRow({ render, playing, inlinePlayer, onPlay, onDelete }: RowProps) {
  const [confirming, setConfirming] = useState(false);
  const time = renderTime(render.created_at);
  const credit = `ต้นฉบับ: ${render.sources.join(", ")}`;
  const { copied, copy } = useCopy(credit);
  const mp4 = renderFileUrl(render.name, ".mp4");

  return (
    <li
      aria-label={`render ${time}`}
      className={`flex flex-col gap-3 border-t border-border px-4 py-3 ${playing ? "bg-muted" : "bg-card"}`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-4">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <button
            type="button"
            aria-label={playing ? "หยุด" : "เล่น"}
            onClick={onPlay}
            className={`relative h-24 w-[54px] shrink-0 overflow-hidden rounded-lg bg-surface-inverse ${playing ? "border-2 border-brand-accent" : ""}`}
          >
            {/* The first frame stands for the render; no picture is kept apart from the mp4. */}
            <video src={`${mp4}#t=0.5`} preload="metadata" muted className="absolute inset-0 h-full w-full object-cover" />
            <span className="absolute inset-0 bg-black/25" />
            <span className="absolute top-1/2 left-1/2 flex size-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/60">
              <img src={playing ? pauseIcon : playIcon} alt="" width={14} height={14} />
            </span>
          </button>
          <div className="flex min-w-0 flex-1 flex-col gap-0.5 leading-normal">
            <p className="flex items-center gap-2">
              <span className="text-[15px] font-medium text-foreground">{time}</span>
              {render.ep !== null && (
                <span className="rounded-full bg-muted px-2 py-0.5 font-button text-xs leading-4 font-medium text-mid">
                  {epLabel(render.ep)}
                </span>
              )}
              {playing && <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">กำลังเล่น</span>}
            </p>
            <p className="font-mono text-xs text-muted-foreground">ความยาว {formatDuration(Math.round(render.duration_s))}</p>
            <p className="flex items-center gap-0.5">
              <span className="min-w-0 text-[13px] text-mid lg:max-w-[420px] lg:truncate">{credit}</span>
              <button
                type="button"
                aria-label={copied ? "copy แล้ว" : "copy ชื่อต้นฉบับ"}
                onClick={() => void copy()}
                className={`size-11 ${GHOST_BUTTON}`}
              >
                <img src={copied ? checkIcon : copyIcon} alt="" width={16} height={16} />
              </button>
            </p>
            {render.sound_name !== null && <p className="text-[13px] text-mid">เสียงพื้น: {render.sound_name}</p>}
          </div>
        </div>
        {playing && inlinePlayer && <Player render={render} className="aspect-[9/16] w-full" />}
        <div className="flex items-center gap-2">
          <a href={mp4} download className={`h-11 flex-1 px-4 lg:flex-none ${OUTLINE_BUTTON}`}>
            <img src={downloadIcon} alt="" width={16} height={16} />
            mp4
          </a>
          <a href={renderFileUrl(render.name, ".srt")} download className={`h-11 flex-1 px-4 lg:flex-none ${OUTLINE_BUTTON}`}>
            <img src={downloadIcon} alt="" width={16} height={16} />
            .srt
          </a>
          <button
            type="button"
            aria-label={`ลบ render ${time}`}
            onClick={() => setConfirming(true)}
            className={`size-11 ${GHOST_BUTTON} ${confirming ? "bg-muted" : ""}`}
          >
            <img src={confirming ? trashConfirmIcon : trashIcon} alt="" width={16} height={16} />
          </button>
        </div>
      </div>
      {confirming && (
        <div className="flex flex-col gap-3 rounded-lg bg-muted p-3">
          <div className="flex flex-col gap-0.5 leading-normal">
            <p className="text-sm font-medium text-foreground">ลบผล render “{time}”?</p>
            <p className="text-[13px] text-mid">ลบทั้ง mp4 และ .srt แล้วกู้คืนไม่ได้</p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              autoFocus
              onClick={() => {
                setConfirming(false);
                onDelete();
              }}
              className={`h-11 flex-1 px-4 lg:flex-none ${DESTRUCTIVE_BUTTON}`}
            >
              ลบ
            </button>
            <button type="button" onClick={() => setConfirming(false)} className={`h-11 flex-1 px-4 lg:flex-none ${OUTLINE_BUTTON}`}>
              ยกเลิก
            </button>
          </div>
        </div>
      )}
    </li>
  );
}

/** Figma `Player panel`: the render being played, 9:16, beside the list on a desktop. */
function PlayerPanel({ render }: { render: RenderResult }) {
  return (
    <section aria-label="เล่น render" className="flex shrink-0 flex-col gap-3 rounded-2xl border border-border bg-card p-4 lg:sticky lg:top-4">
      <Player render={render} className="h-[576px] w-[324px]" />
      <div className="flex flex-col gap-0.5 leading-normal">
        <p className="text-sm font-medium text-foreground">{renderTime(render.created_at)}</p>
        <p className="font-mono text-xs text-muted-foreground">1080×1920 · {formatDuration(Math.round(render.duration_s))}</p>
      </div>
    </section>
  );
}

/** Figma `Vertical player`: the browser's own controls over the 1080×1920 mp4. */
function Player({ render, className }: { render: RenderResult; className: string }) {
  return (
    <video
      key={render.name}
      src={renderFileUrl(render.name, ".mp4")}
      controls
      autoPlay
      playsInline
      aria-label={`render ${renderTime(render.created_at)}`}
      className={`rounded-[19px] bg-surface-inverse object-contain ${className}`}
    />
  );
}
