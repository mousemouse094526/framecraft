# 01: ติดตั้ง Qwen, ช่อง GPU และดูภาพ

**What to build:** Setup script โหลด Qwen3.5 9B และ mlx-vlm บน Mac และ Status check มีแถวของทั้งสอง. ในแถว Temp clip ที่ถอดแล้วผู้ใช้กด "ดูภาพ" เห็น % จนเป็น "ดูภาพแล้ว" ยกเลิกได้ และ backend ได้ Shot พร้อม Shot description กับภาพเล็กของทุก Shot. งาน GPU ทุกชนิดจองช่อง GPU ช่องเดียวก่อนเริ่ม: ถอดกับดูภาพไม่รันพร้อมกัน และลบคลิปที่กำลังดูภาพไม่ได้.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D13, D14, D15, D16, D17, D45, D49 (`clip_busy` ของ Describe job), D50, D51, spoil D24
- ADR: 0004, 0009, 0010, 0011, 0012, 0013, 0015, 0016, 0018
- Screens: แถว Temp clip ใน tab สปอย (ยกเว้นคำเตือนของคลิปใน Spoil draft)
- Seams: 1 (Describe, ช่อง GPU และคลิปที่ไม่ใช้ Spoil draft, Status check ของ `model_qwen` และ `mlx_vlm`, ความปลอดภัยของ route ใน ticket นี้), 2 (ข้อของปุ่มดูภาพและ `gpu_busy`), 3 (Describe job)
- User stories: 1

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้งและ Status check

- `QWEN` ต่อท้าย `MODELS` ตาม spec › Modules touched และ `ModelSpec` มี `platforms`; Setup script บน Mac โหลด Qwen แล้วเขียน Model marker; บน Windows ข้าม (D50)
- `mlx-vlm` pin ตาม spec › Dependencies พร้อม marker `darwin`
- `GET /api/setup/status` มีแถว `model_qwen` และ `mlx_vlm`; `run_checks` กับ `sys_platform` `win32` → ทั้งสองแถว `missing` "ยังไม่รองรับบน Windows"
- marker ของ Qwen หาย → `POST /describes` ได้ `503` `not_ready` มี `model_qwen`

### ช่อง GPU

- `POST /describes` ระหว่าง Transcribe job → `409` `gpu_busy` `running: "transcribe"`; `POST /api/spoil/transcriptions` ระหว่าง Describe job → `409` `gpu_busy`
- `POST /api/spoil/downloads` ระหว่าง Describe job → `202`
- `POST /describes` ซ้อนกันสองครั้ง → ครั้งที่สอง `409` `busy`
- `DELETE /api/spoil/clips/{id}` ระหว่าง Describe job ของคลิปนั้น → `409` `clip_busy`
- ทุกทางออกของงาน (`done`, `failed`, `cancelled`) คืนช่อง GPU: งาน GPU ถัดไปเริ่มได้

### Describe job

- คลิปทดสอบ 3 วินาทีจาก `lavfi` (สีเปลี่ยนที่ 1 และ 2 วินาที) → poll จน `done`, `GET /clips/{id}/shots` มี 3 Shot ที่ `start` 0, 1, 2 (±0.1) และภาพเล็กกว้าง 320 ทุก Shot; `GET /api/spoil/clips` มี `described: true`
- ตัวหาจุดตัดปลอมให้ช่วง 25 วินาที → 3 Shot ยาวเท่ากัน; ช่วง 0.5 วินาทีกลางคลิป → รวมเข้า Shot ก่อนหน้า
- คลิปดูภาพแล้ว ดูภาพใหม่แล้วยกเลิกระหว่าง `describing` → `cancelled`, Shot และภาพเล็กเดิมยังอยู่, ไม่มี folder `.new-{id}`
- `GET /api/spoil/clips/{id}/thumbnail` หลังดูภาพ → ยังเป็น thumbnail เดิมของคลิป
- LLM ปลอมเกิน timeout ของการบรรยายภาพ (ลด timeout ใน test) → `failed` `model_failed`
- ลบคลิปที่ดูภาพแล้ว → Shot ของคลิปหาย; start app ขณะมี `.new-a` → หาย; Temp clip ที่ startup ของ spoil ล้างไม่มี Shot เหลือ
- `/clips/../x/shots` และ `{n}` ที่ไม่มี → `404` `not_found`; POST ที่ `Content-Type: text/plain` → `415`; `Host: evil.example` → `400`

### หน้าเว็บ

- แถวคลิปที่ถอดแล้ว กดดูภาพ, current คืน `describing` 40/100 แล้ว `done` → เห็น 40% แล้ว "ดูภาพแล้ว"
- `409` `gpu_busy` `running: "transcribe"` → เห็น "รอให้งานถอดบทพูดเสร็จก่อน"; ปุ่มกดไม่ได้พร้อมเหตุผลเมื่อมีงาน GPU อื่น
- ดูภาพคลิปที่ดูแล้ว → ยืนยันก่อนส่ง
- หน้าตาตรงแบบของจอ "แถว Temp clip ใน tab สปอย" (Source ยัง `pending`: Blocked #1)

### เช็คมือบน Mac M2 (Seam 3)

- ก่อนเขียน worker จริง ลอง Library assumptions ของ mlx-vlm ทั้ง 3 ข้อ (`load`, `apply_chat_template(enable_thinking=False)`, `generate` กับภาพ) — ไม่ได้ข้อไหน หยุดแล้วถาม
- Describe job หนัง 96 นาที → จบภายใน 60 นาที, 700–1,000 Shot, สุ่ม 10 Shot ตรงภาพ ≥ 8; จดเวลาใน progress
- ยกเลิกระหว่าง `describing` → process ลูกหายภายใน 5 วินาที
