# Progress: spoil

**Now:** 01–05 done บน Mac; ticket 06 (เช็คบน Windows) ย้ายไป `windows-check` 02 (setup-status D25) — เหลือ feature review

**Next:**

```
/warroom-build spoil --review-feature
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง yt-dlp กับ Deno และ Download API | done |
| 02 | แถบ tab และโหลดคลิปใน tab สปอย | done |
| 03 | รายการ Temp clip | done |
| 04 | Backend งานถอดบทพูดและ API | done |
| 05 | หน้าสองคอลัมน์และกล่องถอดบทพูด | done |

## Log

- 2026-10-30: ticket 06 ย้ายทั้ง ticket ไปเป็น `windows-check` 02 พร้อมข้อ Windows ใน For the next ticket ด้านล่าง (setup-status D25, ADR-0014)

### 05: หน้าสองคอลัมน์และกล่องถอดบทพูด — done 2026-10-29

**Built:**
- tab สปอยสองคอลัมน์ (≥ 1024px): ช่องลิงก์ แถบโหลด และรายการในคอลัมน์ซ้าย 520px, ลูกศร →, กล่องถอดบทพูด (`TranscriptPanel`) กินที่เหลือ; แคบกว่าเรียงบนลงล่างพร้อมลูกศร ↓. `PageLayout` มี `wide` (1120px)
- `useTranscribe`: คลิปที่เลือก, Transcript, Transcribe job; เปิด tab ขณะงานยังไม่จบ → เลือกคลิปนั้น (ไม่ autoPlay) และเห็น %; poll แยกจากงานโหลดผ่าน `usePollWhile` ที่ใช้ร่วมกัน; ผลของ `POST` ทุก code (`busy` ของคลิปนี้/คลิปอื่น, `404`, `503`, อื่น → offline); ข้อความหลังงานจบเป็น Alert ในกล่อง
- กล่อง: ทุก state ของตาราง spec (ยังไม่เลือก, not ready, เลือกแล้ว, กำลังเตรียมเสียง/กำลังถอด %/กำลังยกเลิก, คลิปอื่นกำลังถอด, ถอดแล้ว, ไม่พบคำพูด); บรรทัด `[hh:mm:ss]` กดแล้ว `currentTime` + เล่น; Copy เนื้อเดียวกับ `.txt`; ลิงก์ `.txt`/`.srt`. แถวมี badge "ถอดแล้ว"; ลบคลิปที่เลือก → กล่องว่าง; ลบคลิปที่กำลังถอด → `transcribing` ใต้แถวและความคืบหน้ายังอยู่
- ของร่วมใหม่: `ProgressCard` (component `Download progress` ของทั้งสองงาน), `NotReady`, `hooks/notice.ts`, `hooks/gate.ts`, `components/format.ts`, `PRIMARY_BUTTON`; icon ใหม่ arrow-right/down, clock, file-text จาก Figma
- เช็คมือบน Mac ผ่าน Vite proxy: หนังที่ถอดใน 04 → 883 บรรทัด, กด `[00:02:20]` แล้ว player ไป 141.9 วินาทีและเล่น; Copy แล้ว `pbpaste` ตรงกับ `/transcript.txt` ทุก byte (65145 bytes); `.txt` และ `.srt` ตอบ `200` พร้อม `Content-Disposition: attachment` (ไม่ได้กดโหลดไฟล์จริงใน browser); ถอด Shorts NASA 0:39 ใหม่ — กำลังเตรียมเสียง… → "ถอดเสร็จ" กับบรรทัดและ badge ถอดแล้ว ใน ~40 วินาที; ขนาดตรง Figma frame 15–17 (กล่อง 544px, player 284px, บรรทัดสูงสุด 320px) และ 375px ตรง frame 19 ไม่มี scroll แนวนอน

**Decided:**
- D34 — ทางเลือกเล็ก: คลิปที่เลือกอยู่กับ `useTranscribe`, status GET ครั้งเดียว และ `503` เช็คแค่ status, `busy` → GET current, ลบคลิปที่กำลังถอดไม่ปลด player, Transcript เดิมอยู่ถ้าถอดใหม่แล้วยกเลิก, ไม่ autoPlay เมื่อเลือกเพราะงาน, `404` ของ POST เป็น Alert ในกล่องว่าง, `PRIMARY_BUTTON` disabled 60

**For the next ticket:**
- 06: บน Windows เลือกคลิปที่กำลังเล่นแล้วกดลบ — player ในกล่องต้องปลดก่อน `DELETE` (D15) แล้วได้ลบสำเร็จหรือ `in_use`
- 06: ถอดหนังยาวบน `cuda` ผ่านหน้าเว็บ — % ควรขยับทุกช่วง 300 วินาที (บน Mac ไม่ได้ลอง % ของหนังยาวผ่านหน้าเว็บในรอบนี้ ใช้ test ครอบ)
- หลัง `done` กล่องมีสอง Alert ("ถอดเสร็จ" กับ "คลิปนี้ถอดแล้ว") จนเลือกคลิปใหม่ — ตาม spec แต่ถ้าผู้ใช้ว่ารก ให้ซ่อน "คลิปนี้ถอดแล้ว" ขณะมีข้อความ `done`
- เปิด tab ขณะงานยังไม่จบ กล่องขอ Transcript ของคลิปนั้นล่วงหน้า; คลิปที่ยังไม่เคยถอดได้ `404` ใน console ของ browser (ไม่มีผลกับหน้า)
- review ที่ไม่ได้แก้: `gate.ts`, `notice.ts` อยู่ใน `hooks/` ทั้งที่ไม่ใช่ hook (เหมือน `refusal.ts` เดิม); fake backend ใน test ตอบ route ทีละครั้งตามลำดับ อ่านยากเมื่อ route ซ้ำหลายตัว

**Checks:** `uv run pytest` — 165 passed; `npm --prefix frontend test` — 66 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 04: Backend งานถอดบทพูดและ API — done 2026-10-29

**Built:**
- API: `POST /api/spoil/transcriptions` (`202`, gate `torch`/`transformers`/`ffmpeg`/`model_whisper`/device ไม่ใช่ `cpu` → `503`, `404`, `409` `busy`), `GET`/`DELETE /transcriptions/current`, `GET /clips/{id}/transcript`, `.txt`, `.srt` (attachment); `GET /clips` มี `transcribed` และข้าม `*.transcript.json`; `DELETE /clips/{id}` ระหว่างถอดคลิปนั้น → `409` `transcribing` และลบ `{id}.transcript.json` พร้อมคลิป; start ล้าง `*.tmp`; ทุก `POST` ใต้ `/api` ที่ไม่ใช่ JSON → `415` (dependency ระดับ app)
- `backend.spoil.whisper`: `start_worker` (process ลูก `spawn`), `worker` แบ่งช่วงละ 300 วินาที อ่านเสียงด้วย ffmpeg ทีละช่วง ส่ง `Segment`/`WorkerError`/`Done`; `backend.spoil.transcribe`: thread ถือสถานะ, ยกเลิก = terminate (5 วินาทีแล้ว kill), ตายไม่ส่งผล = `crashed`, เขียน Transcript ผ่าน `.tmp`. ของร่วมใหม่ `backend.spoil.job_slot.JobSlot` ใช้ทั้ง `Downloads` และ `Transcriptions`; `checks.check_package`/`check_ffmpeg`/`check_device` เป็น public ให้ gate ใช้กฎเดียวกับ Status check
- ลองโมเดลจริงก่อนเขียน (spec › Library assumptions): `float16` บน `mps` ได้ขยะ → `float32` (D30); long-form 300 วินาทีไม่มี `chunk_length_s` ได้ครบช่วง; timestamp อยู่ในช่วง ยกเว้นเวลาจบเลยช่วงได้ (298.5 → 328.5) → ตัดที่จบช่วง; `language` เป็นชื่อ (`english`) → แปลงเป็น code; process ลูก `spawn` import `backend` ได้ใต้ uvicorn
- เช็คมือบน Mac ผ่าน `curl` กับ backend จริง: หนัง Night of the Living Dead 1:35 ชม. (`f7jkZXvaB4g`) ถอดจน `done` ใน 1284 วินาที (20 ช่วง), `language` `en`, 883 บรรทัด, ระหว่างนั้นโหลด Shorts อีกคลิปจน `done` และ RSS ของ backend อยู่ที่ 38–74 MB; Shorts ภาษาไทยของ TNN (`39qlIkfspBE`) ได้ `th`; ยกเลิกกลางหนัง → process ลูกหายใน 0.18 วินาที, RSS ไม่โต; `kill -9` process ลูกขณะโหลดอีกคลิป → งานถอด `crashed` (exit -9), งานโหลด `done`, POST ถัดไป `202`; `415` จาก `curl` และหน้าเว็บยังส่งโหลดได้ (ลิงก์ซ้ำได้ `409` `duplicate` ไม่ใช่ `415`); เวลาของบรรทัด: สุ่ม 5 บรรทัดแล้วถอดหน้าต่าง 30 วินาทีรอบบรรทัดนั้นใหม่ด้วย timestamp ระดับคำ (บน CPU) — คลาด 0.02, 0.64, 1.46, 2.50 วินาที และอีกบรรทัดตรวจไม่ได้ (รอบตรวจได้ยินคำต่างไป); ผู้ใช้ยอมรับ (D32)
- `.srt`: เครื่องนี้ไม่มี VLC — ผู้ใช้ตกลงให้ใช้ ffmpeg กับ libass (ตัววาด subtitle ตัวเดียวกับ VLC) วาด `.srt` ลงเฟรมแทน: Shorts ไทยวินาทีที่ 13 ขึ้น cue 4 (`00:00:12,700 --> 00:00:15,700`) ตรง
- Open Question 4 (รอยต่อช่วง): บนหนังทั้งเรื่อง 19 รอยต่อ ประโยคที่คร่อมรอยต่อถูกแบ่งเป็นสองบรรทัดติดกันที่ยังอ่านต่อกันรู้เรื่อง (เช่น 3299.08 "Here I have it. Drag your cup..." / 3300.00 "of those chairs together there's a socket…", 3598.98 "all we need to know we have" / 3600.00 "to try to get out of here…") ไม่มีคำหายหรือซ้ำที่เห็น → ไม่เพิ่ม overlap. ช่วงที่มีแต่ดนตรีได้บรรทัดแต่งเต็มหน้าต่าง 30 วินาที (600.00–629.98 "Oh, my God.", 5400.00–5429.98 "Let's go.") — เก็บไว้ตาม D31
- README บอกเรื่องถอดบทพูด, `{id}.transcript.json` และบรรทัดที่ Whisper แต่ง. library notes ใหม่: `transformers`, `torch`, `numpy`; `python` เพิ่ม `multiprocessing`. skill `fastapi-api` บันทึก process ลูก, `require_json`, `FakeWorker`

**Decided:**
- D30 — ทางเลือกเล็ก: `float32` บน `mps`, ชื่อภาษา → code, ตัดเวลาจบที่จบช่วง, gate ใช้ check ของ Status check, `415` ระดับ app, terminate → kill, message เป็น `NamedTuple`, `JobSlot`, Transcript อ่านไม่ได้ → `404`
- D31 — ไม่กรองบรรทัดที่ Whisper แต่งในช่วงไม่มีคำพูด ผู้ใช้ลบเอง (คำตอบของผู้ใช้)
- D32 — ยอมรับเวลาบรรทัดตาม Whisper long-form แม้บางบรรทัดคลาด 2–3 วินาที (คำตอบของผู้ใช้)

**For the next ticket:**
- 05: `GET /clips` มี `transcribed`; Transcript ที่ `/clips/{id}/transcript` เวลาเป็นวินาทีของคลิป (`start_s`) — ใช้ตั้ง `currentTime` ได้ตรง; ลิงก์ไฟล์ `/clips/{id}/transcript.txt` และ `.srt`; `language` เป็น code หรือ `null` ("ภาษา: ไม่ทราบ" ตาม D29)
- 05: job ของงานถอดไม่มี `percent` ระหว่าง `preparing` (โหลดโมเดล ~3–5 วินาที) → "กำลังเตรียมเสียง…"; หนังยาว 1 ช่วงใช้ ~60 วินาทีบน Mac จึง % ขยับทุก 5% ของหนัง 1:35 ชม.
- 06: `cuda` ใช้ `float16` ยังไม่เคยลอง — ถ้าได้ขยะแบบ `mps` ให้เปลี่ยนเป็น `float32` ใน `whisper.load`
- 06: Windows ส่ง `TerminateProcess` เมื่อยกเลิก — เช็คว่า process ลูกหายและ ffmpeg ที่มันเปิดอยู่ไม่ค้าง (terminate ไม่ฆ่าหลาน)
- review ที่ไม่ได้แก้: `(mp4, duration_s, snapshot_dir, device)` เดินทางด้วยกัน (Data Clump) — คงไว้เพราะ spec กำหนด signature ของ `worker`; `_missing_tools` ของงานโหลดและงานถอดยังเป็นรายการแยกกัน เพราะ spec ห้ามเรียก `run_checks` ทั้งชุด
- 24 จาก 883 บรรทัดของหนังมีเวลาจบห่างจากเริ่มไม่ถึง 0.3 วินาทีทั้งที่ประโยคยาว (เช่น 3773.88–3774.04) — `.srt` จะโชว์บรรทัดนั้นแวบเดียว; ถ้าผู้ใช้บ่นใน 05 ให้ขยายเวลาจบถึงบรรทัดถัดไป
- `return_timestamps="word"` บน `mps` ช้ามากจนไม่จบใน 10 นาทีสำหรับ 30 วินาที (เจอตอนเช็คเวลา) — ถ้าต้องการเวลาระดับคำในอนาคตต้องลองใหม่

**Checks:** `uv run pytest` — 165 passed; `npm --prefix frontend test` — 48 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 03: รายการ Temp clip — done 2026-10-29

**Built:**
- API: `GET /api/spoil/clips` (json ที่มี mp4 คู่ เรียงตามเวลาโหลดจริงใหม่สุดก่อน; json เสีย, ไม่มี mp4 หรือเวลาไม่มี offset → ข้าม), `/clips/{id}/video` ด้วย `FileResponse` (`Range` → `206`), `/clips/{id}/thumbnail`, `DELETE /clips/{id}` ลบ mp4 กับ thumbnail ก่อน json สุดท้าย, `PermissionError` → `409` `in_use`; id ผิดรูปแบบหรือไม่มี json → `404` `not_found`. `SpoilError` ย้ายไป `backend.spoil.errors`
- หน้าเว็บ (`TempClipList`, `useTempClips`): หัว "คลิปที่โหลดมา" กับจำนวน, แถวตาม Figma `Clip row` (thumbnail, ชื่อ, ช่อง · ความยาว, ขนาดภาพ ตั้ง/นอน · MB/GB · เวลาท้องถิ่น), state ว่าง, กดแถว → `<video controls>` เหนือรายการพร้อม badge "กำลังเล่น", ลบหลัง `confirm` (แถวที่เล่นอยู่ → ปลด player ก่อน `DELETE`), `in_use` → ข้อความใต้แถว. loading รอ `/clips` ด้วย, งานจบหรือหาย → โหลดรายการครั้งเดียว, `done` กับ `duplicate` → highlight แถวและเลื่อนไปหา, not ready ยังเห็นรายการ
- ของร่วมใหม่: `lib/useMountedState` (ใช้ทั้งสาม hook รวม `useSetupStatus`), `features/spoil/hooks/refusal.ts`
- เช็คมือบน Mac ผ่าน Vite proxy: Shorts `-62C9R_41Sc` 1080×1920 เล่นและ seek ไป 0:25 ได้; หนัง 1:35 ชม. 1920×1080 seek ไป 1:30:01 แล้วเล่นต่อ; วางลิงก์ `jNQXAC9IVRw` ซ้ำ → "คลิปนี้โหลดไว้แล้ว" กับแถว highlight; restart `npm run dev` → รายการ 3 คลิปเดิมอยู่ครบ; ขนาดตรง Figma (หัว 45px, แถว 87px, thumbnail 96×54, player 720×405) ทั้ง desktop และ 375px. README บอกเรื่อง tab สปอยและการลบ `media/temp/` ด้วยมือ

**Decided:**
- D20 — ทางเลือกเล็ก: คลิปมีอยู่ = มี json, ลบ json ที่ mp4 หาย, เรียงตามเวลาจริง, ลบได้ `404` = แถวหาย, highlight มาจากข้อความหลังงานจบ, `autoPlay`, ขนาดไฟล์ฐาน 1000, `useMountedState`, token `surface-strong` กับ `surface-inverse`

**For the next ticket:**
- 04: บน Windows ลองเล่นคลิปแล้วกดลบ — ต้องได้ลบสำเร็จ (player ถูกปลดก่อน) หรือ `in_use` ใต้แถวและแถวยังอยู่ (seam 2); ยังไม่เคยเห็น `PermissionError` จริงจาก Windows
- 04: thumbnail ที่ Windows ล็อกไว้ (เปิดใน `<img>`) ถูก log แล้วข้าม — เช็คว่าการล้างตอน start เก็บมันได้
- ไม่มีลบคลิปจริงบน Mac ในรอบนี้ (คลิปใน `media/temp/` เป็นของผู้ใช้) — test ครอบ `204` และ `in_use` แล้ว

**Checks:** `uv run pytest` — 106 passed; `npm --prefix frontend test` — 48 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

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
| 4 | 05 | design: layout สองคอลัมน์ | `/warroom spoil` พร้อมลิงก์ Figma frame | done (Figma 8013-281, D33) |
| 5 | 05 | design: กล่องถอดบทพูด | `/warroom spoil` พร้อมลิงก์ Figma frame | done (Figma 8013-281, D33) |
