# UI prompt: toon

วาง block ข้างล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/toon/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วเอาลิงก์กลับมาด้วย `/warroom toon`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | รายการ Series | 1, 12 | D3, D26 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65674) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65178) |
| 2 | ตั้งค่า Series | 1 | D7, D8, D10, D11, D19, D28, D41 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8122-66685) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8122-65920) |
| 3 | ตัวละครและฉากหลัง | 2, 3, 12 | D13, D23, D25, D31, D32 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8123-68692) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8123-66916) |
| 4 | เลือกภาพอ้างอิง | 2 | D31 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8124-70163) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8124-69800) |
| 5 | รายการ EP ใน Series | 4, 12 | D26, D40 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8126-71235) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8126-70489) |
| 6 | พล็อต | 4, 7 | D12, D13, D15, D24, D43 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8127-72204) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8127-71600) |
| 7 | เส้นเรื่อง (การ์ด) | 5, 6, 8, 9, 10 | D4, D9, D13, D14, D15, D20, D21, D30, D32, D33, D44 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8128-76737) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8128-72085) |
| 8 | คลังเสียงพื้น | 10 | D5, D16, D17, D39 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-79456) |
| 9 | render และผล | 11 | D18, D38, D45 | [section](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8130-81152) · [default 1440](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8130-80526) |

