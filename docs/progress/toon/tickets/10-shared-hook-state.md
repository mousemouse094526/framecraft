# 10: state ที่ใช้ร่วมของ hook หน้าเว็บ toon

**What to build:** hook หน้าเว็บของ toon (render, คลังเสียงพื้น, เลือกภาพอ้างอิง, ตัวละครและฉากหลัง, EP) แก้ state ตอนพร้อมผ่านตัวช่วยตัวเดียว แทนที่จะเขียน `update` เองทุก hook. การส่งของแก้ไข (ตัวละครหรือฉากหลัง, EP) ที่รับ 200/201 แล้วแทนค่าและล้าง notice ไม่งั้นขึ้น `refused` ใช้ทางเดียว. ผู้ใช้เห็นทุกอย่างเหมือนเดิม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D63
- Blocked: #22 (feature review รอบสาม)

**Status:** done

## Acceptance criteria

- hook ทั้งห้าแก้ state ตอนพร้อมผ่านตัวช่วยตัวเดียว; state ที่ไม่ใช่ `ready` → ไม่ถูกแก้ เหมือนเดิม
- แก้ตัวละครหรือฉากหลัง หรือแก้ EP แล้วได้ 200/201 → ค่าบนหน้าเปลี่ยนเป็นค่าที่ backend ตอบ และ notice หายไป
- แก้แล้ว backend ตอบ error → ขึ้นข้อความ `refused` เดิม ค่าบนหน้าไม่เปลี่ยน
- ตัวช่วยอยู่ตามกติกาของ `vite-react-web` SKILL.md และมี test ของตัวเอง; test ของ hook และหน้าที่มีอยู่ยังผ่าน จำนวนไม่ลด
- `npm --prefix frontend run typecheck`, `npm test`, `npm run build`, `uv run pytest` และ CI ทั้งหมดเขียว
