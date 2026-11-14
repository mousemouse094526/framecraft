import type { InputHTMLAttributes } from "react";

const VOLUME_STEP = 5; // the backend's (D40, sound-library D5)

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "min" | "max" | "step" | "className">;

/** A volume slider 0–100 in steps of 5 with its 0 and 100 under it: the original sound's and the
 * background sound's of ตรวจแก้บท. The caller gives its name, value and when it saves. */
export function VolumeRange(props: Props) {
  return (
    <>
      <input type="range" min={0} max={100} step={VOLUME_STEP} {...props} className="h-11 w-full accent-brand-accent" />
      <div className="flex justify-between font-mono text-xs text-muted-foreground">
        <span>0</span>
        <span>100</span>
      </div>
    </>
  );
}
