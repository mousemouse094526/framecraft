# UI prompt: spoil-maker

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พิมพ์ "design docs/features/spoil-maker/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom spoil-maker`

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | ตั้งค่าคลิปสปอย (ขั้น 1 เลือกคลิป) | 5, 6, 14 | D82, D84, D87 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) |
| 2 | หน้าตรวจแก้ (ขั้น 2 ระหว่างร่างและร่างล้ม) | 7, 14 | D81, D83, D85, D86, D87 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833) |

```text
Design the drafting flow of the สปอย tab of framecraft, a local desktop web app that turns a downloaded YouTube video into narrated vertical Thai recap videos for one creator. After the creator presses "ร่างบท" on step 1 "เลือกคลิป", the app now opens step 2 "ตรวจแก้บท" at once and shows the draft's progress there; step 1 is read-only until the draft ends or is cancelled. The style cards on step 1 get a one-line hint. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables (surface, border, text, accent-subtle, accent-strong, warning, error, info); icons: Lucide.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; components and frames of this flow live in section "framecraft — สปอย / EP & เรียบเรียง (D66–D76)" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833); the 3-tab preview frames are in "framecraft — 3 tab" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633).
- Existing screens this flow changes: "Spoiler setup / …" frames (step 1) and "Script review / …" frames (step 2) in the EP & เรียบเรียง section. Match their look.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, touch targets ≥ 44px; a progress bar without percent and a spinner have a still form for reduced motion.

Step 1 — Components
- Change: "Style option" — add a second line under the label, small and muted: "ปั่นตัดเร็ว" → "ประโยคสั้น ตลก เร็ว เล่าเหตุการณ์เด่น"; "เล่าละครหักมุม" → "hook เรื่อง หักมุม แรงจูงใจ คำถามชวนคอมเมนต์ท้ายคลิป"; "เล่าตามลำดับ" → "เล่าทีละฉากตามเวลา มีบทพูดตัวละครแทรกได้". Add a "disabled" state (read-only, selected or not).
- Change: "Source clip row", "Episode row", "Cut point", "Layout option", "Length slider", "Select" — a "disabled" (read-only) state where missing, keeping the selected look readable.
- Change: "Draft action" — the "writing" and "picking" states are no longer used on step 1; keep them for history, no new use.
- New: "Draft progress card" — variants {writing, polishing, matching, cancelling}; content: title "{clip title} · EP {n}", meta line "{style} · {target} วินาที", a list of three phases "เขียนบท", "เรียบเรียง", "เลือกภาพ {x}/{y}" each with a status icon {done, running, waiting}, a progress bar (no percent until matching, then x/y), button "ยกเลิก" (outline). cancelling: the card says "กำลังยกเลิก" and the button is disabled.
- Reuse: "Alert" tones info, error, warning; the existing confirm pattern of "Draft action / replace confirm" ("มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม", "ร่างทับ", "ยกเลิก").
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens
Frame names: "{screen} / {state} / {breakpoint}"; realistic Thai sample data (clip "ยอดนักสืบจิ๋วโคนัน EP.171", EP 1, style เล่าละครหักมุม, 60 วินาที, voice "ลุงเล่าผี"); instances only.

Screen 1 — ตั้งค่าคลิปสปอย, step 1 (redesign of the "Spoiler setup / …" frames in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833: style hints; a read-only state while a draft runs)
- Goal: the creator compares styles before drafting; while a draft runs, they see what was sent and cannot change it until they cancel on step 2.
- Content:
  - Style cards: each shows its hint line (above).
  - While a draft runs: every field shows the values of the running draft (clip, EP, style, layout, length, voice) and is disabled; the "ร่างบท" button is not shown; an info Alert at the top "กำลังร่างบท {clip title} · EP {n}: ยกเลิกการร่างก่อนจึงเลือกใหม่ได้" with link "ไปที่ตรวจแก้บท".
  - The step bar's step 1 status reads "{clip title} · EP {n}" and step 2 shows the spinner with "กำลังร่าง".
- States: 1 Default with style hints. 2 Locked while drafting. 3 Locked, the draft's clip no longer in the list (only its title shown, no EP list). 4 Locked, the draft's voice deleted: voice field "เสียงถูกลบแล้ว". 5 Another tab already drafting: error Alert "มีงานร่างบทอยู่แล้ว" then the locked state. Each at 1440 and 375.

Screen 2 — หน้าตรวจแก้, step 2 (redesign of the "Script review / …" frames in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8083-27833: a progress card while drafting, and the failed-draft states)
- Goal: right after pressing ร่างบท the creator waits here, sees how far the draft is, and can cancel; when it fails they retry or go back to change the setup.
- Content:
  - While drafting: the Draft progress card replaces the script (writing → polishing → matching "เลือกภาพ 4/12"). "ยกเลิก" → "กำลังยกเลิก" → back to step 1 with the values still selected.
  - Cancelled too late: the new script with an info Alert "ยกเลิกไม่ทัน บทร่างเสร็จแล้ว".
  - Failed: an error Alert "AI ร่างบทไม่สำเร็จ 3 ครั้ง" with buttons "ลองอีกครั้ง" and "กลับไปแก้ตั้งค่า", above the previous script (still editable) or the existing empty state "ยังไม่มีบท".
  - "ลองอีกครั้ง" with a previous script: the replace confirm "มี Spoil draft อยู่แล้ว: ร่างใหม่จะทับของเดิม" with "ร่างทับ" and "ยกเลิก" before sending.
  - Retry refused because the cut changed: the same Alert reads "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง" with "กลับไปแก้ตั้งค่า".
  - Backend stopped mid-draft: Alert "งานหยุดกลางทาง" with "กลับไปแก้ตั้งค่า".
- States: 1 Writing. 2 Polishing. 3 Matching 4/12. 4 Cancelling. 5 Cancelled too late. 6 Failed, no previous script. 7 Failed over a previous script. 8 Retry confirm. 9 Retry refused (cut changed). 10 Job lost. Each at 1440 and 375.

Step 3 — Preview
- In the EP & เรียบเรียง section, add these frames under the existing ones, default first, at 1440 and 375.
- Prototype links: "Spoiler setup / 2 Clip chosen — 2 EPs" "ร่างบท" → Screen 2 state 1 → 2 → 3 → the existing "3 tab / สปอย 2 ตรวจแก้บท" frame; Screen 2 "ยกเลิก" → state 4 → Screen 1 default with the values selected; Screen 2 state 6 "กลับไปแก้ตั้งค่า" → Screen 1 default; "ลองอีกครั้ง" in state 7 → state 8 → state 1; the step bar's step 1 in Screen 2 states 1–3 → Screen 1 state 2; its link "ไปที่ตรวจแก้บท" → Screen 2 state 1. The existing links stay as they are.

Do not include
- Choosing several clips, or drafting several EPs at once.
- Cancelling the draft from step 1.
- A list of saved drafts or of past draft jobs.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom spoil-maker`
