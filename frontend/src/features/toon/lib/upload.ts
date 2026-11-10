import { sendFile, type FileUpload } from "../../../lib/api";
import type { Refusal } from "../../../lib/refusal";
import { sendEdit } from "./edit";
import { noticeOf, type Notice } from "./notice";

/** A file the tab takes in through `{path}/check` (its `checkBody`), then `{path}?{query}` (ADR 0028). */
export type FileToSend = {
  path: string;
  checkBody: unknown;
  query: string;
  file: File;
  /** The notice's title when the check or the upload refuses it, e.g. "เอาไฟล์ ลม.wav เข้าไม่ได้". */
  title: string;
  /** The refusal codes whose notice is a `warning` (`NOT_NOW`); none by default. */
  warnings?: readonly string[];
};

/** How a file's import ended: `ok` with the backend's 200 or 201 body (the new sound, or the
 * Series with its new reference image), `refused` with the notice, or `aborted` by `abort()`. */
export type SendReply<T> = { kind: "ok"; value: T } | { kind: "refused"; notice: Notice } | { kind: "aborted" };

/**
 * The check, then the file as the raw body with `sendFile` (no timeout, spoil D58): a refused
 * check sends nothing. `started` gets the upload as it goes out, before any `progress` (its
 * percent); `abort()` on it cancels. A refusal, or no backend, is `refused`.
 */
export async function sendChecked<T>(
  { path, checkBody, query, file, title, warnings = [] }: FileToSend,
  on: { started: (upload: FileUpload<T | Refusal>) => void; progress: (percent: number) => void },
): Promise<SendReply<T>> {
  const refused = (body: unknown): SendReply<T> => ({ kind: "refused", notice: noticeOf(title, body, warnings) });
  const check = await sendEdit<unknown>("POST", `${path}/check`, checkBody, title, { ok: [200], warnings });
  if (check.kind === "refused") return { kind: "refused", notice: check.notice };
  // Nothing to do once the whole body is out: the answer ends it.
  const upload = sendFile<T | Refusal>(`${path}?${query}`, file, on.progress, () => {});
  on.started(upload);
  const reply = await upload.reply;
  if (reply.kind === "aborted") return reply;
  if (reply.kind === "answer" && (reply.status === 200 || reply.status === 201)) return { kind: "ok", value: reply.body as T };
  return refused(reply.kind === "answer" ? reply.body : null);
}
