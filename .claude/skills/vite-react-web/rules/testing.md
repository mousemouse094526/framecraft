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

## Good examples

- None yet — the first ticket that touches this layer sets it.
