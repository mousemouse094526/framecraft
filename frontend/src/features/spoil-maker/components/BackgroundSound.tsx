import { useId, useRef, useState } from "react";
import { Alert } from "../../../components/ui/Alert";
import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import musicIcon from "../../../components/ui/assets/music.svg";
import playIcon from "../../../components/ui/assets/play-16.svg";
import { playAudio } from "../../../lib/audio";
import { soundFilePath, soundsHash, type PlayedSound, type Sound } from "../../sound-library/lib/sounds";
import type { ChangeResult } from "../hooks/useScriptReview";
import { REVIEW_HASH, type SoundChoice } from "../lib/draft";

const VOLUME_STEP = 5; // the backend's (sound-library D5)
/** An option for a sound the draft keeps but the library lost (sound-library D8, D13). */
const GONE = "ไม่พบเสียงนี้ในคลังเสียง";

type Props = {
  sound: PlayedSound | null;
  /** The library's sounds; null until read. */
  sounds: Sound[] | null;
  /** A job changes the draft or renders: the picker and the slider wait (spoil-maker D51). */
  locked: boolean;
  onChange: (sound: SoundChoice) => Promise<ChangeResult>;
  /** The library lost the sound just chosen: read it again. */
  onSoundGone: () => void;
};

/**
 * ตรวจแก้บท's background sound (sound-library D5, D11): ไม่มีเสียงพื้น or one sound of the
 * library, with its volume sent when the slider is let go and a button to hear it, and
 * "ไปคลังเสียง" to the library and back. A refused choice leaves the picker on the draft's sound.
 */
export function BackgroundSound({ sound, sounds, locked, onChange, onSoundGone }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [refusals, setRefusals] = useState(0); // each one starts the slider again from the draft
  const id = useId();
  const chosen = sound ? sounds?.find((option) => option.id === sound.sound_id) : undefined;

  const send = async (next: SoundChoice) => {
    const result = await onChange(next);
    setError(result.kind === "refused" ? result.message : null);
    if (result.kind === "refused") setRefusals((n) => n + 1);
    if (result.kind === "refused" && result.code === "sound_not_found") onSoundGone();
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-sm leading-5">
        <label htmlFor={id} className="flex-1 font-medium text-foreground">
          เสียงพื้น
        </label>
        <a href={soundsHash(REVIEW_HASH)} className="font-medium text-link underline">
          ไปคลังเสียง
        </a>
      </div>
      {sounds !== null && sounds.length === 0 && sound === null ? (
        <p className="text-sm text-mid">ยังไม่มีเสียงในคลัง</p>
      ) : (
        <div className="flex items-center gap-2">
          <span className="relative flex h-10 min-w-0 flex-1 items-center gap-2 rounded-lg border border-border bg-card px-3 has-disabled:bg-muted">
            <img src={musicIcon} alt="" width={16} height={16} />
            <select
              id={id}
              value={sound?.sound_id ?? ""}
              disabled={locked}
              onChange={(event) => void send(event.target.value ? { sound_id: event.target.value } : null)}
              className="min-w-0 flex-1 appearance-none bg-transparent pr-5 text-sm text-foreground"
            >
              <option value="">ไม่มีเสียงพื้น</option>
              {sounds?.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
              {sound && !chosen && <option value={sound.sound_id}>{sounds === null ? "กำลังโหลด…" : GONE}</option>}
            </select>
            <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none -ml-6" />
          </span>
          {chosen && (
            <button
              type="button"
              aria-label={`ฟัง ${chosen.name}`}
              onClick={() => playAudio(soundFilePath(chosen.id))}
              className="flex size-10 items-center justify-center rounded-lg hover:bg-muted"
            >
              <img src={playIcon} alt="" width={16} height={16} />
            </button>
          )}
        </div>
      )}
      {error && <Alert tone="error">{error}</Alert>}
      {sound && (
        <SoundVolume
          key={`${sound.volume}-${refusals}`}
          volume={sound.volume}
          disabled={locked}
          onCommit={(volume) => void send({ sound_id: sound.sound_id, volume })}
        />
      )}
    </div>
  );
}

/** The background sound's volume 0–100 in steps of 5, sent once when the slider is let go. */
function SoundVolume({ volume, disabled, onCommit }: { volume: number; disabled: boolean; onCommit: (volume: number) => void }) {
  // The parent remounts this with `key` when the draft's volume changes or a change is refused,
  // so `value` starts from the draft's.
  const [value, setValue] = useState(volume);
  const sent = useRef(volume); // letting go fires pointerup, keyup and blur: send each value once
  const commit = () => {
    if (value === sent.current) return;
    sent.current = value;
    onCommit(value);
  };
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2 text-sm leading-5 text-foreground">
        <span className="flex-1">ความดังเสียงพื้น</span>
        <span className="font-mono font-medium">{value}</span>
      </div>
      <input
        type="range"
        aria-label="ความดังเสียงพื้น"
        min={0}
        max={100}
        step={VOLUME_STEP}
        value={value}
        disabled={disabled}
        onChange={(event) => setValue(Number(event.target.value))}
        onPointerUp={commit}
        onKeyUp={commit}
        onBlur={commit}
        className="h-11 w-full accent-brand-accent"
      />
    </div>
  );
}
