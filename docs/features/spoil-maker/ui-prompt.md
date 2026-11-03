# UI prompt: spoil-maker

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พิมพ์ "design docs/features/spoil-maker/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom spoil-maker`

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | หน้าตรวจแก้ (สวิตช์ลายน้ำ และคำเตือนลายน้ำทับข้อความบน) | 7, 11 | D41, D64, D65 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390) |

```text
Design the watermark switch and the overlap warning of the Script review screen of framecraft, a local desktop web app that turns movie clips into narrated vertical Thai recap videos for one creator. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables (brand-accent for "on", border-strong for "off", warning / warning-surface / warning-border for warnings, muted-foreground for dimmed text); icons: Lucide.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; use its existing components page, variables, and preview page.
- Existing screens this feature changes: "Script review" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390). Match its look; only the parts below change.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, touch targets ≥ 44px.

Step 1 — Components
- Reuse: "Alert" tone warning as is (triangle-alert icon, warning surface and border).
- Reuse: "Position cell" for the 44px touch target size.
- New: "Switch" — variants {on, off, on/disabled, off/disabled, focus}; properties {label (for screen readers)}. Track filled brand-accent when on, outlined border-strong when off; the whole control is a 44×44 touch target.
- Change: the watermark row inside "Settings card" — header gets the Switch between the title "ลายน้ำ {n}" and the delete (trash) button; add a variant "off" where the title is muted-foreground and the fields below stay editable.
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens
Frame names: "Script review / {state} / {breakpoint}"; realistic Thai sample data; instances only.

Screen 1 — Script review (redesign of https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390: watermark rows get a switch; the overview card gets an overlap warning)
- Goal: the creator wants to turn a watermark off for one video without deleting it, and to know before rendering when a watermark will cover the text at the top of the video. Comes from step 1 "เลือกคลิป" after a draft is written; goes to step 3 "ผล render" via "render".
- Content:
  - Watermark row header: title "ลายน้ำ {n}"; Switch labelled "แสดงลายน้ำ {n}"; delete button "ลบลายน้ำ {n}". Off: the title is muted, the render does not draw it, its text, position, and size stay as they were. An off watermark still counts toward the limit of 6.
  - Overview card ("ภาพรวมบท", top of the script column): under the text field "Hook" (layout A) or "ชื่อตอน" (layout C) and its hint "ข้อความบนสุดของวิดีโอ", and above the length line, an Alert warning: "ลายน้ำ {n} อยู่บนกลาง จะทับ Hook ในวิดีโอ: ปิดหรือย้ายลายน้ำถ้าไม่ต้องการ" (layout C says "ชื่อตอน" instead of "Hook"; several watermarks list their numbers as "ลายน้ำ 1, 3"). Shown only when a switched-on watermark is at the top-centre position and the top text is not empty; it follows the text as typed. The render button stays enabled.
  - The length line next to it keeps its existing look ("ความยาวประมาณ {s} / {target} วินาที · {n} ประโยค", warning pill when off target).
- States: 1 Default: two watermarks, both on, none at top centre, no warning. 2 Watermark off: watermark 2 switched off, title muted. 3 Overlap warning, layout A: watermark 1 on at top centre, Hook "ศพลุกขึ้นมาเดินได้ คืนนั้นทุกคนต้องหนี", the Alert under the Hook field. 4 Overlap warning, layout C with "ชื่อตอน". 5 Overlap resolved: the same as 3 with watermark 1 switched off, no Alert. 6 Locked (a job is running): the Switch disabled with every other field.

Step 3 — Preview
- On the existing preview page, replace the Script review frames with the new ones (default first, the state frames under it) at 1440 and 375.
- Prototype links: Switch on watermark 1 in state 3 → state 5; Switch in state 5 → state 3; the existing links in and out of Script review stay as they are.
- Every action named in step 2 leads to a frame. The system's existing start frame stays the start.

Do not include
- Moving the watermark or the top text automatically, or blocking the render on overlap.
- One switch that turns every watermark off at once.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom spoil-maker`
