import { Alert } from "./Alert";
import { OUTLINE_BUTTON } from "./buttonStyles";
import type { Notice } from "../../lib/notice";

/** A refused or failed request of a page (`noticeOf`), a line per item under it when it lists
 * some, with a link to ติดตั้ง when a model is missing. */
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
      {notice.lines?.length ? (
        <>
          <p>{notice.text}</p>
          <ul>
            {notice.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </>
      ) : (
        notice.text
      )}
    </Alert>
  );
}
