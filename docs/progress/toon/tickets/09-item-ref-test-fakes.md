# 09: ItemRef และ fixture ของ test ที่ใช้ร่วม

**What to build:** ตัวละครหรือฉากหลังหนึ่งตัวของ Series (project, Series, ชนิด, id) เดินในโค้ดเป็นค่าเดียว `ItemRef` ทั้งในส่วนภาพอ้างอิงของ Series และใน route ของ toon. fixture ของ Qwen, klein, ตัวพูด และ client ที่ test API ของ toon เขียนซ้ำกันเหลือ helper ชุดเดียว. ผู้ใช้เห็นทุกอย่างเหมือนเดิม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D61, D63
- Blocked: #23, #24 (feature review รอบสาม)

**Status:** done

## Acceptance criteria

### ItemRef

- ฟังก์ชันภาพอ้างอิงของ Series (แผนภาพอ้างอิง, ภาพที่เลือก, ภาพที่รอเลือก, เก็บภาพที่รอเลือก, เลือกภาพ, เช็คและรับไฟล์ที่อัปโหลด) รับ `ItemRef` ค่าเดียว ไม่รับ project, Series, ชนิด และ id สี่ตัวคู่กัน
- 8 route ของ toon ที่ทำงานกับตัวละครหรือฉากหลังตัวเดียวสร้าง `ItemRef` จาก path ครั้งเดียวแล้วส่งต่อ → ทุก route ตอบ status และ body เหมือนเดิม, Series หรือ item ที่ไม่มี → error เดิม
- `ItemRef` อยู่ตามกติกา "Where shared code goes" ของ backend และ `fastapi-api` SKILL.md กับ spec › Modules touched เขียนถึง

### fixture ของ test

- fixture `llm`, `klein`, `tts`, `client` ของ test API ของ toon (images, ref, render, eps, sounds) มาจาก helper ใน fakes ของ test ตัวเดียว; ไฟล์ test ไม่เขียน fixture ชุดนั้นเอง
- conftest มีแค่ `fake_root`
- test ทุกตัวที่มีอยู่ยังผ่าน จำนวนไม่ลด
- `uv run pytest`, `npm test`, `npm run build` และ CI ทั้งหมดเขียว
