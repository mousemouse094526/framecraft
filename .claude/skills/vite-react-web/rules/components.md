# Components

**Owns:** rendering a feature's states and wiring user actions to its hook.

**Must not:** call `fetch` directly; hold request logic.

## Shape

```tsx
export function SetupStatusPage() {
  const { state, refresh } = useSetupStatus();
  if (state.kind === "loading") return <p>กำลังเช็ค…</p>;
  // ...
}
```

## Rules

- Model screen states as one discriminated union (`loading`, `result`,
  `refreshing`, `offline`), not separate booleans.
- Follow the screen's Figma frame when spec › Design has one.

## Good examples

- None yet — the first ticket that touches this layer sets it.
