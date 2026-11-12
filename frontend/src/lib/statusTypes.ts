// The shape of GET /api/setup/status (backend.checks.StatusResponse); both tabs read it.
export type ItemStatus = "ok" | "missing" | "warning";

/** "command" is copied and run as-is; "hint" is a sentence to read. */
export type FixKind = "command" | "hint";

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
  fix_kind: FixKind | null;
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
