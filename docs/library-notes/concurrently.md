# concurrently

**Kind:** runtime

**Version:** 10.0.6

**Docs:** https://github.com/open-cli-tools/concurrently

## Best practices

- Quote each command; in `package.json` escape double quotes (`\"`), which are the only quotes Windows accepts — [README](https://github.com/open-cli-tools/concurrently)
- Name commands with `-n a,b` (comma separated); the prefix then shows the name instead of the index — [Prefixing](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/prefixing.md)
- `-k` / `--kill-others` stops the rest when any command exits, whatever its code; `--kill-others-on-fail` only on non-zero — [Terminating](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/terminating.md)
- Add `--kill-timeout <ms>` so a process that ignores `SIGTERM` is `SIGKILL`ed — [Terminating](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/terminating.md)
- **Avoid:** `-r`/`--raw` when you need to tell outputs apart; it drops prefixes and colours — [CLI options](https://github.com/open-cli-tools/concurrently/blob/main/bin/index.ts)

## Pattern

```json
{
  "scripts": {
    "dev": "concurrently -k -n api,web \"uv run uvicorn backend.app:app --host 127.0.0.1 --port 8000\" \"npm --prefix frontend run dev\""
  }
}
```

Follows [Prefixing](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/prefixing.md) and [Terminating](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/terminating.md).

## Traps

- v10 is ESM-only and needs Node 22+ — [v10.0.0 release](https://github.com/open-cli-tools/concurrently/releases/tag/v10.0.0)
- v10 removed `--name-separator` (commas only) and the API `killOthers` option (use `killOthersOn`) — [v10.0.0 release](https://github.com/open-cli-tools/concurrently/releases/tag/v10.0.0)
- v10 prefix colours default to automatic instead of `reset` — [v10.0.0 release](https://github.com/open-cli-tools/concurrently/releases/tag/v10.0.0)
- The overall exit code is set by `-s` / `--success` (`first`, `last`, `all`, `command-{name}`, `!`-prefixed to exclude) — [CLI options](https://github.com/open-cli-tools/concurrently/blob/main/bin/index.ts)
- stdin is not forwarded unless `-i` / `--handle-input` — [CLI options](https://github.com/open-cli-tools/concurrently/blob/main/bin/index.ts)

## Sources

- [README](https://github.com/open-cli-tools/concurrently) — quoting, API options (accessed 2026-10-29)
- [Prefixing](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/prefixing.md) — `-n`, `-p`, `-c` (accessed 2026-10-29)
- [Terminating](https://github.com/open-cli-tools/concurrently/blob/main/docs/cli/terminating.md) — kill flags (accessed 2026-10-29)
- [CLI options (bin/index.ts)](https://github.com/open-cli-tools/concurrently/blob/main/bin/index.ts) — aliases `-k`, `-s`, `-r`, `-i` (accessed 2026-10-29)
- [v10.0.0 release](https://github.com/open-cli-tools/concurrently/releases/tag/v10.0.0) — breaking changes (accessed 2026-10-29)
