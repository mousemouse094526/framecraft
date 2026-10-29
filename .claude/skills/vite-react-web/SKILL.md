---
name: vite-react-web
description: >-
  How framecraft's web UI (frontend/) is structured and written: Vite, React,
  TypeScript, Tailwind CSS, Vitest with React Testing Library. Use whenever
  writing, moving, or reviewing code under frontend/.
---

# Vite React web

The local UI. It only talks to the backend through `/api` (Vite proxy to
127.0.0.1:8000, ADR 0001).

## Folder structure

```
frontend/src/
├── main.tsx
├── App.tsx
├── features/[feature]/
│   ├── components/   ← UI for this feature, *.test.tsx beside each
│   └── hooks/        ← data fetching and state (calls lib/api)
├── components/ui/    ← shared once a second user exists: PageLayout (wordmark,
│                        tab bar, action; `wide` = 1120px from lg for two
│                        columns), OfflinePanel, RefreshButton
└── lib/
    ├── api.ts        ← getJson / sendJson, both with the 30 s timeout
    ├── statusTypes.ts← GET /api/setup/status types; both tabs read them
    ├── useHashTab.ts ← which top tab is open, from the URL hash
    └── useMountedState.ts ← useState that drops answers after unmount; every fetching hook
```

No router library and no `routes/`: `App` picks the page from the hash
(`#/spoil`, `#/setup`, spoil D10). Each page wraps itself in `PageLayout`,
whose tabs are plain `#/…` links, so clicks and the back button both just
change the hash.

## Flow

App → feature component → hook → lib/api → `/api/...`

## Where shared code goes

- Code one feature uses lives in that feature.
- A second user appears → move it to `components/ui/` or a top-level folder
  named for its kind, in the same change.

## Never break

- Every backend call goes through `lib/api.ts` with a timeout.
- UI text is Thai.
- Styling is Tailwind classes; no separate CSS files except the Tailwind entry.

## Rules by layer

| File | Covers |
|---|---|
| [rules/components.md](rules/components.md) | feature components and states |
| [rules/testing.md](rules/testing.md) | Vitest, RTL, fetch fakes |

A layer with no rules file → stop and ask before writing it.
