import { useEffect, useId, useRef, useState } from "react";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { CLIPS_PATH } from "../../../lib/clips";
import { formatClock } from "../../../lib/format";
import checkLinkIcon from "../assets/check-link.svg";
import checkWhiteIcon from "../assets/check-white.svg";
import chevronDownIcon from "../assets/chevron-down.svg";
import xIcon from "../assets/x.svg";
import { episodeOf, shotImageUrl, type Sentence, type Shot, type ShotRef } from "../lib/draft";

type Props = {
  sentence: Sentence;
  number: number;
  /** Which of the sentence's two Shots this picks. */
  slot: number;
  clipIds: string[];
  shots: Record<string, Shot[]>;
  onPick: (shot: ShotRef) => void;
  onClose: () => void;
};

/**
 * Figma `Shot picker`: the Shots within ±30 s of the cited lines, or every Shot of one
 * episode with ดูทั้งคลิป; a sentence citing no line opens on the whole first episode
 * (spoil-maker D26, D27). Pointing at a Shot shows its description and plays its stretch;
 * clicking it picks it and closes. Esc closes; focus starts on the close button.
 */
export function ShotPicker({ sentence, number, slot, clipIds, shots, onPick, onClose }: Props) {
  /** ±30 s around the cited lines, or null for a sentence citing none (D26). */
  const near = sentence.window;
  const [whole, setWhole] = useState(near === null);
  const [clipId, setClipId] = useState(near?.clip_id ?? clipIds[0]);
  const current = sentence.shots[slot];
  const listed = (shots[clipId] ?? []).filter(
    (shot) => whole || near === null || (shot.end > near.start && shot.start < near.end),
  );
  const [shown, setShown] = useState<Shot | null>(
    (current && current.clip_id === clipId ? shots[clipId]?.[current.n] : null) ?? listed[0] ?? null,
  );
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") trapFocus(event, dialog.current);
    };
    document.addEventListener("keydown", keydown);
    return () => document.removeEventListener("keydown", keydown);
  }, [onClose]);

  const firstCited = sentence.ref_lines.find((line) => line.clip_id === near?.clip_id);
  const info = whole
    ? `ทุก Shot ของ ${episodeOf(clipIds, clipId)} · ${listed.length} Shot`
    : `Shot ภายใน ±30 วินาทีจาก ${episodeOf(clipIds, clipId)} ${formatClock(firstCited?.start ?? 0)} · ${listed.length} Shot`;

  return (
    <div className="fixed inset-0 z-10 flex items-start justify-center overflow-y-auto bg-surface-inverse/50 sm:items-center sm:p-8">
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex w-full flex-col gap-3 bg-card px-4 pt-3 pb-4 sm:max-w-[886px] sm:gap-5 sm:rounded-3xl sm:border sm:border-border sm:px-6 sm:pt-5 sm:pb-6 sm:shadow-[0_16px_48px_0_rgba(0,0,0,0.18)]"
      >
        <div className="flex h-11 items-center gap-2">
          <h3 id={titleId} className="min-w-0 flex-1 text-lg font-semibold text-foreground">
            เลือกภาพให้ประโยค {number}
          </h3>
          <button type="button" autoFocus onClick={onClose} aria-label="ปิด" className="flex size-11 items-center justify-center rounded-lg hover:bg-muted">
            <img src={xIcon} alt="" width={16} height={16} />
          </button>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-6">
          <ShotPlayer clipId={clipId} shot={shown} episode={episodeOf(clipIds, clipId)} />
          <div className="flex min-w-0 flex-1 flex-col gap-3">
            <div className="flex flex-col gap-2">
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  aria-pressed={whole}
                  // A sentence citing no line has no ±30 s to go back to (D26, D27).
                  disabled={near === null}
                  onClick={() => {
                    setWhole(!whole);
                    if (whole && near) setClipId(near.clip_id);
                  }}
                  className={`h-11 px-6 ${OUTLINE_BUTTON} ${whole ? "border-brand-accent bg-accent-subtle text-link hover:bg-accent-subtle" : ""} disabled:opacity-100`}
                >
                  {whole && <img src={checkLinkIcon} alt="" width={16} height={16} />}
                  ดูทั้งคลิป
                </button>
                {whole && (
                  <label className="flex min-w-0 flex-1 flex-col gap-2">
                    <span className="text-sm leading-5 font-medium text-foreground">ตอน</span>
                    <span className="relative">
                      <select
                        value={clipId}
                        onChange={(event) => setClipId(event.target.value)}
                        className="h-10 w-full appearance-none rounded-lg border border-border bg-card px-3 pr-9 font-button text-sm leading-5 text-foreground"
                      >
                        {clipIds.map((id) => (
                          <option key={id} value={id}>
                            {episodeOf(clipIds, id)}
                          </option>
                        ))}
                      </select>
                      <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute top-3 right-3" />
                    </span>
                  </label>
                )}
              </div>
              <p className="text-[13px] text-mid">{info}</p>
            </div>
            <ul aria-label="Shot" className="grid h-[330px] grid-cols-3 content-start gap-x-2 gap-y-3 overflow-y-auto p-[3px] sm:grid-cols-4">
              {listed.map((shot) => (
                <PickThumb
                  key={shot.n}
                  clipId={clipId}
                  shot={shot}
                  current={current?.clip_id === clipId && current.n === shot.n}
                  onShow={() => setShown(shot)}
                  onPick={() => onPick({ clip_id: clipId, n: shot.n })}
                />
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

type ThumbProps = { clipId: string; shot: Shot; current: boolean; onShow: () => void; onPick: () => void };

/** Figma component `Pick thumb`: hover or focus shows the Shot's description (`Shot tooltip`) and plays it. */
function PickThumb({ clipId, shot, current, onShow, onPick }: ThumbProps) {
  const [pointed, setPointed] = useState(false);
  const tipId = useId();
  const point = () => {
    setPointed(true);
    onShow();
  };
  return (
    <li className="relative">
      <button
        type="button"
        onClick={onPick}
        onMouseEnter={point}
        onFocus={point}
        onMouseLeave={() => setPointed(false)}
        onBlur={() => setPointed(false)}
        aria-describedby={pointed ? tipId : undefined}
        aria-label={`Shot ${formatClock(shot.start)}`}
        className="group flex w-full flex-col gap-1 text-left"
      >
        <span
          className={`relative aspect-[16/9] w-full overflow-hidden rounded-lg bg-surface-inverse ${
            current ? "border-3 border-brand-accent" : "group-hover:border-2 group-hover:border-brand-accent group-focus-visible:border-2 group-focus-visible:border-brand-accent"
          }`}
        >
          <img src={shotImageUrl(clipId, shot.n)} alt="" loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
          {current && (
            <span className="absolute top-0.5 left-0.5 flex rounded-full bg-brand-accent p-[3px]" title="ใช้อยู่">
              <img src={checkWhiteIcon} alt="ใช้อยู่" width={12} height={12} />
            </span>
          )}
        </span>
        <span className={`font-mono text-[11px] ${current ? "text-link" : "text-mid"}`}>{formatClock(shot.start)}</span>
      </button>
      {pointed && (
        <span
          id={tipId}
          role="tooltip"
          className="absolute top-full left-0 z-10 mt-2 w-[220px] rounded-lg bg-surface-inverse px-2.5 py-2 font-button text-xs leading-[18px] text-card"
        >
          {shot.description}
        </span>
      )}
    </li>
  );
}

/** Figma component `Shot player`: the clip's own video, playing only the Shot's stretch (spec › Frontend). */
function ShotPlayer({ clipId, shot, episode }: { clipId: string; shot: Shot | null; episode: string }) {
  const video = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (video.current && shot) video.current.currentTime = shot.start;
  }, [shot]);

  return (
    <div className="flex flex-col gap-2 sm:w-[400px] sm:shrink-0">
      <video
        ref={video}
        src={`${CLIPS_PATH}/${clipId}/video`}
        controls
        preload="metadata"
        onTimeUpdate={(event) => {
          if (shot && event.currentTarget.currentTime >= shot.end) event.currentTarget.pause();
        }}
        className="aspect-video w-full rounded-xl bg-surface-inverse"
      />
      <p className="font-mono text-xs text-mid">
        {shot ? `${episode} · ${formatClock(shot.start)} – ${formatClock(shot.end)}` : episode}
      </p>
    </div>
  );
}

/** Keeps Tab inside the dialog (Figma `Picker header`: focus is trapped while it is open). */
function trapFocus(event: KeyboardEvent, dialog: HTMLElement | null) {
  if (!dialog) return;
  const focusable = dialog.querySelectorAll<HTMLElement>("button:not(:disabled), select, video, [tabindex]");
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
