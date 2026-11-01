import { useEffect, useState } from "react";

// The top tabs and their hashes, in the order the tab bar shows them (spoil-maker D53).
export const TABS = [
  { id: "setup", label: "ติดตั้ง", hash: "#/setup" },
  { id: "clips", label: "คลิป", hash: "#/clips" },
  { id: "spoil", label: "สปอย", hash: "#/spoil" },
] as const;

export type TabId = (typeof TABS)[number]["id"];

/** `#/spoil/…` is a step of สปอย; an empty or unknown hash opens ติดตั้ง (spoil D10, spoil-maker D53). */
export function tabOf(hash: string): TabId {
  if (hash.startsWith("#/spoil/")) return "spoil";
  return TABS.find((tab) => tab.hash === hash)?.id ?? "setup";
}

/**
 * The URL hash, kept current. The tabs and steps are plain `#/…` links, so
 * clicking one and the browser's back button both change the hash; this only follows it.
 */
export function useHash(): string {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const follow = () => setHash(window.location.hash);
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  return hash;
}
