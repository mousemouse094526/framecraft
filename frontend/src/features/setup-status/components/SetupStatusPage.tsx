import type { StatusResponse } from "../hooks/useSetupStatus";
import { useSetupStatus } from "../hooks/useSetupStatus";
import lastCheckedIcon from "../assets/last-checked.svg";
import spinnerLoadingIcon from "../assets/spinner-loading.svg";
import { Checklist } from "./Checklist";
import { OfflinePanel } from "./OfflinePanel";
import { RefreshButton } from "./RefreshButton";
import { Verdict } from "./Verdict";

export function SetupStatusPage() {
  const { state, refresh } = useSetupStatus();

  return (
    <main className="min-h-screen bg-muted px-4 pt-6 pb-8 sm:px-0 sm:pt-16 sm:pb-20">
      <div className="mx-auto flex w-full max-w-[720px] flex-col gap-4">
        <header className="flex items-center gap-3 pb-1">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <Wordmark />
            <div className="h-5 w-px bg-border" />
            <h1 className="text-[15px] font-medium sm:text-base whitespace-nowrap text-mid">Setup status</h1>
          </div>
          <RefreshButton stateKind={state.kind} onClick={refresh} />
        </header>

        {state.kind === "loading" && <Loading />}
        {state.kind === "offline" && <OfflinePanel />}
        {(state.kind === "result" || state.kind === "refreshing") && <Result status={state.status} />}
      </div>
    </main>
  );
}

function Wordmark() {
  return (
    <p className="font-brand text-[20.8px] font-semibold tracking-[-0.62px] sm:text-[26px] sm:tracking-[-0.78px] whitespace-nowrap text-brand">
      frame<span className="text-brand-accent">craft</span>
    </p>
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
