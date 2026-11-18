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
- A hook or `lib/` helper that several hooks share gets its own test beside it as `*.test.ts`: a hook through `renderHook`, a request through `testBackend` (toon D65).
- Query by visible text or role, the way the user sees it.
- The tabs' tests answer `fetch` through `src/testing/testBackend.ts` (`serve`, `get`, `send`, `phased`, `sent`); a new test uses it, not a copy.
- Backend state that a user action causes (a job that starts on a POST) changes inside that request's `reply`, never in a test line before the click: a page that loads late would see it first and lock the button the test clicks (ui-nav bug 2026-11-17).
- What an answered request or a `useEffect` changes (text, `disabled`, focus, `localStorage`, a menu closing) is asserted with `findBy…` or `waitFor` after the `await` that started it, never with `getBy…` on the next line: `await user.click`, `findBy…` of something else, and a poll's `advanceTimersByTimeAsync` all return before React runs that work, and the gap only shows under load (reels-only bug 2026-11-18). A listener on `window` that a test fires at once goes in `useLayoutEffect`, so it is on in the commit that shows its element.
- An `Alert` (role `status`) is found by the text it shows with `src/testing/statusBox.findStatusWith`, not by walking up from the text; its tone is its Tailwind class (jsdom has no colour, toon D72).
- An upload (`sendFile`) is answered by `src/testing/fakeXhr.ts`: `vi.stubGlobal("XMLHttpRequest", FakeXhr)`, then fire `progress`, `allSent`, `respond`, `fail` from the test.
- Media with no role (`<video>`, a decorative `<img alt="">` thumbnail) and the hidden `<input type="file">` behind a pick button (`user.upload` needs it) are the exceptions: find its row by role, then `querySelector` inside it. Counting it on the whole page is allowed only to prove there is no other one (one player, or none).
- jsdom has no playback, layout or `confirm`: stub `HTMLMediaElement.prototype.load` (and `play`, resolved, when the code calls it), `Element.prototype.scrollIntoView` and `confirm` per test (docs/library-notes/vitest.md). `currentTime` is a plain property there, so a seek can be asserted.
- No browser e2e tool yet: a ticket's `(e2e)` criteria are Vitest tests through `App` with the fake backend (story-kb D18); the Vite proxy and the look are checked by hand.
- Typecheck: `npm --prefix frontend run typecheck`; build: `npm --prefix frontend run build`.
- A pending request is a `new Promise(() => {})` or a deferred you resolve
  inside `act`; timeouts use `vi.useFakeTimers()` and `vi.advanceTimersByTime`.

## Good examples

- [SetupStatusPage.test.tsx](../../../../frontend/src/features/setup-status/components/SetupStatusPage.test.tsx) — `vi.stubGlobal("fetch", ...)`, a `statusOf(items)` builder, rows found by `getByRole("listitem", { name })`.
