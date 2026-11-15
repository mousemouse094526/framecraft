import { useRef } from "react";
import { useBackground } from "../../lib/useBackground";
import { GHOST_BUTTON, SECONDARY_BUTTON } from "./buttonStyles";

/** Beside the button, as video-gen legal item 3 asks (video-gen D23, drum-cover legal 3). */
export const RIGHTS_NOTE = "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม";

type Props = {
  /** The route of the picture: a lesson's or a reel cover's `…/background`. */
  path: string;
  /** The saved one's: the picture is on the backend the moment a pick answers. */
  background: "color" | "image";
  /** Where the cropped picture is shown from, new with each picture (`?v=`). */
  imageUrl: string;
  apply: (body: unknown) => void;
};

/**
 * พื้นหลัง: the app's colours, or the user's PNG or JPG that each render blurs and darkens
 * (video-gen D6, drum-cover D8). The one picture a clip takes: no logo or watermark (video-gen D23).
 * The สอนกลอง tab's lesson editor and the reel page share it.
 */
export function BackgroundPicker({ path, background, imageUrl, apply }: Props) {
  const { state, pick, remove } = useBackground(path, apply);
  const file = useRef<HTMLInputElement>(null);
  const sending = state.kind === "sending";

  return (
    <section aria-label="พื้นหลัง" className="flex flex-col gap-3">
      <h3 className="text-sm leading-[1.5] font-medium text-foreground">พื้นหลัง</h3>
      <div className="flex items-start gap-4">
        {background === "image" ? (
          <img src={imageUrl} alt="ภาพพื้นหลัง" className="aspect-[9/16] w-20 shrink-0 rounded-lg border border-border object-cover" />
        ) : (
          <div className="flex aspect-[9/16] w-20 shrink-0 items-end rounded-lg border border-border bg-gradient-to-b from-drum-clip-top to-drum-clip-bottom p-1.5">
            <span className="text-[11px] leading-4 text-card/80">สีของแอป</span>
          </div>
        )}
        <div className="flex min-w-0 flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={sending} onClick={() => file.current?.click()} className={`h-11 w-fit px-4 sm:h-10 ${SECONDARY_BUTTON}`}>
              {sending ? "กำลังส่งภาพ…" : "เลือกภาพ"}
            </button>
            {background === "image" && (
              <button type="button" disabled={sending} onClick={() => void remove()} className={`h-11 px-3 sm:h-10 ${GHOST_BUTTON}`}>
                ลบภาพ
              </button>
            )}
          </div>
          <input
            ref={file}
            type="file"
            accept="image/png,image/jpeg"
            aria-label="ไฟล์ภาพพื้นหลัง"
            className="hidden"
            onChange={(event) => {
              const picked = event.target.files?.[0];
              event.target.value = "";
              if (picked) void pick(picked);
            }}
          />
          <p className="text-xs leading-4 text-muted-foreground">{RIGHTS_NOTE}</p>
          {state.kind === "refused" && <p className="font-button text-xs leading-4 text-destructive">{state.text}</p>}
        </div>
      </div>
    </section>
  );
}
