# UI prompt: drum-cover

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/drum-cover/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บทำตาม block นี้กับ design system เดิม ไม่รอ Figma (D14); แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom drum-cover`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | หน้าเพลง — ส่วนที่เพิ่ม | 1, 7 | D9, D11 | new (ส่วนเพิ่มในหน้าเดิมของ drum-notes) |
| 2 | หน้า reel | 2, 3, 4, 5, 6 | D2, D6, D7, D8, D12, D18, D19 | new |

```text
Design the "Reel cover" screens of framecraft: a local desktop web app, used by one person on their own Mac, that makes short vertical clips. The "แกะเพลง" tab already turns a song into found drum hits; this feature turns those hits into ONE vertical reel cover clip (animated drum kit whose sticks hit exactly the found hits, notes scrolling past a playhead, drum sound mixed by the app, optional own background picture). It is not a lesson: no BPM, no chapters, no teaching labels. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser; breakpoints: desktop 1440 (primary), narrow 1024. Touch targets ≥ 44px below 640px. No mobile.
- Design system: the project's existing Tailwind tokens and components; dark neutral page, white text, one accent for primary actions, Thai-friendly sans for UI. Match the existing "แกะเพลง / หน้าเพลง" and "สอนกลอง / หน้าแก้บทเรียนกลอง" and "สอนกลอง / ผล render" screens in spacing, buttons, cards, alerts and dialogs.
- Figma file: the project's framecraft file; components on "Components", tokens on "Tokens", preview on "Preview". If these pages do not exist, create them.
- Existing screens this feature connects to: "แกะเพลง / หน้าเพลง" (Screen 1 adds two sections to it), "แกะเพลง / รายการเพลง", "สอนกลอง / หน้าแก้บทเรียนกลอง" (the secondary lesson path), "ติดตั้ง" (Status check rows named in FixCommand chips). Match their look.
- No new tab: the reel page opens from the song page.
- Language on screen: Thai. Use the copy below exactly. Code-like tokens (mp4, .srt, PNG, JPG, MB) stay Latin.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, click targets ≥ 44px.

Step 1 — Components
- Reuse as is: "Layout/PageLayout", "Form/TextInput", "Button/Primary", "Button/Secondary", "Button/Danger", "Button/Ghost", "Feedback/Alert", "Feedback/ProgressBar" (percent, label, cancel), "Feedback/FixCommand", "Feedback/RefusedAlert", "Dialog/ModalDialog", "Songs/BarStrip" (read-only variant).
- Reuse "Drums/BackgroundPicker" (from the lesson editor: colour or own picture, 9:16 thumbnail, change, remove) — now shared; add property {warning text}.
- New: "Cover/RangeCard" — fields start and end (seconds) within the picked range, length line, Ghost button "เริ่มที่การตีแรก", a read-only BarStrip of the found bars with hit counts; variants {default, error (field message)}.
- New: "Cover/SoundChoice" — segmented control "กลองล้วน" | "กลอง + เพลงต้นฉบับ"; with the second: a slider/number "ความดังเพลง" 10–100 and a warning Alert; variants {drums, backing, disabled-midi}.
- New: "Cover/ActionBar" — sticky bottom bar: Secondary "บันทึก" with an "ยังไม่บันทึก" dot, Secondary "ฟัง", Primary "render reel"; variants {saved, unsaved, listening ("กำลังผสมเสียง…"), rendering (ProgressBar + "ยกเลิก")}.
- New: "Cover/RenderRow" — created time, length, stretch, badges "มีเพลงต้นฉบับ" and "แกะใหม่แล้ว"; variants {default, selected, stale}; actions "โหลด mp4", "โหลด .srt", "ลบ".
- New: "Songs/CoverSection" — card on the song page: line "ช่วงแกะ {start}–{end} วินาที · {n} การตี · render แล้ว {m} ครั้ง", Primary "ทำ reel cover".
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "Reel cover / {screen} / {state} / {breakpoint}"; realistic sample data (song "Yellow", subtitle "Coldplay · drum cover", picked 0.0–30.0 s, first hit 11.5 s, 88 hits); instances only.

Screen 1 — หน้าเพลง, added sections (new parts of "แกะเพลง / หน้าเพลง")
- Goal: ผู้ทำคลิป wants to know where the drums start and go make the reel. Everything else on the page stays as it is.
- Content:
  - Above the section "ผลแกะ", once a pick is done: Alert (warning) "ไม่พบการตีกลองในช่วง {start}–{end} วินาที ลองเลื่อนช่วงไปที่กลองเริ่มเล่น" when nothing was found; or Alert (info) "ห้อง 1–{k} ไม่มีการตี การตีแรกอยู่ที่ {t} วินาที" with Secondary button "เริ่มช่วงที่การตีแรก" (sets the range to start at the first hit, saves, and picks again at once) when the first found bars are empty.
  - Above the section "สร้างบทเรียน", once an analysis exists: CoverSection "Reel cover" with "ช่วงแกะ 0.0–30.0 วินาที · 88 การตี · render แล้ว 2 ครั้ง" and Primary "ทำ reel cover" → Screen 2. The lesson button "สร้างบทเรียนกลอง" becomes Secondary.
- States: 1 Picked, drums start late (Alert "ห้อง 1–5 ไม่มีการตี การตีแรกอยู่ที่ 11.5 วินาที" + button). 2 Picked, no hits (warning Alert; CoverSection still shows "0 การตี" and its button). 3 Picked normally (CoverSection only). 4 Re-picking after "เริ่มช่วงที่การตีแรก" (the existing pick ProgressBar). 5 Not picked yet (no new parts).

