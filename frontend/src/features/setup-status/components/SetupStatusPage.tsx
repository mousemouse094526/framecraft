import type { StatusResponse } from "../../../lib/statusTypes";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import { useSetupStatus } from "../hooks/useSetupStatus";
import lastCheckedIcon from "../assets/last-checked.svg";
import spinnerLoadingIcon from "../assets/spinner-loading.svg";
import { Checklist } from "./Checklist";
import { Verdict } from "./Verdict";

export function SetupStatusPage() {
  const { state, refresh } = useSetupStatus();

  return (
    <PageLayout
      tab="setup"
      action={<RefreshButton onClick={refresh} disabled={state.kind === "loading"} spinning={state.kind === "refreshing"} />}
    >
      {state.kind === "loading" && <Loading />}
      {state.kind === "offline" && <OfflinePanel />}
      {(state.kind === "result" || state.kind === "refreshing") && <Result status={state.status} />}
    </PageLayout>
  );
}

function Loading() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card py-[72px]">
      <img src={spinnerLoadingIcon} alt="" width={24} height={24} className="animate-spin" />
      <p className="text-[15px] font-medium text-mid">กำลังเช็ค…</p>
    </div>
  );
}

function Result({ status }: { status: StatusResponse }) {
  return (
    <>
      <p className="flex items-center gap-1.5 text-[13px] text-muted-foreground">
        <img src={lastCheckedIcon} alt="" width={14} height={14} />
        เช็คล่าสุด: <time className="font-mono">{timeOfDay(status.checked_at)}</time>
      </p>
      <Verdict status={status} />
      <Checklist items={status.items} />
      <p className="text-right font-mono text-sm font-medium text-foreground">
        {status.ok_count}/{status.total}
      </p>
    </>
  );
}

/** "2026-10-29T17:42:10+07:00" → "17:42:10": the backend's clock, which is this machine's. */
function timeOfDay(checkedAt: string): string {
  return checkedAt.slice(11, 19);
}
