import { useCallback, useEffect } from "react";
import { getJson } from "../../../lib/api";
import type { StatusResponse } from "../../../lib/statusTypes";
import { useMountedState } from "../../../lib/useMountedState";

export type SetupStatusState =
  | { kind: "loading" }
  | { kind: "result"; status: StatusResponse }
  | { kind: "refreshing"; status: StatusResponse }
  | { kind: "offline" };

const STATUS_PATH = "/api/setup/status";

/** Checks once on mount; never polls. `refresh` checks again on demand. */
export function useSetupStatus() {
  const [state, setState, setIfMounted] = useMountedState<SetupStatusState>({ kind: "loading" });

  const check = useCallback(async () => {
    try {
      const status = await getJson<StatusResponse>(STATUS_PATH);
      setIfMounted({ kind: "result", status });
    } catch {
      // Any failure (no backend, not 200, timeout) means the backend is offline.
      setIfMounted({ kind: "offline" });
    }
  }, [setIfMounted]);

  useEffect(() => {
    void check();
  }, [check]);

  // Refresh is disabled while a check runs, so two checks never overlap.
  const refresh = useCallback(() => {
    // Keep the old checklist while checking again; from offline there is none.
    setState((previous) =>
      previous.kind === "result" ? { kind: "refreshing", status: previous.status } : { kind: "loading" },
    );
    void check();
  }, [check]);

  return { state, refresh };
}
