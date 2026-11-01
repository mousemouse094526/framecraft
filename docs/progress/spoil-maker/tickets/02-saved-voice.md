# 02: Saved voice

**What to build:** ผู้ใช้เปิด `#/spoil/voices` ใต้ tab สปอย เลือกเพศ วัย ระดับเสียง และ speed แล้วกดสุ่มเพื่อฟังประโยคตัวอย่าง; พอใจก็บันทึกพร้อมชื่อเป็น Saved voice ที่เปลี่ยนชื่อ ฟังซ้ำ และลบได้. backend มีตัวแปลงตัวเลขเป็นคำไทย และวัดความเร็วพูดของเสียงไว้ประมาณความยาวบท.

**Blocked by:** 01: ติดตั้ง Qwen, ช่อง GPU และดูภาพ

**Covers:**
- Decisions: D1, D32, D35, D36, D37, D41 (NOTICE.md), D43 (ยกเว้น `voice_in_use`), D44, D45 (pythainlp), D48, spoil D10
- ADR: 0003, 0009, 0012, 0015, 0017, 0019
- Screens: Saved voice (ยกเว้น error ลบเสียงที่ Spoil draft ใช้) — [Figma: Saved voice](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220)
- Seams: 1 (เสียงและตัวเลข ข้อ `design_preview` และชื่อเสียง; Status check ของ `pythainlp`), 2 (หน้า Saved voice ยกเว้น `voice_in_use`), 3 (pythainlp ไม่สร้าง `~/pythainlp-data`)
- User stories: 2, 4
- Legal: 2

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้งและตัวเลข

- `pythainlp` pin ตาม spec › Dependencies; `PYTHAINLP_DATA_DIR` ตั้งก่อน import; `GET /api/setup/status` มีแถว `pythainlp`
- ตัวแปลงตัวเลข: `ปี 1968 เวลา 10:30 ราว 50% หรือ 3.25 เท่า ๑๑ คน 114,000 บาท 007` → ข้อความตามตัวอย่างใน spec › Seams 1 › เสียงและตัวเลข
- จำนวนเต็มตามกฎใน spec › ตัวเลขเป็นคำ: `21` → `ยี่สิบเอ็ด`, `101` → `หนึ่งร้อยเอ็ด`, `10` → `สิบ`, `1000000000000` → `หนึ่งล้านล้าน`, `10:00` → `สิบนาฬิกา`, `1/2` → `หนึ่ง/สอง`
- NOTICE.md แนะนำให้ใส่เครดิตโมเดล ไม่บังคับ (D41)

### Voice job `design_preview` และ Saved voice

- `design_preview` แล้ว `POST /voices` → `201`; `GET /voices` มีเสียงนั้นพร้อม `chars_per_s` = ตัวอักษรของประโยคตัวอย่างหลังแปลง / ความยาว wav ปลอม
- TTS ปลอมได้ `instruct` ตามค่าที่เลือก, speed ที่เลือก และ `num_step` 16
- `design_preview` speed 1.3 หรือ `age` `baby` → `400` `invalid_voice`
- `POST /voices` ไม่มี preview → `409` `no_preview`; สุ่มซ้ำ → preview ล่าสุดทับของเดิม
- `PATCH /voices/{id}` ชื่อ 41 ตัวอักษรหรือช่องว่างล้วน → `400` `invalid_voice`; ชื่อ `ผู้ชายเสียงต่ำ` → `200` และ `GET /voices` เห็นชื่อใหม่
- `DELETE /voices/{id}` → `204` และไฟล์ทั้งสามของเสียงหาย; `GET /voices/{id}/sample.wav` หลังลบ → `404`
- `POST /voice-jobs` ระหว่าง Describe job → `409` `gpu_busy` `running: "describe"`; marker ของ Qwen หาย → `POST /voice-jobs` ยัง `202`
- start app ขณะมี preview ค้าง → preview หาย

### หน้าเว็บ

- หน้า Saved voice ตรง [Figma: Saved voice](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220) ทุก state ที่ 375 และ 1440 (ยกเว้น error `voice_in_use`) อยู่ใต้แถบ tab ของ ticket 00
- `#/spoil/voices` เปิด tab สปอยที่หน้า Saved voice; hash ที่ขึ้นต้นด้วย `#/spoil/` ทุกอันเปิด tab สปอย
- กดสุ่ม current `done` → มีปุ่มฟังและช่องชื่อ; บันทึก → อยู่ในรายการ; เปลี่ยนชื่อ → ส่ง `PATCH`; ลบ → ยืนยันก่อนส่ง `DELETE`
- ไม่มี Saved voice → เห็น "ยังไม่มีเสียง กดสุ่มเพื่อออกแบบเสียงแรก"
- หน้าตาตรงแบบของจอ "Saved voice" (Source ยัง `pending`: Blocked #2)

### เช็คมือบน Mac M2 (Seam 3)

- ก่อนเขียน worker จริง ลอง Library assumptions ของ omnivoice (`generate(instruct=…)`, `create_voice_clone_prompt` แล้ว `save`/`load`, `speed`, `num_step`) — ไม่ได้ข้อไหน หยุดแล้วถาม
- ออกแบบเสียงหญิง young adult แล้วบันทึก → ฟังประโยคตัวอย่างได้; ฟังซ้ำหลัง restart backend → เสียงเดิม
- import `pythainlp` แล้วตัดคำ → ไม่มี `~/pythainlp-data` ถูกสร้าง
