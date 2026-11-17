import { useCallback, useEffect, useId, useMemo, useRef, useState, type MouseEvent, type ReactNode, type Ref } from "react";
import { LIBRARY_ITEMS, LIBRARY_LABEL, locationOf, NAV_TOPICS, SETUP_ITEM, type NavItem } from "../../lib/nav";
import { useDismiss } from "../../lib/useDismiss";
import { tabLabel, useHash, type TabId } from "../../lib/useHash";
import { useMediaQuery } from "../../lib/useMediaQuery";
import { useRecent } from "../../lib/recent";
import menuIcon from "./assets/menu.svg";

type Props = {
  tab: TabId;
  /** A button at the right end of the header, such as Refresh. */
  action?: ReactNode;
  /** From 1024px the column is 1120px wide, for a page with two columns (spoil D25, D33). */
  wide?: boolean;
  children: ReactNode;
};

// Tailwind's `xl`: from here the menu is a sidebar pinned at the left, below it a drawer. Not `lg`:
// the pages switch to two columns at a 1024px window, and a 256px sidebar there would leave them
// 704px (ui-nav D11).
const PINNED = "(min-width: 1280px)";

const COLLAPSED_KEY = "framecraft.nav.collapsed";

/** Whether the user collapsed the pinned sidebar; anything but "true", or no storage, is open (ui-nav D4, D10). */
function readCollapsed(): boolean {
  try {
    return window.localStorage.getItem(COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

function writeCollapsed(collapsed: boolean) {
  try {
    if (collapsed) window.localStorage.setItem(COLLAPSED_KEY, "true");
    else window.localStorage.removeItem(COLLAPSED_KEY);
  } catch {
    // The sidebar just won't remember it.
  }
}

// The menu button of the page that mounted last, and whether a pick in the drawer still owes it the
// focus: after the pick the page may be a new one, and the focus goes to its button rather than
// falling to <body> (ui-nav D10).
let latestButton: HTMLButtonElement | null = null;
let refocus = false;

function takeRefocus(button: HTMLButtonElement | null) {
  if (!refocus || !button) return;
  refocus = false;
  button.focus();
}

/** The column every page sits in: the main menu, then the header (menu button, wordmark, where the
 * user is, the page's action) and the page's content (ui-nav D4, D6). */
export function PageLayout({ tab, action, wide = false, children }: Props) {
  const hash = useHash();
  const pinned = useMediaQuery(PINNED);
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [drawer, setDrawer] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const menu = useRef<HTMLElement>(null);
  const menuId = useId();
  const recent = useRecent();
  // ล่าสุด as menu items under their topic; a page under one (its `/cast`, `/renders`, …) opens it too (ui-nav D5, D11).
  const recentItems = useMemo(() => {
    const items: Partial<Record<TabId, NavItem[]>> = {};
    for (const [area, list] of Object.entries(recent)) items[area as TabId] = list.map(({ hash, label }) => ({ hash, label, prefix: true }));
    return items;
  }, [recent]);
  const { item, text } = locationOf(hash, tab, (topic) => recentItems[topic] ?? []);

  const drawerOpen = drawer && !pinned;
  const shown = pinned ? !collapsed : drawerOpen;

  const closeDrawer = useCallback(() => setDrawer(false), []);
  useDismiss(drawerOpen, closeDrawer, button, menu);

  // A new hash (a pick, or back and forward while the drawer is open) closes the drawer, and the
  // page that drew it takes the focus a pick owes (D10).
  useEffect(() => {
    setDrawer(false);
    takeRefocus(button.current);
  }, [hash]);

  // Crossing into the pinned width closes the drawer; the sidebar then follows its own setting.
  useEffect(() => {
    if (pinned) setDrawer(false);
  }, [pinned]);

  // An opened drawer takes the focus to the open item, or its first one.
  useEffect(() => {
    if (!drawerOpen) return;
    const target = menu.current?.querySelector<HTMLElement>('[aria-current="page"]') ?? menu.current?.querySelector<HTMLElement>("a");
    target?.focus();
  }, [drawerOpen]);

  const setButton = useCallback((element: HTMLButtonElement | null) => {
    if (element) latestButton = element;
    else if (latestButton === button.current) latestButton = null;
    button.current = element;
  }, []);

  const toggle = () => {
    if (!pinned) return setDrawer((was) => !was);
    setCollapsed((was) => {
      writeCollapsed(!was);
      return !was;
    });
  };

  const picked = (event: MouseEvent<HTMLAnchorElement>) => {
    if (pinned) return;
    setDrawer(false);
    if (event.currentTarget.hash === window.location.hash) {
      button.current?.focus();
      return;
    }
    // The hash moves after this click: the page that draws it takes the focus, or, when the leave is
    // declined and nothing draws, this fallback does.
    refocus = true;
    window.addEventListener("hashchange", () => setTimeout(() => takeRefocus(latestButton)), { once: true });
  };

  return (
    <div className="flex min-h-screen bg-muted">
      {drawerOpen && <div aria-hidden="true" className="fixed inset-0 z-20 bg-surface-inverse/40 xl:hidden" />}
      <MainMenu
        ref={menu}
        id={menuId}
        tab={tab}
        current={item}
        recent={recentItems}
        onPick={picked}
        className={`${collapsed ? "xl:hidden" : "xl:flex"} ${drawerOpen ? "max-xl:flex" : "max-xl:hidden"}`}
      />
      <main className={`min-w-0 flex-1 px-4 pt-6 pb-8 sm:px-6 sm:pt-12 sm:pb-20 ${wide ? "lg:px-8" : ""}`}>
        <div className={`mx-auto flex w-full max-w-[720px] flex-col gap-4 ${wide ? "lg:max-w-[1120px]" : ""}`}>
          {/* The header names the page; the heading is for screen readers. */}
          <h1 className="sr-only">{tabLabel(tab)}</h1>
          <header className="flex flex-wrap items-center gap-x-3 gap-y-1 pb-1">
            <button
              ref={setButton}
              type="button"
              aria-label={`เมนู: ${text}`}
              aria-expanded={shown}
              aria-controls={menuId}
              onClick={toggle}
              className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-border bg-card hover:bg-muted"
            >
              <img src={menuIcon} alt="" width={16} height={16} />
            </button>
            <Wordmark />
            <p className="order-last basis-full truncate text-sm leading-[1.5] font-medium text-mid sm:order-none sm:basis-auto">{text}</p>
            <div className="flex-1" />
            {/* Behind an open drawer only the menu button stays live (D10). */}
            <div inert={drawerOpen || undefined} className="contents">
              {action}
            </div>
          </header>
          <div inert={drawerOpen || undefined} className="flex flex-col gap-4">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

function Wordmark() {
  return (
    <p className="font-brand text-[26px] font-semibold tracking-[-0.78px] whitespace-nowrap text-brand">
      frame<span className="text-brand-accent">craft</span>
    </p>
  );
}

type MenuProps = {
  ref: Ref<HTMLElement>;
  id: string;
  tab: TabId;
  current: NavItem | null;
  recent: Partial<Record<TabId, NavItem[]>>;
  onPick: (event: MouseEvent<HTMLAnchorElement>) => void;
  className: string;
};

/** The main menu: ติดตั้ง, each topic under its heading with its items, then the libraries
 * (ui-nav D1–D3). One element for both widths: a sidebar from 1280px, a drawer below (D4, D11). */
function MainMenu({ ref, id, tab, current, recent, onPick, className }: MenuProps) {
  const headingId = useId();
  return (
    <nav
      ref={ref}
      id={id}
      aria-label="เมนูหลัก"
      className={`flex-col gap-1 overflow-y-auto border-border bg-card p-3 max-xl:fixed max-xl:inset-y-0 max-xl:left-0 max-xl:z-30 max-xl:w-[min(320px,85vw)] max-xl:shadow-lg xl:sticky xl:top-0 xl:h-screen xl:w-64 xl:shrink-0 xl:border-r ${className}`}
    >
      <MenuLink item={SETUP_ITEM} current={current === SETUP_ITEM} onPick={onPick} />
      {NAV_TOPICS.map((topic) => (
        <MenuGroup key={topic.id} id={`${headingId}-${topic.id}`} label={topic.label} current={tab === topic.id}>
          {topic.items.map((item) => (
            <MenuLink key={item.hash} item={item} current={current === item} onPick={onPick} />
          ))}
          {!!recent[topic.id]?.length && (
            <>
              <p className="px-3 pt-1.5 text-[11px] leading-[1.5] font-medium text-muted-foreground">ล่าสุด</p>
              {recent[topic.id]!.map((item) => (
                <MenuLink key={item.hash} item={item} current={current === item} onPick={onPick} />
              ))}
            </>
          )}
        </MenuGroup>
      ))}
      <MenuGroup id={`${headingId}-library`} label={LIBRARY_LABEL} current={false}>
        {LIBRARY_ITEMS.map((item) => (
          <MenuLink key={item.hash} item={item} current={current === item} onPick={onPick} />
        ))}
      </MenuGroup>
    </nav>
  );
}

/** A topic's heading and its items; the open topic's heading stands out (ui-nav D3, D6). */
function MenuGroup({ id, label, current, children }: { id: string; label: string; current: boolean; children: ReactNode }) {
  return (
    <div role="group" aria-labelledby={id} aria-current={current || undefined} className="mt-1 flex flex-col gap-0.5 border-t border-border pt-2">
      <p id={id} className={`px-3 pb-0.5 text-xs leading-[1.5] font-semibold ${current ? "text-brand" : "text-mid"}`}>
        {label}
      </p>
      {children}
    </div>
  );
}

/** One item: a plain `#/…` link, so the leave guard and the back button work as before (ui-nav D6). */
function MenuLink({ item, current, onPick }: { item: NavItem; current: boolean; onPick: MenuProps["onPick"] }) {
  const usesId = useId();
  return (
    <a
      href={item.hash}
      aria-current={current ? "page" : undefined}
      aria-describedby={item.uses ? usesId : undefined}
      onClick={onPick}
      // Below 1280px the drawer's items are 44px touch targets.
      className={`flex min-h-9 items-center gap-2 rounded-lg px-3 py-1.5 text-sm leading-[1.5] max-xl:min-h-11 ${
        current ? "bg-accent-subtle font-semibold text-brand" : "font-medium text-mid hover:bg-muted"
      }`}
    >
      {item.step !== undefined && (
        <span
          aria-hidden="true"
          className={`flex size-5 shrink-0 items-center justify-center rounded-full font-button text-[11px] font-bold ${
            current ? "bg-brand-accent text-card" : "border border-border text-muted-foreground"
          }`}
        >
          {item.step}
        </span>
      )}
      <span className="flex min-w-0 flex-col">
        <span className="truncate">{item.label}</span>
        {item.uses && <span id={usesId} aria-hidden="true" className="truncate text-xs font-normal text-muted-foreground">{item.uses}</span>}
      </span>
    </a>
  );
}
