# Testing

**Owns:** proving UI behaviour with Vitest and React Testing Library.

**Must not:** hit a real backend.

## Shape

```tsx
vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(readyStatus)));
render(<SetupStatusPage />);
expect(await screen.findByText("พร้อมใช้งาน")).toBeInTheDocument();
```

## Rules

- Runner: `npm --prefix frontend test`. Tests sit beside the component as `*.test.tsx`.
- Query by visible text or role, the way the user sees it.
- No browser e2e tool yet; the Vite proxy is checked by hand per the spec.
- Typecheck: `npm --prefix frontend run typecheck`; build: `npm --prefix frontend run build`.
- A pending request is a `new Promise(() => {})` or a deferred you resolve
  inside `act`; timeouts use `vi.useFakeTimers()` and `vi.advanceTimersByTime`.

## Good examples

- [SetupStatusPage.test.tsx](../../../../frontend/src/features/setup-status/components/SetupStatusPage.test.tsx) — `vi.stubGlobal("fetch", ...)`, a `statusOf(items)` builder, rows found by `getByRole("listitem", { name })`.
