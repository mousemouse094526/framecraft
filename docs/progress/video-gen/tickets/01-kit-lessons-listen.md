# 01: ติดตั้งเสียงกลอง บทเรียน และฟังจังหวะ

**What to build:** Setup script โหลด sample กลอง Big Rusty Drums สามชั้นความแรงลง `models/drums/` และ Status check มีแถว `drum_kit`. ผู้ใช้เปิด tab "สอนกลอง" สร้าง ทำซ้ำ ลบบทเรียนกลอง กรอก Groove บนตาราง 16 ช่องต่อห้อง แบ่งท่อนสอน แล้วกด "ฟังจังหวะ" ได้ยินนับเข้ากับกลองทุกท่อนตามความเร็วของท่อน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D4, D5, D8, D9, D10 (รายการ สร้าง ทำซ้ำ ลบ), D11, D13 (นับเข้า ความแรง round-robin), D15, D16, D19, D20, D21, D22 (id ใน path, ลบบทเรียน, บทเรียนใหม่, ฟังจังหวะ, ขอบของโน้ต, marker), D23 (ป้ายตั้งต้น), setup-status D9, setup-status D25, setup-status D26, story-kb D11, story-kb D12, story-kb D16, story-kb D18, spoil-maker D21, spoil-maker D63
- ADR: 0002, 0003, 0004, 0009, 0013, 0041, 0042
- Screens: รายการบทเรียนกลอง (ยกเว้นป้าย render), หน้าแก้บทเรียนกลอง (ยกเว้นส่วน render และภาพพื้นหลัง)
- Seams: 1 (บทเรียนใหม่, ยาวเกิน, กฎ D20, id ใน path, copy และ delete, `lesson.json` เสีย, listen, `not_ready` ของ `drum_kit`), 2 (`timeline.build`, `mixer`), 3 (tab, ตาราง Groove, flam, ท่อนสอน, ฟังจังหวะ, ถามก่อนออก, ทำซ้ำ ลบ)
- User stories: 1, 2, 3 (ท่อนสอนกับความเร็ว), 5 (รายการบทเรียน)
- Legal: 1, 4 (ป้ายตั้งต้น `ลองเล่นเอง`)

**Status:** done

## Acceptance criteria

### ติดตั้งและ Status check

- ตาราง (`piece`, ชั้น `soft`/`mid`/`hard`, round-robin, path, sha256) ใน `backend.drum_kit` สร้างจาก `.sfz` ของ repo ที่ commit `f07ce00` ครบ 10 ชิ้นตาม spec › Drum kit ไมค์ `cl`
- Setup script โหลดไฟล์ที่ขาดหรือ hash ไม่ตรงหลัง Kanit ลองสามครั้งต่อไฟล์ แล้วเขียน marker ใน `paths.markers_dir` เมื่อ sha256 ตรงทุกไฟล์ (test ด้วย `fetch` ปลอม)
- ไฟล์หนึ่งโหลดพังครบสามครั้ง → Setup จบด้วย error ที่บอกชื่อไฟล์ ไม่มี marker
- `GET /api/setup/status` มีแถว `drum_kit` ("Drum samples", ค่า `Big Rusty Drums · f07ce00`) ต่อจาก `font_kanit`; ไม่มีไฟล์หรือ marker → `missing` พร้อม `fix` คำสั่ง Setup script; การเช็คไม่เขียนไฟล์
- `fakes.write_drum_kit(root)` เขียน FLAC 0.1 วินาทีที่เริ่มด้วยเสียงคลิกทุกไฟล์ในตารางและ marker; ไม่โหลดจากเน็ต
- ฟัง `hihat_14/chik` และทอม 14/15/18 จริง → แก้ตาราง Drum kit ถ้าไม่ตรง แล้วจดผลใน `progress.md` (Open Question 1)
- `pillow` และ `soundfile` pin เป็น dependency ตรงใน `pyproject.toml` ตามรุ่นใน `uv.lock`

### บทเรียนกลอง

