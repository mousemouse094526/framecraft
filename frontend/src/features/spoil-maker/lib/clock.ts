/** Seconds from `h:mm:ss`, `m:ss` or `s` as a person types an EP's cut; null for anything else. */
export function parseClock(text: string): number | null {
  const parts = text.trim().split(":");
  if (parts.length > 3 || !parts.every((part) => /^\d+$/.test(part))) return null;
  return parts.reduce((seconds, part) => seconds * 60 + Number(part), 0);
}
