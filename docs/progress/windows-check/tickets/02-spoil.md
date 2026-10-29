# 02: เช็ค spoil บน Windows NVIDIA

**What to build:** ผู้ใช้ Windows ที่มีการ์ด NVIDIA โหลด เล่น ลบ และถอดบทพูดของ Temp clip ใน tab สปอยได้เหมือนบน Mac. แก้สิ่งที่พังเฉพาะ Windows.

**Blocked by:** 01: เช็ค setup-status บน Windows NVIDIA

**Covers:**
- Decisions: spoil D15, spoil D30, setup-status D25
- ADR: 0012, 0014
- Seams: 2, 3

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้งและโหลด

- รัน `setup.cmd` → exit 0 และหน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิป → ได้ mp4 ด้านสั้น ≤ 1080 และเล่นได้ใน player
- ยกเลิกกลางทาง → หยุดภายใน 5 วินาที และ `.partial/` ว่าง
- ลิงก์ live ที่ยังไม่เริ่ม → `live`
- Ctrl+C ระหว่างโหลด → ไม่มี process ค้าง
- restart `npm run dev` → รายการเดิมอยู่ครบ

### ลบ

- เล่นคลิปใน player แล้วกดลบ → player ปลดก่อน `DELETE` แล้วลบได้ หรือได้ `in_use` และแถวยังอยู่
- thumbnail ที่ Windows ล็อกไว้ตอนลบ → ถูกล้างตอน start ครั้งถัดไป
- ลบคลิปที่ถอดแล้วขณะ player เปิดอยู่ → ลบได้ หรือได้ `in_use` และ Transcript ยังอยู่คู่คลิป

### ถอดบทพูด

- ถอด Shorts หนึ่งคลิปและหนังยาวกว่า 1 ชั่วโมงหนึ่งคลิปบน `cuda` → `done` และ Transcript อ่านรู้เรื่อง; ได้ขยะ → เปลี่ยน `cuda` เป็น `float32` (spoil D30)
- Shorts ภาษาไทย → เวลาของบรรทัดตรงกับเสียงภายใน 2 วินาที (สุ่มดู 5 บรรทัด)
- Copy แล้ววาง → ได้ข้อความครบ; `.srt` เปิดใน VLC แล้ว subtitle ตรงเวลา
- restart `npm run dev` → ยังเห็น Transcript
- ถอดหนังยาวผ่านหน้าเว็บ → % ขยับทุกช่วง 300 วินาที
- ถอดพร้อมโหลดคลิปอื่น → ทั้งสองงาน `done`
- ฆ่า process ลูกด้วยมือระหว่างถอดขณะมีงานโหลด → งานถอด `crashed`, งานโหลดเดินต่อจน `done`
- process ลูก `spawn` เริ่มได้บน Windows
- ยกเลิกงานถอด → process ลูกและ ffmpeg ที่มันเปิดหายภายใน 5 วินาที และ memory ของ backend ไม่โตขึ้น
