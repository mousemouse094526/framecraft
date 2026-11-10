# 11: ค่า EP เดียวและ helper ของ test ที่ใช้ร่วม

**What to build:** EP หนึ่งตอนของ Series (project, Series, EP) เดินในโค้ด backend ของ toon และ `paths.py` เป็นค่าเดียว แทนสามค่าคู่กันราว 20 signature (render, การเสียงและ render, ลบไฟล์ของการ์ด ฯลฯ). fixture `project` และ helper ที่ test API ของ toon import ข้ามไฟล์กันย้ายเข้า fakes ของ test. ผู้ใช้เห็นทุกอย่างเหมือนเดิม.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D64
- Blocked: #26, #27 (feature review รอบสี่)

**Status:** ready

## Acceptance criteria

### ค่า EP เดียว

- ฟังก์ชันใน `toon/` และ `paths.py` ที่รับ project, Series และ EP สามตัวคู่กัน (เช่น `render._run`, `_voice_and_render`, `_render`, `episodes.remove_card_files`) รับค่าเดียว ไม่รับสามตัวคู่กัน
- ชื่อ type ไม่ชน `EpRef` ที่ response model ใช้อยู่ ไม่ชน `ItemRef` (D64) และอยู่ตามกติกา "Where shared code goes" ของ backend; `fastapi-api` SKILL.md กับ spec › Modules touched เขียนถึง
- route ของ toon ที่ทำงานกับ EP ตัวเดียวสร้างค่านี้จาก path ครั้งเดียวแล้วส่งต่อ → ทุก route ตอบ status และ body เหมือนเดิม, Series หรือ EP ที่ไม่มี → error เดิม

### helper ของ test

- fixture `project(fake_root)` ของ test API ของ toon มาจาก fakes ของ test ตัวเดียว; ไฟล์ test ของ toon ไม่เขียนเอง
- helper ที่ test ของ toon ใช้ข้ามไฟล์ (`Writer`, `new_ep`, `run`, `start`, `create`, `png`, `upload`, `add`, `import_tone`) อยู่ใน fakes; ไม่มีไฟล์ test ใด import จากไฟล์ test อื่น
- conftest มีแค่ `fake_root`
- test ทุกตัวที่มีอยู่ยังผ่าน จำนวนไม่ลด
- `uv run pytest`, `npm test`, `npm run build` และ CI ทั้งหมดเขียว
