# UI prompt: drum-notes

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/drum-notes/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บทำตาม block นี้กับ design system เดิมแล้ว (D28) ไม่มีแบบใน Figma; แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom drum-notes`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | รายการเพลง | 1, 4, 6 | D3, D4, D15, D18, D20 | built (D28) |
| 2 | หน้าเพลง | 2, 3, 5, 6 | D5, D6, D10, D11, D12, D13, D14, D18, D20, D21 | built (D28) |

```text
Design the "แกะเพลง" (songs) screens of framecraft: a local desktop web app, used by one person on their own Mac, that makes short vertical drum-lesson clips. This tab turns a song (a link, an audio file, or a MIDI file) into a draft drum lesson that the existing "สอนกลอง" tab then edits and renders. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser; breakpoints: desktop 1440 (primary), narrow 1024. No mobile.
- Design system: the project's existing Tailwind tokens and components; dark neutral page, white text, one accent for primary actions, Kanit-like Thai-friendly sans for UI. Match the existing "สอนกลอง" screens (lesson list, lesson editor, renders page) in spacing, buttons, cards, and dialogs.
- Figma file: the project's framecraft file; components on "Components", tokens on "Tokens", preview on "Preview". If these pages do not exist, create them.
- Existing screens this feature connects to: "สอนกลอง / รายการบทเรียนกลอง" (the top tab bar, same PageLayout), "สอนกลอง / หน้าแก้บทเรียนกลอง" (the new lesson opens here), "ติดตั้ง" (Status check rows named in `fix` chips). Match their look.
- The top tab bar gains a sixth tab "แกะเพลง" after "สอนกลอง".
- Language on screen: Thai. Use the copy below exactly. Code-like tokens (BPM, L/R, MIDI) stay Latin.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, click targets ≥ 44px.

Step 1 — Components
- Reuse: "Layout/PageLayout" (wordmark, tab bar, page title, optional action) as is; "Form/TextInput" (link box, number fields) — add variant "with trailing button"; "Button/Primary", "Button/Secondary", "Button/Danger", "Button/Ghost" as is; "Feedback/Alert" (toned box, optional title) as is; "Feedback/ProgressBar" (percent, label, cancel) as is; "Feedback/FixCommand" (a command chip with copy button for a `not_ready` row) as is; "Dialog/ModalDialog" (confirm delete) as is; "Drums/GrooveGrid" (the 16-steps-per-bar grid of the lesson editor: rows = drum pieces, columns = steps, note heads coloured per piece, "R"/"L" letter on each note) — add variant "read-only" (no hover, no click affordance, slightly dimmed header).
- New: "Songs/SongRow" — variants {default, hover, picking (progress badge), midi (MIDI badge), unanalysed}; properties {title, subtitle, sourceKind (ลิงก์ | ไฟล์ | MIDI), duration, analysisLabel, lessonCount, onDelete}.
- New: "Songs/ImportJobCard" — variants {checking, downloading (percent), converting, failed (message), uploading (percent), converting-file}; properties {title, percent, errorText, onCancel}.
- New: "Songs/RangeFields" — variants {default, error (field message), disabled (MIDI)}; properties {start, end, length, cap "90", onUseCurrentStart, onUseCurrentEnd}.
- New: "Songs/ModeToggle" — segmented control with two options "กลอง" and "ทำนอง"; variants {drums, melody, disabled}.
- New: "Songs/BarStrip" — a horizontal strip of found bars; each bar is a cell with its number, start time (m:ss.s) and hit count; clicking a bar seeks the player to its start and makes it the first bar of the window; variants {default, selected (part of the chosen window), first-of-window (stronger outline), not-4-4 (dimmed, tooltip "ห้องนี้ไม่ใช่ 4/4", not clickable), disabled (would exceed the found bars)}; properties {bars[], firstBar, count}.
- New: "Songs/WindowControls" — properties {bars count stepper 1–4, BPM number field 40–240, dropped list}; variants {default, error}.
- New: "Songs/DroppedList" — a compact list "ตัดโน้ตที่มือตีไม่ได้:" followed by chips "{piece} ห้อง {n} ช่อง {m}"; variants {empty (hidden), some}.
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "แกะเพลง / {screen} / {state} / {breakpoint}"; realistic sample data in Thai and English song titles (e.g. "Smells Like Teen Spirit", "Nirvana"); instances only.

