# 09: Backend เอาไฟล์ mp4 ในเครื่องเข้า

**What to build:** `POST /api/spoil/imports/check` แล้ว `POST /api/spoil/imports` ที่ body เป็นไฟล์ mp4 ดิบ ได้ Temp clip `local-…` ที่เล่น ถอด ตัด ได้เหมือนคลิปที่โหลด. ไฟล์ที่ไม่ใช่ mp4 h264/aac ≤ 1080 ถูกปฏิเสธพร้อมเหตุ; ไฟล์ซ้ำชี้แถวเดิม; รันพร้อม Download job ไม่ได้; upload ค้างหรือถูกตัดไม่ทิ้งไฟล์และไม่ค้าง `busy`. ลองครบด้วย `curl --data-binary`.

**Blocked by:** 08

**Covers:**
- Decisions: D49, D50, D51 (ไฟล์ในเครื่อง), D52 (File import, ทีละงาน, เช็คดิสก์, ข้อมูลในแถว), D53, D55 (upload ค้าง, thread, ADR-0013 ต่อ route)
- ADR: 0027, 0028, 0013, 0010
- Seams: 1 (ข้อของ `/imports`), 2 (ไฟล์ ≥ 4 GB ผ่าน proxy ของ Vite)
- User stories: 15 (ฝั่ง API)
- Legal: 8

**Status:** done

## Acceptance criteria

### API

- test ของ seam 1 ทุกข้อของ `/imports` และ `/imports/check` ผ่าน; test เดิมทั้งหมดผ่าน
- ทุกขั้นของ spec › File import (0–7) และทุก error ในแถว API ทำตาม spec
- `POST /imports` รับ `application/octet-stream` อย่างเดียว; route อื่นที่ส่ง octet-stream และ `multipart/form-data` ทุก route ยังได้ `415` (ADR-0028)
- เขียนไฟล์และเรียก ffmpeg ใน thread; poll `GET /downloads/current` ระหว่างรับไฟล์ตอบภายใน 1 วินาที
- flag "กำลังรับไฟล์" ปล่อยทุกทาง: สำเร็จ, error, `ClientDisconnect`, `stalled`

### เช็คมือบน Mac

- `curl --data-binary @a.mp4 -H 'Content-Type: application/octet-stream'` ของ mp4 ยาวกว่า 1 ชั่วโมง → `201`; ถอดและตัดคลิปนั้นได้; ไฟล์ต้นฉบับไม่เปลี่ยน (เทียบ sha1)
- ไฟล์ ≥ 4 GB ผ่าน `npm run dev` → `201`; ถูกตัดราว 300 วินาที → แก้ตาม spec › Seams ข้อ 2; แก้ไม่ได้ → หยุดแล้วถามผู้ใช้; จดเวลาของไฟล์ 2 GB ลง progress.md
- Ctrl+C ระหว่างรับไฟล์ แล้ว `npm run dev` ใหม่ → `.partial/` ว่าง
