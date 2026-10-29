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
- Icons and images exported from Figma live in `features/{feature}/assets/`
  and are used as `<img>` with the SVG's own `width` and `height`.
- Colors and fonts come from the `@theme` tokens in `src/index.css`
  (`bg-muted`, `text-destructive`, `font-mono`); no hex values in components.
- Mobile first: the base classes are the 375px frame, `sm:` the desktop one.

## Good examples

- [SetupStatusPage.tsx](../../../../frontend/src/features/setup-status/components/SetupStatusPage.tsx) — switches on `state.kind`, one branch per screen state.
- [useSetupStatus.ts](../../../../frontend/src/features/setup-status/hooks/useSetupStatus.ts) — the state union and the API types live with the hook that fetches them.
