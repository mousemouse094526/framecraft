# UI prompt: story-kb

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พิมพ์ "design docs/features/story-kb/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom story-kb`

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | คลังความรู้ (รายการ Story) | 1, 4 | D9 | new |
| 2 | แก้ Story | 1, 2, 3, 4 | D2, D6, D10, D11, D16 | new |
| 3 | ขั้น 1 ตั้งค่าคลิปสปอย: ช่อง Story | 5 | D3, D14, D15, D16 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) |
| 4 | ขั้น 2 กล่องเรียบเรียงใหม่ | 6 | D5, D16 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) |

```text
Design the คลังความรู้ (knowledge base) screens of framecraft, a local desktop web app that turns a downloaded YouTube video into narrated vertical Thai recap videos for one creator. A Story is one film or series the creator writes up once (title, article, characters) so the AI drafting the Thai script spells names right and knows who is who. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables (foreground #121110, mid #44403c, muted #f5f5f4, card #ffffff, border #e7e5e4, brand #26241f, brand accent #5a3ee0, destructive); font IBM Plex Sans Thai; icons: Lucide (plus, trash-2, pencil, book-open, external-link).
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft. The tab bar is in section "framecraft — 3 tab" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633), component "Tab". The สปอย step 1 frames "Spoiler setup / …" and the review frames "Script review / …" are in section "framecraft — สปอย / EP & เรียบเรียง" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833). The Saved voice page (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220) is the closest existing list-and-delete page: match its look.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, icon buttons have an aria-label, touch targets ≥ 44px.

Step 1 — Components
- Change: "Tab" bar — four tabs in this order: "ติดตั้ง", "คลิป", "คลังความรู้", "สปอย".
- New: "Story row" — title, "{n} ตัวละคร", "ใช้อยู่ {n} คลิป" (hidden when 0), last edited time; variants default, hover.
- New: "Character row" — input "ชื่อ" (max 40), input "คำอธิบายสั้น" (optional, max 200), trash icon button (aria-label "ลบตัวละคร {name}"); variants default, error (message under the name input).
- New: "Story picker" for step 1 — label "เรื่องในคลังความรู้", a select ("ไม่ใช้" first, then every Story by title), helper text "จำให้คลิปนี้ทุก EP เมื่อกดร่างบท", link "แก้เรื่องนี้" (external-link icon, opens a new browser tab) when a Story is chosen, link "เพิ่มเรื่องในคลังความรู้" (opens a new browser tab); variants none chosen, chosen, no stories yet (select shows only "ไม่ใช้"), locked (plain text instead of the select, while a draft runs).
- Change: the step 1 token meter — text "{EP + Story} / 32,000" with a second line "เรื่อง {n} token" when a Story is chosen; over the limit uses the existing error state.
- Reuse: "Alert", "ModalDialog" (the delete confirm of the Saved voice page), the offline panel, buttons and inputs as they are.
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens
Frame names: "{screen} / {state} / {breakpoint}"; realistic Thai sample data (Story "ยอดนักสืบจิ๋วโคนัน" with characters "โคนัน" — "ชินอิจิในร่างเด็ก ไขคดีแทนลุงโคโกโร่", "รัน", "โคโกโร่" — "นักสืบเอกชน พ่อของรัน"; a second Story "วันพีซ"); instances only.

Screen 1 — คลังความรู้ (new)
- Goal: the creator sees every Story and opens or adds one. Comes from the tab bar; goes to Screen 2 by a row or "เพิ่มเรื่อง".
- Content:
  - Button "เพิ่มเรื่อง" (plus icon) in the tab's action slot.
  - Story rows, last edited first.
- States: 1 Default with two rows. 2 Empty: "ยังไม่มีเรื่องในคลังความรู้" with the button "เพิ่มเรื่อง". 3 Loading. 4 Offline (the existing offline panel). Each at 1440 and 375.

Screen 2 — แก้ Story (new)
- Goal: the creator writes or fixes a Story and saves it once. Comes from Screen 1; "กลับ" link returns to Screen 1.
- Content:
  - Input "ชื่อเรื่อง" (required, one line, max 100).
  - Textarea "บทความ" (several lines, max 5,000) with the counter "{n} / 5,000" and the hint "เรื่องย่อ ปม และบทบาทตัวละคร ใช้เป็นพื้นหลังให้ AI".
  - Section "ตัวละคร" with Character rows in the order typed and the button "+ เพิ่มตัวละคร" (hidden at 30).
  - Button "บันทึก": disabled when nothing changed and while saving; after a save "บันทึกแล้ว".
  - Button "ลบเรื่อง" (destructive, existing Story only) opens a confirm "ลบ {ชื่อเรื่อง}?" with the line "ใช้อยู่ {n} คลิป คลิปเหล่านั้นจะเป็น ไม่ใช้" when n > 0, buttons "ลบ" and "ยกเลิก".
  - Leaving with unsaved changes asks "ออกโดยไม่บันทึก?" (browser confirm; no frame needed).
- States: 1 New, empty. 2 Filled, unsaved. 3 Saving. 4 Saved ("บันทึกแล้ว"). 5 Field errors: "ใส่ชื่อเรื่อง", "บทความยาวเกิน 5,000 ตัวอักษร", "ชื่อตัวละครซ้ำ". 6 30 characters (no add button). 7 Delete confirm with "ใช้อยู่ 2 คลิป". 8 Not found: "ไม่พบเรื่องนี้" with a link back to คลังความรู้. Each at 1440 and 375.

Screen 3 — ขั้น 1 ตั้งค่าคลิปสปอย, the Story picker (redesign of "Spoiler setup / …" in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833: add the Story picker under the chosen clip and the combined token meter)
- Goal: the creator picks the clip's Story before pressing ร่างบท; the clip remembers it for every EP.
- Content: the Story picker below the clip list, above the EP list; the token meter with the Story line.
- States: 1 Clip chosen, Story remembered ("ยอดนักสืบจิ๋วโคนัน", meter "21,400 / 32,000" and "เรื่อง 3,100 token"). 2 "ไม่ใช้". 3 No stories yet with "เพิ่มเรื่องในคลังความรู้". 4 Over the limit: meter error "EP กับเรื่องรวม 33,200 token เกิน 32,000 (เรื่อง 4,200)", ร่างบท disabled. 5 Drafting (locked): picker as plain text "ยอดนักสืบจิ๋วโคนัน". 6 Story gone: Alert error "ไม่พบเรื่องนี้ในคลังความรู้แล้ว", picker back to "ไม่ใช้". Each at 1440 and 375.
- Also: the draft progress card of step 2 ("Script review / Draft flow …") gets the line "เรื่อง: ยอดนักสืบจิ๋วโคนัน" under the clip and style line.

Screen 4 — ขั้น 2 กล่องเรียบเรียงใหม่ (redesign of the polish dialog in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833: one line about the Story)
- Goal: the creator knows which Story the polish uses, and that the hook is not rewritten.
- Content: the line "ใช้เรื่อง: {ชื่อเรื่อง}" or "ไม่ได้ใช้เรื่องในคลังความรู้"; in layouts A and C the line "hook และชื่อตอนไม่ถูกเรียบเรียง แก้เองได้ที่ช่องด้านบน".
- States: 1 With a Story. 2 Without. Each at 1440 and 375.

Step 3 — Preview
- On the existing preview page, add Screens 1 and 2 between the คลิป tab and the สปอย tab frames, default frames in flow order with their state frames under them, at each breakpoint; replace the step 1 and polish dialog frames with Screens 3 and 4.
- Prototype links: tab "คลังความรู้" → Screen 1; Screen 1 row or "เพิ่มเรื่อง" → Screen 2; Screen 2 "กลับ" or a confirmed delete → Screen 1; Screen 3 "แก้เรื่องนี้" or "เพิ่มเรื่องในคลังความรู้" → Screen 2; Screen 3 "ร่างบท" → the draft progress card; "เรียบเรียงใหม่" on the review page → Screen 4.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- Searching or fetching articles from the web.
- Other names or misspellings per character.
- Any Story setting for picking Shots or for the คลิป tab.
- A way to set a clip's Story without drafting.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom story-kb`
