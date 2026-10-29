# tailwindcss

**Kind:** library

**Version:** tailwindcss 4.3.3, @tailwindcss/vite 4.3.3

**Docs:** https://tailwindcss.com/docs

## Best practices

- With Vite, add `tailwindcss()` from `@tailwindcss/vite` to `plugins`; no PostCSS config needed — [Using Vite](https://tailwindcss.com/docs/installation/using-vite)
- One line replaces the old directives: `@import "tailwindcss";` — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- Define design tokens in `@theme` (`--color-*`, `--font-*`, `--radius-*`, …); each generates utilities and a CSS variable — [Theme variables](https://tailwindcss.com/docs/theme)
- Reset a namespace with `--color-*: initial;` before defining your own palette — [Theme variables](https://tailwindcss.com/docs/theme)
- Use `@theme inline` when a token references another variable; use `:root` for variables that should not make utilities — [Theme variables](https://tailwindcss.com/docs/theme)
- **Avoid:** `@layer utilities` for custom classes; use `@utility` — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)

## Pattern

```css
/* src/index.css */
@import "tailwindcss";

@theme {
  --color-ok: oklch(0.72 0.17 150);
  --color-fail: oklch(0.63 0.22 25);
  --font-sans: "Inter", sans-serif;
}
```

```tsx
<li className={step.ok ? "text-ok" : "text-fail"}>{step.name}</li>
```

Follows [Using Vite](https://tailwindcss.com/docs/installation/using-vite) and [Theme variables](https://tailwindcss.com/docs/theme).

## Traps

- `tailwind.config.js` is not auto-detected; load it with `@config` (no `corePlugins`, `safelist`) — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- Scales shifted: `shadow-sm`→`shadow-xs`, `shadow`→`shadow-sm` (same for `rounded`, `blur`); `outline-none`→`outline-hidden`; `ring` is 1px — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- Border and ring colours default to `currentColor`; buttons get `cursor: default`; `hover:` applies only on hover-capable devices — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- Syntax: variable shorthand is `bg-(--x)`, important is a suffix `bg-red-500!`, stacked variants read left to right — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- `@theme` variables must be top-level (not inside selectors or media queries) — [Theme variables](https://tailwindcss.com/docs/theme)
- `node_modules` is not scanned for classes by default since 4.1; use `@source` to add paths — [Changelog](https://github.com/tailwindlabs/tailwindcss/blob/main/CHANGELOG.md)
- `text-sm`, `text-xs` and the other size utilities also set `line-height` (`text-sm` → 20px), which beats a `leading-*` inherited from a parent; put `leading-*` on the same element, or use `text-sm/[1.5]` — [font-size](https://tailwindcss.com/docs/font-size)
- Needs Safari 16.4+, Chrome 111+, Firefox 128+; Vite 8 support landed in 4.2.2 — [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide), [Changelog](https://github.com/tailwindlabs/tailwindcss/blob/main/CHANGELOG.md)

## Sources

- [font-size](https://tailwindcss.com/docs/font-size) — size utilities set a line-height too (accessed 2026-10-29)
- [Installing with Vite](https://tailwindcss.com/docs/installation/using-vite) — plugin and CSS import (accessed 2026-10-29)
- [Theme variables](https://tailwindcss.com/docs/theme) — `@theme`, namespaces, `inline`, constraints (accessed 2026-10-29)
- [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide) — v3 → v4 breaking changes (accessed 2026-10-29)
- [Changelog](https://github.com/tailwindlabs/tailwindcss/blob/main/CHANGELOG.md) — 4.1–4.3 changes, Vite 8 support (accessed 2026-10-29)