Screen 1 — รายการเพลง (new)
- Goal: ผู้ทำคลิป wants to bring a song in and reach its page. Comes from the top tab "แกะเพลง"; goes to Screen 2 by clicking a row or right after a file import finishes; goes to "สอนกลอง / หน้าแก้บทเรียนกลอง" only through Screen 2.
- Content:
  - Page title "แกะเพลง"; under it a one-line note "ใช้เพลงเพื่อแกะโน้ตเท่านั้น เสียงเพลงไม่เข้าคลิป".
  - Link box: TextInput label "ลิงก์เพลง", placeholder "วางลิงก์ YouTube หรือเว็บอื่นที่โหลดได้", trailing Primary button "เอาเพลงเข้า"; disabled while an import runs or the box is empty. The whole box also accepts a dropped file.
  - Secondary button "เลือกไฟล์ในเครื่อง" with helper text "ไฟล์เสียง (mp3, m4a, wav, mp4) ไม่เกิน 200 MB หรือไฟล์ MIDI (.mid) ไม่เกิน 5 MB".
  - ImportJobCard under the box while a link job runs: title (or the link while "checking"), state text {"กำลังอ่านข้อมูล…", "กำลังโหลด… {n}%", "กำลังแปลงเสียง…"}, Ghost button "ยกเลิก". For a file: ProgressBar "กำลังส่งไฟล์… {n}%" then "กำลังแปลงเสียง…" (no cancel after upload completes).
  - Song list, newest change first: SongRow with title, subtitle (artist/channel, may be empty), sourceKind badge {"ลิงก์", "ไฟล์", "MIDI"}, duration m:ss, analysisLabel {"ยังไม่แกะ", "แกะแล้ว {n} ห้อง", "กำลังแกะ {n}%"}, "{n} บทเรียน", Danger icon button "ลบ".
  - Delete confirm dialog: title "ลบเพลงนี้?", body "บทเรียนที่สร้างจากเพลงนี้ยังอยู่ใน tab สอนกลอง", buttons "ลบ" / "ยกเลิก".
- States: 1 Default (list with 3 songs). 2 Empty: "ยังไม่มีเพลง วางลิงก์เพลงแรกหรือเลือกไฟล์ในเครื่อง" with the link box focused. 3 Loading: skeleton rows. 4 Import running (link, 42%). 5 Import failed: Alert error under the box with one of: "เว็บนี้ไม่รองรับ ลองโหลดไฟล์เองแล้วเลือกไฟล์ในเครื่อง", "ลิงก์นี้เป็น playlist ใส่ลิงก์เพลงเดียว", "ลิงก์นี้เป็น live ยังไม่มีไฟล์", "เว็บนี้ขอให้ login โหลดอัตโนมัติไม่ได้ โหลดเสียงเองแล้วเอาไฟล์เข้า", "เพลงนี้ดูไม่ได้แล้ว", "เพลงยาวเกิน 10 นาที", "เพลงสั้นกว่า 4 วินาที", "โหลดเสียงจากลิงก์นี้ไม่สำเร็จ", "ดิสก์เหลือไม่พอ", "กำลังเอาเพลงอื่นเข้าอยู่". 6 File refused: "ไฟล์นี้ไม่มีเสียงที่อ่านได้" / "ไฟล์ใหญ่เกิน 200 MB" / "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลอง" / "เพลงสั้นกว่า 4 วินาที". 6b Duplicate: toast "เพลงนี้มีอยู่แล้ว เปิดให้แล้ว" then Screen 2. 7 Not ready: Alert "ติดตั้งยังไม่ครบ" with FixCommand chips for the missing rows (yt-dlp, Deno, ffmpeg). 8 Delete blocked: inline "กำลังแกะเพลงนี้อยู่" or "ไฟล์ยังเปิดอยู่ ปิด player ก่อน". 9 Offline: the shared OfflinePanel.

