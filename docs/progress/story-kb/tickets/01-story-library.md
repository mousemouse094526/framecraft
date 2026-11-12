# 01: คลังความรู้ — เพิ่ม แก้ ลบ Story

**What to build:** ผู้ใช้เปิด tab คลังความรู้ เห็นรายการ Story กด "เพิ่มเรื่อง" ใส่ชื่อเรื่อง บทความ และตัวละคร แล้วกดบันทึกครั้งเดียว; เปิด Story เดิมมาแก้หรือลบได้ และออกจากหน้าตอนยังไม่บันทึกถูกถามก่อน. Story และ Story ที่คลิปจำอยู่ข้าม restart; ลบคลิปแล้ว key ของคลิปหาย. ยังไม่มีอะไรใน tab สปอยใช้ Story.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D6, D7, D9, D10, D11, D12, D16 (lock, ขึ้นบรรทัดใหม่, บันทึกซ้ำ, ถามก่อนออก), spoil-maker D53
- ADR: 0011, 0013, 0022, 0023
- Screens: คลังความรู้ (รายการ Story), แก้ Story
- Seams: 1 (CRUD, `invalid_story`, `DELETE` Story, ลบคลิป, Trim job, restart), 2 (หน้าคลังความรู้, ตัวกันออก, ลบ Story)
- User stories: 1, 2, 3, 4

**Status:** done

## Acceptance criteria

### Stories API

- `POST /api/stories` แล้ว `GET /api/stories/{id}` → ค่าเดิมหลังตัดช่องว่างหัวท้าย; ขึ้นบรรทัดใน `title`, `name`, `description` เป็นช่องว่าง; `article` คงขึ้นบรรทัด
- `GET /api/stories` → เรียงแก้ล่าสุดก่อน แต่ละแถวมีจำนวนตัวละคร, `clips`, `tokens` (`null` เมื่อไม่มี tokenizer ของ Qwen) และ `updated_at`
- `title` ว่าง, บทความ 5,001 ตัวอักษร, ตัวละคร 31 ตัว, ชื่อตัวละครซ้ำ (ต่างแค่ตัวพิมพ์หรือช่องว่าง) → `400` `invalid_story` พร้อม `field` ตาม spec › Data
- บทความ 5,000 ตัวอักษรไทยที่มีสระและวรรณยุกต์ (นับ code point) → `201`
- body ไม่ใช่ object หรือฟิลด์ผิดชนิด → `400` `invalid_request`; ไม่ใช่ JSON → `415`
- `{id}` ไม่ตรง `^st_[0-9a-f]{8}$` หรือไม่มีไฟล์ → `404` `not_found`
- `PUT` → แทนทั้งเรื่อง `updated_at` เป็นตอนนี้
- `DELETE` Story ที่ 2 คลิปจำ → `204` และ `GET /api/story-clips` ไม่มีทั้ง 2 key

### Story ที่คลิปจำ และ Ops

- `DELETE /api/spoil/clips/{id}` ของคลิปที่จำ Story → key ของคลิปหาย, Story ยังอยู่
- Trim job ของคลิปที่จำ Story จบ `done` → key ยังอยู่ (D7)
- สร้าง app ใหม่บน root เดิม → Story และ key ยังอยู่; `media/stories/*.tmp` ถูกลบ; key ของคลิปที่ไม่มี json หรือของ Story ที่ไม่มีไฟล์ถูกลบ
- `clip-stories.json` อ่านไม่ได้ → `GET /api/story-clips` ได้ `{}` และมี log
- ไฟล์ Story อ่านไม่ได้ → ไม่อยู่ใน `GET /api/stories` และ log มีแค่ id ไม่มีบทความหรือชื่อตัวละคร

### tab คลังความรู้

- แถบ tab → ติดตั้ง · คลิป · คลังความรู้ · สปอย; `#/stories/…` เลือก tab คลังความรู้ (e2e)
- ไม่มี Story → "ยังไม่มีเรื่องในคลังความรู้" กับปุ่ม "เพิ่มเรื่อง"; backend ไม่ตอบ → `OfflinePanel` (e2e)
- กด "เพิ่มเรื่อง" ใส่ชื่อ เพิ่มตัวละคร 2 ตัว ลบ 1 ตัว บันทึก → `POST` body ตรง, hash เป็น `#/stories/{id}` และไม่ถาม "ออกโดยไม่บันทึก?" (e2e)
- กดบันทึก 2 ครั้งเร็วๆ → `POST` ครั้งเดียว (e2e)
- เปิด Story เดิม แก้ 2 ช่อง บันทึก → `PUT` ครั้งเดียว body ครบ, "บันทึกแล้ว", ปุ่มบันทึกกดไม่ได้จนแก้อีก (e2e)
- `400` `invalid_story` `field` `characters.0.name` → error ใต้ช่องนั้นตามตารางข้อความ error ของ spec (e2e)
- ชื่อเรื่องว่าง → "ใส่ชื่อเรื่อง" ไม่ส่ง request; ครบ 30 ตัว → ไม่มีปุ่ม "+ เพิ่มตัวละคร"; ตัวนับ "{n} / 5,000" นับ code point (e2e)
- แก้แล้วกด tab อื่น → ถาม "ออกโดยไม่บันทึก?"; ปฏิเสธ → hash เดิม ค่าที่พิมพ์ยังอยู่ ไม่ถามซ้ำ; ปิดแท็บ → `beforeunload` (e2e)
- ลบ Story ที่ใช้อยู่ 2 คลิป → กล่องยืนยันบอก "ใช้อยู่ 2 คลิป"; ยืนยัน → `DELETE` แล้ว hash `#/stories` (e2e)
- เปิด `#/stories/{id}` ที่ไม่มีแล้ว → "ไม่พบเรื่องนี้" กับลิงก์กลับคลังความรู้ (e2e)
- หน้าตาตรง Figma ของสองหน้าจอนี้ทั้ง desktop และ 375px
