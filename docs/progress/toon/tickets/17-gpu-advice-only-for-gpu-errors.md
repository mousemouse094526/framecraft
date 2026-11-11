# 17: คำแนะนำ "ปิดโปรแกรมอื่นที่ใช้ GPU" เฉพาะ error ที่เกี่ยวกับ GPU

**What to build:** งานที่ใช้โมเดล (toon, spoil-maker, spoil) ล้มเพราะโค้ดผิดใน process ลูก → ข้อความบอกชนิดและข้อความสั้นของ error โดยไม่มี "ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง" ที่พาไปผิดทาง. error ของ GPU, timeout และ process ลูกที่ตายยังได้คำแนะนำเดิม. `error.code` และหน้าเว็บไม่เปลี่ยน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D84
- Blocked: #36

**Status:** done

## Acceptance criteria

- klein ปลอมของ Ref job หรือ Image job ตอบ `WorkerError` ที่มาจาก `TypeError` → งาน `failed` `model_failed`, ข้อความมีชื่อชนิดและข้อความสั้นของ error, ไม่มี `gpu.ADVICE`
- klein ปลอมตอบ `WorkerError` จาก `RuntimeError` (เช่น MPS out of memory) → `model_failed` และข้อความลงท้าย `gpu.ADVICE` ตามเดิม
- process ลูกปลอมตาย หรือเงียบเกิน timeout → `crashed` / `model_failed` พร้อม `gpu.ADVICE` ตามเดิม
- กติกาเดียวกันกับ process ลูกของ Qwen, OmniVoice ของ toon, งานของ spoil-maker ที่อ่านผ่าน `backend.jobs` และ Transcribe job ของ spoil: มี test อย่างน้อยหนึ่งตัวต่อ feature ที่ error ของโค้ดไม่มี `gpu.ADVICE`
- ชนิดของ error ที่ถือว่าโค้ดผิดอยู่ที่เดียวตาม D84 และ spec ของ spoil › ตาราง error (`model_failed`) บอกว่า error ของโค้ดไม่มีคำแนะนำ
- test ที่มีอยู่ยังผ่าน จำนวนไม่ลด; `uv run pytest` และ `npm test` เขียว

## Notes

- `TypeError` ที่ทำให้เปิด #36 มาจาก backend เก่าที่ยังรันอยู่ (#33 › record Timeline 13:00); ticket นี้ไม่แก้ #33
