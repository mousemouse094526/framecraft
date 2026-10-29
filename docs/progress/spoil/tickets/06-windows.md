# 06: เช็คบน Windows NVIDIA

**What to build:** ผู้ใช้บน Windows ที่มีการ์ด NVIDIA รัน `setup.cmd` แล้วโหลด เล่น ลบ และถอดบทพูดของ Temp clip ใน tab สปอยได้เหมือนบน Mac. ticket นี้คือเช็คมือบนเครื่องจริงและแก้สิ่งที่พังเฉพาะ Windows.

**Blocked by:** 05: หน้าสองคอลัมน์และกล่องถอดบทพูด, setup-status 03: Windows NVIDIA

**Covers:**
- ADR: 0006, 0012
- Seams: 2, 3 (บน Windows)

**Status:** ready-for-agent

## Acceptance criteria

- รัน `setup.cmd` → exit 0 และหน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิป → ได้ mp4 ด้านสั้น ≤ 1080 และเล่นได้ใน player
- ยกเลิกกลางทาง → หยุดภายใน 5 วินาที และ `.partial/` ว่าง
- เล่นคลิปใน player แล้วกดลบ → ลบได้ หรือได้ `in_use` และแถวยังอยู่
- restart `npm run dev` → รายการเดิมอยู่ครบ
- Ctrl+C ระหว่างโหลด → ไม่มี process ค้าง
- ถอด Shorts หนึ่งคลิปและหนังยาวกว่า 1 ชั่วโมงหนึ่งคลิปบน `cuda` → `done` และ Transcript อ่านรู้เรื่อง
- process ลูก `spawn` เริ่มได้บน Windows; ยกเลิกงานถอด → process ลูกหายภายใน 5 วินาที
- ลบคลิปที่ถอดแล้วขณะ player เปิดอยู่ → ลบได้ หรือได้ `in_use` และ Transcript ยังอยู่คู่คลิป
