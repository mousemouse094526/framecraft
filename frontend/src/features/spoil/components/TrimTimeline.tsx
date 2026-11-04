import { useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import type { Range } from "../../../lib/clips";
import { formatAxisTime, formatTime, handleBounds, SIDE_WORDS, toTenth, type Side } from "../lib/trim";

/** A valid range on the timeline, with its number in the list ("ช่วง {n}"). */
export type TimelineRange = { n: number; range: Range };

type Props = {
  /** The clip's length in seconds: the timeline's whole width. */
  length: number;
  ranges: TimelineRange[];
  playhead: number;
  /** A click on the track moves the player there. */
  onSeek: (seconds: number) => void;
  /** A handle moved: `seconds` is already kept inside its bounds and rounded to 0.1 s. */
  onMove: (n: number, side: Side, seconds: number) => void;
};

const percentOf = (seconds: number, length: number) => `${(seconds / length) * 100}%`;

/**
 * Figma component `Trim timeline`: the ranges as accent bars with a handle at each end, and
 * the playhead (D38, D44). Handles are sliders: dragged with a pointer or moved with the arrow
 * keys (1 s, 10 s with Shift), never past the other end of their range or a neighbour.
 */
export function TrimTimeline({ length, ranges, playhead, onSeek, onMove }: Props) {
  const track = useRef<HTMLDivElement>(null);

  /** The time under a pointer's x on the track. */
  const timeAt = (clientX: number) => {
    const box = track.current!.getBoundingClientRect();
    return box.width > 0 ? ((clientX - box.left) / box.width) * length : 0;
  };

  const seek = (event: PointerEvent<HTMLDivElement>) => {
    // Only the track and the bars seek; a handle takes its own pointer.
    if ((event.target as HTMLElement).closest("[role=slider]")) return;
    onSeek(toTenth(Math.min(Math.max(timeAt(event.clientX), 0), length)));
  };

  return (
    <div className="flex w-full flex-col gap-0.5">
      <div ref={track} onPointerDown={seek} className="relative h-11 w-full touch-none">
        <div className="absolute inset-x-0 top-[18px] h-2 rounded-full border border-border bg-muted" />
        {ranges.map(({ n, range }) => (
          <div
            key={n}
            className="absolute top-[14px] h-4 rounded border border-brand-accent bg-accent-subtle"
            style={{ left: percentOf(range.start_s, length), width: percentOf(range.end_s - range.start_s, length) }}
          />
        ))}
        <div
          className="pointer-events-none absolute top-1 h-9 w-0.5 -translate-x-1/2 rounded-[1px] bg-foreground"
          style={{ left: percentOf(Math.min(playhead, length), length) }}
        />
        {ranges.flatMap(({ n, range }) =>
          (["start", "end"] as const).map((side) => {
            const others = ranges.filter((other) => other.n !== n).map((other) => other.range);
            const [low, high] = handleBounds(range, side, others, length);
            return (
              <Handle
                key={`${n}-${side}`}
                label={`${SIDE_WORDS[side].handle}ช่วง ${n}`}
                value={side === "start" ? range.start_s : range.end_s}
                low={low}
                high={high}
                length={length}
                timeAt={timeAt}
                onMove={(seconds) => onMove(n, side, seconds)}
              />
            );
          }),
        )}
      </div>
      <div className="flex justify-between font-mono text-xs leading-[1.5] whitespace-nowrap text-muted-foreground">
        <span>{formatAxisTime(0)}</span>
        <span>{formatAxisTime(length)}</span>
      </div>
    </div>
  );
}

type HandleProps = {
  label: string;
  value: number;
  low: number;
  high: number;
  length: number;
  timeAt: (clientX: number) => number;
  onMove: (seconds: number) => void;
};

/** One end of a range: a 44px target around a 10×26 grip; dragging shows the time above it (Figma states). */
function Handle({ label, value, low, high, length, timeAt, onMove }: HandleProps) {
  const [dragging, setDragging] = useState(false);
  const moveTo = (seconds: number) => onMove(toTenth(Math.min(Math.max(seconds, low), high)));

  const keyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const step = event.shiftKey ? 10 : 1;
    if (event.key === "ArrowRight" || event.key === "ArrowUp") moveTo(value + step);
    else if (event.key === "ArrowLeft" || event.key === "ArrowDown") moveTo(value - step);
    else return;
    event.preventDefault();
  };

  return (
    <div
      role="slider"
      tabIndex={0}
      aria-label={label}
      aria-valuemin={low}
      aria-valuemax={high}
      aria-valuenow={value}
      aria-valuetext={formatTime(value)}
      onKeyDown={keyDown}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        setDragging(true);
      }}
      onPointerMove={(event) => dragging && moveTo(timeAt(event.clientX))}
      onPointerUp={() => setDragging(false)}
      onPointerCancel={() => setDragging(false)}
      className="group absolute top-0 h-11 w-11 -translate-x-1/2 cursor-ew-resize outline-none"
      style={{ left: percentOf(value, length) }}
    >
      <span className="absolute top-[9px] left-[17px] h-[26px] w-2.5 rounded-full border-2 border-card bg-brand-accent group-focus-visible:outline-2 group-focus-visible:outline-offset-2 group-focus-visible:outline-brand-accent" />
      {dragging && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 rounded-md bg-surface-inverse px-2 py-1 font-mono text-xs leading-[1.5] whitespace-nowrap text-card">
          {formatTime(value)}
        </span>
      )}
    </div>
  );
}
