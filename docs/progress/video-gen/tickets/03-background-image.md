# 03: ภาพพื้นหลังของผู้ใช้

**What to build:** ในหน้าแก้บทเรียน ผู้ใช้เลือกภาพ PNG หรือ JPG ของตัวเองเป็นพื้นหลัง เห็นคำเตือนเรื่องสิทธิ์ของภาพข้างปุ่ม แล้ว render ได้คลิปที่พื้นหลังเป็นภาพนั้นเบลอและทำมืด. ลบภาพแล้วกลับเป็นสีของแอป.

**Blocked by:** 02: render คลิปสอนกลอง

**Covers:**
- Decisions: D6, D23 (ข้อความข้างปุ่มเลือกภาพ, ไม่มีช่องโลโก้)
- ADR: 0013, 0028
- Screens: ส่วนพื้นหลังของหน้าแก้บทเรียนกลอง
- Seams: 1 (`PUT /background` PNG, ไฟล์ข้อความ, เกิน 20 MB), 3 (เลือกภาพและคำเตือน)
- User stories: 6
- Legal: 3, 4 (ไม่มีช่องใส่ภาพอื่นนอกจากพื้นหลัง)

**Status:** done

## Acceptance criteria

### API ของภาพ

- `PUT /lessons/{id}/background` PNG → `background.jpg` 1080×1920 หันตาม EXIF, `background` = `image`
- ไฟล์ข้อความ → `415` `unsupported_image`; เกิน 20 MB → `413` `file_too_large`; body ไม่ใช่ `application/octet-stream` → error ตาม ADR-0028
- `DELETE /lessons/{id}/background` → ไม่มี `background.jpg`, `background` = `color`
- `PUT` หรือ `DELETE` ภาพระหว่าง render ของบทเรียนนั้น → `409` `lesson_busy`
- `PUT /lessons/{id}` ที่ `background` = `image` แต่ไม่มี `background.jpg` → `400` `invalid_request` `field` `background`
- `copy` บทเรียนที่มีภาพ → สำเนามี `background.jpg` ด้วย

### render

- render บทเรียนที่มีภาพ → พื้นหลังเป็นภาพ blur รัศมี 24 ทับดำ 55%; พิกเซลมุมจอต่างจากพื้นหลังสี
- เปลี่ยนภาพระหว่าง render → ผลใช้ภาพตอนเริ่ม (สำเนาใน `.render/`)

### หน้าเว็บ

- เลือกภาพในหน้าแก้ → `PUT /background` แล้วเห็นภาพ; ลบภาพ → กลับเป็นสีของแอป (e2e)
- ข้างปุ่มเลือกภาพมีข้อความ "ใช้ภาพของคุณเองหรือภาพที่มีสิทธิ์ใช้ ห้ามใช้ปกอัลบั้ม" (e2e)
- `413` และ `415` → ข้อความ error ข้างปุ่ม (e2e)
