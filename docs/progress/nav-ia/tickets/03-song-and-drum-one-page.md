# 03: เพลงกับ reel cover และ reel กลองกับผล render เป็นหน้าเดียว

**What to build:** หน้าเพลง `#/covers/{id}` มีแกะโน้ตแล้วส่วน reel (เครื่องดนตรี ช่วง ข้อความ เสียง ฟัง render ผล render) ในหน้าเดียว พร้อมปุ่ม "ไปที่ reel". หน้า reel กลอง `#/drums/{id}` มีผล render ใต้ฟอร์ม. `#/songs/{id}/cover` และ `#/drums/{id}/renders` เก่าพามาหน้าเดียวของมัน.

**Blocked by:** 01: เมนูและที่อยู่ใหม่ พร้อม redirect

**Covers:**
- Decisions: D6, D7, D9 (cover, renders), D14 (`App` ประกอบช่อง `reel`, แกะใหม่ถาม leave guard, job hook ตัวเดียว, ไปที่ reel)
- ADR: 0069, 0052
- Seams: 3 (เพลง, reel กลอง)
- User stories: 4, 5
- Legal: ข้อความเงื่อนไขการใช้ของ reel cover และ reel คาลิมบาย้ายมาครบ

**Status:** done

## Acceptance criteria

- เพลงที่แกะแล้ว → ผลแกะ, "ไปที่ reel", ส่วน reel ที่ฟัง render ลบผล ได้เหมือนหน้า reel เดิม (กลองและคาลิมบา)
- เพลงที่ยังไม่แกะ → ไม่มีส่วน reel
- แกะใหม่ขณะ reel ยังไม่บันทึก → ถาม "ออกโดยไม่บันทึก?"; ตอบไม่ → ไม่แกะ; แกะเสร็จ → ส่วน reel อ่าน cover ใหม่
- render reel กลองที่หน้านี้เริ่มเสร็จ → ผลใหม่ขึ้นใต้ฟอร์ม เลื่อนไปที่ผล hash ไม่เปลี่ยน
- `#/songs/{id}/cover` → `#/covers/{id}`; `#/drums/{id}/renders` → `#/drums/{id}`
- `kalimba-cover/ui-prompt.md` และข้อความ board แถว drum-notes บอกหน้าเดียว `#/covers/{id}`
