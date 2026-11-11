# 15: งานภาพที่จบเองและไม่ swap บน Mac 16 GB

**What to build:** บน M1 16 GB ผู้ใช้สร้างภาพอ้างอิง 3 แบบ และ "สร้างภาพที่ขาดทั้งหมด" ได้โดยงานจบเองทุกครั้ง เครื่องไม่ swap หนัก และเวลาต่อภาพใกล้ trial. เหตุของงานที่ค้างใน Blocked #32 ถูกหาและแก้ หรือมีตัวดึง traceback รอจับรอบหน้า. ค่าการสร้างภาพเป็นขั้นแรกของ D74 ที่ผ่านเกณฑ์ทั้งเครื่อง.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D74, D75
- ADR: 0036
- Seams: 1 (klein ปลอมเงียบ)
- Blocked: #32

**Status:** ready-for-agent

## Acceptance criteria

### งานที่ค้าง (D75)

- log `[api]` ของสองรอบที่ค้างใน Blocked #32 → จดใน bug record ว่าแต่ละรอบค้างนานเท่าไรก่อน restart
- หาเหตุด้วย `/kiki-debug` → bug record และ postmortem ใน `bugs/` ของ toon; พบเหตุ → regression test ที่ล้มก่อนแก้
- ไม่เกิดซ้ำใน Ref job จริง 5 ครั้ง → ตัวดึง traceback อยู่ใน backend และ process ลูกของ klein, bug record บอกว่ายังไม่พบเหตุ แล้ววัดตาม D74 ต่อ
- klein ปลอมไม่ตอบ `Encode` ของ Ref job เกิน timeout ต่อภาพ → งาน `failed` `model_failed`, process ปลอมหยุด, เริ่ม Ref job ใหม่ได้ทันทีโดยไม่ได้ `gpu_busy`
- klein ปลอมไม่ตอบ `Draw` ใบที่สองของ Image job → งาน `failed` `model_failed`, ภาพใบแรกอยู่, process ปลอมหยุด

### memory ทั้งเครื่อง (D74)

- ขั้น 0 บน M1 16 GB ตามวิธีวัดของ D74 → ตัวเลขทีละช่วงของทุก process อยู่ใน `progress.md`
- ขั้นแรกที่ผ่าน: Ref job 3 ครั้งติดกัน, Image job กรณีหนักสุด และ "สร้างภาพที่ขาดทั้งหมด" 20 การ์ด → swap เพิ่มไม่เกิน 1 GB, `memory_pressure` ไม่ถึง critical, ทุกงาน `done` ไม่มี `failed_cards`, เวลาต่อภาพไม่เกิน 1.5 เท่าของ trial
- ขั้น 1 ที่ใช้ → Ref job และ Image job ได้ภาพเหมือนเดิมที่ seed เดียวกัน; process ลูกที่ encode จบก่อน process ลูกที่วาดเริ่ม
- ขั้น 2–3 ที่ใช้ → ลองคงตัวละคร 10 ภาพผ่านแบบ D49 ภาพอยู่ใน `trial-images/`
- ขั้น 2 ที่ใช้ → เครื่องที่มีแต่ Q4_K_M เห็นแถว `model_klein_gguf` `missing` และ setup โหลด Q3_K_M
- ขั้น 3 ที่ใช้ → ภาพการ์ด ฉากหลัง และตัวละครใหม่เป็นขนาดใหม่, render ได้ 1080×1920 เหมือนเดิม, ภาพที่มีอยู่ยังใช้ได้
- ขั้นที่ใช้จดเป็น `D{n}` (`From: build ticket 15`) พร้อมตัวเลขทุกขั้นที่ลอง; หน้าเลือกภาพบอกเวลาตามที่วัดได้บน M1
- ไม่มีขั้นไหนผ่าน → Blocked row ใหม่ Needs `/warroom toon` พร้อมตัวเลขทุกขั้น
- test ที่มีอยู่ยังผ่าน จำนวนไม่ลด; `uv run pytest` และ check ของหน้าเว็บเขียว
