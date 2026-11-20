import { clockOf } from "../../lib/format";
import { useSound, type PlayStatus } from "../../lib/player";
import loaderIcon from "./assets/loader.svg";
import pauseIcon from "./assets/pause-16.svg";
import playIcon from "./assets/play-16.svg";

type Props = {
  /** What plays, for its name: "ลมพัด" → "ฟัง ลมพัด" / "หยุดชั่วคราว ลมพัด" (audio-player D4). */
  label: string;
  /** A word shown beside the icon, which then is its name: "ฟังจังหวะ" (D3). */
  text?: string;
  status: PlayStatus;
  /** Seconds played, shown while playing or paused (D5). */
  position?: number;
  /** Seconds in all, or null until the file says: then the time played alone. */
  duration?: number | null;
  onPress: () => void;
  disabled?: boolean;
  title?: string;
  /** The look of the place it sits in: a `buttonStyles` look with its height and padding. */
  className: string;
};

/**
 * The one play/pause button of every sound in the app (audio-player D3, D4, ADR 0073): play when
 * ready or paused, pause while playing, with the time played "0:03 / 0:12" (D5); a mixed preview
 * says กำลังผสมเสียง… until its wav plays (D7).
 */
export function PlayButton({ label, text, status, position = 0, duration = null, onPress, disabled = false, title, className }: Props) {
  const mixing = status === "mixing";
  const playing = status === "playing";
  const name = mixing ? "กำลังผสมเสียง…" : playing ? `หยุดชั่วคราว ${text ?? label}` : (text ?? `ฟัง ${label}`);
  return (
    <button
      type="button"
      aria-label={name}
      // Mixing keeps the focus on the button just pressed: it says so, and a press does nothing (D15).
      disabled={disabled}
      aria-disabled={mixing || undefined}
      title={title}
      onClick={mixing ? undefined : onPress}
      className={`${className} focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-accent`}
    >
      {mixing ? (
        <>
          <img src={loaderIcon} alt="" width={16} height={16} className="motion-safe:animate-spin" />
          กำลังผสมเสียง…
        </>
      ) : (
        <>
          <img src={playing ? pauseIcon : playIcon} alt="" width={16} height={16} />
          {text}
          {/* The name says what a press does; the time changes every second, so it isn't read out. */}
          {(playing || status === "paused") && (
            <span aria-hidden className="font-mono text-xs leading-4 font-medium text-mid tabular-nums">
              {clockOf(position)}
              {duration !== null && ` / ${clockOf(duration)}`}
            </span>
          )}
        </>
      )}
    </button>
  );
}

/** A `PlayButton` of a file the API serves: the voice, sentence, card and library sounds (audio-player D3).
 * `src` null: nothing to play yet. */
export function SoundButton({ src, ...props }: Omit<Props, "status" | "onPress"> & { src: string | null }) {
  const sound = useSound(src, props.disabled);
  return <PlayButton {...props} status={sound.status} position={sound.position} duration={sound.duration} onPress={sound.toggle} />;
}
