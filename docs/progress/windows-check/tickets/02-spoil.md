# 02: เช็ค spoil บน Windows NVIDIA

**What to build:** ผู้ใช้ Windows ที่มีการ์ด NVIDIA โหลด เล่น ลบ และถอดบทพูดของ Temp clip ใน tab คลิป (spoil-maker D53) และแก้ Transcript ทีละบรรทัดได้เหมือนบน Mac. แก้สิ่งที่พังเฉพาะ Windows.

**Blocked by:** 01: เช็ค setup-status บน Windows NVIDIA

**Covers:**
- Decisions: spoil D15, spoil D30, spoil D36, spoil D42, setup-status D25, spoil-maker D54
- ADR: 0012, 0014
- Seams: 2, 3, 3a (ข้อ Windows)

**Status:** ready-for-agent

## Acceptance criteria

### ติดตั้งและโหลด

- รัน `setup.cmd` → exit 0 และหน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิป → ได้ mp4 ด้านสั้น ≤ 1080 และเล่นได้ใน player
- ยกเลิกกลางทาง → หยุดภายใน 5 วินาที และ `.partial/` ว่าง
- ลิงก์ live ที่ยังไม่เริ่ม → `live`
- Ctrl+C ระหว่างโหลด → ไม่มี process ค้าง
- restart `npm run dev` → รายการเดิมอยู่ครบ

- คลิป public ของ Facebook และ TikTok (spoil ticket 08 ใช้ `https://www.facebook.com/nasalarc/videos/coming-for-landing-watch-a-rocket-sled-test-of-nasa-technology/518525165385328/` และ `https://www.tiktok.com/@nasa/video/7679483952507276558`) → `done`, mp4 h264 ≤ 1080 เล่นได้, thumbnail ของ TikTok ขึ้นในแถว; ลิงก์ซ้ำ → `duplicate` ชี้แถวเดิม (spoil D51, D56)
- ลิงก์ `https://example.com/a` → `unsupported`; `.partial/` ว่างหลังคลิป Facebook ที่ได้ `unsupported_format`

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
- แก้บรรทัดของ Transcript แล้วกด "บันทึก" → `PATCH` ได้ `200`, บรรทัดมีป้าย "แก้แล้ว"; `.tmp` rename ทับ `{id}.transcript.json` ได้บน Windows และไม่มี `{id}.transcript.json.tmp` ค้าง; restart `npm run dev` → ข้อความที่แก้ยังอยู่ (spoil-maker D54)

### ตัดช่วง (spoil seam 3a, D36, D42)

- ตัดหนังยาวกว่า 1 ชั่วโมงสองช่วงผ่าน `curl -X POST http://127.0.0.1:8000/api/spoil/trims` → `done` ด้วย `libx264`, เล่นได้ใน player, ความยาวตรงภายใน 1 วินาที และภาพเสียงตรงกันรอบรอยตัด; จดเวลาที่ใช้ลง progress.md
- ตัดขณะ player เปิดคลิปนั้นอยู่ในอีก tab ของ browser → `done` หรือ `in_use` ที่ไฟล์เดิมยังเล่นได้ และ `.partial/` ว่าง
- ยกเลิกที่ประมาณ 30% → ffmpeg หายภายใน 5 วินาที (Task Manager) และไฟล์เดิมเล่นได้
