# 02: แถบ tab และโหลดคลิปใน tab สปอย

**What to build:** ผู้ใช้สลับ tab สปอยกับ Setup status จากแถบด้านบน และ refresh แล้วอยู่ tab เดิม. ใน tab สปอยวางลิงก์ YouTube กดโหลด เห็น % ยกเลิกได้ และเห็นข้อความที่บอกว่าทำไมโหลดไม่ได้กับวิธีแก้.

**Blocked by:** 01: ติดตั้ง yt-dlp กับ Deno และ Download API

**Covers:**
- Decisions: D6, D8, D9, D10, D15, setup-status D20, setup-status D21
- Screens: แถบ tab, tab สปอย
- Seams: 3 (tab, not ready, โหลด, %, ยกเลิก, error, งานหาย)
- User stories: 1, 2, 3, 7

**Status:** ready-for-agent

## Acceptance criteria

### แถบ tab

- hash ว่างหรือไม่รู้จัก → เห็นหน้า Setup status และ tab นั้นเด่นกว่า
- กด tab สปอย → hash เป็น `#/spoil`; refresh แล้วยังอยู่ tab สปอย
- กดปุ่ม back ของ browser → กลับ tab ก่อนหน้าตาม hash
- `OfflinePanel` และ type ของ `/api/setup/status` ใช้ร่วมกันได้ทั้งสอง tab; หน้า Setup status ยังผ่าน test เดิม

### tab สปอย

- status ที่ `deno` เป็น `missing` → "ยังติดตั้งไม่ครบ: Deno" กับลิงก์ไป Setup status และไม่มีช่องลิงก์
- วางลิงก์ กดโหลด, current คืน `downloading` 40 แล้ว `done` → เห็น 40% แล้ว "โหลดเสร็จ: {title}"
- current คืน `downloading` ที่ `percent: null` → แถบไม่มีตัวเลข
- ระหว่างงานยังไม่จบ → ปุ่มโหลด disabled; ตอน `merging` ไม่มีปุ่มยกเลิก
- กดยกเลิก → ส่ง `DELETE /api/spoil/downloads/current`; current คืน `cancel_requested: true` → "กำลังยกเลิก…"
- ได้ `409` `merging` → "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว"
- งาน `failed` → เห็น `error.message`; มี `fix` → คำสั่งเป็นบรรทัดพร้อมปุ่ม copy
- `400` `invalid_url` หรือ `409` `busy` → ข้อความตาราง Frontend ของ spec
- กำลังติดตามงานแล้ว current คืน `null` → "งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง"
- เปิด tab แล้ว current เป็นงาน `failed` ที่จบแล้ว → เห็น `error.message`
- fetch ล้มหรือเกิน 30 วินาที → `OfflinePanel` พร้อมปุ่ม Refresh
- หน้าตาตาม Figma frame ของแถบ tab และ tab สปอยใน spec › Design
- เช็คมือผ่าน Vite proxy: วางลิงก์ Shorts จริงใน tab สปอย → เห็น % เดินจนโหลดเสร็จ
