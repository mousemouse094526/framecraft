/** The two states every fetching hook starts in or falls back to. */
type Unsettled = { kind: "loading" } | { kind: "offline" };

/** Each of the states with `loading` and `offline` taken out. */
type Settled<States extends readonly { kind: string }[]> = { [I in keyof States]: Exclude<States[I], Unsettled> };

/**
 * True when no hook is `loading` or `offline`. It narrows the tuple itself, so read the
 * states out of it afterwards to see each one narrowed.
 */
export function allSettled<States extends readonly { kind: string }[]>(states: States): states is States & Settled<States> {
  return states.every((one) => one.kind !== "loading" && one.kind !== "offline");
}