Screen 2 — หน้าเพลง (new)
- Goal: ผู้ทำคลิป wants to pick notes for a stretch of the song, choose 1–4 found bars, and make a lesson. Comes from Screen 1 (row click or import done); goes to "สอนกลอง / หน้าแก้บทเรียนกลอง" via "สร้างบทเรียนกลอง"; back link "← รายการเพลง" to Screen 1.
- Content:
  - Header: title (h1), subtitle, sourceKind badge, duration. For MIDI songs the badge reads "MIDI" and the player, range, mode and pick sections are not shown.
  - Player: a native `<audio controls>` of the song, full width.
  - Section "ช่วงแกะ": RangeFields — "เริ่ม (วินาที)" and "จบ (วินาที)" number fields each with a Ghost button "ใช้เวลาที่เล่นอยู่"; text "ยาว {n} วินาที (ไม่เกิน 90)"; field error "ช่วงต้องยาว 4–90 วินาที และอยู่ในเพลง".
  - Section "โหมด": ModeToggle "กลอง" | "ทำนอง"; helper text under "ทำนอง": "แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน".
  - Primary button "แกะโน้ต" (disabled while a pick job runs anywhere); while running: ProgressBar with text {"กำลังเตรียมเสียง…", "กำลังแกะโน้ต… {n}%"} and Ghost "ยกเลิก". Errors as Alert: "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น", "โมเดลทำงานผิดพลาด: {message}", "กำลังแกะเพลงอื่นอยู่ ({title})", Not ready → FixCommand chips (ADTOF drum model, Beat This! model, Basic Pitch model, onnxruntime, ffmpeg); "ไฟล์โมเดลเสีย รัน setup ใหม่" with a FixCommand chip for `model_broken`.
  - Hint before any pick (no analysis yet): "ตั้งช่วงแล้วกด แกะโน้ต"; the sections ผลที่แกะได้ and สร้างบทเรียน are hidden.
  - Section "ผลที่แกะได้" (shown once analysis exists, or always for MIDI): "BPM ที่พบ {n}", "{n} ห้อง", mode label "กลอง"/"ทำนอง"; BarStrip of found bars (number, start m:ss.s, hits count; bars that are not 4/4 dimmed), horizontally scrollable; clicking a bar seeks the player.
  - Section "สร้างบทเรียน": WindowControls — instruction "กดห้องแรกบนแถบ แล้วเลือกจำนวนห้อง"; stepper "จำนวนห้อง" 1–4 (options beyond the remaining bars disabled); number field "BPM ของบทเรียน" 40–240 prefilled; read-only GrooveGrid of the chosen window with R/L letters; DroppedList under the grid (hidden when empty); for melody mode the grid shows the added kick and hi-hat too; Secondary button "ฟัง" (plays the drum sound of this grid; while mixing the label is "กำลังผสมเสียง…" and the button is disabled); Primary button "สร้างบทเรียนกลอง"; helper "แก้โน้ต ท่อนสอน และ render ต่อใน tab สอนกลอง".
  - Section "บทเรียนจากเพลงนี้": list of links "{lesson title} → เปิดใน สอนกลอง"; empty: "ยังไม่มี".
- States: 1 Default before any pick (sections ผลที่แกะได้ and สร้างบทเรียน hidden, hint shown). 2 Picking (progress 35%). 3 Picked (12 bars found, one bar dimmed as not 4/4, bars 3–4 selected, grid filled, dropped list with one chip). 3b Listening ("กำลังผสมเสียง…"). 4 Pick failed: no_beats Alert. 5 MIDI song (no range/mode/pick; bars from the file; grid filled). 6 Melody mode picked (grid with snare from melody plus kick and hi-hat). 7 Not ready (FixCommand chips). 8 Range error (field message). 9 Creating lesson (button spinner) then navigating. 10 Not found: Alert "ไม่พบเพลงนี้" with link back.

Step 3 — Preview
- On the existing preview page "Preview", add each screen's default frame in flow order, its state frames under it, at each breakpoint.
- Prototype links: top tab "แกะเพลง" → Screen 1; Screen 1 row click → Screen 2; Screen 1 file import done → Screen 2; Screen 2 "← รายการเพลง" → Screen 1; Screen 2 "สร้างบทเรียนกลอง" → "สอนกลอง / หน้าแก้บทเรียนกลอง"; Screen 2 lesson link → "สอนกลอง / หน้าแก้บทเรียนกลอง"; FixCommand → "ติดตั้ง".
- Every action named in step 2 leads to a frame. The system's existing start frame ("ติดตั้ง") stays the start.

Do not include
- A waveform editor, drag handles on the audio, or a visual timeline of hits over the waveform.
- Playing the original song together with the picked notes.
- Editing notes on this page; the grid is read-only.
- Whole-song analysis, automatic section detection, or chapter labels.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```
