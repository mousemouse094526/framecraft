# 02: Worker Qwen บน Windows และ timeout ต่อ OS

**What to build:** บน Windows ที่ทุกแถวผ่าน กด "บรรยายฉาก" ใน tab คลิป หรือร่างบทและเรียบเรียงบทใน tab สปอย แล้วงานเริ่มด้วย worker transformers ที่โหลด `Qwen/Qwen3.5-9B` แบบ 4-bit บนการ์ด. งานที่ช้ากว่า Mac ไม่ถูกตัดกลางทางเพราะ timeout อ่านจากตารางของ OS นั้น; Mac ใช้ worker mlx-vlm และ timeout เดิม. ทุกอย่างเช็คบน Mac ด้วย worker ปลอม.

**Blocked by:** 01: Status check, gate และ Setup script ของ Qwen ต่อ OS

**Covers:**
- Decisions: D3 (worker transformers 4-bit), D7, D10 (bfloat16 ทางเดียว), D12 (ข้ามการย่อ, timeout), spoil-maker D47, spoil-maker D51
- ADR: 0008, 0012
- Seams: 2 (งานเริ่มกับ snapshot ของ Windows), 3
- User stories: 2, 3, 4

**Status:** done

## Acceptance criteria

### เลือก worker ต่อ OS

- `win32` ทุกแถวผ่าน → `POST /api/describes` และ `POST /api/draft-jobs` เริ่มงาน และ worker ปลอมได้ snapshot ของ `Qwen/Qwen3.5-9B`
- `darwin` → ใช้ worker mlx-vlm เดิม; ข้อความระหว่าง process (`Generate`, `Ready`, `Generated`, `WorkerError`) ไม่เปลี่ยน
- import backend ไม่ import module ของ worker Windows, transformers หรือ bitsandbytes; module นั้น import ทั้งสองภายใน process ลูกเท่านั้น

### Worker ของ Windows

- snapshot ไม่ใช่ folder → `FileNotFoundError` ก่อนเรียก transformers จึงไม่มีการโหลดจาก network
- โหลดตาม spec › Windows worker: `local_files_only`, `cuda:0`, nf4, compute bfloat16, `llm_int8_skip_modules` `["model.visual", "lm_head"]` (D16)
- หลังโหลด → log ชื่อ module ที่ไม่ได้ย่อ และ VRAM ที่ใช้ แล้วส่ง `Ready`
- `Generate` → chat template ด้วย `enable_thinking=False` พร้อมภาพเมื่อมี; `temperature` 0 → ไม่ sample; ส่ง `Generated` เป็นข้อความเฉพาะ token ใหม่ ไม่มี prompt และ special token
- exception ใดๆ → `WorkerError("model_failed", …)` แล้วออก

### Timeout ต่อ OS

- ตาราง `Timeouts(describe, write, polish, pick)` อยู่ที่เดียว: Mac 60, 600, 300, 60 วินาที; Windows 300, 3000, 1500, 300 วินาที; อ่านตอนเริ่มงาน
- ตารางสลับเป็น Mac 0.2 วินาที Windows 1 วินาที กับ worker ปลอมที่ตอบใน 0.5 วินาที → ทั้งสี่ขั้น (บรรยาย, เขียน, เรียบเรียง, เลือก Shot) บน `win32` จบ `done`
- ตารางเดียวกันบน `darwin` → บรรยายและเลือก Shot จบ `model_failed` ข้อความบอกวินาทีจากตาราง; เขียนบทและเรียบเรียงเป็นการลองที่ไม่สำเร็จหนึ่งครั้งตามเดิม (D16)
- test timeout เดิมสลับตารางแทนการ patch ค่าคงที่
