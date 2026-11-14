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
├── features/[feature]/   ← spoil (คลิป tab), story-kb (คลังความรู้ tab), sound-library
│                           (คลังเสียง tab: its `lib/sounds` is what toon and spoil-maker read
│                           of the library; it imports neither, sound-library D11),
│                           spoil-maker (สปอย tab), toon (การ์ตูนเล่า tab), video-gen (สอนกลอง tab),
│                           drum-notes (แกะเพลง tab), setup-status
│   ├── components/   ← UI for this feature, *.test.tsx beside each
│   ├── hooks/        ← data fetching and state (calls lib/api)
│   └── lib/          ← plain modules the hooks share, no React (spoil D35)
├── components/ui/    ← shared once a second user exists: PageLayout (wordmark,
│                        tab bar in groups from `sm`, one menu button below it,
│                        sound-library D3; action; `wide` = 1120px from lg for two
│                        columns), OfflinePanel, RefreshButton, ProgressBar,
│                        Alert (the Figma toned box, optional title), Labeled (a field with its label, hint and error), FixCommand (a `fix` command with
│                        its copy button: spoil's notices, a `not_ready` of สอนกลอง), ModalDialog (overlay, Esc,
│                        focus kept inside), GrooveGrid (the Groove table: editing with `editing`
│                        for the lesson editor, read-only without it for the song page's preview),
│                        buttonStyles, NoticeLine (a `Notice` as an Alert), RefusedAlert (a
│                        `Refused` as an Alert with its fix commands: the สอนกลอง and แกะเพลง tabs),
│                        CommitField (a field that sends on blur or Enter); assets/
│                        holds the icons two features use (copy, trash, x, …)
├── testing/          ← testBackend.ts: the fake backend every tab's tests answer `fetch` with; fakeXhr.ts:
│                        the `XMLHttpRequest` an upload test stubs (`sendFile`); statusBox.ts:
│                        `findStatusWith`, the `Alert` that shows a text, for a test to read its tone
└── lib/
    ├── api.ts        ← getJson / sendJson, both with the 30 s timeout; postForBlob (a file answer,
    │                   the wav of ฟังจังหวะ, or its JSON refusal); sendFile (XHR upload with
    │                   its %, no timeout, spoil D58)
    ├── statusTypes.ts← GET /api/setup/status types; both tabs read them
    ├── useHash.ts    ← the URL hash (`useHash`, a moved page's old hash put back as its new one),
    │                   which top tab it opens (`tabOf`), the tabs and their groups (`TABS`, `TAB_GROUPS`), and
    │                   `useLeaveGuard` (asks "ออกโดยไม่บันทึก?" before the hash moves, story-kb D18)
    ├── setupFixes.ts ← `fixesOf(rows)`: the fix command of each Status check row a `not_ready`
    │                   names, read from `/api/setup/status` (setup-status D26); video-gen and drum-notes
    ├── useDismiss.ts ← closes a disclosure's panel on `Esc` (focus back on its button) or a press
    │                   outside: the คลังเสียง info box and the narrow tab menu (sound-library D16)
    ├── useMountedState.ts ← useState that drops answers after unmount; every fetching hook
    ├── useReadyState.ts ← a hook's state union with `update`, which changes only a `ready` state (toon D65)
    ├── edit.ts       ← `sendEdit` (one request, its answer as ok, refused with a `Notice`) and `stopJob`
    ├── notice.ts     ← `Notice`, the line a refused or failed request shows, `noticeOf`, `NOT_NOW`
    ├── upload.ts     ← `sendChecked`: a file's `/check`, then its raw body with its % (ADR 0028)
    ├── usePollWhile.ts ← polls a job's `…/current` every second while it runs
    ├── job.ts        ← `isUnfinishedIn`, `onlyWhen`, `cancelCurrent` for every job hook
    ├── audio.ts      ← `playAudio`: the ฟัง buttons of the สปอย and การ์ตูนเล่า tabs
    ├── useListen.ts  ← a ฟัง button that plays a wav the backend mixes from a blob URL, stopping the
    │                   one before (`request()` fetches it, null plays nothing): ฟังจังหวะ of สอนกลอง
    │                   and ฟัง of หน้าเพลง (drum-notes D21)
    ├── kit.ts        ← the ten drum pieces with their Thai names, `isFoot`: สอนกลอง and แกะเพลง
    ├── lesson.ts     ← a drum lesson as `/api/drums/lessons` answers it, its hashes (`drumsViewOf`,
    │                   `lessonHash`), the D20 hand rules the Groove grid shares with the backend's
    │                   `PUT`, `countOf`; the song page reads its Groove and opens its editor
    ├── refusal.ts    ← the API's `{code, message}` refusal, and `refusalLine`
    │                   (the one line a refused button shows)
    ├── refused.ts    ← `Refused`, the one shape a refused request takes on the สอนกลอง and แกะเพลง
    │                   pages (tone, line, fix commands, the field named), `refusedOf(body, warnings)`,
    │                   `refusedLine`, `OFFLINE`, `NOT_NOW` (drum-notes D30)
    ├── gpu.ts        ← "รอให้งาน{running}เสร็จก่อน" for `gpu_busy` (spoil-maker D45)
    ├── clips.ts      ← the Temp clip type and `/api/spoil/clips`: both tabs read it
    ├── stories.ts    ← a Story's list row, `/api/stories`, `/api/story-clips` (`readStoryLinks`
    │                   reads both) and the คลังความรู้ hashes: the สปอย tab's step 1 and polish
    │                   choice read them too (story-kb D19, D20)
    └── format.ts     ← a clip's length, `hh:mm:ss` of a line or a Shot, and `editedAt` ("5 พ.ย. 14:20")
```

No router library and no `routes/`: `App` picks the page from the hash
(`#/setup`, `#/clips`, `#/stories`, `#/sounds`, `#/spoil`, spoil D10, spoil-maker D53, story-kb D9,
sound-library D2; `#/sounds?back={hash}` is คลังเสียง with a "← กลับ" link, sound-library D11); a page with
steps reads its step from `useHash()` (`#/spoil/review`), so a step is a link too;
`#/spoil/voices` is a page of the สปอย tab without the steps (spoil-maker D59); `#/toon/…` pages are picked by `pageOf` in `features/toon/lib/series.ts` (toon D52, D53, D56: a Series' EPs, its `/cast`, an EP's plot, storyline or `/render`; `#/toon/sounds` became `#/sounds`, sound-library D6); `#/stories/new` and `#/stories/{id}` open แก้ Story (story-kb); `#/drums/{id}` opens หน้าแก้บทเรียนกลอง and any other `#/drums…` hash the lesson list (`drumsViewOf` in `lib/lesson.ts`, shared with the แกะเพลง tab since drum-notes D25); `#/songs/{id}` opens หน้าเพลง and any other `#/songs…` hash the song list (`songsViewOf` in `features/drum-notes/lib/songs.ts`, drum-notes D2);
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
