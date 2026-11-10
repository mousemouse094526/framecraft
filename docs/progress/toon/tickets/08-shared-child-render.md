# 08: เริ่มและหยุด child และ render ที่ซ้ำข้าม feature

**What to build:** การเริ่ม child (start, `track`, รอ `Ready`) และการหยุด child (`track(None)`, `stop_process`) อยู่ที่เดียวที่ Qwen, klein และตัวพูดใช้ร่วมกัน; render ของการ์ตูนเล่ากับของสปอยใช้ `on_progress` และการคืน GPU ชุดเดียว; ส่วนที่ซ้ำใน toon (map `ref_rev`, `_plot_items`) เหลือตัวเดียว. ผู้ใช้เห็นทุกอย่างเหมือนเดิม.

**Blocked by:** 07: โครงงานของ toon และชื่อที่ชนกัน

**Covers:**
- Decisions: D60, spoil-maker D60
- ADR: 0012, 0015
- Blocked: #20 (feature review)

**Status:** ready-for-agent

## Acceptance criteria

### child

- เริ่ม Qwen, klein หรือตัวพูด → ผ่านฟังก์ชันเริ่ม child ตัวเดียวที่อยู่ module กลางตามกติกา "Where shared code goes" ของ backend; child ไม่ตอบ `Ready` → error และ GPU slot ถูกคืนเหมือนเดิม
- หยุด child ทุกที่ (ขั้นของ Toon job, `_free_gpu`) ผ่านฟังก์ชันหยุดตัวเดียว → ยกเลิก job กลางทาง ไม่มี process ค้าง
- `on_progress` และ `_free_gpu` ของ `toon.render` และ `spoil_maker.render` เขียนที่เดียว → test render ของทั้งสอง feature ผ่านเหมือนเดิม

### ส่วนที่ซ้ำใน toon

- map `ref_rev` ของ Series สร้างที่เดียว; Image job, render และ Cards job เรียกตัวนั้น → การ์ดที่ภาพอ้างอิงเปลี่ยนยังขึ้นสถานะเดิม
- `_plot_items` เหลือตัวเดียวที่เลือกพฤติกรรมได้ (ตัดทิ้งสำหรับคำตอบของ Qwen, raise สำหรับ body ของผู้ใช้) → test ของ writer และ EP ผ่านเหมือนเดิม
- `backend.renders` รับ `(folder, name)` เป็นค่าเดียว ไม่ส่งสองตัวคู่กัน
- `uv run pytest`, `npm test`, `npm run build` และ CI ทั้งหมดเขียว
