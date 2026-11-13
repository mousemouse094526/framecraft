# UI prompt: video-gen

วาง block ข้างล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พิมพ์ "design docs/features/video-gen/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft"; แล้วเอาลิงก์กลับมาด้วย `/warroom video-gen`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | รายการบทเรียนกลอง | 5 | D9, D10, D22 | new |
| 2 | หน้าแก้บทเรียนกลอง | 1, 2, 3, 6 | D4, D5, D6, D8, D14, D16, D20, D21, D22, D23 | new |
| 3 | ผล render ของบทเรียน | 4, 5 | D10, D14, D22 | new |

```text
Design the "สอนกลอง" (drum lesson) tab of framecraft: a local desktop web app where one creator makes vertical short videos on their own Mac. In this tab they type a drum groove on a grid, split it into teaching chapters, listen to it, and render a 1080×1920 drum-tutorial video. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser; breakpoints: desktop 1440, mobile 375 (the grid scrolls sideways at 375).
- Design system: the framecraft Figma file's own components (Tailwind CSS 4 in code); tokens: foreground #121110, muted #f5f5f4, border #e7e5e4, brand #26241f, brand-accent #5a3ee0, link #4a30bd, destructive #dc2626, success #15803d; fonts IBM Plex Sans Thai (UI), IBM Plex Mono (numbers, times), Manrope (buttons), Geist (brand). Icons: the set already in the file.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft — reuse its component, token and preview pages.
- Existing screens this feature connects to: the top tab bar (tabs ติดตั้ง · คลิป · คลังความรู้ · สปอย · การ์ตูนเล่า; add "สอนกลอง" last) and the การ์ตูนเล่า tab's list, render and progress screens. Match their look: PageLayout, Alert, ModalDialog, ProgressBar, primary and secondary buttons.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, touch targets ≥ 44px; grid cells are buttons with an accessible name like "สแนร์ ห้อง 1 ช่อง 3".
- Drum piece colours (used in the grid rows and chips): hi-hat and hi-hat pedal #E8C547, crash and ride #E8894A, snare #4A7FE8, high and mid tom #2E8C82, floor tom #6B4FC2, kick #E84A6B.

Step 1 — Components
- Reuse: tab bar (add tab "สอนกลอง"), PageLayout, Alert (info, warning, error), ModalDialog (confirm), ProgressBar, primary and secondary buttons, text input, number input, select.
- New: "Drums/LessonRow" — variants default, rendering (badge "กำลัง render 42%"), hover; properties title, length, render count, updated time.
- New: "Drums/GrooveGrid" — rows = 10 drum pieces in this order: ไฮแฮทปิด, ไฮแฮทเปิด, แครช, ไรด์, สแนร์, ทอมสูง, ทอมกลาง, ทอมต่ำ, กระเดื่อง, ไฮแฮทเท้า; columns = 16 steps per bar with headers "1 e & a 2 e & a 3 e & a 4 e & a", 1–4 bars side by side with a bar number above each bar.
- New: "Drums/GridCell" — variants empty, empty-disabled (both hands busy on that step), note (shows R or L, or nothing for kick and hi-hat pedal), note-accent (larger), note-ghost (faded), note-flam (small grace mark before), selected; colour = the row's piece colour.
- New: "Drums/NoteInspector" — for the selected note: segmented "มือ" R / L (an option that would put one hand on two pieces is disabled), segmented "ลักษณะตี" ปกติ / เน้น / เบา / flam (flam disabled on foot pieces), button "ลบโน้ต".
- New: "Drums/ChapterCard" — fields "ป้าย" (placeholder "ว่าง = แสดงหัวเรื่อง", max 16), "คำอธิบาย" (max 60), "ชิ้นที่เน้น" (multi-select chips of the 10 pieces), "รอบ" 1–8, "ความเร็ว" 50–100% step 5; actions เลื่อนขึ้น, เลื่อนลง, ลบท่อน.
- New: "Drums/LengthMeter" — variants ok "ความยาว 24.6 / 90 วินาที", over "ยาวเกิน 12.4 วินาที — ลดรอบหรือท่อนก่อนฟังหรือ render".
- New: "Drums/ListenButton" — variants default "ฟังจังหวะ", working "กำลังผสมเสียง…" (disabled), playing (with stop), disabled (too long).
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "{screen} / {state} / {breakpoint}"; realistic Thai sample data (e.g. "SMELLS LIKE TEEN SPIRIT", "Nirvana · how to play the intro fill"); instances only.

Screen 1 — รายการบทเรียนกลอง (new)
- Goal: the creator wants to pick, start, copy or delete a drum lesson. Comes from the tab bar "สอนกลอง"; goes to Screen 2 by clicking a row or after creating one.
- Content:
  - Heading "บทเรียนกลอง" with count.
  - Rows (LessonRow), newest edit first: title, clip length "24.6 วินาที", "render แล้ว 3 ครั้ง", "แก้ล่าสุด 13 พ.ย. 10:30".
  - Button "สร้างบทเรียนใหม่": opens a dialog with field "หัวเรื่อง" (required, max 40) and button "สร้าง".
  - Row actions "ทำซ้ำ", "ลบ"; "ลบ" asks "ลบ "{title}" และผล render 3 ไฟล์? ย้อนกลับไม่ได้" with "ลบ" / "ยกเลิก".
- States: 1 Default. 2 Empty: "ยังไม่มีบทเรียนกลอง สร้างบทเรียนแรกเพื่อทำคลิปสอนกลอง" with "สร้างบทเรียนใหม่". 3 Loading: skeleton rows. 4 Error: delete refused while rendering → inline Alert "กำลัง render บทเรียนนี้อยู่ ลบได้เมื่อ render จบ"; file open → "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง". 5 Rendering: one row shows the rendering badge with %. 6 Offline: the existing offline panel.

Screen 2 — หน้าแก้บทเรียนกลอง (new)
- Goal: the creator wants to type the groove, set up chapters, listen and render. Comes from Screen 1; goes to Screen 3 when a render it started finishes, or via link "ผล render (3)".
- Content, top to bottom:
  - Back link "บทเรียนกลอง". Header with the lesson title.
  - Card "ข้อมูลคลิป": "หัวเรื่อง" (max 40), "บรรทัดรอง" (max 60), "คำบรรยายล่าง" (max 60), "BPM" (40–240).
  - Card "พื้นหลัง": radio "สีเข้มของแอป" / "ภาพของฉัน"; with an image: thumbnail 9:16, "เปลี่ยนภาพ", "ลบภาพ"; note beside the picker "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม"; accepts PNG or JPG up to 20 MB.
  - Card "Groove": GrooveGrid with "เพิ่มห้อง" / "ลดห้อง" (1–4 bars; reducing a bar with notes asks "ลบโน้ตในห้อง 3 (5 ตัว)?"); clicking an empty cell adds a note with the free hand; NoteInspector beside the grid (below it at 375).
  - Card "ท่อนสอน": list of ChapterCard (1–6), button "เพิ่มท่อน" (disabled at 6).
  - Sticky footer bar: LengthMeter, button "บันทึก" (with "ยังไม่บันทึก" dot when dirty), ListenButton, primary button "render คลิป".
  - While rendering this lesson: footer shows ProgressBar "กำลัง render 42%" and "ยกเลิก".
- States: 1 Default (sample lesson with 2 bars and 3 chapters KICK, FLAMS, ลองเล่นเอง). 2 New lesson: 1-bar rock beat, chapter 1 label empty, chapter 2 "ลองเล่นเอง". 3 Note selected. 4 Too long: LengthMeter over, listen and render disabled, save still enabled. 5 Listening: working then playing. 6 Rendering. 7 Render failed: Alert "render ไม่สำเร็จ: {message}" with "ลองอีกครั้ง". 8 Render cancelled: Alert "ยกเลิก render แล้ว" with "render อีกครั้ง". 9 Not ready: Alert "ยังติดตั้งไม่ครบ: Drum samples" with the fix command chip and copy button. 10 Busy: "กำลัง render "{other title}" อยู่ รอให้จบก่อน". 11 Field error: message under the field from the API. 12 Leave with unsaved changes: confirm "ออกโดยไม่บันทึก?" "ออก" / "อยู่ต่อ".

Screen 3 — ผล render ของบทเรียน (new)
- Goal: the creator wants to watch, download or delete renders. Comes from Screen 2 (render finished, or link "ผล render"); back link to Screen 2.
- Content:
  - List of renders newest first: created time, length; selecting one plays it in a 9:16 player.
  - Buttons "โหลด mp4", "โหลด .srt", "ลบ" (confirm "ลบผล render นี้?").
  - Opened right after a render: the newest one is selected.
- States: 1 Default. 2 Empty: "ยังไม่เคย render บทเรียนนี้" with link back to the editor. 3 Rendering: ProgressBar at top. 4 Error: delete while the file is open → "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง".

Step 3 — Preview
- On the existing preview page, add each screen's default frame in flow order, its state frames under it, at each breakpoint.
- Prototype links: tab bar "สอนกลอง" → Screen 1; Screen 1 row → Screen 2; "สร้างบทเรียนใหม่" → dialog → Screen 2 (new lesson); Screen 2 "render คลิป" → Rendering state → Screen 3; Screen 2 "ผล render" → Screen 3; Screen 3 back → Screen 2; Screen 2 back → Screen 1.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- Other instruments, MIDI import, audio upload or transcription.
- Time signatures other than 4/4, triplets.
- Backing tracks or the การ์ตูนเล่า sound library.
- A live video preview before render.
- Options for layout, colours or fonts of the video.
- Any logo or watermark field.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

เสร็จแล้วเอาลิงก์กลับมาด้วย `/warroom video-gen`.
