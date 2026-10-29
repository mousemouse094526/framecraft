# react

**Kind:** library

**Version:** react 19.3.1, react-dom 19.3.1, @types/react 19.3.0

**Docs:** https://react.dev/llms.txt

## Best practices

- Mount with `createRoot` from `react-dom/client`; `ReactDOM.render` is removed — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- Fetching in an Effect needs a cleanup (an `ignore` flag) so a stale response cannot overwrite newer state — [useEffect](https://react.dev/reference/react/useEffect)
- List every reactive value the Effect reads; never omit the dependency array for a fetch that sets state — [useEffect](https://react.dev/reference/react/useEffect)
- In development Strict Mode runs setup → cleanup → setup, so a fetch Effect fires twice; the cleanup keeps it correct — [useEffect](https://react.dev/reference/react/useEffect)
- Use TypeScript props with default parameters; `defaultProps`/`propTypes` on function components are ignored — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- **Avoid:** suppressing the dependency linter — [useEffect](https://react.dev/reference/react/useEffect)

## Pattern

```tsx
type SetupStatus = { ready: boolean; steps: { name: string; ok: boolean }[] };

export function SetupStatusPage() {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    fetch("/api/setup/status")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: SetupStatus) => { if (!ignore) setStatus(data); })
      .catch((e: Error) => { if (!ignore) setError(e.message); });
    return () => { ignore = true; };
  }, []);

  if (error) return <p role="alert">{error}</p>;
  return status ? <p>{status.ready ? "Ready" : "Not ready"}</p> : <p>Loading…</p>;
}
```

Follows [useEffect: fetching data](https://react.dev/reference/react/useEffect).

## Traps

- `act` moved from `react-dom/test-utils` to `react`; other test-utils helpers throw — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- Render errors are no longer rethrown: uncaught go to `window.reportError`, caught to `console.error` (configure `onUncaughtError`/`onCaughtError` on `createRoot`) — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- Types: `useRef()` needs an argument; a ref callback's return value is treated as cleanup, so do not return implicitly; global `JSX` is now `React.JSX` — [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- 19.3 warns when `use` is called conditionally, and batches `resize`-event updates to the next frame — [React 19.3](https://react.dev/blog/2026/09/09/react-19-3)
- Install `@types/react-dom` too when typechecking `react-dom` imports (Testing Library also needs it) — [RTL releases v16.0.0](https://github.com/testing-library/react-testing-library/releases)

## Sources

- [useEffect](https://react.dev/reference/react/useEffect) — fetch pattern, cleanup, dependencies, Strict Mode (accessed 2026-10-29)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide) — removed APIs, `act`, error handling, type changes (accessed 2026-10-29)
- [React 19.3](https://react.dev/blog/2026/09/09/react-19-3) — features and behaviour changes in 19.3 (accessed 2026-10-29)
