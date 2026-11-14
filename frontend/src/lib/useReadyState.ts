import { useCallback } from "react";
import { useMountedState } from "./useMountedState";

type Ready<S> = Extract<S, { kind: "ready" }>;

/**
 * A page's state with `[state, setState, update]`. `setState` is `useMountedState`'s
 * `setIfMounted`: it sets a whole state (e.g. after a read) and drops it once the component
 * is gone. `update` changes the `ready` state only and leaves `loading`, `offline` and the
 * rest as they are. Every hook of การ์ตูนเล่า and คลังเสียง with a `ready` state uses it (toon D65).
 */
export function useReadyState<S extends { kind: string }>(initial: S) {
  const [state, , setIfMounted] = useMountedState<S>(initial);

  const update = useCallback(
    (change: (s: Ready<S>) => S) => setIfMounted((s) => (s.kind === "ready" ? change(s as Ready<S>) : s)),
    [setIfMounted],
  );

  return [state, setIfMounted, update] as const;
}
