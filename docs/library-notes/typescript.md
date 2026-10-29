# typescript

**Kind:** language

**Version:** 7.0.2 (native Go port; `strict: true`; typecheck with `tsc --noEmit` / `tsc -b`)

**Docs:** https://www.typescriptlang.org/docs/

## Best practices

- Install `typescript`; it ships the native `tsc` binary, so `tsc` scripts keep working — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- List global type packages in `compilerOptions.types` (e.g. `vite/client`); the default is now `[]` — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- Use `moduleResolution: "bundler"` (or `nodenext`) with `module: "esnext"` — [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)
- Vite only transpiles: set `isolatedModules: true`, and run `tsc --noEmit` (or `--watch`) as a separate step — [Vite Features](https://vite.dev/guide/features#typescript)
- **Avoid:** `const enum` and implicit type-only imports; the Oxc transform has no type info — [Vite Features](https://vite.dev/guide/features#typescript)

## Pattern

```jsonc
// tsconfig for the browser app
{
  "compilerOptions": {
    "strict": true,
    "target": "es2022",
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "isolatedModules": true,
    "noEmit": true,
    "skipLibCheck": true,
    "types": ["vite/client"],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

Follows [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) and [Vite Features](https://vite.dev/guide/features#typescript).

## Traps

- Hard errors in 7.0: `baseUrl`, `moduleResolution` `node`/`node10`/`classic`, `target: es5`, `downlevelIteration`, `module` `amd`/`umd`/`systemjs`/`none`, `outFile`, and setting `esModuleInterop`, `allowSyntheticDefaultImports` or `alwaysStrict` to `false` — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- Without `baseUrl`, `paths` entries must be relative (`./src/*`) — [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/)
- New defaults: `strict: true`, `module: esnext`, `noUncheckedSideEffectImports: true`, `rootDir: ./`, `types: []` (so `vitest/globals`, jest-dom types etc. must be listed or imported) — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- `tsc file.ts` errors when a `tsconfig.json` is present; pass `--ignoreConfig` or use `-p` — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- No stable programmatic API in 7.0; tools that embed TypeScript may need `@typescript/typescript6` (`tsc6`) — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- `--checkers`, `--builders` (parallel `-b`) are experimental; `--singleThreaded` turns parallelism off — [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)

## Sources

- [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) — install, removed options, defaults, flags, API status (accessed 2026-10-29)
- [Announcing TypeScript 6.0](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/) — deprecations removed in 7.0, `baseUrl` migration (accessed 2026-10-29)
- [Vite Features: TypeScript](https://vite.dev/guide/features#typescript) — transpile-only, `isolatedModules`, `vite/client` types (accessed 2026-10-29)
