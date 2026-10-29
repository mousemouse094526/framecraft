import type { ReactNode } from "react";
import { TABS, type TabId } from "../../lib/useHashTab";

type Props = {
  tab: TabId;
  /** A button at the right end of the header, such as Refresh. */
  action?: ReactNode;
  children: ReactNode;
};

/** The column every tab sits in: wordmark, tab bar, the tab's action, then its content. */
export function PageLayout({ tab, action, children }: Props) {
  return (
    <main className="min-h-screen bg-muted px-4 pt-6 pb-8 sm:px-0 sm:pt-16 sm:pb-20">
      <div className="mx-auto flex w-full max-w-[720px] flex-col gap-4">
        {/* The open tab names the page; the tab bar shows it, so the heading is for screen readers. */}
        <h1 className="sr-only">{TABS.find((t) => t.id === tab)?.label}</h1>
        {/* 375px frame 13: wordmark and action on one row, tabs below; desktop: one row. */}
        <header className="flex flex-wrap items-center gap-3 pb-1">
          <Wordmark />
          <div className="hidden h-5 w-px bg-border sm:block" />
          <div className="order-last basis-full sm:order-none sm:basis-auto">
            <TabBar active={tab} />
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

function TabBar({ active }: { active: TabId }) {
  return (
    <nav className="flex w-fit gap-0.5 rounded-xl border border-border bg-card p-[3px]">
      {TABS.map((tab) => {
        const isActive = tab.id === active;
        return (
          <a
            key={tab.id}
            href={tab.hash}
            aria-current={isActive ? "page" : undefined}
            className={`rounded-lg px-3.5 py-1.5 text-sm leading-[1.5] whitespace-nowrap ${
              isActive ? "bg-accent-subtle font-semibold text-brand" : "font-medium text-mid hover:bg-muted"
            }`}
          >
            {tab.label}
          </a>
        );
      })}
    </nav>
  );
}
