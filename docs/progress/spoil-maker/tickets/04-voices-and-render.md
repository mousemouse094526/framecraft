# 04: เสียงต่อประโยคและ render

**What to build:** ในหน้าตรวจแก้ผู้ใช้สร้างและฟังเสียงทีละประโยคหรือทั้งหมด เห็นความยาวรวม ใส่ลายน้ำหลายอันที่แอปจำไว้ แล้วกด render: แอปสร้างเสียงที่ขาดให้ก่อน แล้วได้ mp4 1080×1920 ที่มีภาพตาม layout ซับไทยด้วย Kanit และเสียงต้นฉบับเบาๆ กับ `.srt`. หน้าผล render แสดงทุกรอบใหม่สุดก่อน ให้เล่น โหลด ลบ และ copy ชื่อต้นฉบับไปใส่คำอธิบายคลิป.

**Blocked by:** 03: ร่างบทและหน้าตรวจแก้

**Covers:**
- Decisions: D9, D10, D20, D21, D22, D24, D30, D31, D36 (`.srt` ไม่แปลงตัวเลข), D40, D41, D42, D45 (Kanit, ค่าที่จำไว้), D49 (`clip_busy` ช่วง `voicing`), D51
- ADR: 0005, 0009, 0010, 0012, 0015, 0017
- Screens: หน้าตรวจแก้ (เสียง ลายน้ำ เสียงต้นฉบับ และ render) — [Figma: Script review](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390); ผล render — [Figma: Render results](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850); ขั้น 3 ใน [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633)
- Seams: 1 (เสียงและตัวเลขข้อ Voice job `sentences`, Render, ข้อ Voice job ของแก้ draft, `clip_busy` และ `rendering` ของช่อง GPU, start ข้อ `.partial` และ `.render/`, Status check ของ `font_kanit` และแถวรวมทั้ง 4), 2 (หน้าตรวจแก้ข้อเสียงและลายน้ำ, ผล render), 3 (เสียงประโยค, ตัวเลข, render, iPhone และ YouTube Shorts)
- User stories: 9, 10, 11
- Legal: 1

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้ง Kanit

- Setup script โหลด `Kanit-Bold.ttf` กับ `OFL.txt` ตาม spec › Modules touched, ตรวจ sha256 แล้วเขียน marker; sha256 ไม่ตรง → ลบไฟล์และ Setup script ล้ม
- `GET /api/setup/status` มีครบ 4 แถว `model_qwen`, `mlx_vlm`, `pythainlp`, `font_kanit` ต่อจากแถวเดิม

### Voice job `sentences`

- Voice job `sentences` ของประโยคตัวอย่างใน spec › Seams 1 › เสียงและตัวเลข → TTS ปลอมได้ข้อความที่แปลงแล้ว; `.srt` หลัง render ยังเป็นตัวเลข
- TTS ปลอมคืน wav 2 วินาที → `audio.duration_s` 2.0; ยกเลิกหลังประโยคแรก → ประโยคแรก `ready` ประโยคสอง `no_audio`
- `PATCH` ระหว่าง Voice job `sentences` → `409` `draft_locked`; `GET /draft` มี `locked: true`
- id ที่ไม่มีใน draft → `400` `invalid_request`

### Render job

