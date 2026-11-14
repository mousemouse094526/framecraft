import { act, renderHook } from "@testing-library/react";
import { expect, test } from "vitest";
import { useReadyState } from "./useReadyState";

type State = { kind: "loading" } | { kind: "offline" } | { kind: "ready"; n: number };

function hookOf(initial: State) {
  const hook = renderHook(() => useReadyState<State>(initial));
  const state = () => hook.result.current[0];
  const [, setState, update] = hook.result.current;
  return { state, setState, update };
}

test("update changes a ready state", () => {
  const { state, update } = hookOf({ kind: "ready", n: 1 });

  act(() => update((s) => ({ ...s, n: s.n + 1 })));

  expect(state()).toEqual({ kind: "ready", n: 2 });
});

test("update leaves a state that isn't ready as it is", () => {
  const { state, setState, update } = hookOf({ kind: "loading" });

  act(() => update((s) => ({ ...s, n: 5 })));
  expect(state()).toEqual({ kind: "loading" });

  act(() => setState({ kind: "offline" }));
  act(() => update((s) => ({ ...s, n: 5 })));
  expect(state()).toEqual({ kind: "offline" });
});
