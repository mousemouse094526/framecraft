import { useCallback } from "react";
import { OFFLINE_TEXT, sendFile, sendJson } from "../../../lib/api";
import { refusalOf } from "../../../lib/refusal";
import { useMountedState } from "../../../lib/useMountedState";
import { backgroundPath, type Lesson } from "../../../lib/lesson";

/** `sending`: a picture going out, or its removal; both buttons wait. `refused`: the API's message, or offline. */
export type BackgroundState = { kind: "idle" } | { kind: "sending" } | { kind: "refused"; text: string };

/** What a background route answered; `offline` when nothing did. */
type Reply = { kind: "answer"; status: number; body: unknown } | { kind: "offline" };

async function jsonReply(method: string, path: string, body?: unknown): Promise<Reply> {
  try {
    return { kind: "answer", ...(await sendJson<unknown>(method, path, body)) };
  } catch {
    return { kind: "offline" };
  }
}

/**
 * The lesson's background picture: a picked file is checked (`/background/check`), then sent
 * as the raw body with `PUT` (ADR 0028); ลบภาพ is a `DELETE`. Each answers the lesson, which
 * goes to `applyBackground` (D6, spec › API).
 */
export function useBackground(id: string, applyBackground: (lesson: Lesson) => void) {
  const [state, , setIfMounted] = useMountedState<BackgroundState>({ kind: "idle" });

  const end = useCallback(
    (reply: Reply) => {
      if (reply.kind === "answer" && reply.status === 200 && reply.body) {
        applyBackground(reply.body as Lesson);
        setIfMounted({ kind: "idle" });
      } else {
        setIfMounted({ kind: "refused", text: (reply.kind === "answer" && refusalOf(reply.body)?.message) || OFFLINE_TEXT });
      }
    },
    [applyBackground, setIfMounted],
  );

  const pick = useCallback(
    async (file: File) => {
      setIfMounted({ kind: "sending" });
      const check = await jsonReply("POST", `${backgroundPath(id)}/check`, { size: file.size });
      if (check.kind === "offline" || check.status !== 200) {
        end(check);
        return;
      }
      // 20 MB at most, on this machine: no percent to show (no `onProgress`, no `onSent`), the
      // button says it is sending.
      const noop = () => {};
      const sent = await sendFile<unknown>(`${backgroundPath(id)}?size=${file.size}`, file, noop, noop, "PUT").reply;
      end(sent.kind === "answer" ? sent : { kind: "offline" });
    },
    [id, end, setIfMounted],
  );

  const remove = useCallback(async () => {
    setIfMounted({ kind: "sending" });
    end(await jsonReply("DELETE", backgroundPath(id)));
  }, [id, end, setIfMounted]);

  return { state, pick, remove };
}
