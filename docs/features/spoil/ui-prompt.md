# UI prompt: spoil

วาง block ด้านล่างครั้งเดียวในเครื่องมือออกแบบ หรือใน Claude Code ที่มี Figma MCP พูดว่า "design docs/features/spoil/ui-prompt.md in https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft" แล้วนำลิงก์กลับมาด้วย `/warroom spoil`.

| # | Screen | User stories | Decisions | Now |
|---|---|---|---|---|
| 1 | tab คลิป — ช่องลิงก์และการเลือกไฟล์ | 2, 3, 6, 7, 14, 15 | D47, D49, D50, D51, D52, D54, D55 | [redesign](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) |

```text
Design one change to framecraft, a local desktop web app where one Thai creator brings source videos in and turns them into narrated recap clips: the link area at the top of the คลิป tab now takes a video link from YouTube or any other site the app can download, and also lets the user pick or drag in an mp4 file from their computer. Steps, in order: 1 Components, 2 Screens, 3 Preview.

Context
- Platform: web app; breakpoints: mobile 375, desktop 1440.
- Design system: the one already in the Figma file (React + Tailwind CSS in code); tokens: the file's variables on page ":: Token" (surface, border, text mid/subtle, accent, destructive); components there: Button, Field, Alert, Badge; icons: Lucide (link, upload, file-video, x).
- Figma file: https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft. Current link area: section "framecraft — สปอย" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) frames 1–13 and component "Download progress"; the คลิป tab in "framecraft — 3 tab" (https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633). Component "Clip row".
- What changes: the link field is no longer YouTube-only; a file picker and a drop area are added beside or under it; "Download progress" gains file-sending states; "Clip row" shows the site name or "ไฟล์ในเครื่อง". Everything else in the tab stays as it is.
- Language on screen: Thai. Use the copy below exactly.
- Accessibility: WCAG 2.2 AA contrast, visible focus, a label on every input and icon button, touch targets ≥ 44px; the drop area is also a keyboard-reachable button.

Step 1 — Components
- Field (existing): link input, placeholder "วางลิงก์คลิป (YouTube, Facebook, TikTok …)".
- New "File drop": variants default, drag-over (accent border and fill), disabled. Content: icon upload, button "เลือกไฟล์ในเครื่อง", hint "หรือลากไฟล์ mp4 มาวาง · รับ mp4 (H.264, AAC) ไม่เกิน 1080p".
- Download progress (existing): add variants importing ("กำลังเอาไฟล์เข้า {ชื่อไฟล์}", progress bar with %, button "ยกเลิก") and checking-file ("กำลังตรวจไฟล์…", indeterminate bar, no cancel button).
- Clip row (existing): add property "Source" = site | local; site shows "{ชื่อช่อง} · {ชื่อเว็บ}", local shows "ไฟล์ในเครื่อง" in place of the channel.

Step 2 — Screens (desktop 1440 and mobile 375 for each state; the clip list and transcript panel stay as they are below)
1. Idle: link field with "โหลด" button, then File drop; list below. Empty list text "ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน".
2. Drag-over: File drop in drag-over state.
3. Importing at 42%: Download progress importing; link field, "โหลด" and File drop disabled.
4. Checking file: Download progress checking-file.
5. Import done: Alert success "เอาไฟล์เข้าเสร็จ: {title}"; new row on top with Source local, highlighted.
6. File errors, one frame each as Alert error under the link area:
   - "รับเฉพาะไฟล์ mp4 แปลงไฟล์เองก่อน"
   - "ภาพเป็น hevc แปลงเป็น mp4 (H.264, AAC) ไม่เกิน 1080p ด้วยโปรแกรมอื่นแล้วลองอีกครั้ง"
   - "เอาไฟล์เข้าไม่สำเร็จ ลองอีกครั้ง"
   - "เอาเข้าได้ทีละไฟล์" (warning)
7. File duplicate: Alert "ไฟล์นี้เอาเข้าไว้แล้ว" and the existing row highlighted.
8. Link errors that point to the file picker, Alert error with the "เลือกไฟล์ในเครื่อง" button of File drop visually emphasised:
   - "เว็บนี้โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด \"เลือกไฟล์ในเครื่อง\""
   - "เว็บนี้ขอให้ login หรือยืนยันว่าไม่ใช่ bot โหลดอัตโนมัติไม่ได้ โหลดคลิปเองแล้วกด \"เลือกไฟล์ในเครื่อง\""
   - "เว็บนี้ไม่มีไฟล์ H.264 ไม่เกิน 1080p ให้โหลด โหลดเองแล้วแปลง จากนั้นกด \"เลือกไฟล์ในเครื่อง\""
9. Other link errors: "ลิงก์นี้ใช้ไม่ได้ วางลิงก์ http หรือ https ของคลิป", "ลิงก์นี้เป็น playlist วางลิงก์ของคลิปเดียว", "กำลังโหลดหรือเอาไฟล์อื่นเข้าอยู่".
10. List with mixed sources: one YouTube row, one row "ชื่อช่อง · Facebook", one row "ไฟล์ในเครื่อง".

Step 3 — Preview
- Add these frames to the existing preview page and wire them: Idle → Drag-over → Importing → Checking file → Import done; Idle → each error frame and back on dismiss; link "โหลด" keeps its existing downloading frames.

Do not include
- File conversion, multiple-file queues, cookies or login for sites, a list of supported sites, a copyright warning.

Bring the Figma link back with /warroom spoil.
```
