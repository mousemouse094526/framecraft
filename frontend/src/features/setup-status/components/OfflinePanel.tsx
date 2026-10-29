import type { ReactNode } from "react";
import serverOfflineIcon from "../assets/server-offline.svg";

/** Shown in place of the checklist when the backend gave no usable answer (D13). */
export function OfflinePanel() {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-error-surface p-2">
          <img src={serverOfflineIcon} alt="" width={20} height={20} />
        </div>
        <h2 className="text-lg font-semibold text-foreground">Backend offline</h2>
      </div>
      <OfflineCase label="ยังไม่ได้ start:">
        รัน <Code>npm run dev</Code>
      </OfflineCase>
      <OfflineCase label="รันอยู่แล้ว:">
        ดู <Code>error</Code> ในบรรทัด [api] ของ <Code>terminal</Code> ที่รัน <Code>npm run dev</Code> หรือรัน{" "}
        <Code>setup</Code> ใหม่
      </OfflineCase>
    </div>
  );
}

function OfflineCase({ label, children }: { label: string; children: ReactNode }) {
  return (
    <p className="flex flex-col gap-1 rounded-lg bg-muted px-3.5 py-3 text-sm leading-[22px] sm:flex-row sm:gap-3">
      <strong className="shrink-0 font-semibold text-foreground sm:w-[120px]">{label}</strong>{" "}
      <span className="flex-1 text-mid">{children}</span>
    </p>
  );
}

function Code({ children }: { children: ReactNode }) {
  return <code className="font-mono text-[13px]">{children}</code>;
}
