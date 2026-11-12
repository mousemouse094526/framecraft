# 16: Plot job ที่ผ่านกับ Qwen จริงเกือบทุกครั้ง และ log ที่บอกว่าคำตอบผิดตรงไหน

**What to build:** Plot job กับ Qwen จริงได้ `acts` เท่าองก์ของ EP แทบทุกครั้ง (วันนี้ ~25% ของคำตอบมีจำนวนช่องผิด จน ~1.6% ของงานยัง `write_failed`). คำตอบของ Qwen ที่อ่านไม่ได้ทิ้งร่องรอยใน log พอให้วินิจฉัยโดยไม่ต้องรัน Qwen ซ้ำ. test ของ Plot job มีคำตอบตามรูปที่ Qwen จริงตอบ ไม่ใช่แค่รูปในตัวอย่างของ prompt.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D81, D82
- Blocked: #35 (Prevention ใน [record](../bugs/2026-11-11-plot-job-write-failed-with-qwen.md))

**Status:** done

## Acceptance criteria

- คำตอบที่อ่านไม่ได้ของงาน Qwen (Plot, Cards) → log บอกเหตุ (อ่าน JSON ไม่ได้ / จำนวนองก์ผิดเท่าไร / ไม่มีฉากหลัง ฯลฯ) และต้นของคำตอบที่ตัดให้สั้น
- test ของ Plot job และ Cards job มีคำตอบอย่างน้อยหนึ่งชุดที่ย่อจากคำตอบจริงของ Qwen ในรอบ debug ของ #35 (`acts` เป็นข้อความ, ของเดิมที่มี `name`/`description` ติดมากับ `id`)
- prompt ของ Plot job ที่ปรับแล้ว กับ Qwen จริงบน M1 20 ครั้งของ EP `e_14c37720` → `acts` เท่าองก์อย่างน้อย 19/20 (เดิม 15/20); ถ้าไม่ถึง จดผลและทางที่ลองใน `progress.md`
- test ที่มีอยู่ยังผ่าน จำนวนไม่ลด; `uv run pytest` เขียว

## Notes

- #35 เก็บแต่คำตอบของ Plot prompt: คำตอบจริงของ Cards prompt เก็บในรอบนี้ (4 องก์ของ `e_14c37720`, plot จากคำตอบ key ต่อองก์) แล้วย่อเป็น test