- มีประโยค `no_shot` → `400` `missing_shots`; ที่ว่างปลอม 0.5 GiB → `507` `disk_full`; ไม่มี Spoil draft → `404` `no_draft`
- draft 2 ประโยค (เสียงปลอม 2.0 และ 1.5 วินาที) layout A, B, C → mp4 1080×1920 ยาว 3.5 ±0.2 วินาที มีเสียง, `.srt` 2 cue ที่ `00:00:00,000 --> 00:00:02,000` และ `00:00:02,000 --> 00:00:03,500`
- ประโยค layout A ยาว 3.0 วินาที → ไฟล์ ASS มีซับท่อนละ 2–4 คำ ไม่เกิน 15 ตัวอักษรที่กินที่ และเวลารวม 3.0
- ประโยคและลายน้ำที่มี `{\b1}` และขึ้นบรรทัดใหม่ → ไฟล์ ASS escape แล้วและไม่มีขึ้นบรรทัดใหม่ในข้อความ
- Shot ท้ายคลิปที่เสียงยาวกว่าที่เหลือ → ยาวครบ ไม่ error
- ประโยคขาดเสียง → state ผ่าน `voicing` แล้ว `rendering`; TTS ปลอมถูกเรียกเฉพาะประโยคนั้น
- `DELETE /api/spoil/clips/{id}` ระหว่าง `voicing` ของ draft ที่ใช้คลิปนั้น → `409` `clip_busy`; render ที่ไม่มีประโยคขาดเสียง ระหว่าง `rendering` → `POST /describes` ของคลิปอื่น `202`
- ยกเลิกระหว่าง `rendering` → `cancelled`, ไม่มี `.partial` และ `.render/`; start app ขณะมี `renders/x.partial` → หาย
- render สองครั้ง → `GET /renders` มี 2 รายการ พร้อม `sources` เป็นชื่อคลิป; `DELETE /renders/{name}` → `204` และไฟล์ทั้งสามหาย; `/renders/../x.mp4` → `404`; ลบคลิปแล้วผล render ยังอยู่
- `PATCH /settings` ลายน้ำ 7 อัน หรือ `position` นอกตาราง → `400` `invalid_settings`

### หน้าเว็บ

- หน้าตาตรง Figma ทุก state ที่ 375 และ 1440: ส่วนเสียง ลายน้ำ เสียงต้นฉบับ และปุ่ม render ตาม [Figma: Script review](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390); ขั้น 3 ตาม [Figma: Render results](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850) วางในขั้นของ tab สปอยตาม [Figma: 3 tab](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8071-18633)
- หน้าตรวจแก้: ฟังเสียงประโยค, สร้างเสียงใหม่, ปุ่มสร้างเสียงทั้งหมด; ความยาวประมาณ / เป้าหมายพร้อมคำเตือนเมื่อนอก ±25%
- `GET /draft` มี `locked: true` และ current ของ Voice job `sentences` 1/3 → เห็น "สร้างเสียง 1/3" ปุ่มยกเลิก และช่องข้อความกดไม่ได้
- ประโยค `no_shot` → ปุ่ม render กดไม่ได้
- เพิ่มลายน้ำ 2 อันแล้ว reload → ยังอยู่ (จาก `GET /settings`)
- render current คืน `voicing` 1/3 แล้ว `rendering` 50 แล้ว `done` → เห็น "สร้างเสียง 1/3", "render 50%" แล้วรายการใหม่ที่มีลิงก์ mp4 และ `.srt` และ "ต้นฉบับ: {ชื่อคลิป}" พร้อมปุ่ม copy
- render current `failed` `ffmpeg_failed` → เห็น "render ไม่สำเร็จ"; ไม่มีผล render → "ยังไม่มีผล render"
- หน้าตาตรงแบบของจอ "หน้าตรวจแก้" และ "ผล render" (Source ยัง `pending`: Blocked #4, #6)

### เช็คมือบน Mac M2 (Seam 3)

- เสียงหญิง young adult ที่บันทึกใน 02 → 5 ประโยคฟังเป็นเสียงเดียวกัน; ประโยคที่มี `1968` และ `10:30` → อ่านถูก
- render คลิป 60 วินาทีทั้ง 3 layout → ข้อความไทยที่มีสระบนล่างและวรรณยุกต์ไม่ซ้อนผิด, ภาพตรงตาราง layout, ลายน้ำ 6 ตำแหน่งอยู่ถูกมุม, เสียงต้นฉบับ 20% ได้ยินแต่ไม่กลบ; จดเวลา render ใน progress (Open Question 1)
- เปิด mp4 บน iPhone และอัปโหลดขึ้น YouTube Shorts แบบ private → เล่นได้แนวตั้ง
- README บอกเรื่อง spoil-maker และที่เก็บไฟล์ใน `media/temp/shots/` และ `media/spoil-maker/`
