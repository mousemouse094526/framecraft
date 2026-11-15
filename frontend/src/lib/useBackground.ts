import { useCallback } from "react";
import { OFFLINE_TEXT, sendFile, sendJson } from "./api";
import { refusalOf } from "./refusal";
import { useMountedState } from "./useMountedState";

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
 * A background picture at `path` (a drum lesson's or a reel cover's `…/background`, video-gen D6,
 * drum-cover D21): a picked file is checked (`{path}/check`), then sent as the raw body with `PUT`
 * (ADR 0028); ลบภาพ is a `DELETE`. Each answers what owns the picture, which goes to `apply`.
 */
export function useBackground(path: string, apply: (body: unknown) => void) {
  const [state, , setIfMounted] = useMountedState<BackgroundState>({ kind: "idle" });

  const end = useCallback(
    (reply: Reply) => {
      if (reply.kind === "answer" && reply.status === 200 && reply.body) {
        apply(reply.body);
        setIfMounted({ kind: "idle" });
      } else {
        setIfMounted({ kind: "refused", text: (reply.kind === "answer" && refusalOf(reply.body)?.message) || OFFLINE_TEXT });
      }
    },
    [apply, setIfMounted],
  );

  const pick = useCallback(
    async (file: File) => {
      setIfMounted({ kind: "sending" });
      const check = await jsonReply("POST", `${path}/check`, { size: file.size });
      if (check.kind === "offline" || check.status !== 200) {
        end(check);
        return;
      }
      // 20 MB at most, on this machine: no percent to show (no `onProgress`, no `onSent`), the
      // button says it is sending.
      const noop = () => {};
      const sent = await sendFile<unknown>(`${path}?size=${file.size}`, file, noop, noop, "PUT").reply;
      end(sent.kind === "answer" ? sent : { kind: "offline" });
    },
    [path, end, setIfMounted],
  );

  const remove = useCallback(async () => {
    setIfMounted({ kind: "sending" });
    end(await jsonReply("DELETE", path));
  }, [path, end, setIfMounted]);

  return { state, pick, remove };
}
