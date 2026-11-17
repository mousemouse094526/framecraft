# UI prompt: kalimba-cover

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/kalimba-cover/ui-prompt.md in {ลิงก์ไฟล์ Figma}"; หน้าเว็บทำตาม block นี้กับ design system เดิม ไม่รอ Figma (D10); แบบ Figma ถ้าทำภายหลังเป็น change request ผ่าน `/warroom kalimba-cover`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | หน้า reel — ส่วนที่เพิ่ม | 1, 2, 3, 4, 6 | D1, D4, D9, D10, D14 | new (ส่วนเพิ่มในหน้า reel ของ drum-cover) |
| 2 | หน้าเพลงและรายการเพลง — ส่วนที่เพิ่ม | 5, 6 | D2, D3, D13 | new (ข้อความเพิ่มในหน้าเดิมของ drum-notes) |

```text
Design the kalimba additions to the "Reel cover" screens of framecraft: a local desktop web app, used by one person on their own Mac, that makes short vertical clips. The reel page already makes a vertical drum cover from a song's found drum hits; this feature lets the same reel be rendered as a KALIMBA cover instead (the song's melody notes, arranged onto a 17-key C-major kalimba, notes falling onto the tines), from the same stretch, texts, background and backing. MIDI files with melody only can now be imported as songs. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app in a desktop browser; breakpoints: desktop 1440 (primary), narrow 1024. Touch targets ≥ 44px below 640px. No mobile.
- Design system: the project's existing Tailwind tokens and components; dark neutral page, white text, one accent for primary actions, Thai-friendly sans for UI. Match the existing "แกะเพลง / หน้า reel", "แกะเพลง / หน้าเพลง" and "แกะเพลง / รายการเพลง" screens exactly; this is an addition, not a redesign.
- Figma file: the project's framecraft file; components on "Components", tokens on "Tokens", preview on "Preview". If these pages do not exist, create them.
- Existing screens this feature connects to: "แกะเพลง / หน้า reel" (Screen 1 adds to it), "แกะเพลง / หน้าเพลง" and "แกะเพลง / รายการเพลง" (Screen 2 adds lines to them).
- Language on screen: Thai. Use the copy below exactly. Code-like tokens (mp4, MIDI, .mid) stay Latin.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, click targets ≥ 44px.

Step 1 — Components
- Reuse as is: "Feedback/Alert", "Feedback/RefusedAlert", "Cover/ActionBar", "Cover/RangeCard", "Drums/BackgroundPicker", "Songs/CoverSection".
- New: "Cover/SegmentedChoice" — a radiogroup of two pill buttons, the same look as the existing "กลองล้วน" | "กลอง + เพลงต้นฉบับ" control; properties {label 1, label 2, aria label}; variants {first selected, second selected, second disabled}. Used for the instrument choice and the sound choice.
- New: "Cover/InstrumentCard" — card titled "เครื่องดนตรี" holding a SegmentedChoice "กลอง" | "คาลิมบา"; with คาลิมบา, a line under it: "{n} โน้ตทำนองในช่วง", then " · ย้ายคีย์ {+k}" when the key moved, then " · ตัด {d} โน้ต" when notes were dropped, then " · ปรับ {b} โน้ตให้เข้าสเกล" when notes were bent into the scale; variants {drums, kalimba, kalimba moved dropped and bent}.
- Change: "Cover/SoundChoice" — the voice row is one component with property {instrument label: "กลอง" or "คาลิมบา"}: switch "ปิดเสียง{label}", slider "ความดัง{label}" 10–100 (hidden while off); choice labels "{label}ล้วน" | "{label} + เพลงต้นฉบับ"; variants {on, off, silent error}.
- Change: "Cover/RenderRow" — add badges "คาลิมบา", "คาลิมบา {v}%", "ไม่มีเสียงคาลิมบา".
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens (one section per screen)
Frame names: "{screen} / {state} / {breakpoint}"; realistic sample data in Thai (song "Yellow (kalimba)", channel "DRUMMATE"); instances only.

Screen 1 — หน้า reel, additions (new parts on the existing reel page)
- Goal: the clip maker wants a kalimba reel of the same stretch. Comes from "แกะเพลง / หน้าเพลง" via "ทำ reel cover"; stays on this page to listen and render.
- Content:
  - InstrumentCard is the FIRST card, above "ช่วงของ reel". Default selected: "กลอง". A melody-only MIDI song opens with "คาลิมบา" selected.
  - Switching the instrument marks the form "ยังไม่บันทึก" (existing dot on ActionBar "บันทึก").
  - With คาลิมบา: the "เสียง" card shows the kalimba voice row ("ปิดเสียงคาลิมบา", "ความดังคาลิมบา" 10–100 default 100) and "คาลิมบาล้วน" | "คาลิมบา + เพลงต้นฉบับ"; the existing backing volume, the existing copyright warning and the MIDI "เพลงจาก MIDI ไม่มีเสียงต้นฉบับ" disabled state stay as they are.
  - With คาลิมบา the line "เพลงนี้แกะโหมดทำนอง reel มีแต่สแนร์" and the Alert "ช่วงนี้ไม่มีการตีกลอง…" are not shown.
  - Render list rows show "คาลิมบา" for kalimba renders, plus "คาลิมบา {v}%" when the volume is not 100 and "ไม่มีเสียงคาลิมบา" when the kalimba was off.
- States: 1 Default (กลอง, as today). 2 คาลิมบา: "48 โน้ตทำนองในช่วง · ย้ายคีย์ +2 · ตัด 3 โน้ต · ปรับ 4 โน้ตให้เข้าสเกล". 2b คาลิมบา with backing on and the key moved: warning under the backing choice "คาลิมบาย้ายคีย์ +2 เสียงจะไม่ตรงกับเพลงต้นฉบับ". 3 Not picked for kalimba: Alert "เพลงนี้แกะก่อนมีคาลิมบา แกะใหม่ที่หน้าเพลงเพื่อได้โน้ตทำนอง" with a link back to the song page (a MIDI song instead: "เพลงนี้นำเข้าก่อนมีคาลิมบา นำเข้าไฟล์ MIDI เดิมอีกครั้ง" with a link to the song list); "ฟัง" and "render reel" disabled. 4 No notes: Alert "ช่วงนี้ไม่มีโน้ตทำนอง เลื่อนช่วงหรือเลือกกลอง"; "ฟัง" and "render reel" disabled. 5 Silent: kalimba off and no backing → "เปิดเสียงคาลิมบาหรือเพลงต้นฉบับอย่างน้อยหนึ่งอย่าง" under the voice row; "ฟัง" and "render reel" disabled. 6 Listening and rendering: the existing ActionBar states. 7 Error: a refused listen or render shows its message in the existing RefusedAlert. 8 Done: the new render row selected, badge "คาลิมบา".

Screen 2 — หน้าเพลงและรายการเพลง, additions (new lines on existing pages)
- Goal: the clip maker brings in a melody MIDI file and sees that a song has melody notes.
- Content:
  - "แกะเพลง / รายการเพลง", hint under "เลือกไฟล์ในเครื่อง": keep the existing hint and add "MIDI: ช่อง 10 เป็นกลอง ช่องอื่นเป็นทำนองสำหรับคาลิมบา" and "ใช้ไฟล์ MIDI ที่ทำเองหรือมีสิทธิ์ใช้".
  - Refused MIDI file message: "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลองหรือโน้ตทำนอง".
  - "แกะเพลง / หน้าเพลง", "Reel cover" section line: existing "ช่วงแกะ {start}–{end} วินาที · {n} การตี · render แล้ว {m} ครั้ง" plus " · {m} โน้ตทำนอง" when the song has melody notes.
- States: 1 Default with the new hint. 2 Error: the refused MIDI message. 3 Song with notes: "… · 120 โน้ตทำนอง". 4 Song picked before this feature: the line without the notes part.

Step 3 — Preview
- On the existing preview page "Preview", add each screen's default frame next to the screen it extends, its state frames under it, at each breakpoint.
- Prototype links: "แกะเพลง / หน้าเพลง" "ทำ reel cover" → Screen 1 default; Screen 1 "คาลิมบา" → state 2; state 3 link → "แกะเพลง / หน้าเพลง"; Screen 1 "render reel" → state 6 → state 8; "แกะเพลง / รายการเพลง" file choice → Screen 2 state 1 → the new song's page.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- MusicXML, PDF or image sheet import.
- A kalimba with other keys, chromatic tines, or a key chooser.
- Editing notes or choosing how they are arranged.
- A reel with drums and kalimba together.
- A MIDI track picker.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

ทำแบบใน Figma แล้ว เอาลิงก์กลับมาด้วย `/warroom kalimba-cover`.
