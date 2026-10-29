import notReadyIcon from "../assets/not-ready.svg";

/** In place of an action while items it needs are missing: the link field (D9, D10) or ถอดบทพูด (D27). */
export function NotReady({ missing }: { missing: string[] }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-warning-border bg-warning-surface px-4 py-3.5">
      <img src={notReadyIcon} alt="" width={20} height={20} className="shrink-0" />
      <p className="flex-1 text-sm leading-[1.5] font-medium text-warning">ยังติดตั้งไม่ครบ: {missing.join(", ")}</p>
      <a
        href="#/setup"
        className="flex h-9 shrink-0 items-center rounded-lg px-4 font-button text-sm leading-5 font-medium text-brand hover:bg-warning-border/10"
      >
        ไปหน้า Setup status
      </a>
    </div>
  );
}