- `POST /lessons {"title": ...}` → `201` บทเรียนค่าตั้งต้นตาม spec › Data (Groove ร็อก 1 ห้อง, BPM 100, ท่อนแรกป้ายว่าง, ท่อนสองป้าย `ลองเล่นเอง`); `GET /lessons` มีบทเรียนนี้พร้อม `length_s` และ `renders` 0
- `PUT` ที่ `length_s` > 90 → `200` บันทึกแล้ว; `POST /listen` → `422` `too_long`
- `PUT` ที่ผิดกฎ D20 แต่ละข้อ (มือเดียวสองชิ้น, โน้ตมือสามตัว, `hihat_open` คู่ `hihat_closed`, `flam` บนเท้า, `flam` ข้างโน้ตมืออีกตัว) และโน้ตเลยห้องสุดท้าย → `400` `invalid_request` พร้อม `field` ของโน้ตนั้น และ `lesson.json` ไม่เปลี่ยน
- ค่าใดใน spec › Data ผิดขอบ (`bpm` 39, `chapters` 7 ท่อน, `speed` 72, `title` 41 ตัวอักษร) → `400` พร้อม `field`
- id `..`, `%2E%2E`, ตัวใหญ่ หรือยาวไม่ใช่ 12 → `404` `not_found` และไม่มีไฟล์ใดหาย
- `POST /lessons/{id}/copy` → id ใหม่ หัวเรื่องต่อท้าย " (สำเนา)" ตัดที่ 40 ไม่มีผล render
- `DELETE` → folder ของบทเรียนหาย; `lesson.json` ที่อ่านไม่ได้ → ไม่อยู่ในรายการ (log) แต่ `DELETE` ได้
- รายการเรียง `updated_at` ใหม่สุดก่อน

### ตารางเวลาและเสียง

- BPM 120 ท่อนแรกความเร็ว 50 → นับเข้ายาว 4.0 วินาที โน้ต step 2 ของห้องแรกอยู่ที่ 4.5 วินาที (step 4 ที่ 5.0, D27)
- `flam` → สองการตีห่าง 0.03 วินาที โน้ตนำเป็นมืออีกข้างชั้น `soft` โน้ตหลัก `mid`
- `accent` / `normal` / `ghost` → ชั้น `hard` / `mid` / `soft`; round-robin วนตามลำดับการตีของชิ้นและชั้นตั้งแต่ต้นคลิป
- `length_s` ตามสูตรใน spec › Data รวมหางเสียง 1.5 วินาที; เวลาทุกการตีปัดเป็น sample 44.1 kHz ใน `timeline` ที่เดียว (ADR-0041)
- ไฮแฮทเปิดตามด้วยไฮแฮทปิดหรือเท้า → เสียงเปิดถูกตัด fade 10 ms
- `mixer` สองครั้งบนบทเรียนเดิม → wav เดียวกันทุก byte; peak −1 dBFS, 16-bit, 44.1 kHz stereo
- Groove ไม่มีโน้ต → wav มีนับเข้าแล้วเงียบ ยาว `length_s`
- `POST /listen` → `audio/wav` ยาว `length_s` และ `Cache-Control: no-store`; ไม่มี sample → `503` `not_ready` มี `rows: ["drum_kit"]`
- คลิป 90 วินาที "ฟังจังหวะ" เสร็จใน 5 วินาทีบน Mac → จดเวลาที่วัดใน `progress.md`

### หน้าเว็บ

- กด tab "สอนกลอง" ต่อจาก `toon` → `#/drums` รายการ; ว่าง → ข้อความชวนสร้างบทเรียนแรก (e2e)
- สร้างใหม่ถามหัวเรื่อง → เปิด `#/drums/{id}` (e2e)
- กดช่องว่างในช่องที่ R ใช้อยู่ → โน้ตใหม่เป็น L; ช่องที่สองมือไม่ว่างกดไม่ได้ (e2e)
- เลือกโน้ตแล้วเปลี่ยนเป็น flam แล้วบันทึก → `PUT` ส่ง `hit: "flam"`; ตัวเลือกที่ทำให้มือชนกันกดไม่ได้; ชิ้นของเท้าไม่มีตัวเลือกไม้และ flam (e2e)
- ลดห้องที่มีโน้ตเลยห้องสุดท้าย → ถามก่อน แล้วโน้ตนั้นหาย (e2e)
- เพิ่ม เลื่อน ลบท่อนสอน แล้วบันทึก → `PUT` ส่ง `chapters` ตามลำดับใหม่ (e2e)
- ความยาวรวมเกิน 90 วินาที → บอกว่าเกินกี่วินาที บันทึกได้ "ฟังจังหวะ" กดไม่ได้ (e2e)
- "ฟังจังหวะ" → `PUT` (เมื่อยังไม่บันทึก, D29) แล้ว `POST /listen` ปุ่มเป็น "กำลังผสมเสียง…" แล้วเล่น blob; กดใหม่ระหว่างเล่นหยุดของเดิม (e2e)
- `not_ready` ของ listen → ใต้ปุ่มแสดง `fix` ของแถว `drum_kit` (e2e)
- `PUT` ได้ `invalid_request` → error ที่ช่องตาม `field` (e2e)
- ออกจากหน้าแก้ก่อนบันทึก → ถามยืนยัน (e2e)
- ทำซ้ำ และลบพร้อมยืนยัน (บอกจำนวนผล render ที่จะหาย) ในรายการ → `POST /copy`, `DELETE` (e2e)
- หน้าตาตามแบบ Figma เมื่อ Blocked แถว design ของสองหน้านี้ปิด; ก่อนนั้นใช้ component เดิมของแอป
