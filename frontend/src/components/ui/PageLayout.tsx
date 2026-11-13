import { useCallback, useId, useRef, useState, type ReactNode } from "react";
import { useDismiss } from "../../lib/useDismiss";
import { TAB_GROUPS, tabLabel, TABS, type TabId } from "../../lib/useHash";
import menuIcon from "./assets/menu.svg";

type Props = {
  tab: TabId;
  /** A button at the right end of the header, such as Refresh. */
  action?: ReactNode;
  /** From 1024px the column is 1120px wide, for a page with two columns (spoil D25, D33). */
  wide?: boolean;
  children: ReactNode;
};

/** The column every tab sits in: wordmark, tab bar, the tab's action, then its content. */
export function PageLayout({ tab, action, wide = false, children }: Props) {
  return (
    <main className={`min-h-screen bg-muted px-4 pt-6 pb-8 sm:px-0 sm:pt-16 sm:pb-20 ${wide ? "lg:px-8" : ""}`}>
      <div className={`mx-auto flex w-full max-w-[720px] flex-col gap-4 ${wide ? "lg:max-w-[1120px]" : ""}`}>
        {/* The open tab names the page; the tab bar shows it, so the heading is for screen readers. */}
        <h1 className="sr-only">{tabLabel(tab)}</h1>
        {/* 375px frame 13: wordmark and action on one row, the tab menu below; from 640px one row
            with the tab bar (sound-library D3). */}
        <header className="flex flex-wrap items-center gap-3 pb-1">
          <Wordmark />
          <div className="hidden h-5 w-px bg-border sm:block" />
          <div className="order-last basis-full sm:order-none sm:basis-auto">
            <TabBar active={tab} />
            <TabMenu active={tab} />
          </div>
          <div className="flex-1" />
          {action}
        </header>
        {children}
      </div>
    </main>
  );
}

function Wordmark() {
  return (
    <p className="font-brand text-[26px] font-semibold tracking-[-0.78px] whitespace-nowrap text-brand">
      frame<span className="text-brand-accent">craft</span>
    </p>
  );
}

type Tab = (typeof TABS)[number];

const UNGROUPED = TABS.filter((t) => t.group === null);
const GROUPED = TAB_GROUPS.map((group) => ({ ...group, tabs: TABS.filter((t) => t.group === group.id) }));

/** From 640px: the tabs in a row, a line between the groups, each group named only for screen
 * readers (sound-library D3). */
function TabBar({ active }: { active: TabId }) {
  return (
    <nav
      aria-label="แถบ tab"
      className="hidden w-fit items-center gap-0.5 rounded-xl border border-border bg-card p-[3px] sm:flex"
    >
      {UNGROUPED.map((t) => (
        <TabLink key={t.id} tab={t} active={active} />
      ))}
      {GROUPED.map((group) => (
        <div key={group.id} role="group" aria-label={group.label} className="flex items-center gap-0.5">
          <div className="mx-1 h-5 w-px bg-border" />
          {group.tabs.map((t) => (
            <TabLink key={t.id} tab={t} active={active} />
          ))}
        </div>
      ))}
    </nav>
  );
}

/** Below 640px: one button naming the open page; it opens every tab under its group's heading.
 * Closed by picking a tab, pressing the button again, `Esc` (focus back on the button) or a
 * click outside (sound-library D3). */
function TabMenu({ active }: { active: TabId }) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLElement>(null);
  const menuId = useId();
  const headingId = useId();

  const close = useCallback(() => setOpen(false), []);
  useDismiss(open, close, button, menu);
  const label = tabLabel(active);

  return (
    <div className="relative sm:hidden">
      <button
        ref={button}
        type="button"
        aria-label={`เมนู tab: ${label}`}
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((was) => !was)}
        className="flex min-h-11 items-center gap-2 rounded-xl border border-border bg-card px-3.5 py-2 text-sm leading-[1.5] font-semibold whitespace-nowrap text-brand"
      >
        <img src={menuIcon} alt="" width={16} height={16} />
        {label}
      </button>
      {open && (
        <nav
          ref={menu}
          id={menuId}
          aria-label="เมนู tab"
          className="absolute top-full left-0 z-20 mt-1 flex w-56 flex-col gap-0.5 rounded-xl border border-border bg-card p-[3px] shadow-sm"
        >
          {UNGROUPED.map((t) => (
            <TabLink key={t.id} tab={t} active={active} onClick={close} />
          ))}
          {GROUPED.map((group) => (
            <div
              key={group.id}
              role="group"
              aria-labelledby={`${headingId}-${group.id}`}
              className="flex flex-col gap-0.5 border-t border-border pt-1"
            >
              <p id={`${headingId}-${group.id}`} className="px-3.5 pt-1 text-xs leading-[1.5] font-medium text-mid">
                {group.label}
              </p>
              {group.tabs.map((t) => (
                <TabLink key={t.id} tab={t} active={active} onClick={close} />
              ))}
            </div>
          ))}
        </nav>
      )}
    </div>
  );
}

/** One tab: a plain `#/…` link, the open one highlighted (spoil-maker D53). */
function TabLink({ tab, active, onClick }: { tab: Tab; active: TabId; onClick?: () => void }) {
  const isActive = tab.id === active;
  return (
    <a
      href={tab.hash}
      aria-current={isActive ? "page" : undefined}
      onClick={onClick}
      // In the phone menu each item is a 44px touch target.
      className={`rounded-lg px-3.5 py-1.5 text-sm leading-[1.5] whitespace-nowrap ${onClick ? "flex min-h-11 items-center" : ""} ${
        isActive ? "bg-accent-subtle font-semibold text-brand" : "font-medium text-mid hover:bg-muted"
      }`}
    >
      {tab.label}
    </a>
  );
}
