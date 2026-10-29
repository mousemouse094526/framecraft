# 01: ติดตั้ง yt-dlp กับ Deno และ Download API

**What to build:** ผู้ใช้รัน Setup script แล้วได้ yt-dlp กับ Deno และเห็นหน้า Setup status 11 แถว. Backend รับลิงก์ YouTube เป็น Download job เบื้องหลัง บอก % และยกเลิกได้ จนได้ Temp clip ใน `media/temp/` โดยยังไม่มีหน้าจอใหม่ (เรียกผ่าน API). ก่อนเขียนงานโหลด ลองข้อที่ spec › Library assumptions บอกให้ลองกับ YouTube จริงก่อน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D5, D6, D8, D9, D11, D12, D14, D15, setup-status D7
- ADR: 0003, 0005, 0008, 0009, 0010, 0011
- Seams: 1 (ทุกข้อของ `/downloads`, Status check, การล้างตอน start และ Host), 2 (บน Mac)
- User stories: 2, 3, 6, 7
- Legal: 1, 2 (ผู้ใช้รับความเสี่ยงใน D13)

**Status:** done

## Acceptance criteria

### ลองกับ YouTube จริงก่อน

- ยกเลิกด้วย `DownloadCancelled` จาก progress hook → การโหลดหยุด; ไม่ได้ → ใช้ทางสำรองใน spec › Library assumptions
- merge 1080p ด้วย ffmpeg ของ imageio ที่ไม่มี ffprobe → ได้ mp4 มีเสียง; ไม่ได้ → หยุดแล้วถามผู้ใช้ตาม spec ก่อนเขียนต่อ
- ลิงก์ live ที่ยังไม่เริ่ม และคลิปที่ YouTube ขอ login → ข้อความ error จริงตรงกับตารางแยก error ใน spec; ต่าง → แก้ตารางนั้นและบันทึก `D{n}`

### Setup และ Status check

- รัน `./setup.sh` บน Mac → ติดตั้ง `yt-dlp[default,deno]` ตาม `uv.lock` และ exit 0
- หลัง setup → หน้า Setup status มี 11 แถว, `yt_dlp` และ `deno` อยู่ต่อจาก `ffmpeg` เป็น `ok` พร้อมเวอร์ชัน
- deno probe raise → แถว `deno` เป็น `missing` และยังมี 11 แถว
- test ที่นับ 9 แถว → นับ 11

### Download job

- ลิงก์ทุกแบบในตารางลิงก์ของ spec → `202`; ลิงก์ Vimeo หรือ playlist → `400` `invalid_url`
- adapter ปลอมสำเร็จ → poll `GET /downloads/current` ได้ `checking`, `downloading` กับ `percent`, `merging` แล้ว `done` พร้อม `clip_id`
- งาน `done` → `media/temp/` มี `{id}.mp4`, thumbnail และ `{id}.json` ครบทุกฟิลด์ตาม spec › Temp clip
- ลิงก์ของ id ที่มี json แล้ว → `409` `duplicate` พร้อม `clip_id`
- POST ระหว่างงานยังไม่จบ → `409` `busy`
- POST สองครั้งพร้อมกันจากสอง thread → หนึ่ง `202` หนึ่ง `409` `busy`
- probe ตัวใดใน `yt_dlp`, `deno`, `ffmpeg` ไม่ผ่าน → `503` `not_ready`
- marker ของโมเดลหาย แต่ probe สามตัวผ่าน → `202`
- ขนาดประมาณไม่ได้ → `percent` เป็น `null`; ไม่เคยเกิน 100

### ยกเลิกและ error

- `DELETE /downloads/current` ระหว่าง `downloading` → `cancelled` และ `.partial/` ไม่มีไฟล์ของ id นั้น
- ยกเลิกระหว่าง `checking` → `cancelled` และไม่มีไฟล์
- `DELETE /downloads/current` ระหว่าง `merging` → `409` `merging` และงานจบเป็น `done`
- ไม่มีงานที่ยังไม่จบ แล้ว `DELETE /downloads/current` → `404` `not_found`
- `live_status` เป็น `is_live` → `failed` `live`
- ที่ว่างน้อยกว่าขนาดประมาณ + 1 GiB → `failed` `disk_full` และ adapter ไม่ถูกเรียกโหลด
- error ที่มี "Sign in to confirm" → `failed` `login_required`
- `GeoRestrictedError` → `failed` `unavailable`
- error อื่น → `failed` `youtube_error` พร้อม `yt_dlp_version` และ `fix`

### Start, shutdown และ Host

- start app ขณะ `.partial/` มีไฟล์ หรือมี `{id}.mp4` ที่ไม่มี json → ไฟล์เหล่านั้นหาย
- request ที่ `Host: evil.example` → `400`; test เดิมทุกตัวยังผ่านกับ host `127.0.0.1`
- `media/` อยู่ใน gitignore

### เช็คมือบน Mac

- โหลด Shorts หนึ่งคลิป → mp4 ด้านสั้น ≤ 1080 มีเสียง
- โหลดคลิปแนวนอนยาวกว่า 1 ชั่วโมง → mp4 1920×1080 หรือเล็กกว่า
- ยกเลิกที่ประมาณ 30% → หยุดภายใน 5 วินาที ไม่มีไฟล์ค้าง
- Ctrl+C ระหว่างโหลดแล้ว `npm run dev` ใหม่ → ไม่มี process ค้าง และ `.partial/` ว่าง
- README บอกที่เก็บ `media/temp/` และวิธีอัปเดต yt-dlp
