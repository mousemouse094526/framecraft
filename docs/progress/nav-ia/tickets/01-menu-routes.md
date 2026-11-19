# 01: เมนูและที่อยู่ใหม่ พร้อม redirect

**What to build:** เมนูหลักมีรายการตามตาราง spec › Design และทุกหน้าอยู่ใต้ hash ของที่มันอยู่ในเมนู: คลิปทั้งหมดใต้สปอย, เสียงพากย์ที่ `#/voices`, หัวข้อ reel cover ที่ `#/covers`. hash เก่าทุกตัวพาไปหน้าใหม่ และล่าสุดของเพลงเดิมย้ายตาม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D3, D4, D6 (ชื่อหัวข้อและ hash), D9, D14 (ลบค่าคงที่, ลิงก์ `ClipPicker`)
- ADR: 0067, 0068
- Seams: 1
- User stories: 1, 2, 7

**Status:** done

## Acceptance criteria

- เมนู → เล่าเรื่อง (สปอย: ทำสปอย · คลิปทั้งหมด; การ์ตูนเล่า) · ดนตรี (reel cover: เพลงทั้งหมด; reel กลอง) · คลัง (คลังความรู้ · คลังเสียง · เสียงพากย์ พร้อม "ใช้กับ …") · ตั้งค่า (ติดตั้ง)
- `#/spoil/clips` → หน้าคลิปทั้งหมด หัวหน้า "สปอย / คลิปทั้งหมด" หัวข้อสปอยสว่าง
- `#/voices` → หน้า Saved voice หัวหน้า "คลัง / เสียงพากย์" ไม่มีหัวข้อสว่าง ไม่มีปุ่มกลับไปสปอย
- `#/covers` และ `#/covers/{id}` → รายการเพลงและหน้าเพลง หัวข้อ reel cover สว่าง
- hash เก่า `#/clips`, `#/spoil/voices`, `#/songs`, `#/songs/{id}` → `location.hash` เป็น hash ใหม่ และหน้าใหม่ขึ้น
- ล่าสุดที่เก็บใต้กุญแจ `songs` เป็น `#/songs/{id}` → เมนูแสดง `#/covers/{id}` ใต้ reel cover
- ลิงก์ในแอปที่เคยชี้ `#/clips`, `#/spoil/voices`, `#/songs…` ชี้ hash ใหม่ตรง
- ทุก test เดิมผ่าน หลังแก้แค่ hash
