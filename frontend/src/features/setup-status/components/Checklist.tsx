import { useState } from "react";
import type { ChecklistItem, ItemStatus, License } from "../hooks/useSetupStatus";
import copyIcon from "../assets/copy.svg";
import externalLinkIcon from "../assets/external-link.svg";
import rowMissingIcon from "../assets/row-missing.svg";
import rowOkIcon from "../assets/row-ok.svg";
import rowWarningIcon from "../assets/row-warning.svg";

const ROW_LOOK: Record<ItemStatus, { icon: string; alt: string; rowClass: string; detailClass: string }> = {
  ok: { icon: rowOkIcon, alt: "ผ่าน", rowClass: "", detailClass: "font-mono text-[13px] text-mid" },
  missing: { icon: rowMissingIcon, alt: "ขาด", rowClass: "bg-error-surface", detailClass: "text-sm text-destructive" },
  warning: { icon: rowWarningIcon, alt: "คำเตือน", rowClass: "bg-warning-surface", detailClass: "text-sm text-warning" },
};

/** The Checklist items in the order the API sends them. */
export function Checklist({ items }: { items: ChecklistItem[] }) {
  return (
    <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
      {items.map((item) => (
        <Row key={item.id} item={item} />
      ))}
    </ul>
  );
}

function Row({ item }: { item: ChecklistItem }) {
  const look = ROW_LOOK[item.status];
  const labelId = `checklist-${item.id}`;
  return (
    <li aria-labelledby={labelId} className={`flex items-start gap-3 px-4 py-3 ${look.rowClass}`}>
      <img src={look.icon} alt={look.alt} width={20} height={20} className="mt-px shrink-0" />
      <div className="flex min-w-0 flex-1 flex-col gap-1 sm:flex-row sm:gap-3">
        <p id={labelId} className="shrink-0 text-sm leading-[22px] font-medium text-foreground sm:w-40">
          {item.label}
        </p>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <p className={`leading-[22px] break-words ${look.detailClass}`}>{item.detail}</p>
          {item.status !== "ok" && item.fix && <Fix fix={item.fix} />}
          {item.license && <LicenseLine license={item.license} />}
        </div>
      </div>
    </li>
  );
}

/**
 * The API sends one `fix` for the OS the backend runs on (D15). A command
 * (`./setup.sh`, `setup.cmd`) has no spaces and gets a copy chip; a sentence
 * is shown as plain text.
 */
function Fix({ fix }: { fix: string }) {
  if (/\s/.test(fix)) {
    return <p className="text-[13px] leading-5 text-foreground">{fix}</p>;
  }
  return <CommandChip command={fix} />;
}

function CommandChip({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
  };
  return (
    <div className="flex w-fit items-center gap-2 rounded-md border border-border bg-muted py-1 pr-2 pl-2.5">
      <code className="font-mono text-[13px] font-medium whitespace-nowrap text-foreground">{command}</code>
      <button
        type="button"
        onClick={copy}
        aria-label={`คัดลอก ${command}`}
        title={copied ? "คัดลอกแล้ว" : "คัดลอก"}
        className="shrink-0 rounded-sm hover:opacity-70"
      >
        <img src={copyIcon} alt="" width={14} height={14} />
      </button>
    </div>
  );
}

/** Attribution the model licenses ask for (D11, legal item 1). */
function LicenseLine({ license }: { license: License }) {
  return (
    <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
      <span>
        {license.name} · {license.author} ·
      </span>
      <ExternalLink href={license.url}>license</ExternalLink>
      <ExternalLink href={license.model_url}>model</ExternalLink>
    </p>
  );
}

function ExternalLink({ href, children }: { href: string; children: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-0.5 font-medium text-link underline"
    >
      {children}
      <img src={externalLinkIcon} alt="" width={12} height={12} />
    </a>
  );
}
