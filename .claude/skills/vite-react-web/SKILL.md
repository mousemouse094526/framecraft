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
├── features/[feature]/   ← spoil (คลิป tab), spoil-maker (สปอย tab), setup-status
│   ├── components/   ← UI for this feature, *.test.tsx beside each
│   ├── hooks/        ← data fetching and state (calls lib/api)
│   └── lib/          ← plain modules the hooks share, no React (spoil D35)
├── components/ui/    ← shared once a second user exists: PageLayout (wordmark,
│                        tab bar, action; `wide` = 1120px from lg for two
│                        columns), OfflinePanel, RefreshButton, ProgressBar,
│                        Alert (the Figma toned box), buttonStyles
└── lib/
    ├── api.ts        ← getJson / sendJson, both with the 30 s timeout
    ├── statusTypes.ts← GET /api/setup/status types; both tabs read them
    ├── useHash.ts    ← the URL hash (`useHash`) and which top tab it opens (`tabOf`)
    ├── useMountedState.ts ← useState that drops answers after unmount; every fetching hook
    ├── usePollWhile.ts ← polls a job's `…/current` every second while it runs
    ├── job.ts        ← `isUnfinishedIn`, `onlyWhen`, `cancelCurrent` for every job hook
    ├── refusal.ts    ← the API's `{code, message}` refusal, and `refusalLine`
    │                   (the one line a refused button shows)
    ├── gpu.ts        ← "รอให้งาน{running}เสร็จก่อน" for `gpu_busy` (spoil-maker D45)
    ├── clips.ts      ← the Temp clip type and `/api/spoil/clips`: both tabs read it
    └── format.ts     ← a clip's length and `hh:mm:ss` of a line or a Shot
```

No router library and no `routes/`: `App` picks the page from the hash
(`#/setup`, `#/clips`, `#/spoil`, spoil D10, spoil-maker D53); a page with
steps reads its step from `useHash()` (`#/spoil/review`), so a step is a link too;
`#/spoil/voices` is a page of the สปอย tab without the steps (spoil-maker D59);
the สปอย tab's hashes live in `features/spoil-maker/lib/draft.ts`, the voice and render API shapes in `lib/render.ts`. Each page wraps itself in `PageLayout`,
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