Screen 2 — หน้า reel (new, `#/songs/{id}/cover`)
- Goal: ผู้ทำคลิป wants to set the reel's stretch, text, background and sound, hear it, render it as a vertical mp4, and download it. Comes from Screen 1 "ทำ reel cover"; back link "← {ชื่อเพลง}" to Screen 1.
- Content:
  - Header: back link "← Yellow", page title "Reel cover".
  - Card "ช่วงของ reel": RangeCard — "เริ่ม (วินาที)" and "จบ (วินาที)" within the picked range; "ยาว {n} วินาที (2–90)"; Ghost "เริ่มที่การตีแรก"; read-only BarStrip of the found bars with hit counts; link line "อยากได้ท่อนอื่น? แกะช่วงใหม่ที่หน้าเพลง" → "แกะเพลง / หน้าเพลง".
  - Card "ข้อความบนจอ": "หัวเรื่อง" (1–40 letters, prefilled with the clip's title) with hint "ค่าตั้งต้นมาจากชื่อคลิปและช่อง แก้เป็นชื่อเพลงและศิลปิน", "บรรทัดรอง" (0–60, prefilled with the clip's channel), "คำบรรยายล่าง" (0–60, empty); a letter counter under each.
  - Card "พื้นหลัง": BackgroundPicker — "สีเข้มของแอป" / "ภาพของฉัน"; choose PNG/JPG ≤ 20 MB, 9:16 thumbnail, "เปลี่ยนภาพ", "ลบภาพ"; warning "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม".
  - Card "เสียง": SoundChoice — "กลองล้วน" (default) / "กลอง + เพลงต้นฉบับ"; with the second: "ความดังเพลง" 10–100 (default 35) and warning "เพลงต้นฉบับมีลิขสิทธิ์ แพลตฟอร์มอาจ claim ปิดเสียง หรือบล็อกคลิป เปิดเมื่อคุณมีสิทธิ์ใช้เสียงนี้". A MIDI song: the second option disabled with "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ".
  - ActionBar: "บันทึก" (dot "ยังไม่บันทึก" once edited; leaving the page unsaved asks "ออกโดยไม่บันทึก?" with "ออก" / "อยู่ต่อ"), "ฟัง" (saves first → "กำลังผสมเสียง…" → plays), Primary "render reel" (saves first, then ProgressBar "กำลัง render… {n}%" with "ยกเลิก").
  - Card "ผล render": RenderRows newest first, each with its stretch "{start}–{end} วินาที" and badge "แกะใหม่แล้ว" when it was made from an older pick; a 9:16 player of the selected one (the newest right after a render ends); "โหลด mp4", "โหลด .srt", "ลบ" (confirm dialog "ลบผล render นี้?" with "ลบ" / "ยกเลิก").
- States: 1 Default, never rendered ("ยังไม่เคย render reel นี้"). 2 Unsaved edits (dot shown). 3 Listening ("กำลังผสมเสียง…"). 4 Backing on (volume and warning shown). 5 Own picture chosen (thumbnail). 6 Rendering 42% with cancel. 7 Rendered (two rows, newest selected and playing, one with badge "มีเพลงต้นฉบับ"). 8 Render failed: Alert "render ไม่สำเร็จ: {message}" with "ลองอีกครั้ง"; cancelled: "ยกเลิก render แล้ว" with "ลองอีกครั้ง". 9 Field error under the field (e.g. "ช่วงต้องยาว 2–90 วินาที และอยู่ในช่วงแกะ", "หัวเรื่องต้องยาว 1–40 ตัวอักษร"). 10 Not ready: RefusedAlert with FixCommand chips (drum samples, ffmpeg). 11 Busy: "กำลัง render {ชื่อเพลง} อยู่". 12 Song busy: "กำลังแกะเพลงนี้อยู่". 13 Picture refused: "ไฟล์นี้ไม่ใช่ภาพ PNG หรือ JPG" / "ภาพใหญ่เกิน 20 MB" next to the picker. 14 Not picked yet: "แกะโน้ตก่อน แล้วกลับมาทำ reel" with the back link. 15 Not found: back to "แกะเพลง / รายการเพลง". 16 No hits in the stretch: Alert "ช่วงนี้ไม่มีการตีกลอง เลื่อนช่วงหรือกด เริ่มที่การตีแรก", "ฟัง" and "render reel" disabled. 17 Range adjusted after a new pick: Notice "ช่วงแกะเปลี่ยน ช่วงของ reel ถูกปรับเป็น 11.5–30.0 วินาที" and the unsaved dot. 18 Melody-mode song: line "เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์". "ฟัง" is disabled while its request runs.

Step 3 — Preview
- On the existing preview page "Preview", add each screen's default frame in flow order, its state frames under it, at each breakpoint.
- Prototype links: "แกะเพลง / หน้าเพลง" "ทำ reel cover" → Screen 2; Screen 1 "เริ่มช่วงที่การตีแรก" → Screen 1 state 4 → state 3; Screen 2 "← Yellow" → Screen 1; Screen 2 "render reel" → state 6 → state 7; FixCommand → "ติดตั้ง".
- Every action named in step 2 leads to a frame. The system's existing start frame ("ติดตั้ง") stays the start.

Do not include
- BPM, chapters, count-in, teaching labels, or any lesson field on the reel page.
- Editing single notes of the reel, or staff notation.
- A list of reels of its own, or a new tab.
- Fades or ducking of the original song; backing on by default.
- Reels longer than 90 seconds.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```
