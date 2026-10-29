# testing-library

**Kind:** library

**Version:** @testing-library/react 16.3.3, @testing-library/jest-dom 7.0.1, @testing-library/user-event 14.6.8

**Docs:** https://testing-library.com/docs/

## Best practices

- Install `@testing-library/dom` (and `@types/react-dom` for TS) yourself; both are peer dependencies since RTL 16 and jest-dom 7 — [RTL releases](https://github.com/testing-library/react-testing-library/releases), [jest-dom releases](https://github.com/testing-library/jest-dom/releases)
- Register matchers in a Vitest setup file with `import "@testing-library/jest-dom/vitest"`; name it `.ts` and include it in the tsconfig — [jest-dom README](https://github.com/testing-library/jest-dom)
- Auto cleanup needs a global `afterEach`; without `globals: true`, call `cleanup()` in `afterEach` in the setup file — [RTL setup](https://testing-library.com/docs/react-testing-library/setup)
- Create a `user = userEvent.setup()` and `await` its methods; the direct `userEvent.click` API is for migration — [user-event setup](https://testing-library.com/docs/user-event/setup)
- With fake timers pass `advanceTimers` to `setup()` (Vitest: `vi.advanceTimersByTime`) — [user-event options](https://testing-library.com/docs/user-event/options)
- **Avoid:** `delay: null` to dodge fake-timer timeouts — [user-event options](https://testing-library.com/docs/user-event/options)

## Pattern

```ts
// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
afterEach(() => cleanup());
```

```tsx
it("shows a retry button on error", async () => {
  vi.useFakeTimers();
  const user = userEvent.setup({ advanceTimers: (ms) => { vi.advanceTimersByTime(ms); } });
  vi.stubGlobal("fetch", vi.fn(async () => new Response(null, { status: 500 })));
  render(<SetupStatusPage />);
  await vi.advanceTimersByTimeAsync(0);
  expect(screen.getByRole("alert")).toHaveTextContent("HTTP 500");
  await user.click(screen.getByRole("button", { name: /retry/i }));
});
```

Follows [RTL setup](https://testing-library.com/docs/react-testing-library/setup) and [user-event options](https://testing-library.com/docs/user-event/options).

## Traps

- `waitFor`/`findBy*` default to a 1000 ms timeout and 50 ms interval, and only advance Jest fake timers; under Vitest fake timers advance time yourself — [Async methods](https://testing-library.com/docs/dom-testing-library/api-async), [helpers.ts](https://github.com/testing-library/dom-testing-library/blob/main/src/helpers.ts)
- Flush pending timers before switching back to real timers in `afterEach` — [Using fake timers](https://testing-library.com/docs/using-fake-timers)
- `userEvent.setup()` replaces `navigator.clipboard` with a stub — [user-event setup](https://testing-library.com/docs/user-event/setup)
- jest-dom 7 requires Node 22+; `toContainAnyBy*`/`toContainOneBy*` are new — [jest-dom releases](https://github.com/testing-library/jest-dom/releases)
- Import `act` from `react`, not `react-dom/test-utils` — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)

## Sources

- [RTL setup](https://testing-library.com/docs/react-testing-library/setup) — cleanup with Vitest (accessed 2026-10-29)
- [RTL releases](https://github.com/testing-library/react-testing-library/releases) — v16 peer deps, React 19 support (accessed 2026-10-29)
- [jest-dom README](https://github.com/testing-library/jest-dom) and [releases](https://github.com/testing-library/jest-dom/releases) — Vitest import, v7 changes (accessed 2026-10-29)
- [user-event setup](https://testing-library.com/docs/user-event/setup) and [options](https://testing-library.com/docs/user-event/options) — `setup()`, `advanceTimers`, `delay` (accessed 2026-10-29)
- [Async methods](https://testing-library.com/docs/dom-testing-library/api-async), [Using fake timers](https://testing-library.com/docs/using-fake-timers), [helpers.ts](https://github.com/testing-library/dom-testing-library/blob/main/src/helpers.ts) — `waitFor` and fake timers (accessed 2026-10-29)
