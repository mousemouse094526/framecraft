# 03: เสียงพื้นในคลิปสปอย

**What to build:** ในหน้าตรวจแก้บทของสปอย ผู้ใช้เลือกเสียงพื้นหนึ่งเสียงจากคลังเสียงพร้อมความดัง แล้ว render ได้คลิปที่เสียงพื้นวนใต้เสียงบรรยายจนจบคลิป. ผล render บอกชื่อเสียงพื้นที่ใช้. ลบเสียงที่ Spoil draft ใช้อยู่ไม่ได้ และ render ที่กำลังทำอยู่ไม่เสียเมื่อเสียงถูกลบ.

**Blocked by:** 01: คลังเสียงกลางที่ tab คลังเสียง

**Covers:**
- Decisions: D5, D7, D8, D11, D12, D13, spoil-maker D9, spoil-maker D40, spoil-maker D51, spoil-maker D71
- ADR: 0021, 0022, 0038
- Screens: เสียงพื้นในหน้าตรวจแก้ของสปอย, ผล render ของสปอย
- Seams: 1 (Spoil draft `in_use`, render ระหว่างลบเสียง, chaos ของ lock), 2, 3 (หน้าตรวจแก้, render `sound_not_found`, "ไปคลังเสียง", ผล render)
- User stories: 4, 5
- Legal: 1 (`sound_name` ในผล render)

**Status:** ready-for-agent

## Acceptance criteria

### Spoil draft และ settings

- draft ไฟล์เก่าที่ไม่มี `sound` → อ่านเป็น `null`; `version` คง 2
- `PATCH /draft` `sound` `{sound_id, volume: 45}` → draft มี `sound`; `GET /settings` มี `sound_volume` 45
- `PATCH /draft` `sound` ที่ไม่มี `volume` → ใช้ `sound_volume` (ตั้งต้น 30)
- `PATCH /draft` เสียงที่ไม่มีในคลัง → `400` `sound_not_found`; `volume` ไม่ใช่ 0–100 ทีละ 5 → `400` `invalid_request`; ระหว่างงานที่ล็อก draft → `409` `draft_locked`
- `sound_volume` ผิดใน `PATCH /settings` → `400` `invalid_settings`
- ร่างใหม่ → `sound` `null`; เรียบเรียงใหม่ → `sound` เดิม
- `GET /draft` → `sound` ตามที่เก็บ ไม่เช็คคลัง (D13)

### ลบเสียงที่ใช้อยู่

- Spoil draft ที่ `sound` ชี้เสียง → ลบ → `409` `in_use` `users` มี `tab` `spoil` label `Spoil draft: {ชื่อคลิป} · EP {n}`; toon มาก่อน spoil
- ลบเสียงพร้อมกับ `PATCH /draft` เลือกเสียงเดียวกันใน thread อื่น 50 รอบ → ทุกรอบได้ผลอย่างใดอย่างหนึ่งตาม spec › Seams ข้อ 1; ไม่ค้างเกิน 5 วินาที

### Render job

- `sound` `null` → คำสั่ง ffmpeg เหมือนเดิมทุกตัวอักษร
- draft ชี้เสียงที่ไม่มีในคลัง → `400` `sound_not_found`
- เสียงพื้นยาว 1 วินาที `volume` 50 กับคลิป 3 วินาที (ffmpeg จริง) → mp4 ยาวเท่าเดิม และวินาทีที่ 2–3 ไม่เงียบเมื่อเสียงบรรยายและต้นฉบับเป็น 0
- Render job กำลัง `rendering` ด้วยเสียง แล้ว `PATCH /draft` `sound: null` และลบเสียง (`204`) → งานจบ `done` และ mp4 มีเสียงพื้น (D12)
- เสียงหายก่อนก๊อปเข้า `.render/` → งาน `failed` `sound_not_found`
- ผล render → `{name}.json` มี `sound_name` หรือ `null`; ไฟล์เก่าอ่านเป็น `null`

### หน้าเว็บ

- หน้าตรวจแก้ → ตัวเลือกเสียงพื้นใต้ระดับเสียงต้นฉบับ ค่าแรก "ไม่มีเสียงพื้น" ตามด้วยชื่อเสียงในคลัง
- เลือกเสียง → `PATCH /draft` มี `sound`; ปล่อย slider → `PATCH /draft` หนึ่งครั้งมี `volume` (e2e)
- คลังว่าง → บรรทัด "ยังไม่มีเสียงในคลัง" พร้อมลิงก์ "ไปคลังเสียง" (e2e)
- กด "ไปคลังเสียง" → `#/sounds?back=#/spoil/review` มีลิงก์ "← กลับ"; กดแล้วกลับหน้าตรวจแก้และรายการเสียงอ่านใหม่ (e2e)
- `PATCH /draft` ได้ `400` `sound_not_found` → ตัวเลือกกลับค่าเดิม เห็น "เสียงนี้ถูกลบจากคลังเสียงแล้ว เลือกเสียงอื่น" (e2e)
- render ได้ `400` `sound_not_found` → Alert "ไม่พบเสียงพื้นนี้ในคลังเสียง เลือกเสียงใหม่ก่อน render" และอ่าน draft ใหม่ (e2e)
- ระหว่างงานที่ล็อก draft → ตัวเลือกและ slider กดไม่ได้
- ผล render ที่ `sound_name` "ฝนตก" → บรรทัด "เสียงพื้น: ฝนตก" ใต้ "ต้นฉบับ"; `null` → ไม่มีบรรทัด (e2e)
- หน้าตาตรงแบบของจอเสียงพื้นในหน้าตรวจแก้และผล render (Blocked #3–4)
