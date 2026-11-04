# UI prompt: spoil

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/spoil/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom spoil`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | ส่วนตัดช่วง | 12, 13 | D36, D37, D38, D40, D41, D42 | new |

```text
Design one addition to framecraft, a local desktop web app that downloads YouTube videos and turns them into narrated vertical Thai recap videos for one creator: a trim section in the คลิป tab where the user marks time ranges (intro ads, opening and ending songs, next-episode previews) on the selected clip's timeline and cuts them out of the video file for good. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables on page ":: Token" (surface, border, text mid/subtle, accent, destructive); components there: Button, Field, Alert, Badge; icons: Lucide (scissors, plus, x, clock).
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; the คลิป tab is frame "3 tab / คลิป" in section "framecraft — 3 tab" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633); components "Transcript panel" (all states), "Player", "Clip row" (property "Show transcribed"), "Download progress" are in section "framecraft — สปอย" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281).
- Existing screens this connects to: "3 tab / คลิป" (clip selected, not transcribed) and "3 tab / คลิป" transcribed. Match their look.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input and icon button, touch targets ≥ 44px; timeline handles are sliders reachable by keyboard.

Step 1 — Components
- Reuse: "Download progress" as is (with and without a number); "Alert" success, info, warning, error; "Button" primary, secondary, ghost, disabled; "Field" with error state.
- Change: "Clip row" — new boolean property "Show trimmed": a Badge "ตัดแล้ว" placed before "ถอดแล้ว".
- Change: "Transcript panel" — under the clip title and length a secondary button "ตัดช่วง" (scissors icon); new state "trim open" that holds the "Trim section" instance between the title block and the "ถอดบทพูด" button; in that state "ถอดบทพูด" is disabled with the helper text "กดตัดคลิปหรือยกเลิกก่อน".
- New: "Trim timeline" — a full-width bar the length of the clip; marked ranges are filled blocks (accent at reduced opacity) with a handle at each end; a thin playhead marker; variants: empty, one range, several ranges, handle focused, handle dragging; properties: number of ranges, playhead position.
- New: "Trim range row" — "{n}." then two time Fields "เริ่ม" and "จบ" (format h:mm:ss.s, e.g. "0:01:30.0"), ghost buttons "เริ่ม = ตอนนี้" and "จบ = ตอนนี้", icon button x (aria-label "ลบช่วง {n}"); variants: default, field error.
- New: "Trim section" — heading "ตัดช่วง", "Trim timeline", the list of "Trim range row", button "+ เพิ่มช่วง", summary line "ตัดออก {x} · เหลือ {y}" (e.g. "ตัดออก 4:22 · เหลือ 1:53:40"), primary button "ตัดคลิป", secondary button "ยกเลิก"; variants: editing, editing with error (ตัดคลิป disabled), trimming, replacing.
- Auto layout everywhere; colour, type, spacing and radius bound to the tokens; each state is a variant.

Step 2 — Screens
Frame names: "คลิป — ตัดช่วง / {state} / {breakpoint}"; realistic sample data in Thai (a 1:58:02 film); instances only.

Screen 1 — ส่วนตัดช่วง (new), inside the right-hand box of the คลิป tab, under the player
- Goal: the creator wants to remove ads and opening or ending songs before transcribing. Comes from "3 tab / คลิป" via the "ตัดช่วง" button; returns to the same box when done or cancelled.
- Content:
  - Timeline: click an empty spot moves the playhead there; drag a handle to change a range end; handles never cross each other or a neighbouring range.
  - Range rows: time Fields "เริ่ม" and "จบ" required, format h:mm:ss.s; a bad value shows the field error "เวลาไม่ถูกต้อง".
  - Button "+ เพิ่มช่วง": adds a 30-second range at the playhead; disabled at 20 ranges or when no free space.
  - Summary "ตัดออก {x} · เหลือ {y}".
  - Button "ตัดคลิป": disabled when there is no range, a field is in error, or less than 10 seconds would remain.
  - Button "ยกเลิก": closes the section and clears the ranges.
- States: 1 Closed: the box with the "ตัดช่วง" button. 2 Empty: section open, no range yet, "ตัดคลิป" disabled. 3 Editing: two ranges 0:00:00.0–0:01:30.0 and 1:55:10.0–1:58:02.0, summary "ตัดออก 4:22 · เหลือ 1:53:40". 4 Field error: one field "1:99" with "เวลาไม่ถูกต้อง", "ตัดคลิป" disabled. 5 Confirm: browser confirm dialog shown over state 3 with "ตัดคลิปจะลบ Transcript (รวมบรรทัดที่แก้ไว้), ภาพฉากและการตัด EP, Spoil draft ของคลิปนี้ ตัดต่อไหม?" (draw it as a plain system-style dialog). 6 Trimming: the player is empty, "กำลังตัดคลิป" with "Download progress" at 37% and "37%" on the right, button "ยกเลิก". 7 Cancelling: "กำลังยกเลิก…", the cancel button disabled. 8 Replacing: "กำลังแทนไฟล์…" with "Download progress" without a number, no cancel button. 9 Done: Alert success "ตัดคลิปเสร็จ: เหลือ 1:53:40", the section closed, the player loaded again, the clip row shows "ตัดแล้ว". 10 Cancelled: Alert info "ยกเลิกแล้ว", the ranges still there. 11 Failed: Alert error "แทนไฟล์ไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง", the ranges still there. 12 Lost: Alert warning "งานตัดหายเพราะ backend เริ่มใหม่ ลองตัดอีกครั้ง". 13 Another clip trimming: "ตัดช่วง" disabled with "กำลังตัด {ชื่อคลิปนั้น}".
- Mobile 375: the คลิป tab is stacked (list, arrow down, box); the trim section uses the full box width, range rows wrap the two fields onto one line and the three buttons onto the next, handles keep a 44px touch area. Draw states 3, 6 and 9 at 375.

Step 3 — Preview
- On the existing preview page of the file, add the default frame of Screen 1 after "3 tab / คลิป", with its state frames under it, at both breakpoints.
- Prototype links: "3 tab / คลิป" "ตัดช่วง" → state 2; state 2 "+ เพิ่มช่วง" → state 3; state 3 "ตัดคลิป" → state 5; state 5 OK → state 6; state 6 → state 8 → state 9; state 6 "ยกเลิก" → state 7 → state 10; state 3 "ยกเลิก" → "3 tab / คลิป"; state 9 → "3 tab / คลิป" with the "ตัดแล้ว" row.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- Keeping the original video or undoing a cut.
- Playing the video while skipping the marked ranges before cutting.
- Automatic detection of ads or songs.
- Hiding single Transcript lines.
- Any other video editing (reordering, inserting, effects), or any field, step, screen or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom spoil`.
