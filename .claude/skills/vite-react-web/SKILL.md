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
├── features/[feature]/   ← spoil (คลิป tab), story-kb (คลังความรู้ tab),
│                           spoil-maker (สปอย tab), toon (การ์ตูนเล่า tab), video-gen (สอนกลอง tab),
│                           drum-notes (แกะเพลง tab), setup-status
│   ├── components/   ← UI for this feature, *.test.tsx beside each
│   ├── hooks/        ← data fetching and state (calls lib/api)
│   └── lib/          ← plain modules the hooks share, no React (spoil D35)
├── components/ui/    ← shared once a second user exists: PageLayout (wordmark,
│                        tab bar, action; `wide` = 1120px from lg for two
│                        columns), OfflinePanel, RefreshButton, ProgressBar,
│                        Alert (the Figma toned box, optional title), FixCommand (a `fix` command with
│                        its copy button: spoil's notices, a `not_ready` of สอนกลอง), ModalDialog (overlay, Esc,
│                        focus kept inside), buttonStyles; assets/
│                        holds the icons two features use (copy, trash, x, …)
├── testing/          ← testBackend.ts: the fake backend every tab's tests answer `fetch` with; fakeXhr.ts:
│                        the `XMLHttpRequest` an upload test stubs (`sendFile`); statusBox.ts:
│                        `findStatusWith`, the `Alert` that shows a text, for a test to read its tone
└── lib/
    ├── api.ts        ← getJson / sendJson, both with the 30 s timeout; postForBlob (a file answer,
    │                   the wav of ฟังจังหวะ, or its JSON refusal); sendFile (XHR upload with
    │                   its %, no timeout, spoil D58)
    ├── statusTypes.ts← GET /api/setup/status types; both tabs read them
    ├── useHash.ts    ← the URL hash (`useHash`), which top tab it opens (`tabOf`), and
    │                   `useLeaveGuard` (asks "ออกโดยไม่บันทึก?" before the hash moves, story-kb D18)
    ├── setupFixes.ts ← `fixesOf(rows)`: the fix command of each Status check row a `not_ready`
    │                   names, read from `/api/setup/status` (setup-status D26); video-gen and drum-notes
    ├── useMountedState.ts ← useState that drops answers after unmount; every fetching hook
    ├── usePollWhile.ts ← polls a job's `…/current` every second while it runs
    ├── job.ts        ← `isUnfinishedIn`, `onlyWhen`, `cancelCurrent` for every job hook
    ├── audio.ts      ← `playAudio`: the ฟัง buttons of the สปอย and การ์ตูนเล่า tabs
    ├── refusal.ts    ← the API's `{code, message}` refusal, and `refusalLine`
    │                   (the one line a refused button shows)
    ├── gpu.ts        ← "รอให้งาน{running}เสร็จก่อน" for `gpu_busy` (spoil-maker D45)
    ├── clips.ts      ← the Temp clip type and `/api/spoil/clips`: both tabs read it
    ├── stories.ts    ← a Story's list row, `/api/stories`, `/api/story-clips` (`readStoryLinks`
    │                   reads both) and the คลังความรู้ hashes: the สปอย tab's step 1 and polish
    │                   choice read them too (story-kb D19, D20)
    └── format.ts     ← a clip's length, `hh:mm:ss` of a line or a Shot, and `editedAt` ("5 พ.ย. 14:20")
```

No router library and no `routes/`: `App` picks the page from the hash
(`#/setup`, `#/clips`, `#/stories`, `#/spoil`, spoil D10, spoil-maker D53, story-kb D9); a page with
steps reads its step from `useHash()` (`#/spoil/review`), so a step is a link too;
`#/spoil/voices` is a page of the สปอย tab without the steps (spoil-maker D59); `#/toon/…` pages are picked by `pageOf` in `features/toon/lib/series.ts` (toon D52, D53, D56: a Series' EPs, its `/cast`, an EP's plot, storyline or `/render`, and `#/toon/sounds`); `#/stories/new` and `#/stories/{id}` open แก้ Story (story-kb); `#/drums/{id}` opens หน้าแก้บทเรียนกลอง and any other `#/drums…` hash the lesson list (`lessonIdOf` in `features/video-gen/lib/lesson.ts`, which also holds the D20 hand rules the Groove grid shares with the backend's `PUT`); `#/songs/{id}` opens หน้าเพลง and any other `#/songs…` hash the song list (`songsViewOf` in `features/drum-notes/lib/songs.ts`, drum-notes D2);
the สปอย tab's hashes, the Draft job's shapes, the styles and `sendDraft` (the one `POST` of a whole new draft, step 1 and step 2 both send it) live in `features/spoil-maker/lib/draft.ts`, the voice and render API shapes and `startJob` in `lib/render.ts` — a `lib/` module may call `lib/api` when two hooks send the same request. The tab's steps share one state (`useStepStatus`): `StepsRefreshContext` reads it again, `DraftRunContext` gives the latest Draft job to step 1 (locked while it runs) and step 2 (its progress card). Each page wraps itself in `PageLayout`,
whose tabs are plain `#/…` links, so clicks and the back button both just
change the hash.

## Flow

App → feature component → hook → lib/api → `/api/...`

## Where shared code goes

- Code one feature uses lives in that feature.
- A second user appears → move it to `components/ui/` or a top-level folder
  named for its kind, in the same change.

## Never break

- Every backend call goes through `lib/api.ts` with a timeout. The one exception is
  `sendFile`, the file import's upload: no timeout, the user cancels it (spoil D50, D58).
- UI text is Thai.
- Styling is Tailwind classes; no separate CSS files except the Tailwind entry.

## Rules by layer

| File | Covers |
|---|---|
| [rules/components.md](rules/components.md) | feature components and states |
| [rules/testing.md](rules/testing.md) | Vitest, RTL, fetch fakes |

A layer with no rules file → stop and ask before writing it.
