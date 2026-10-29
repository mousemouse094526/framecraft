import { useEffect, useState } from "react";

// The top tabs and their hashes, in the order the tab bar shows them (spoil D10).
export const TABS = [
  { id: "spoil", label: "สปอย", hash: "#/spoil" },
  { id: "setup", label: "Setup status", hash: "#/setup" },
] as const;

export type TabId = (typeof TABS)[number]["id"];

/** An empty or unknown hash opens Setup status (spoil D10). */
function tabFromHash(hash: string): TabId {
  return TABS.find((tab) => tab.hash === hash)?.id ?? "setup";
}

/**
 * Which top tab is open. The tabs are plain `#/…` links, so clicking one and
 * the browser's back button both change the hash; this only follows it.
 */
export function useHashTab(): TabId {
  const [tab, setTab] = useState(() => tabFromHash(window.location.hash));

  useEffect(() => {
    const follow = () => setTab(tabFromHash(window.location.hash));
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return tab;
}
