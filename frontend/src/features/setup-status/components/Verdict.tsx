import type { StatusResponse } from "../../../lib/statusTypes";
import verdictAlertIcon from "../assets/verdict-alert.svg";
import verdictOkIcon from "../assets/verdict-ok.svg";
import warningHintIcon from "../assets/warning-hint.svg";

const BANNER_LOOK = {
  ready: { icon: verdictOkIcon, boxClass: "border-success-border bg-success-surface", textClass: "text-success" },
  notReady: { icon: verdictAlertIcon, boxClass: "border-error-border bg-error-surface", textClass: "text-destructive" },
};

/** The one-line answer to "is this machine ready?", from `ready` (D13). */
export function Verdict({ status }: { status: StatusResponse }) {
  const look = status.ready ? BANNER_LOOK.ready : BANNER_LOOK.notReady;
  // The labels of warning rows show as pills beside a ready verdict (Figma frame 3).
  const warnings = status.ready ? status.items.filter((item) => item.status === "warning") : [];
  return (
    <div className={`flex items-center gap-3 rounded-xl border px-4 py-3.5 ${look.boxClass}`}>
      <img src={look.icon} alt="" width={22} height={22} />
      <p className={`flex-1 text-lg leading-[26px] font-semibold ${look.textClass}`}>{verdictText(status)}</p>
      {warnings.map((item) => (
        <span
          key={item.id}
          className="flex shrink-0 items-center gap-1 rounded-full border border-warning-border bg-warning-surface px-2 py-0.5 font-mono text-xs font-medium text-warning"
        >
          <img src={warningHintIcon} alt="" width={14} height={14} />
          {item.label}
        </span>
      ))}
    </div>
  );
}

function verdictText(status: StatusResponse): string {
  if (!status.ready) return `ยังไม่พร้อม: ขาด ${status.missing_count} รายการ`;
  if (status.warning_count === 0) return "พร้อมใช้งาน";
  return `พร้อมใช้งาน (มีคำเตือน ${status.warning_count} รายการ)`;
}