```text
Design the "การ์ตูนเล่า" (toon) tab of framecraft, a local desktop web app that turns an idea into a vertical 1080×1920 narrated cartoon clip: the user sets up a Series, AI drafts a plot and cards, a local model draws one image per card, and the app renders an mp4. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser on the user's own machine; breakpoints: desktop 1440, narrow desktop 1024.
- Design system: the existing framecraft components in the Figma file (Tailwind CSS in code); tokens: foreground #121110, mid #44403c, muted #f5f5f4, muted-foreground #57534e, card #ffffff, border #e7e5e4, brand #26241f, brand-accent #5a3ee0; font IBM Plex Sans Thai (400/500/600), IBM Plex Mono for numbers and file names; icons: the Lucide-style icons already in the file.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; reuse its components page, tokens and preview page.
- Existing screens this feature connects to: the top tab bar (tabs ติดตั้ง, คลิป, คลังความรู้, สปอย — add a fifth tab "การ์ตูนเล่า" after สปอย), the สปอย tab's Saved voice page (linked from Series settings), the ติดตั้ง tab (linked from "not ready" banners). Match their look: ProgressBar, Alert, ModalDialog, RefreshButton, PageLayout.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, targets ≥ 44px.

Step 1 — Components
- Reuse: "PageLayout" (add tab "การ์ตูนเล่า"), "ProgressBar", "Alert" (info, warning, error), "ModalDialog" (confirm delete), "Button" styles as they are.
- New: "Toon/SeriesRow" — default, hover; shows name, channel name, layout badge (กรอบดำ / เต็มจอ), EP count.
- New: "Toon/RefTile" — variants: has image, no image ("ยังไม่มีภาพ"), pending ("3 แบบรอเลือก"), generating (progress); properties name, short tag, description.
- New: "Toon/Card" — one storyline card; variants: default, editing, locked (fields disabled during a job), silent (no narration text); badges "แก้เอง", "ภาพอ้างอิงเปลี่ยน", "ยังไม่มีภาพอ้างอิง"; contains narration text, 0–2 character chips, image description, motion select (นิ่ง / ซูมเข้า / ซูมออก / เลื่อนซ้าย / เลื่อนขวา), flicker toggle "ไฟกะพริบ", extra hold stepper 0–5 s by 0.5, narration buttons (สร้างเสียง / ฟัง / สร้างใหม่), card image with "สร้างภาพใหม่" and "สลับภาพก่อนหน้า".
- New: "Toon/SegmentHeader" — background name and thumbnail, background sound select with volume slider 0–100 and "ไม่มีเสียงพื้น".
- New: "Toon/JobBanner" — running (name, done/total, stop button), done, failed; used for every long job.
- New: "Toon/LengthMeter" — total seconds against target 60–120; states under, in range, over.
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "{screen} / {state} / {breakpoint}"; realistic Thai sample data (Series "รุ่นพี่เล่าว่า…", character "พีค / สายแฟ", background "กองไฟในป่า"); instances only.

Screen 1 — รายการ Series (new)
- Goal: the user picks or creates a Series. Comes from the tab bar; goes to Screen 5 by clicking a row, to Screen 2 via "สร้าง Series".
- Content: list of SeriesRow; button "สร้าง Series"; per row a delete action.
- States: 1 Default. 2 Empty: "ยังไม่มีชุด สร้างชุดแรกเพื่อเริ่มทำการ์ตูนเล่า" with "สร้าง Series". 3 Loading. 4 Delete confirm: ModalDialog "ลบชุดนี้และ EP ทั้งหมด {n} ตอน? กู้คืนไม่ได้ Saved voice และคลังเสียงพื้นยังอยู่". 5 Busy: "ลบไม่ได้ระหว่างที่มีงานของชุดนี้ทำอยู่".

Screen 2 — ตั้งค่า Series (new)
- Goal: create or edit a Series. Comes from Screen 1 or Screen 5; goes back to Screen 5 on save.
- Content:
  - ชื่อชุด: text, required, 1–60.
  - ชื่อช่อง: text, optional, 0–60.
  - แบบจอ: two cards "กรอบดำ" (landscape picture mid-screen, title and EP badge on top, channel name at bottom) and "เต็มจอ" (9:16 full screen, white subtitles over the picture); choosable only when creating; read-only after with note "เปลี่ยนแบบจอไม่ได้หลังสร้างชุด".
  - แนว: "หลอน" / "ตลก"; only when creating; fills the fields below.
  - สไตล์ภาพ (English): multiline text.
  - น้ำเสียงเล่า: multiline Thai text.
  - โครงองก์: list of act names, add, remove, rename; note "มีผลกับ EP ที่สร้างหลังจากนี้เท่านั้น".
  - เสียงเล่าหลัก: select from Saved voices.
  - ป้ายชื่อตัวละคร: switch.
  - Button "บันทึก".
- States: 1 Create. 2 Edit. 3 No Saved voice: Alert "ยังไม่มี Saved voice" with link "ไปสร้างเสียงที่ tab สปอย". 4 Validation error inline.

Screen 3 — ตัวละครและฉากหลัง (new)
- Goal: give every character and background a reference image. Part of the Series page; reached from Screen 5 and from Screen 7's "make references first" list.
- Content: two lists of RefTile, "ตัวละคร" and "ฉากหลัง"; add buttons; per tile: name, short tag (characters), description, "สร้างภาพ 3 แบบ", "เอาไฟล์เข้า" (PNG or JPG), delete.
- Before the file picker for a character image, always show: "ใช้ภาพหรือตัวละครที่คุณวาดเองหรือได้รับอนุญาต และอย่าใช้ภาพคนจริงในเรื่องที่ทำให้เขาเสียชื่อเสียง".
- States: 1 Default. 2 Empty lists. 3 Delete blocked: "ลบไม่ได้ ใช้อยู่ใน EP {n} {ชื่อตอน}". 4 Upload error: "ไฟล์นี้ไม่ใช่ PNG หรือ JPG". 5 GPU busy: "รอให้งาน{ชื่องาน}เสร็จก่อน". 6 Not ready: Alert with link to ติดตั้ง.

Screen 4 — เลือกภาพอ้างอิง (new)
- Goal: pick one of three generated images. Comes from Screen 3; returns to Screen 3.
- Content: job progress ("กำลังสร้าง 2/3", about 4.5 minutes), three images, select one, "ใช้ภาพนี้", "ยกเลิก"; note "ภาพที่ยังไม่เลือกหายเมื่อปิดแอป".
- States: 1 Generating. 2 Ready to pick. 3 Failed with retry. 4 Cancelled.

Screen 5 — รายการ EP ใน Series (new)
- Goal: open or start an EP. Comes from Screen 1; goes to Screen 6 or 7.
- Content: Series header with links to Screen 2 and Screen 3; list of EPs: "EP{nn}", title, stage (พล็อต / การ์ด), images done of total, last render time; button "EP ใหม่" opening an idea field (1–500 chars) with "ให้ AI ร่างพล็อต"; delete per EP.
- States: 1 Default. 2 Empty: "ยังไม่มี EP". 3 Delete confirm: "ลบ EP{nn} พร้อมพล็อต การ์ด ภาพ เสียง และคลิปที่ render แล้ว? ตัวละครและฉากหลังยังอยู่ในชุด". 4 Delete blocked while a job runs on that EP.

Screen 6 — พล็อต (new)
- Goal: fix the story direction before cards. Comes from Screen 5; goes to Screen 7 on confirm.
- Content: editable episode title; one editable summary per act; characters and backgrounds the plot uses, each tagged "ใหม่" or "ในชุด", a new item can be swapped for an existing one; button "ยืนยันพล็อต" (first time) or "แตกการ์ดใหม่" (later) with the list of acts that will be re-split.
- States: 1 Drafting (JobBanner). 2 Draft ready. 3 Re-split confirm: ModalDialog listing per act "การ์ดแก้เอง {n} ใบ ภาพ {n} ภาพ เสียง {n} เสียง จะหาย". 4 Nothing changed: "ยังไม่มีองก์ที่พล็อตเปลี่ยน". 5 Failed: "AI ร่างไม่สำเร็จ ลองอีกครั้ง".

Screen 7 — เส้นเรื่อง (new)
- Goal: edit cards, make images and narration. Comes from Screen 6 or 5; goes to Screen 9.
- Content: acts → segments (SegmentHeader) → Card list; add/remove act, segment, card; LengthMeter; buttons "สร้างภาพที่ขาดทั้งหมด" and "สร้างภาพใหม่การ์ดที่ภาพอ้างอิงเปลี่ยน"; list "ต้องสร้างภาพอ้างอิงก่อน" with characters/backgrounds and card counts linking to Screen 3; button "ไปหน้า render".
- States: 1 Default. 2 Image job running: JobBanner "กำลังสร้างภาพ 12/30 ข้าม 3", images appear one by one, stop button. 3 Locked during AI card writing: card fields disabled. 4 Over target: LengthMeter over. 5 Nothing to draw: "ทุกการ์ดที่เหลือต้องมีภาพอ้างอิงก่อน". 6 GPU busy.

Screen 8 — คลังเสียงพื้น (new)
- Goal: add and manage background sounds shared by every Series. Reached from a link on Screen 7 and from the tab's top level.
- Content: list: editable name, duration, play, delete; "เอาไฟล์เข้า" with upload %; link field with "โหลด" and %; before choosing a file or pasting a link, always show: "ใช้เสียงของคุณเอง หรือเสียงที่ license ให้ใช้ในวิดีโอที่เผยแพร่ได้ และใส่เครดิตตามที่ license กำหนด".
- States: 1 Default. 2 Empty. 3 Importing. 4 Errors: "ไฟล์นี้ไม่มีเสียงที่อ่านได้", "เสียงยาวเกิน 20 นาที", link errors. 5 Delete blocked: "ลบไม่ได้ ใช้อยู่ใน EP {n}".

Screen 9 — render และผล (new)
- Goal: get the mp4. Comes from Screen 7.
- Content: "render" button; states "กำลังสร้างเสียงที่ขาด 3/5" then "กำลัง render 40%"; list of rendered clips: play, download, delete.
- States: 1 Ready. 2 Voicing. 3 Rendering. 4 Cards not ready: "การ์ด {n} ใบยังไม่มีภาพ" with jump links. 5 Failed. 6 Empty list.

Step 3 — Preview
- On the existing preview page, add each screen's default frame in flow order, its state frames under it, at each breakpoint.
- Prototype links: tab "การ์ตูนเล่า" → Screen 1; Screen 1 row → Screen 5; "สร้าง Series" → Screen 2; Screen 5 → Screen 3, Screen 6, Screen 7; Screen 3 "สร้างภาพ 3 แบบ" → Screen 4 → Screen 3; Screen 6 "ยืนยันพล็อต" → Screen 7; Screen 7 → Screen 8, Screen 9; Screen 2 no-voice link → the สปอย Saved voice page.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- A preview player for the whole EP or a draft render.
- Text boxes on the picture other than the character name tag.
- Highlight colours in subtitles.
- Painting or fixing part of an image.
- Several images to choose from per card.
- A voice per character.
- AI-generated background sounds.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

เอาลิงก์ Figma กลับมาด้วย `/warroom toon`.

**แบบเสร็จ 2026-11-10** — 9 จอ ทุก state สองขนาด (1440/1024) อยู่ในหน้า `:: Website` ใต้ section components ของ toon

- Components: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8118-64964
- Prototype (เริ่มที่จอ 1): https://www.figma.com/proto/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65178&starting-point-node-id=8121-65178
- หมายเหตุจากคนออกแบบ: ภาพในแบบเป็น placeholder วาดด้วย vector (ไม่ใช้ Figma AI); tab bar เพิ่มแท็บ "การ์ตูนเล่า" ทุก variant; จุดที่ควรแก้ — จอ 6 state "Failed" ควรเป็นการ์ดว่าง ไม่ใช่การ์ดพล็อตจาง
