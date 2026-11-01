# 00: แถบ 3 tab และแก้ Transcript

**What to build:** แถบ tab ด้านบนเป็น 3 tab ตามลำดับ ติดตั้ง (`#/setup`) · คลิป (`#/clips`) · สปอย (`#/spoil`). หน้าเดิมของ tab สปอยของ spoil (ช่องลิงก์, แถบโหลด, รายการ Temp clip, กล่องถอดบทพูด) ย้ายไป tab คลิปแบบสองคอลัมน์เดิม และปรับหน้าตาทั้งหน้าให้ตรง Figma frame "คลิป". tab สปอยมีตัวบอกขั้น 1 เลือกคลิป → 2 ตรวจแก้บท → 3 ผล render ที่ `#/spoil`, `#/spoil/review`, `#/spoil/renders` (เนื้อหาของแต่ละขั้นมาใน ticket 03 และ 04). ใน tab คลิปผู้ใช้แก้ข้อความ Transcript ทีละบรรทัด และถอดใหม่ของคลิปที่แก้แล้วต้องยืนยันก่อน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D53, D54; spoil D9, D10, D25, D33, D34 (ส่วนที่ D53 เปลี่ยน)
- ADR: 0018
- Screens: แถบ tab, Transcript ที่แก้ได้ใน tab คลิป, ตัวบอกขั้นของ tab สปอย — [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633)
- Seams: 1 (`PATCH .../transcript/lines/{n}`, `has_edits`), 2 (แถบ tab, route, แก้บรรทัด)
- User stories: 13; spoil 1

**Status:** ready-for-agent

## Acceptance criteria

### แถบ tab และ route

- แถบ tab แสดง "ติดตั้ง" · "คลิป" · "สปอย" ตามลำดับนี้ tab ที่เปิดอยู่เด่นกว่า; ไม่มี hash หรือ hash ไม่รู้จัก → tab ติดตั้ง
- `#/clips` เปิดหน้าเดิมของ spoil ทั้งหมด (ช่องลิงก์ รายการ กล่องถอด) สองคอลัมน์ ≥1024 และเรียงบนลงล่างที่จอแคบ
- หน้าตาตรง [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633) ทุก state ที่ 375 และ 1440: แถบ tab ตาม header ของทุก frame; tab คลิปทั้งหน้า (ช่องลิงก์ แถบโหลด รายการคลิป player กล่อง Transcript) ตาม frame "คลิป"; ตัวบอกขั้นตาม component `Spoil steps`
- `#/spoil`, `#/spoil/review`, `#/spoil/renders` เปิด tab สปอยพร้อมตัวบอกขั้นที่ขั้นนั้นเด่น; กดขั้นแล้ว hash เปลี่ยน; มือถือแสดงชื่อเฉพาะขั้นปัจจุบัน
- ติดตั้งไม่ครบ: tab คลิปเช็คแค่แถว `yt_dlp`, `deno`, `ffmpeg` (และแถวของงานถอดตามเดิม) แล้วแสดงข้อความกับลิงก์ "ไปหน้าติดตั้ง" แทนช่องลิงก์

### แก้ Transcript (API)

- `PATCH /api/spoil/clips/{id}/transcript/lines/{n}` `{"text": "ใหม่"}` → `200` บรรทัดนั้นมี `edited: true`; `{id}.transcript.json` เวลาและจำนวนบรรทัดเท่าเดิม ไม่เหลือ `.tmp`
- `text` เป็นช่องว่าง → `400` `invalid_request`; `n` เกินจำนวนบรรทัดหรือคลิปไม่มี Transcript → `404` `not_found`
- ระหว่าง Transcribe job ของคลิปนั้น → `409` `transcribing`; ระหว่าง Draft job ที่ใช้คลิปนั้น → `409` `clip_busy`; คลิปที่อยู่ใน Spoil draft แต่ไม่มีงาน → `200`
- `GET .../transcript.txt` และ `.srt` หลังแก้ → ข้อความใหม่
- `POST /api/spoil/transcriptions` ของคลิปที่มีบรรทัด `edited` ไม่มี `confirm_edit_loss` → `409` `has_edits`; ส่งซ้ำพร้อม `confirm_edit_loss: true` → `202` และ `done` แล้วไม่มี `edited` เหลือ

### แก้ Transcript (หน้าเว็บ)

- บรรทัด Transcript ตาม frame "คลิป — แก้ประโยค" และ component `Transcript line` state hover, editing, edited
- ชี้บรรทัด → ปุ่ม "แก้"; กด → ช่องพิมพ์ข้อความเดิมกับ "บันทึก" และ "ยกเลิก"; ช่องว่าง → "บันทึก" กดไม่ได้
- "บันทึก" ได้ `200` → บรรทัดแสดงข้อความใหม่พร้อมป้าย "แก้แล้ว"; "ยกเลิก" → ข้อความเดิม ไม่ส่ง request
- `409` `transcribing` หรือ `clip_busy` → ข้อความตาราง Frontend ของ spoil-maker
- ถอดใหม่ได้ `409` `has_edits` → ยืนยัน "ถอดใหม่จะลบบทพูดที่แก้ไว้"; ยืนยันแล้วส่งซ้ำพร้อม `confirm_edit_loss: true`
