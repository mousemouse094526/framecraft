# Progress: spoil

**Now:** 01 done; design ของทั้งสามจออยู่ใน Figma แล้ว (Blocked #1–3 done, D18) — 02 เริ่มได้

**Next:**

```
/warroom-build spoil 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง yt-dlp กับ Deno และ Download API | done |
| 02 | แถบ tab และโหลดคลิปใน tab สปอย | ready |
| 03 | รายการ Temp clip | ready |
| 04 | เช็คบน Windows NVIDIA | ready |

## Log

### 01: ติดตั้ง yt-dlp กับ Deno และ Download API — done 2026-10-29

**Built:**
- `./setup.sh` ติดตั้ง `yt-dlp[default,deno]` ตาม `uv.lock` (yt-dlp 2026.10.26, Deno 2.9.8) และ Status check มี 11 แถว: `yt_dlp` กับ `deno` ต่อจาก `ffmpeg`
- `POST /api/spoil/downloads` รับลิงก์ YouTube แล้วโหลดเบื้องหลังเป็น Temp clip ใน `media/temp/` (`{id}.mp4`, thumbnail, `{id}.json`); poll `GET /downloads/current` เห็น `checking` → `downloading` กับ % → `merging` → `done`; `DELETE /downloads/current` ยกเลิกได้จนก่อนรวมไฟล์; error แยกเป็น `live`, `disk_full`, `unavailable`, `login_required`, `youtube_error`
- backend start ล้างไฟล์ค้าง, รับเฉพาะ Host ที่เป็น localhost (ADR 0011). เช็คมือบน Mac กับ YouTube จริงผ่าน: Shorts ได้ 1080×1920 มีเสียง, หนัง 1:35 ชม. ได้ 1920×1080, ยกเลิกที่ 31% หยุดใน 0.34 วินาทีไม่มีไฟล์ค้าง, Ctrl+C ระหว่างโหลดไม่มี process ค้างและ `.partial/` ว่างหลังเปิดใหม่, live / live ที่ยังไม่เริ่ม / คลิปจำกัดอายุ ได้ `live`, `live`, `login_required`

**Decided:**
- D16 — ตารางแยก error ตามข้อความจริงจาก YouTube: live ที่ยังไม่เริ่มดูจาก "This live event will begin", ไม่ใช้คำ "age" เดี่ยวๆ (แก้ spec › Download แล้ว)
- D17 — ทางเลือกเล็ก: gate กับ Status check ใช้ probe ตัวเดียวกันใน `backend.checks`, adapter รับ `ProjectPaths`, ตัดช่องว่างลิงก์ก่อนส่ง yt-dlp, ลบไฟล์ค้างแบบ best effort, percent ไม่ถอย, `backend.disk.free_bytes` ใช้ร่วมกับ setup

**For the next ticket:**
- 02: error body ของทุก route เป็น `{"code", "message"}` (+ `clip_id` ของ `duplicate`); `message` ภาษาไทยพร้อมแสดง. Download job ตาม spec › API; `GET /downloads/current` คืน `null` ก่อนมีงานแรก
- 02: `SetupStatusPage.test.tsx` ใช้ fixture 11 แถวแล้ว (มี `yt_dlp`, `deno`) — tab สปอยอ่าน label ของสามแถวนี้ได้เลย
- 03: `backend/spoil/clips.py` มี `TempClip`, `has_clip`, `json_path`, `find_thumbnail` แล้ว — route `/clips` ใช้ต่อ; ลบตามลำดับ mp4 และ thumbnail ก่อน json (spec › Temp clip)
- test ชน POST สองครั้งพร้อมกันผ่านแทบทุกครั้งแม้ไม่มี lock เพราะช่วงชนสั้น — พิสูจน์ lock ไม่ได้จริง; ถ้าจะให้แน่นต้องมีจุดหยุดใน `Downloads.start`
- ลิงก์ live ที่ยังไม่เริ่มใช้ข้อความภาษาอังกฤษของ YouTube; yt-dlp ขอ `hl=en` อยู่แล้ว แต่ถ้าวันหนึ่ง YouTube เปลี่ยนข้อความ จะตกไป `youtube_error`

**Checks:** `uv run pytest` — 82 passed; `npm --prefix frontend test` — 12 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 02 | design: แถบ tab | `/warroom spoil` พร้อมลิงก์ Figma frame | done (Figma 8013-281) |
| 2 | 02 | design: tab สปอย | `/warroom spoil` พร้อมลิงก์ Figma frame | done (Figma 8013-281) |
| 3 | 03 | design: หน้าต่างรายการ Temp clip | `/warroom spoil` พร้อมลิงก์ Figma frame | done (Figma 8013-281) |
