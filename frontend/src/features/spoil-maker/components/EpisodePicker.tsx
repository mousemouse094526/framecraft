import { useEffect, useId, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import { formatDuration } from "../../../lib/format";
import { parseClock } from "../lib/clock";
import chevronDownIcon from "../assets/chevron-down.svg";
import radioSelectedIcon from "../assets/radio-selected.svg";
import radioIcon from "../assets/radio.svg";
import { MINUTES, type Episode, type EpisodesState } from "../hooks/useEpisodes";
import { epLabel, shotImageUrl } from "../lib/draft";

type Props = {
  clipId: string;
  state: EpisodesState;
  /** The picked EP's number, or null. */
  picked: number | null;
  disabled: boolean;
  onPick: (n: number) => void;
  onMinutes: (minutes: number) => void;
  /** All the cuts, with the one the user moved. */
  onCuts: (cuts: number[]) => void;
};

/** `h:mm:ss` of a cut (D70); a cut sits on a Shot start, which may have tenths. */
const clock = (seconds: number) => formatDuration(Math.floor(seconds));

/**
 * The picked clip cut into EPs (spoil-maker D66, D67, D69–D71): the length of an EP, each EP
 * with its number, range, thumbnail, tokens, renders and whether the Spoil draft is of it,
 * picked one at a time, and the cut between two EPs editable, saved on blur. Built from the
 * cards of `Spoiler setup` until the new design is in (Blocked 13).
 */
export function EpisodePicker({ clipId, state, picked, disabled, onPick, onMinutes, onCuts }: Props) {
  const minutesId = useId();
  if (state.kind === "none") return null;
  const cut = state.kind === "loaded" ? state.cut : null;
  const cuts = cut ? cut.episodes.slice(1).map((ep) => ep.start_s) : [];

  const changeMinutes = (minutes: number) => {
    // Cuts the user moved go with a new length (D71).
    if (cut?.custom && !window.confirm("จุดตัดที่เลื่อนเองจะหาย เปลี่ยนความยาวต่อ EP ไหม")) return;
    onMinutes(minutes);
  };

  return (
    <section aria-label="เลือก EP" className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card lg:w-[560px] lg:shrink-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3">
        <h3 className="flex flex-1 items-center gap-2 leading-[1.5] whitespace-nowrap">
          <span className="text-sm font-medium text-foreground">เลือก EP</span>
          {cut && <span className="font-mono text-[13px] text-muted-foreground">{cut.episodes.length}</span>}
        </h3>
        {cut && (
          <>
            <label htmlFor={minutesId} className="text-sm leading-5 text-mid">
              ความยาวต่อ EP
            </label>
            <span className="relative">
              <select
                id={minutesId}
                value={cut.minutes}
                disabled={disabled}
                onChange={(event) => changeMinutes(Number(event.target.value))}
                className="h-10 appearance-none rounded-lg border border-border bg-card px-3 pr-9 font-button text-sm leading-5 text-foreground"
              >
                {MINUTES.map((minutes) => (
                  <option key={minutes} value={minutes}>
                    {minutes} นาที
                  </option>
                ))}
              </select>
              <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute top-3 right-3" />
            </span>
            {cut.custom && (
              <button type="button" disabled={disabled} onClick={() => onMinutes(cut.minutes)} className={`h-10 px-3 ${OUTLINE_BUTTON}`}>
                ตัดใหม่ตามความยาว
              </button>
            )}
          </>
        )}
      </div>
      {state.kind === "loading" && <p className="border-t border-border px-4 py-6 text-center text-sm text-muted-foreground">กำลังโหลด…</p>}
      {state.kind === "offline" && (
        <p className="border-t border-border px-4 py-6 text-center text-sm text-mid">ติดต่อ backend ไม่ได้ ลองเลือกคลิปใหม่</p>
      )}
      {(state.kind === "refused" || (state.kind === "loaded" && state.error)) && (
        <div className="border-t border-border px-4 py-3">
          <Alert tone="error">{state.error}</Alert>
        </div>
      )}
      {cut && (
        <ul>
          {cut.episodes.map((ep, index) => (
            <li key={`${ep.n}-${ep.start_s}`} className="border-t border-border">
              {index > 0 && (
                <CutField
                  label={`จุดตัดระหว่าง EP ${index} กับ EP ${ep.n}`}
                  seconds={ep.start_s}
                  disabled={disabled}
                  onChange={(seconds) => onCuts(cuts.map((at, i) => (i === index - 1 ? seconds : at)))}
                />
              )}
              <EpisodeRow
                clipId={clipId}
                ep={ep}
                limit={cut.limit}
                picked={picked === ep.n}
                disabled={disabled}
                onPick={() => onPick(ep.n)}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

type RowProps = { clipId: string; ep: Episode; limit: number; picked: boolean; disabled: boolean; onPick: () => void };

/** One EP, built like `Pick clip row`: the whole row is the radio's label. */
function EpisodeRow({ clipId, ep, limit, picked, disabled, onPick }: RowProps) {
  const label = epLabel(ep.n);
  return (
    <label
      aria-label={label}
      className={`flex cursor-pointer items-center gap-3 py-2.5 pr-2 pl-4 has-disabled:cursor-default ${picked ? "bg-accent-subtle" : ""}`}
    >
      <span className="flex h-11 w-6 shrink-0 items-center justify-center">
        <input type="radio" name="episode" checked={picked} disabled={disabled} onChange={onPick} aria-label={`เลือก ${label}`} className="peer sr-only" />
        <img src={picked ? radioSelectedIcon : radioIcon} alt="" width={16} height={16} />
      </span>
      <img src={shotImageUrl(clipId, ep.thumb_shot)} alt="" className="h-[45px] w-20 shrink-0 rounded bg-surface-strong object-cover" />
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <span className="text-sm leading-[21px] font-medium text-foreground">{label}</span>
          <span className="font-mono text-xs leading-4 text-mid">
            {clock(ep.start_s)}–{clock(ep.end_s)}
          </span>
          {ep.in_draft && (
            <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">
              อยู่ใน Spoil draft
            </span>
          )}
        </span>
        <span className="flex flex-wrap gap-x-3 text-xs leading-4 text-mid">
          <span className={`font-mono ${ep.tokens !== null && ep.tokens > limit ? "text-destructive" : ""}`}>
            {ep.tokens === null ? "—" : ep.tokens.toLocaleString("en-US")} / {limit.toLocaleString("en-US")} token
          </span>
          <span>render แล้ว {ep.renders}</span>
        </span>
      </span>
    </label>
  );
}

type CutProps = { label: string; seconds: number; disabled: boolean; onChange: (seconds: number) => void };

/** The cut between two EPs as `h:mm:ss`, saved on blur when it changed (D70); the backend moves it to a Shot start. */
function CutField({ label, seconds, disabled, onChange }: CutProps) {
  const [text, setText] = useState(clock(seconds));
  const [wrong, setWrong] = useState(false);
  const id = useId();
  // A new cut from the backend (moved to a Shot, or cut again) shows as it is.
  useEffect(() => {
    setText(clock(seconds));
    setWrong(false);
  }, [seconds]);

  const save = () => {
    const typed = parseClock(text);
    if (typed === null) {
      setWrong(true);
      return;
    }
    setWrong(false);
    if (typed !== Math.floor(seconds)) onChange(typed);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 bg-muted px-4 py-1.5">
      <label htmlFor={id} className="text-[13px] leading-5 text-mid">
        {label}
      </label>
      <input
        id={id}
        value={text}
        disabled={disabled}
        inputMode="numeric"
        onChange={(event) => setText(event.target.value)}
        onBlur={save}
        aria-invalid={wrong}
        className="h-11 w-28 rounded-lg border border-border bg-card px-3 font-mono text-sm text-foreground sm:h-8"
      />
      {wrong && <span className="text-[13px] text-destructive">ใส่เวลาแบบ ชม:นาที:วินาที</span>}
    </div>
  );
}
