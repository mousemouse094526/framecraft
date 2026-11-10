import { sendJson } from "../../../lib/api";
import type { Refusal } from "../../../lib/refusal";
import { noticeOf, type Notice } from "./notice";

/** How an edit ended: what it changed as it is now, or why it didn't. */
export type EditReply<T> = { kind: "saved"; value: T } | { kind: "refused"; notice: Notice };

/**
 * An add, change or delete whose answer is what it changed as it is now (a Series, an EP):
 * a 200 or 201 is `saved`; a refusal, or no backend, is `refused` with the notice titled
 * `title`. The notice is always `error`: no edit of the tab marks a code as "not now" (`NOT_NOW`).
 */
export async function sendEdit<T>(method: string, path: string, body: unknown, title: string): Promise<EditReply<T>> {
  try {
    const reply = await sendJson<T | Refusal>(method, path, body);
    if (reply.status === 200 || reply.status === 201) return { kind: "saved", value: reply.body as T };
    return { kind: "refused", notice: noticeOf(title, reply.body) };
  } catch {
    return { kind: "refused", notice: noticeOf(title, null) };
  }
}
