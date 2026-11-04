# UI prompt: spoil-maker

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พิมพ์ "design docs/features/spoil-maker/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom spoil-maker`

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | ตัวบอกขั้นของ tab สปอย | 5, 7, 11, 15 | D68, D71 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) |
| 2 | ตั้งค่าคลิปสปอย (ขั้น 1 เลือกคลิป) | 5, 6, 14 | D66, D67, D69, D70, D71 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681) |
| 3 | หน้าตรวจแก้ (เรียบเรียงใหม่) | 16 | D72, D74, D75, D76 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390) |

```text
Design the new step bar, the new step 1 "เลือกคลิป", and the "เรียบเรียงใหม่" (polish) additions to step 2 "ตรวจแก้บท" of the สปอย tab of framecraft, a local desktop web app that turns a downloaded YouTube video into narrated vertical Thai recap videos for one creator. A spoil is now made from ONE source video, cut by time into episodes (EP 1, EP 2, …); the creator spoils one EP at a time. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables (brand-accent, accent-subtle, link, border, border-strong, muted, muted-foreground, warning tokens); icons: Lucide.
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft; use its existing components page, variables, and preview page.
- Existing screens this feature changes: "3 tab / สปอย" frames with the component "Spoil steps" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) and "Spoiler setup" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681). Match their look; the right-hand settings card (style, layout, length, voice, transcript tokens, "ร่างบท") stays as it is except where noted.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input, touch targets ≥ 44px; a spinner must have a still form for reduced motion.

Step 1 — Components
- Change: "Spoil steps" — remove the "passed" variant with a check mark. Every step shows its number in a circle and looks clickable (hover state); the open step stands out (accent-subtle pill, brand-accent number). Each step has a second, smaller muted line under its label: the status. Add a "running" property: a small spinner beside the number. Add a "failed" property: the status line in the error colour. Mobile: only the open step shows its label and status, but a running step's spinner shows on every step.
- Reuse: "Alert" tone warning and error; "Switch"; the existing radio, select and checkbox inputs; the existing clip row with thumbnail; the existing confirm dialog.
- Change: the sentence card of "Script review" — add a small badge "แก้เอง" next to the sentence number (shown when the creator edited or inserted the sentence).
- New: "Episode row" — variants {default, selected, in draft, disabled/no speech}; properties {number "EP {n}", time range "{h:mm:ss}–{h:mm:ss}", thumbnail, token count "{tokens} / 32,000", renders badge "render แล้ว {k}" (hidden at 0), in-draft badge "อยู่ใน Spoil draft"}. The whole row is one radio choice.
- New: "Cut point" — a thin divider between two Episode rows holding an editable time field "{h:mm:ss}" with the label "จุดตัด EP {n}/{n+1}"; variants {default, editing, error}.
- Auto layout everywhere; colour, type, spacing, and radius bound to the tokens; each state is a variant.

Step 2 — Screens
Frame names: "{screen} / {state} / {breakpoint}"; realistic Thai sample data; instances only.

Screen 1 — ตัวบอกขั้นของ tab สปอย (redesign of the "Spoil steps" component in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633: passed steps no longer look locked; each step shows real status)
- Goal: the creator wants to see where every step stands, notice a job running on another step, and jump back to any step. Sits at the top of every step of the สปอย tab; clicking a step opens it.
- Content:
  - Step 1 "เลือกคลิป": status "{clip title} · EP {n}" when a draft exists, else "ยังไม่เลือก".
  - Step 2 "ตรวจแก้บท": "กำลังร่าง" while the AI writes, "กำลังเลือกภาพ {x}/{y}" while it picks shots, "สร้างเสียง {x}/{y}" while voicing, else "{n} ประโยค", or "ยังไม่มีบท"; failed: "ร่างบทไม่สำเร็จ" or "สร้างเสียงไม่สำเร็จ".
  - Step 3 "ผล render": "render {p}%", "render…" before a percent is known, "render: สร้างเสียง {x}/{y}" while a render voices missing sentences, else "{n} คลิป", or "ยังไม่มี"; failed: "render ไม่สำเร็จ".
- States: 1 Nothing yet (step 1 open, "ยังไม่เลือก", "ยังไม่มีบท", "ยังไม่มี"). 2 Draft ready (step 2 open, "ยอดนักสืบจิ๋วโคนัน EP.171 · EP 2", "12 ประโยค", "3 คลิป"). 3 Rendering while step 1 is open (step 3 spinner, "render 45%"). 4 Drafting (step 2 spinner, "กำลังเลือกภาพ 4/12"). 5 Render failed ("render ไม่สำเร็จ"). 6 Each of states 2 and 3 at mobile 375.

Screen 2 — ตั้งค่าคลิปสปอย, step 1 (redesign of https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681: the multi-select "เลือกตอน" list of clips becomes one clip plus its EP list)
- Goal: the creator picks the one downloaded video, lets the app cut it into EPs, adjusts a cut if needed, picks one EP, and drafts its script. Comes from the สปอย tab or the step bar; goes to step 2 "ตรวจแก้บท" when the draft finishes.
- Content, left card:
  - Section "คลิปต้นฉบับ": the Temp clips as single-choice rows (thumbnail, title, duration). A clip not ready shows "ยังไม่ถอด" with button "ไปถอด" or "ยังไม่บรรยายฉาก" with button "ไปบรรยายฉาก" and cannot be chosen. No ready clip: "ยังไม่มีคลิปที่ถอดและบรรยายฉากแล้ว" with a link to the clip list.
  - Section "แบ่ง EP" (after a clip is chosen): select "ความยาวต่อ EP" with 5, 10, …, 60 "นาที" (default 30); helper "แอปตัดที่ขอบฉากที่ใกล้ที่สุด"; button "ตัดใหม่ตามความยาว" (shown only after a cut was moved by hand).
  - The Episode rows in time order, a Cut point between each pair. The chosen EP is selected; one EP can be chosen at a time.
  - Changing the length after moving a cut by hand asks first: "เปลี่ยนความยาวจะล้างจุดตัดที่เลื่อนเอง" with "เปลี่ยน" and "ยกเลิก".
- Content, right card (unchanged except): the token line reads the chosen EP: "Transcript ของ EP {n}" "{tokens} / 32,000"; the "ร่างบท" button is disabled with a reason when no EP is chosen ("เลือก EP ก่อน"), when the EP has no speech ("EP นี้ไม่มีบทพูด"), or when over 32,000.
- States: 1 No clip chosen. 2 Clip chosen, 2 EPs at 30 นาที, EP 1 selected. 3 A cut being edited. 4 Cut error: "ตัด EP แบบนี้ไม่ได้: ทุก EP ต้องยาวอย่างน้อย 1 นาทีและเรียงตามเวลา" under the field. 5 EP with a draft and renders ("อยู่ใน Spoil draft", "render แล้ว 2"). 6 EP with no speech, draft button disabled. 7 Cuts changed elsewhere after pressing ร่างบท: Alert "การตัด EP เปลี่ยนไป ตรวจช่วงแล้วกดร่างอีกครั้ง". 8 Confirm before changing the length. 9 No ready clip. 10 Drafting: "กำลังเขียนบท" then "กำลังเลือกภาพ {x}/{y}" with "ยกเลิก". Every state at 1440 and 375 (on mobile the cards stack: clip, EP list, settings).

Screen 3 — หน้าตรวจแก้, step 2 (redesign of https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390: a polish button and its dialog; an "edited by me" badge)
- Goal: the creator wants the AI to rewrite the narration so the sentences flow as one story, without losing the sentences they wrote themselves unless they choose to. Stays on this screen.
- Content:
  - Button "เรียบเรียงใหม่" (secondary, next to "สร้างเสียงทั้งหมด" in the footer, with a sparkle or wand icon).
  - Dialog title "เรียบเรียงบทใหม่"; body "AI จะแก้ถ้อยคำให้ประโยคเล่าต่อกัน ภาพและลำดับประโยคไม่เปลี่ยน"; checkbox "เรียบเรียงประโยคที่แก้เองด้วย" (unticked; shown only when some sentence is "แก้เอง"); when ticked, a warning line "ข้อความที่แก้เอง {n} ประโยคจะถูกเขียนทับ ย้อนกลับไม่ได้"; when some sentence has a voice, a note "ประโยคที่เปลี่ยนต้องสร้างเสียงใหม่"; buttons "เรียบเรียง" (primary) and "ยกเลิก". When every sentence is "แก้เอง" and the box is unticked, "เรียบเรียง" is disabled with "ทุกประโยคแก้เองแล้ว: ติ๊กเพื่อเรียบเรียงทับ".
  - While running: the footer shows "กำลังเรียบเรียง" with a progress bar without percent and "ยกเลิก"; every field is locked as in the existing locked state.
  - After: a success Alert "เรียบเรียง {n} ประโยค" or "ไม่มีประโยคที่เปลี่ยน"; failure Alert "AI เรียบเรียงไม่สำเร็จ บทเดิมไม่เปลี่ยน".
- States: 1 Default with two "แก้เอง" sentences. 2 Dialog, box unticked. 3 Dialog, box ticked, with the overwrite warning. 4 Dialog when every sentence is "แก้เอง" (button disabled). 5 Polishing (locked). 6 Done: "เรียบเรียง 9 ประโยค", changed sentences showing "ต้องสร้างเสียงใหม่". 7 Failed. Each at 1440 and 375.

Step 3 — Preview
- On the existing preview page, replace the step bar instances and the step 1 frames of the สปอย tab with the new ones (default first, the state frames under it) at 1440 and 375.
- Prototype links: Screen 3 "เรียบเรียงใหม่" → state 2; tick → state 3; "เรียบเรียง" → state 5 → state 6; choose a clip in Screen 2 state 1 → state 2; click a Cut point time in state 2 → state 3; "ร่างบท" in state 2 → state 10; state 10 → the existing "ตรวจแก้บท" frame; each step in the step bar → that step's existing frame. The existing links in and out of the สปอย tab stay as they are.

Do not include
- Choosing several clips, or drafting several EPs at once.
- A list of saved drafts.
- Dragging cut points on a timeline.
- Undoing a polish, or polishing a single sentence.
- Any field, step, screen, or feature not listed above.

Deliver: the components made or changed, the screen frames, and the preview's start link.
```

นำลิงก์กลับมาด้วย `/warroom spoil-maker`
