import { OUTLINE_BUTTON } from "./buttonStyles";
import refreshIcon from "./assets/refresh-button.svg";
import spinnerRefreshIcon from "./assets/spinner-refresh.svg";

type Props = {
  onClick: () => void;
  disabled?: boolean;
  /** Spins only while a shown result is being checked again. */
  spinning?: boolean;
};

export function RefreshButton({ onClick, disabled = false, spinning = false }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || spinning}
      className={`h-9 px-4 ${OUTLINE_BUTTON}`}
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
