# 03: รายการ Temp clip

**What to build:** ผู้ใช้เห็นรายการ Temp clip ใต้ช่องลิงก์ เรียงใหม่สุดก่อน กดแถวแล้วเล่นคลิปในหน้าเว็บ และกดลบได้. โหลดเสร็จหรือวางลิงก์ซ้ำ → แถวนั้นถูก highlight. รายการอยู่ครบหลัง restart.

**Blocked by:** 01: ติดตั้ง yt-dlp กับ Deno และ Download API, 02: แถบ tab และโหลดคลิปใน tab สปอย

**Covers:**
- Decisions: D3, D7, D12, D14, D15
- Screens: หน้าต่างรายการ Temp clip
- Seams: 1 (`/clips`, video, thumbnail, ลบ), 3 (รายการ, player, ลบ, ซ้ำ)
- User stories: 4, 5, 6

**Status:** ready-for-agent

## Acceptance criteria

### API

- งาน `done` แล้ว → `GET /clips` มีคลิปนั้นพร้อมทุกฟิลด์ เรียง `downloaded_at` ใหม่สุดก่อน
- json ที่ไม่มี mp4 คู่ หรือ json เสีย → ไม่อยู่ใน `GET /clips`
- `/clips/{id}/video` กับ `Range: bytes=0-99` → `206`
- `/clips/{id}/thumbnail` ไม่มีไฟล์ → `404` `not_found`
- `/clips/../x/video` หรือ id ผิดรูปแบบ → `404`
- `DELETE /clips/{id}` → `204` และไฟล์ทั้งสามหาย
- ลบ mp4 ไม่ได้ (`PermissionError`) → `409` `in_use` และ json ยังอยู่

### หน้าต่างรายการ

- รายการว่าง → "ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน"
- แถวแสดง thumbnail, ชื่อ, ช่อง, ความยาว `h:mm:ss` หรือ `m:ss`, ขนาดภาพกับ "ตั้ง" หรือ "นอน", ขนาดไฟล์ MB หรือ GB, เวลาโหลดท้องถิ่น
- งานจบ `done` → โหลดรายการใหม่ครั้งเดียว และแถวใหม่ highlight
- `409` `duplicate` → "คลิปนี้โหลดไว้แล้ว" แถว `clip_id` highlight และเลื่อนไปหา
- กดแถว → `<video controls>` ที่ `src` เป็น `/api/spoil/clips/{id}/video` เหนือรายการ
- กดลบและยืนยัน → แถวหาย; แถวที่เล่นอยู่ → player ถูกปลดก่อนส่ง `DELETE`
- ลบได้ `409` `in_use` → `message` จาก API ใต้แถวนั้น และแถวยังอยู่
- tab not ready → รายการยังแสดง
- หน้าตาตาม Figma frame ของหน้าต่างรายการใน spec › Design

### เช็คมือบน Mac

- คลิป Shorts และคลิปแนวนอนจาก ticket 01 เล่นได้และ seek ได้ใน player
- restart `npm run dev` → รายการเดิมอยู่ครบ
- README บอกเรื่อง tab สปอยและการลบ `media/temp/` ด้วยมือตอน backend ไม่ได้รัน
