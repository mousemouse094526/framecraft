import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import refreshIcon from "../assets/refresh-cw.svg";
import type { Banner } from "../lib/render";

/** Figma `Review banner`: two lines in its tone, and ลองอีกครั้ง when the job can start again. */
export function ReviewBanner({ banner, onRetry }: { banner: Banner; onRetry: () => void }) {
  return (
    <Alert
      tone={banner.tone}
      action={
        banner.retry ? (
          <button type="button" onClick={onRetry} className={`h-11 px-6 ${OUTLINE_BUTTON}`}>
            <img src={refreshIcon} alt="" width={16} height={16} />
            ลองอีกครั้ง
          </button>
        ) : undefined
      }
    >
      <p className={`font-semibold ${banner.tone === "error" ? "text-destructive" : "text-warning"}`}>{banner.title}</p>
      <p>{banner.text}</p>
    </Alert>
  );
}
