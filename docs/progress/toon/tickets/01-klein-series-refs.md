# 01: ติดตั้ง klein, Series และภาพอ้างอิง

**What to build:** Setup script โหลด FLUX.2 klein 4B (GGUF Q8_0 กับ text encoder และ vae) และ Status check มีแถวของ klein. ผู้ใช้เปิด tab ที่ห้า "การ์ตูนเล่า" สร้าง Series แบบหลอนหรือตลก แก้ค่าของ Series เพิ่มตัวละครและฉากหลัง แล้วสร้างภาพอ้างอิง 3 แบบให้เลือกหนึ่ง หรือเอาไฟล์ภาพเข้า. ลบ Series ได้หลังยืนยัน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D3, D6, D7, D8 (`voice_id` ของ Series), D10, D11, D13 (`ref_rev` 0), D25 (ตัวละคร ฉากหลัง Saved voice ของ Series), D26, D28, D29, D31, D32 (เปลี่ยนภาพอ้างอิง `ref_rev`), D34, D35, D36 (คำสั่งภาพของตัวละครและฉากหลัง), D41, D42, D46, setup-status D9, setup-status D11, spoil-maker D32–D37
- ADR: 0002, 0003, 0004, 0008, 0009, 0010, 0012, 0013, 0015, 0019, 0025, 0026, 0028, 0030, 0031, 0032, 0033
- Screens: รายการ Series (หน้าแรกของ tab), ตั้งค่า Series, ตัวละครและฉากหลัง, เลือกภาพอ้างอิง
- Seams: 1 (Series, ลบ Series, Ref job, `ref/pick`, upload, `not_ready` ของ klein, `voice_in_use` ของ Series, `gpu_busy` ระหว่าง Describe job), 3 (คำเตือนก่อนเลือกไฟล์ภาพ)
- User stories: 1, 2, 3 (เปลี่ยนภาพอ้างอิง), 12 (ลบ Series)
- Legal: 1, 2, 3 (ข้อ 3 และข้อห้ามของ model card ในข้อ 1 เป็นหน้าที่ของผู้ใช้ ไม่มีของต้องสร้าง)

**Status:** in-progress

## Acceptance criteria

### ลองจริงก่อน (Open Question 1)

- ก่อนเขียน worker จริง ลอง klein ผ่าน diffusers 0.42.1 บน torch 2.8.0 ที่ project pin ที่กรณีหนักสุด (GGUF, 3 ภาพอ้างอิง, 576×1024) บน Mac M1 16 GB → จด peak memory และเวลาต่อภาพใน `progress.md` แบบ trial-klein-mac
- ลองคำบรรยายไทยตรงเข้า klein สองสามภาพ → จดผลใน `progress.md` เป็นข้อมูลให้ D36
- peak ทั้งระบบเกิน ~12 GB หรือรันไม่ได้ → หยุด เพิ่ม Blocked row ที่ Needs `/warroom toon` เรื่อง pin

### ติดตั้งและ Status check

- `KLEIN` และ `KLEIN_GGUF` อยู่ใน `MODELS` ตาม spec › Modules touched, revision ของ GGUF pin ตอนนี้; Setup script โหลดต่อจาก Qwen ก่อน Kanit และเขียน Model marker เมื่อทุก folder ใน `allow_patterns` มีไฟล์จริง
- `diffusers` และ `gguf` pin ตาม spec › Dependencies; `REQUIRED_FREE_BYTES` ตาม spec › Modules touched
- `GET /api/setup/status` มีแถว `model_klein`, `model_klein_gguf`, `diffusers`, `gguf` ต่อจาก `font_kanit` พร้อม license ของแต่ละ repo
- marker ของ `model_klein` หาย → Ref job `503` `not_ready` พร้อม `rows`
- `NOTICE.md` มี klein, GGUF ของ unsloth และ Qwen3-4B text encoder (Apache-2.0)

### Series ตัวละคร ฉากหลัง

- สร้าง Series `horror` → `acts`, `style`, `tone` ตามตารางค่าตั้งต้นใน spec; `comedy` ได้ค่าของตลก
- สร้าง Series ด้วย `voice_id` ที่ไม่มี → `400` `voice_not_found`
- `PATCH` Series เปลี่ยน `layout` หรือ `genre` → ไม่เปลี่ยน; `acts` 9 ชื่อหรือชื่อยาว 21 ตัวอักษร → `400`
- ลบ Series ไม่มี `confirm_eps` → `409` `confirm_needed` พร้อม `eps`; ระหว่าง Ref job ของ Series → `409` `series_busy`; ยืนยันแล้ว folder ของ Series หาย Saved voice อยู่
- ลบ Saved voice ที่ Series ใช้ → `409` `voice_in_use`
- `series.json` ที่ `version` อื่นหรืออ่านไม่ได้ → ถูกข้ามในรายการและ log เหตุผล

### Ref job และเอาไฟล์เข้า

- Toon job ทุกงานใช้ slot `toon.jobs`; Ref job ซ้อนกัน → `409` `busy`; Ref job ระหว่าง Describe job → `409` `gpu_busy`
- Ref job ด้วย klein ปลอม → state `translating` แล้ว `drawing` 3/3, `GET /series/{sid}` มี `pending` 3
- `ref/pick {"n": 2}` → `ref_rev` +1, ภาพอ้างอิงเดิมและ `.pending` ของ id นั้นหาย; pick ซ้ำ → `404` `no_pending`; `n` 4 → `400` `invalid_request`
- upload ไฟล์ข้อความ → `400` `unsupported_file`; upload PNG ฉากหลัง 800×800 ใน Series `frame` → ภาพอ้างอิง 1024×576; ตัวละคร 3000 px → ด้านยาว 1536
- start backend ใหม่ → `.pending` ทั้งหมดหาย
- ทุกทางออกของงาน (`done`, `failed`, `cancelled`) คืนช่อง GPU
- `gpu.Kind` มี `toon_image` ใน `RUNNING_NAMES` ("สร้างภาพ"); `JOB_HOLDERS` มี Toon job; router `/api/toon` ถูก include
- ลบ Saved voice นับ Series ผ่าน callback ใน `voice_users` ที่ `backend.toon` ลงทะเบียน; การเขียน `voice_id` ของ Series ถือ `gpu.slot.draft_lock` ก่อน `toon.store.lock`

### หน้าเว็บ

- tab ที่ห้า "การ์ตูนเล่า" ต่อจากสปอย; `#/toon` และ `#/toon/series/{sid}` เปิด tab นี้
- `GPU_JOB_PATHS` ใน `lib/gpu` มี `/api/toon/jobs/current`
- กดเอาไฟล์ภาพตัวละครเข้า → เห็นคำเตือนของ legal ข้อ 2 ก่อนช่องเลือกไฟล์ (e2e)
- ยังไม่มี Saved voice → หน้าตั้งค่า Series มีลิงก์ไปหน้า Saved voice ของ tab สปอย (e2e)
- Ref job ได้ `gpu_busy` → เห็นชื่องานที่รันอยู่จาก `RUNNING_NAMES` (e2e)
- หน้าตาตรงแบบของสี่จอใน Covers (Source ยัง `pending`: Blocked #1–4)
