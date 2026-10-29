import { useCallback, useEffect, useRef, useState } from "react";
import { getJson } from "../../../lib/api";

// The shape of GET /api/setup/status (backend.checks.StatusResponse).
export type ItemStatus = "ok" | "missing" | "warning";

export type License = {
  name: string;
  url: string;
  author: string;
  model_url: string;
};

export type ChecklistItem = {
  id: string;
  label: string;
  status: ItemStatus;
  detail: string;
  fix: string | null;
  license: License | null;
};

export type StatusResponse = {
  checked_at: string;
  ready: boolean;
  ok_count: number;
  warning_count: number;
  missing_count: number;
  total: number;
  items: ChecklistItem[];
};

export type SetupStatusState =
  | { kind: "loading" }
  | { kind: "result"; status: StatusResponse }
  | { kind: "refreshing"; status: StatusResponse }
  | { kind: "offline" };

const STATUS_PATH = "/api/setup/status";

/** Checks once on mount; never polls. `refresh` checks again on demand. */
export function useSetupStatus() {
  const [state, setState] = useState<SetupStatusState>({ kind: "loading" });

  // An answer that arrives after the page is gone is dropped. StrictMode
  // unmounts and remounts once in dev, so the flag is reset on every mount.
  const mounted = useRef(false);

  const check = useCallback(async () => {
    try {
      const status = await getJson<StatusResponse>(STATUS_PATH);
      if (mounted.current) setState({ kind: "result", status });
    } catch {
      // Any failure (no backend, not 200, timeout) means the backend is offline.
      if (mounted.current) setState({ kind: "offline" });
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void check();
    return () => {
      mounted.current = false;
    };
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
