# vite

**Kind:** runtime

**Version:** vite 8.3.5, @vitejs/plugin-react 6.1.2

**Docs:** https://vite.dev/llms.txt

## Best practices

- Write `vite.config.ts` with `defineConfig` (or `satisfies UserConfig`); it is bundled with Rolldown before loading — [Configuring Vite](https://vite.dev/config/)
- `server.proxy` keys are path prefixes (a leading `^` makes a RegExp); the string form keeps the path, so `/api/x` → `<target>/api/x` — [Server Options](https://vite.dev/config/server-options)
- Use the object form (`target`, `changeOrigin`, `rewrite`) only when the path or Host must change — [Server Options](https://vite.dev/config/server-options)
- `.env*` files are not in `process.env` while the config runs; use `loadEnv(mode, process.cwd(), '')` in a function config if needed — [Configuring Vite](https://vite.dev/config/)
- Vite does not type-check; run `tsc` separately and add `vite/client` to `types` — [Features](https://vite.dev/guide/features#typescript)
- **Avoid:** `rewriteWsOrigin`; it can leave the proxy open to CSRF — [Server Options](https://vite.dev/config/server-options)

## Pattern

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
```

Follows [Server Options](https://vite.dev/config/server-options).

## Traps

- Vite 8 replaces esbuild + Rollup with Rolldown + Oxc; `esbuild`, `optimizeDeps.esbuildOptions` and `build.rollupOptions` are deprecated aliases for `oxc`, `optimizeDeps.rolldownOptions`, `build.rolldownOptions` — [Migration from v7](https://vite.dev/guide/migration)
- CSS is minified by Lightning CSS by default; object-form `manualChunks` is removed — [Migration from v7](https://vite.dev/guide/migration)
- Default `build.target` is now Chrome 111 / Firefox 114 / Safari 16.4 — [Migration from v7](https://vite.dev/guide/migration)
- `server.hmr` options were renamed to `server.ws` in 8.1 — [Vite changelog](https://github.com/vitejs/vite/blob/main/packages/vite/CHANGELOG.md)
- plugin-react 6 needs Vite 8; the `babel` option is removed (use `@rolldown/plugin-babel`) — [plugin-react changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md)
- If the port is busy Vite silently picks the next one unless `strictPort: true`; `localhost` may resolve differently in Node and the browser — [Server Options](https://vite.dev/config/server-options)
- Node 20.19+ or 22.12+ required — [Announcing Vite 8](https://vite.dev/blog/announcing-vite8)

## Sources

- [Server Options](https://vite.dev/config/server-options) — `proxy`, `host`, `port`, `strictPort` (accessed 2026-10-29)
- [Configuring Vite](https://vite.dev/config/) — config file loading, `loadEnv` (accessed 2026-10-29)
- [Migration from v7](https://vite.dev/guide/migration) — Vite 8 breaking changes (accessed 2026-10-29)
- [Announcing Vite 8](https://vite.dev/blog/announcing-vite8) — Node versions, Rolldown, plugin-react v6 (accessed 2026-10-29)
- [Vite changelog](https://github.com/vitejs/vite/blob/main/packages/vite/CHANGELOG.md) — 8.1–8.3 changes (accessed 2026-10-29)
- [plugin-react changelog](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/CHANGELOG.md) — v5/v6 breaking changes (accessed 2026-10-29)
- [Features: TypeScript](https://vite.dev/guide/features#typescript) — transpile-only, client types (accessed 2026-10-29)
