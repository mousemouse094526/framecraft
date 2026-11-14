# UI prompt: sound-library

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/sound-library/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft"; แล้วเอาลิงก์กลับมาด้วย `/warroom sound-library`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | แถบนำทาง | 1, 2 | D2, D3, spoil-maker D53 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) |
| 2 | หน้าคลังเสียง | 1, 3, 5, 6 | D4, D7, D10, D11, toon D56 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163) |
| 3 | เสียงพื้นในหน้าตรวจแก้ของสปอย | 4 | D5, D11, D13, spoil-maker D51 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390) |
| 4 | ผล render ของสปอย | 4 | D5, legal 1 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850) |

```text
Design the sound library screens of framecraft: a local web app that makes vertical short videos (spoiler clips and narrated cartoon clips) on the user's own computer. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app (React, Tailwind); breakpoints: mobile 375, desktop 1440 (content column 720px; the spoil tab is 1120px wide from 1024px).
- Design system: the framecraft Figma file's existing components and tokens. Tokens: foreground #121110, mid #44403c, muted #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, link #4a30bd, accent subtle #f3f1ff, info #1d4ed8 on #eff6ff, error #b91c1c on #fef2f2. Fonts: IBM Plex Sans Thai (text), Geist (wordmark), Manrope (buttons). Icons: the set already used in the file.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft — use its existing components page and preview page.
- Existing screens this feature connects to: the header of every frame in "3 tab" (node 8071-18633), "คลังเสียงพื้น" (node 8129-80163), "Script review" (node 8044-7390), the toon Series list and storyline toolbar (node 8128-76737). Match their look.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, touch targets ≥ 44px.

Step 1 — Components
- Reuse: the existing tab bar in the page header — add a "group divider" between groups and the six items below; the active item keeps today's style (accent subtle background, bold brand text).
- New: "Nav/Menu button" (mobile) — variants closed, open; properties: current page label, menu icon.
- New: "Nav/Menu list" (mobile) — items grouped with headers; variants per active item.
- New: "Info button" — a small round "i" icon button next to a page heading; variants default, hover, focus, pressed (open).
- New: "Info panel" — a light info surface under the heading with three short lines; one variant.
- New: "Sound picker" — a select whose first option is "ไม่มีเสียงพื้น" then the sound names; when a sound is chosen, a volume slider 0–100 and a play button appear beside it; variants none, chosen, empty library, error (an Alert under it), disabled.
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "{screen} / {state} / {breakpoint}"; realistic sample data in Thai; instances only.

Screen 1 — แถบนำทาง (redesign of node 8071-18633: six items in three groups, and a menu on mobile)
- Goal: the user wants to reach any tab and see which tabs prepare material and which make clips. Shown in the header of every page.
- Content:
  - Items, in order: "ติดตั้ง", "คลิป", "คลังความรู้", "คลังเสียง", "สปอย", "การ์ตูนเล่า".
  - Desktop (640px and wider): one tab bar; a thin divider after "ติดตั้ง" and another after "คลังเสียง". No group headings on desktop.
  - Mobile (narrower than 640px): one button showing the open page's name and a menu icon; pressing it opens a list: "ติดตั้ง" on top, then heading "เตรียมของ" with "คลิป", "คลังความรู้", "คลังเสียง", then heading "ทำคลิป" with "สปอย", "การ์ตูนเล่า".
  - Choosing an item closes the menu and opens that tab.
- States: 1 Desktop, each of the six items active (at least "คลังเสียง" and "การ์ตูนเล่า"). 2 Desktop with a page action button at the right end of the header (Refresh), showing how the header wraps when it does not fit. 3 Mobile closed. 4 Mobile open with "คลังเสียง" active. No horizontal scroll at 375px.

Screen 2 — หน้าคลังเสียง (redesign of node 8129-80163: new tab, new heading with an info button)
- Goal: the user wants to keep background sounds in one place for both the cartoon and the spoil tab. Comes from the nav item "คลังเสียง", or from the button "คลังเสียง" in the toon Series list and storyline toolbar (relabelled from "คลังเสียงพื้น").
- Content:
  - Heading "คลังเสียง" with the Info button; accessible name "วิธีใช้คลังเสียง".
  - Info panel lines, exactly:
    - "ใช้ร่วมกันทั้งการ์ตูนเล่าและสปอย: การ์ตูนเล่าเลือกเสียงพื้นต่อช่วง สปอยเลือกหนึ่งเสียงต่อคลิป"
    - "เสียงพื้นคือเสียงบรรยากาศที่เล่นวนใต้เสียงเล่า เช่น เสียงจิ้งหรีด เสียงฝน เสียงห้องเรียน"
    - "เอาเข้าได้จากไฟล์เสียงหรือวิดีโอในเครื่อง หรือวางลิงก์ แอปแปลงเป็นไฟล์เสียงให้เอง"
  - The panel closes on pressing the button again, Esc, or a click outside.
  - No "← การ์ตูนเล่า" back link (the old page had one). When the page was opened from another page it shows a back link "← กลับ" at the top that returns there.
  - Everything else as in node 8129-80163: the rights warning always shown above the file and link inputs ("ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด"), file input with upload %, link input with download %, the list of sounds (editable name, length, play, delete), file and link errors.
- States: 1 Default with three sounds, info closed. 2 Info open. 3 Empty: "ยังไม่มีเสียงในคลัง". 4 Uploading a file with %. 5 Downloading a link with %. 6 Delete refused: message "ยังมีที่ใช้เสียงนี้อยู่ ลบไม่ได้" with one line per user, e.g. "การ์ตูนเล่า · ผีบ้านไม้ · EP 3 คืนฝนตก" and "สปอย · Spoil draft: โคนัน ตอนพิเศษ · EP 2". 7 File error and link error as today. 8 Opened from the spoil review step: back link "← กลับ" at the top. 9 Old sounds not fully moved: warning Alert "ยังย้ายเสียงเดิมจาก media/toon/sounds ไม่ครบ: เช็คที่ว่างดิสก์แล้วเปิดแอปใหม่" above the list. Each at desktop and mobile.

Screen 3 — เสียงพื้นในหน้าตรวจแก้ของสปอย (redesign of node 8044-7390: add the Sound picker)
- Goal: the spoil maker wants one background sound under the narration for the whole clip. Sits under the original sound volume control on the script review step.
- Content:
  - Label "เสียงพื้น"; Sound picker with first option "ไม่มีเสียงพื้น" (the default for a new draft).
  - When a sound is chosen: volume slider 0–100 (sent on release) and a play button.
  - Link "ไปคลังเสียง" beside the picker, always shown; it opens the sound library tab.
- States: 1 None chosen. 2 A sound chosen at volume 30. 3 Empty library: line "ยังไม่มีเสียงในคลัง" with link "ไปคลังเสียง". 4 Picked a sound that was just deleted: the picker returns to the previous value and an error Alert "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น" under it. 5 Render refused: error Alert "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render" where other render errors show. 6 Disabled while a job locks the draft (voicing, rendering, polishing), like the other review controls. Desktop 1440 (wide column) and mobile.

Screen 4 — ผล render ของสปอย (redesign of node 8055-16850: one more credit line)
- Goal: the user wants to know which background sound a clip used, to credit it when publishing.
- Content: under the existing line "ต้นฉบับ: {clip name}", a line "เสียงพื้น: {sound name}" when the clip has one; no line when it has none.
- States: 1 A result with a background sound ("เสียงพื้น: ฝนตกในป่า"). 2 A result without one. Desktop and mobile.

Step 3 — Preview
- On the existing preview page, add each screen's default frame in flow order, its state frames under it, at each breakpoint.
- Prototype links: any page's nav item "คลังเสียง" → Screen 2; mobile menu button → menu open → any item; toon Series list "คลังเสียง" → Screen 2; Screen 3 "ไปคลังเสียง" → Screen 2 state 8; Screen 2 "← กลับ" → Screen 3; Screen 2 nav "สปอย" → the script review step.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- More than one background sound per spoil clip, or a sound per sentence.
- AI choosing the background sound.
- Categories, tags, or search in the sound library.
- A side navigation menu on desktop.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```
