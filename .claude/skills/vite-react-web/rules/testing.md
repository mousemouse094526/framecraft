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
- The tabs' tests answer `fetch` through `src/testing/testBackend.ts` (`serve`, `get`, `send`, `phased`, `sent`); a new test uses it, not a copy.
- Media with no role (`<video>`, a decorative `<img alt="">` thumbnail) and the hidden `<input type="file">` behind a pick button (`user.upload` needs it) are the exceptions: find its row by role, then `querySelector` inside it. Counting it on the whole page is allowed only to prove there is no other one (one player, or none).
- jsdom has no playback, layout or `confirm`: stub `HTMLMediaElement.prototype.load` (and `play`, resolved, when the code calls it), `Element.prototype.scrollIntoView` and `confirm` per test (docs/library-notes/vitest.md). `currentTime` is a plain property there, so a seek can be asserted.
- No browser e2e tool yet: a ticket's `(e2e)` criteria are Vitest tests through `App` with the fake backend (story-kb D18); the Vite proxy and the look are checked by hand.
- Typecheck: `npm --prefix frontend run typecheck`; build: `npm --prefix frontend run build`.
- A pending request is a `new Promise(() => {})` or a deferred you resolve
  inside `act`; timeouts use `vi.useFakeTimers()` and `vi.advanceTimersByTime`.

## Good examples

- [SetupStatusPage.test.tsx](../../../../frontend/src/features/setup-status/components/SetupStatusPage.test.tsx) — `vi.stubGlobal("fetch", ...)`, a `statusOf(items)` builder, rows found by `getByRole("listitem", { name })`.
