import { useCallback, useState } from "react";

/** Copies `text`; `copied` turns true once the clipboard took it. A refused clipboard leaves it false. */
export function useCopy(text: string) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      // No clipboard permission: the command is still on screen to select by hand.
    }
  }, [text]);
  return { copied, copy };
}
