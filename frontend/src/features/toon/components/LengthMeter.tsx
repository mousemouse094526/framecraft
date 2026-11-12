import { TARGET_MAX_S, TARGET_MIN_S } from "../lib/episodes";

const SCALE_S = 150; // the bar runs 0–150 s, the target zone 60–120 inside it

/** Figma `Toon/LengthMeter`: the EP's length against the 60–120 s target (D14); the message
 * says it in words, not by colour only. */
export function LengthMeter({ seconds }: { seconds: number }) {
  const whole = Math.round(seconds);
  const [message, tone, bar] =
    whole > TARGET_MAX_S
      ? [`ยาวเกินเป้า ${whole - TARGET_MAX_S} วิ`, "text-destructive", "bg-destructive"]
      : whole < TARGET_MIN_S
        ? [`สั้นกว่าเป้า ${TARGET_MIN_S - whole} วิ`, "text-warning", "bg-warning"]
        : ["อยู่ในเป้า", "text-success", "bg-success"];
  return (
    <div
      role="meter"
      aria-label="ความยาวรวม"
      aria-valuemin={0}
      aria-valuemax={SCALE_S}
      aria-valuenow={whole}
      aria-valuetext={`${whole} วินาที ${message}`}
      className="flex w-full max-w-[340px] flex-col gap-1.5"
    >
      <div className="flex items-center gap-1.5 leading-[1.5]">
        <span className="text-xs font-medium text-mid">ความยาวรวม</span>
        <span className="font-mono text-sm font-medium text-foreground">{whole} วิ</span>
        <span className="text-xs text-muted-foreground">
          / เป้า {TARGET_MIN_S}–{TARGET_MAX_S} วิ
        </span>
        <span className="flex-1" />
        <span className={`text-xs font-medium ${tone}`}>{message}</span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-surface-strong">
        <div
          className="absolute inset-y-0 bg-success-surface"
          style={{ left: `${(TARGET_MIN_S / SCALE_S) * 100}%`, right: `${100 - (TARGET_MAX_S / SCALE_S) * 100}%` }}
        />
        <div className={`absolute inset-y-0 left-0 rounded-full ${bar}`} style={{ width: `${Math.min(whole / SCALE_S, 1) * 100}%` }} />
      </div>
    </div>
  );
}
