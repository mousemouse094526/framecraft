# Progress: spoil-maker

**Now:** 00 done — แอปมี 3 tab และแก้ Transcript ทีละบรรทัดได้; ต่อไป 01 (Qwen, ช่อง GPU, ดูภาพ)

**Next:**

```
/warroom-build spoil-maker 01
```

## Tickets

| # | Title | Status |
|---|---|---|
| 00 | แถบ 3 tab และแก้ Transcript | done |
| 01 | ติดตั้ง Qwen, ช่อง GPU และดูภาพ | ready |
| 02 | Saved voice | ready |
| 03 | ร่างบทและหน้าตรวจแก้ | ready |
| 04 | เสียงต่อประโยคและ render | ready |

## Log

### 00: แถบ 3 tab และแก้ Transcript — done 2026-11-01

**Built:**
- แถบ tab 3 tab ติดตั้ง (`#/setup`) · คลิป (`#/clips`) · สปอย (`#/spoil`); hash ว่างหรือไม่รู้จัก → ติดตั้ง, `#/spoil/…` → สปอย. `lib/useHashTab.ts` → `lib/useHash.ts` (`useHash`, `tabOf`); nav ของแถบมีชื่อ "แถบ tab"
- tab คลิป: หน้าเดิมของ spoil (`SpoilPage` → `ClipsPage`) ย้ายมาทั้งหน้า; ลิงก์ติดตั้งไม่ครบเป็น "ไปหน้าติดตั้ง"
- tab สปอย (`features/spoil-maker`): `SpoilSteps` ตาม component `Spoil steps` — ขั้นปัจจุบันเด่น ขั้นที่ผ่านมีเครื่องหมายถูก ขั้นอื่นเป็นลิงก์ hash, มือถือแสดงชื่อเฉพาะขั้นปัจจุบัน; ใต้ตัวบอกขั้นยังว่าง (03, 04 ใส่)
- API: `PATCH /api/spoil/clips/{id}/transcript/lines/{n}` → `200` บรรทัดพร้อม `edited: true` เขียนผ่าน `.tmp` ใต้ lock ของงานถอด; `400` `invalid_request`, `404` `not_found`, `409` `transcribing`, `409` `clip_busy` (ผ่าน `transcribe.clip_users`); ข้อความรวมเป็นบรรทัดเดียว; `POST /transcriptions` ของคลิปที่มีบรรทัด `edited` → `409` `has_edits` เว้นแต่ `confirm_edit_loss: true`; `require_json` ครอบ `PATCH`
- หน้าเว็บ: `TranscriptLineItem` ตาม component `Transcript line` (hover "แก้", editing, edited "แก้แล้ว"); Enter บันทึก, Escape ยกเลิก; `409`/`404` แสดงใต้ช่องโดยช่องยังเปิด; ถอดใหม่ได้ `has_edits` → `confirm` แล้วส่งซ้ำ. `GHOST_BUTTON` ใหม่ใน `buttonStyles`; icon pencil และ check จาก Figma
- bug ที่เจอตอนเช็คใน browser: `<video>` กับรายการบรรทัดใช้ key เดียวกัน (React เตือน key ซ้ำ) → แยก key; test "closes the field when another clip is selected" ครอบ
- เช็คมือผ่าน Vite proxy กับ backend จริง: 1440 tab คลิป แก้บรรทัดของ Shorts NASA → บันทึกแล้วขึ้น "แก้แล้ว", ชี้บรรทัดอื่นขึ้น ✎ แก้ ตรง frame "คลิป — แก้ประโยค"; tab สปอย `#/spoil/review` ที่ 1440 และ 375 ตรง frame (375 แสดงชื่อแค่ขั้นปัจจุบัน); 375 tab คลิปไม่มี scroll แนวนอนและจอสัมผัสเห็นปุ่มแก้ตลอด. Transcript ที่แก้ตอนลองคืนจาก backup แล้ว
- README: 3 tab และการแก้บทพูด; skill `vite-react-web` (`useHash.ts`, hash ของขั้น), `fastapi-api` (`PATCH` ต้องเป็น JSON)

**Decided:**
- D55 — ทางเลือกเล็ก: ชื่อ `ClipsPage`/`SpoilMakerPage`/`useHash.ts`, `#/spoil/…` ไม่รู้จัก = ขั้น 1, ขั้นยังว่าง, `clip_users`, `n` เป็นข้อความ ASCII, ลำดับการเช็ค, `PATCH` ต้องเป็น JSON, บรรทัดเดียวเสมอ, ปุ่มแก้บนจอสัมผัส, error ใต้ช่อง, confirm ด้วย `message` ของ `has_edits`

**For the next ticket:**
- 03: Draft job ต้องใส่ check ของตัวเองใน `backend.spoil.transcribe.clip_users` (คืน `True` เมื่อใช้คลิปนั้น) และเปลี่ยน test `clip_busy` ที่ใช้ check ปลอมเป็น Draft job จริง; เพิ่ม test "คลิปใน Spoil draft ที่ไม่มีงาน → `PATCH` `200`" (Seam 1) ที่ ticket นี้ทำไม่ได้เพราะยังไม่มี Spoil draft
- 01: `POST /transcriptions` รับ `confirm_edit_loss` แล้ว — `confirm_draft_loss` และ `gpu_busy` ต่อท้ายลำดับการเช็คเดียวกัน (gate → `404` → `busy` → `has_edits`)
- 02: `#/spoil/voices` ตอนนี้เปิดขั้น 1; ตัดสินว่าหน้า Saved voice แสดงตัวบอกขั้นหรือไม่
- ADR-0013 ยังเขียนว่า "ทุก POST"; spec ของ spoil-maker ขยายเป็น POST และ PATCH แล้ว (โค้ดทำตาม) — แก้ข้อความ ADR ตอน feature review ถ้าผู้ใช้ตกลง
- review ที่ไม่ได้แก้: `_has_edits` อ่าน Transcript ทั้งไฟล์ในตัว `start` (ไฟล์เล็ก ไม่เป็นปัญหา); บรรทัดที่เริ่มวินาทีเดียวกันได้ชื่อ `aria-label` ซ้ำ; ทดสอบ "มือถือแสดงชื่อเฉพาะขั้นปัจจุบัน" เช็คด้วยมือใน browser ไม่มี test (jsdom ไม่มี layout)

**Checks:** `uv run pytest` — 189 passed; `npm --prefix frontend test` — 88 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: แถว Temp clip ใน tab คลิป | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8032-2275)) |
| 2 | 02 | design: Saved voice | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220)) |
| 3 | 03 | design: ตั้งค่าคลิปสปอย | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681)) |
| 4 | 03 | design: หน้าตรวจแก้ (ใช้ต่อใน 04) | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390)) |
| 5 | 03 | design: ตัวเลือก Shot | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8050-16186)) |
| 6 | 04 | design: ผล render | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850)) |
| 7 | 00 | design: แถบ 3 tab, ตัวบอกขั้นของ tab สปอย และ Transcript ที่แก้ได้ใน tab คลิป (D53, D54) | `/warroom spoil-maker` พร้อมลิงก์แบบ | done (Figma 8071-18633) |
