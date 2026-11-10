import { Alert } from "../../../components/ui/Alert";
import { OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import type { Notice } from "../lib/notice";

/** A refusal or failure of the tab's pages, with a link to ติดตั้ง when a model is missing. */
export function NoticeLine({ notice }: { notice: Notice }) {
  return (
    <Alert
      tone={notice.tone}
      title={notice.title}
      action={
        notice.setupLink && (
          <a href="#/setup" className={`h-8 px-3 ${OUTLINE_BUTTON}`}>
            ไปที่ ติดตั้ง
          </a>
        )
      }
    >
      {notice.text}
    </Alert>
  );
}
