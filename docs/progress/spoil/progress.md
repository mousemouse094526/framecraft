# Progress: spoil

**Now:** 01–02 done; tab สปอยโหลดคลิปได้จริงผ่านหน้าเว็บ — ต่อไปคือรายการ Temp clip (03)

**Next:**

```
/warroom-build spoil 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง yt-dlp กับ Deno และ Download API | done |
| 02 | แถบ tab และโหลดคลิปใน tab สปอย | done |
| 03 | รายการ Temp clip | ready |
| 04 | เช็คบน Windows NVIDIA | ready |

## Log

### 02: แถบ tab และโหลดคลิปใน tab สปอย — done 2026-10-29

**Built:**
- แถบ tab "สปอย" กับ "Setup status" ด้านบนของทั้งสองหน้า (`components/ui/PageLayout`): hash ว่างหรือไม่รู้จักเปิด Setup status, กด tab เปลี่ยน hash, refresh กับปุ่ม back อยู่ tab ตาม hash (`lib/useHashTab`)
- tab สปอย (`features/spoil/`): ช่องลิงก์กับปุ่มโหลด, แถบ % (ไม่รู้ขนาด → แถบไม่มีตัวเลข), ยกเลิก (ซ่อนตอนรวมไฟล์), ข้อความหลังงานจบหรือถูกปฏิเสธพร้อมคำสั่ง `fix` และปุ่ม copy, not ready พร้อมลิงก์ไป Setup status, offline พร้อม Refresh, poll ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ
- `lib/api.sendJson` คืน `{status, body}` ให้ refusal เป็นคำตอบ ไม่ throw; type ของ `/api/setup/status` ย้ายไป `lib/statusTypes`, `OfflinePanel` และ `RefreshButton` ไป `components/ui/`
- เช็คมือผ่าน Vite proxy บน Mac: Shorts `-62C9R_41Sc` เห็น กำลังเช็คลิงก์… → 25% → 68% → "โหลดเสร็จ"; หนังยาว (ไม่รู้ขนาดตอนแรก) แถบไม่มีตัวเลข แล้วกดยกเลิก → "ยกเลิกแล้ว" และ `.partial/` ว่าง; ลิงก์ซ้ำ → "คลิปนี้โหลดไว้แล้ว"; หน้าตาตรง frame 2, 4, 6, 9, 13 และ Tab bar ทั้ง 375px และ desktop

**Decided:**
- D19 — ทางเลือกเล็ก: tab เป็นลิงก์ hash, `PageLayout` ร่วมพร้อม `h1` แบบ sr-only, `useCopy` และ `OUTLINE_BUTTON` ใช้ร่วม, tone ของข้อความ, code ที่ไม่รู้จัก = offline, ยกเลิกได้ 404 ไม่ทำอะไร, ปุ่ม "Copy" ภาษาอังกฤษตาม Figma, `<title>` เป็น "framecraft"

**For the next ticket:**
- 03: loading ของ tab สปอยต้องรอ `GET /clips` ด้วย (spec › Frontend) — ตอนนี้ `useSpoilDownload.load` รอแค่ status กับ current; งานจบ `done` ต้องโหลดรายการครั้งเดียวใน `afterPoll`
- 03: `409` `duplicate` แสดงข้อความแล้ว (`REFUSAL_NOTICES`) แต่ยังไม่ highlight แถว `clip_id` และไม่เลื่อนไปหา
- 03: ข้อความหลังงานจบตอนนี้อยู่ใต้แถบความคืบหน้า; รายการต้องอยู่ใต้ข้อความ (frame 6, 9)
- 03: test fake backend `backend()` ใน `SpoilPage.test.tsx` ตอบ route ซ้ำตามลำดับ — เพิ่ม route `/api/spoil/clips` ให้ทุก test เมื่อ loading รอรายการ
- ชื่อไฟล์ `lib/statusTypes.ts` ตาม spec แต่ไม่บอกว่าเป็น status ของอะไร — ถ้ามี status ชนิดอื่นเพิ่ม ให้เปลี่ยนเป็น `setupStatusTypes.ts`

**Checks:** `uv run pytest` — 82 passed; `npm --prefix frontend test` — 38 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

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
