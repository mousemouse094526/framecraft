# 03: ลอง Qwen บนเครื่อง Windows RTX 30xx ขึ้นไป

**What to build:** บนเครื่อง Windows ที่การ์ด RTX 30xx ขึ้นไปและ VRAM ≥ 8 GB ผู้ใช้รัน Setup script แล้วทุกแถวเขียว บรรยายฉาก ร่างบท และเรียบเรียงบทของ Temp clip `f7jkZXvaB4g` จนจบ. ผลวัดจดใน trial และ timeout ของ Windows ตั้งจากผลวัด.

**Blocked by:** 02: Worker Qwen บน Windows และ timeout ต่อ OS — และเครื่อง Windows ที่ตรงเป้า (progress › Blocked #2)

**Covers:**
- Decisions: D5, D7 (ค่าหลังลอง), D11, D12 (token ต่างกัน, เวลาโหลด)
- User stories: 1, 2, 3, 4

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้ง

- รัน Setup script บนเครื่องที่ตรงเป้า → จบปกติ และหน้าติดตั้งทุกแถวเขียว รวม "GPU", "bitsandbytes", "Qwen3.5 9B model"

### งาน Qwen กับ `f7jkZXvaB4g` (D5)

- Describe job ทั้งเรื่อง → `done`
- Draft job ของ EP 30 นาที (ร่างบท เรียบเรียง เลือก Shot) → `done`
- Draft job ที่ Transcript กับ Story ใกล้ 32,000 token → `done` ไม่ out of memory
- ปุ่ม "เรียบเรียงใหม่" → `done`
- ผู้ใช้อ่านบทไทยแล้วบอกว่าใช้ได้

### Trial record

- trial จดตามที่ spec › Testing decisions กำหนด: ชื่อการ์ดและ VRAM, เวลาจากเริ่มงานถึง `Ready`, เวลานานสุดต่อขั้น, VRAM สูงสุด, module ที่ไม่ได้ย่อจาก log
- จำนวน token ของ Transcript ทั้งหมดของ `f7jkZXvaB4g` บน Windows เท่ากับบน Mac; ไม่เท่า → Blocked และ change request
- ตาราง timeout ของ Windows เปลี่ยนเป็น max(ค่าก่อนลอง, นานสุดที่วัด × 3 ปัดขึ้นเป็นนาที) ต่อขั้น
- 8 GB ไม่พอ, ตัวรันใช้ไม่ได้ หรือเวลาโหลดนานจนผู้ใช้คิดว่าค้าง → Blocked และ `/warroom windows-launch` change request แทนการแก้ใน ticket

### Mac

- test ทั้งหมดบน Mac ยังผ่านหลังเปลี่ยนตาราง timeout
