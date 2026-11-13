import { Alert } from "../../../components/ui/Alert";
import { FixCommand } from "../../../components/ui/FixCommand";
import type { Notice } from "../lib/notice";

/** The message after a job or a refusal; a `fix` is a command line with a copy button (setup-status D20). */
export function NoticeAlert({ notice }: { notice: Notice }) {
  return (
    <div className="flex flex-col gap-2.5">
      <Alert tone={notice.tone}>{notice.text}</Alert>
      {notice.fix && <FixCommand command={notice.fix} />}
    </div>
  );
}
