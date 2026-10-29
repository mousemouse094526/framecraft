# vitest

**Kind:** library

**Version:** vitest 5.0.5, jsdom 30.1.3

**Docs:** https://vitest.dev/llms.txt

## Best practices

- Put a `test` block in `vite.config.ts`; with `defineConfig` from `vite`, add `/// <reference types="vitest/config" />` — [Config](https://vitest.dev/config/)
- Set `environment: "jsdom"` (default is `node`) and install `jsdom` yourself — [environment](https://vitest.dev/config/environment)
- `setupFiles` run before each test file, resolved from `root`; their exports are ignored — [setupFiles](https://vitest.dev/config/setupfiles)
- Stub `fetch` with `vi.stubGlobal`, and undo with `vi.unstubAllGlobals()` (or `unstubGlobals: true`) — [vi API](https://vitest.dev/api/vi), [unstubGlobals](https://vitest.dev/config/unstubglobals)
- With fake timers, prefer the async forms (`advanceTimersByTimeAsync`, `runOnlyPendingTimersAsync`) so promise callbacks between timers run — [vi API](https://vitest.dev/api/vi)
- **Avoid:** a separate `vitest.config.*` next to `vite.config.*`; it wins and the Vite config is ignored — [Config](https://vitest.dev/config/)

## Pattern

```ts
/// <reference types="vitest/config" />
export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], unstubGlobals: true },
});

// SetupStatusPage.test.tsx
it("polls status", async () => {
  vi.useFakeTimers();
  vi.stubGlobal("fetch", vi.fn(async () => Response.json({ ready: true, steps: [] })));
  render(<SetupStatusPage />);
  await vi.advanceTimersByTimeAsync(2000);
  expect(fetch).toHaveBeenCalledWith("/api/setup/status");
  vi.useRealTimers();
});
```

Follows [Config](https://vitest.dev/config/) and [vi API](https://vitest.dev/api/vi).

## Traps

- `vi.useFakeTimers()` fakes everything except `nextTick` and `queueMicrotask`; time does not move unless `shouldAdvanceTime: true` — [fakeTimers](https://vitest.dev/config/faketimers)
- Fake timers stay on until `vi.useRealTimers()`; restore in `afterEach` or they leak into later tests — [vi API](https://vitest.dev/api/vi)
- Testing Library's `waitFor`/`findBy*` only auto-advance Jest fake timers (it checks a global `jest`), so under Vitest fake timers they poll on a frozen clock; advance time with `vi.advanceTimersByTimeAsync` instead — [dom-testing-library helpers](https://github.com/testing-library/dom-testing-library/blob/main/src/helpers.ts)
- v5: `clearMocks` defaults to `true`; `vi.mock`/`vi.hoisted` inside functions throw; unawaited `resolves`/`rejects` fail; `toThrow('')` matches anything — [Migration to 5.0](https://vitest.dev/guide/migration)
- v5: needs Vite ≥ 6.4 and Node ≥ 22.12; Vite is a peer dependency; config files are no longer searched in parent folders — [Migration to 5.0](https://vitest.dev/guide/migration)
- `globals` are off unless set; with TS 7 `types: []`, add `vitest/globals` only if `globals: true` — [Config](https://vitest.dev/config/), [TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- jsdom 30 needs Node `^22.22.2 || ^24.15.0 || >=26` — [jsdom releases](https://github.com/jsdom/jsdom/releases)
- jsdom 30 has no media playback or layout: `HTMLMediaElement.load/play/pause` and `window.confirm` log "Not implemented", and `Element.scrollIntoView` is missing. Stub them per test (`vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {})`, `vi.stubGlobal("confirm", ...)`, assign `Element.prototype.scrollIntoView = vi.fn()`) — [jsdom README › Unimplemented parts](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform)

## Sources

- [Config reference](https://vitest.dev/config/) — `test` in Vite config, priority of config files (accessed 2026-10-29)
- [environment](https://vitest.dev/config/environment) — jsdom setup (accessed 2026-10-29)
- [setupFiles](https://vitest.dev/config/setupfiles) — when setup runs (accessed 2026-10-29)
- [vi API](https://vitest.dev/api/vi) — `stubGlobal`, fake timer methods (accessed 2026-10-29)
- [fakeTimers](https://vitest.dev/config/faketimers) and [unstubGlobals](https://vitest.dev/config/unstubglobals) — defaults (accessed 2026-10-29)
- [Migrating to Vitest 5.0](https://vitest.dev/guide/migration) — v5 breaking changes (accessed 2026-10-29)
- [jsdom releases](https://github.com/jsdom/jsdom/releases) — Node minimum for 30.x (accessed 2026-10-29)
- [jsdom README](https://github.com/jsdom/jsdom#unimplemented-parts-of-the-web-platform) — no media playback, layout, or `confirm`; checked against jsdom 30.1.3 source (accessed 2026-10-29)
