import type { SetupStatusState } from "../hooks/useSetupStatus";
import refreshIcon from "../assets/refresh-button.svg";
import spinnerRefreshIcon from "../assets/spinner-refresh.svg";

type Props = {
  stateKind: SetupStatusState["kind"];
  onClick: () => void;
};

/** Disabled while any check runs; spins only when a shown result is being checked again. */
export function RefreshButton({ stateKind, onClick }: Props) {
  const spinning = stateKind === "refreshing";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={stateKind === "loading" || spinning}
      className="flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg border border-border bg-card px-4 font-button text-sm leading-5 font-medium text-foreground hover:bg-muted disabled:opacity-60 disabled:hover:bg-card"
    >
      {spinning ? (
        <img src={spinnerRefreshIcon} alt="" width={14} height={14} className="animate-spin" />
      ) : (
        <img src={refreshIcon} alt="" width={16} height={16} />
      )}
      Refresh
    </button>
  );
}
