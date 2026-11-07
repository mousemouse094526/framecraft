# Progress: spoil

**Now:** 08 โหลดหลายเว็บ done (2026-11-07); 09 พร้อม build, 10 รอแบบ Figma; ก่อนหน้า: merged — PR #7 (`899e9a1`) ตัดช่วง ticket 06–07; 01–05 merged (PR #2, `49ee6de`); เช็คบน Windows อยู่ที่ `windows-check` 02 (setup-status D25)

**Next:** `/warroom-build spoil 09`

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง yt-dlp กับ Deno และ Download API | done |
| 02 | แถบ tab และโหลดคลิปใน tab สปอย | done |
| 03 | รายการ Temp clip | done |
| 04 | Backend งานถอดบทพูดและ API | done |
| 05 | หน้าสองคอลัมน์และกล่องถอดบทพูด | done |
| 06 | Backend Trim job และ API | done |
| 07 | ส่วนตัดช่วงใน tab คลิป | done |
| 08 | โหลดคลิปจากหลายเว็บ | done |
| 09 | Backend เอาไฟล์ mp4 ในเครื่องเข้า | ready |
| 10 | ปุ่มเลือกไฟล์และลากไฟล์มาวางใน tab คลิป | ready |

## Log

### 08: โหลดคลิปจากหลายเว็บ — done 2026-11-07

**Built:**
- `links.parse`: ลิงก์ YouTube ตามตาราง (playlist และ host YouTube ที่ไม่มี id ยัง `invalid_url`) หรือ `http(s)` ของเว็บอื่นที่ host ไม่ใช่ localhost/`*.localhost`/loopback/private/link-local/unspecified และไม่ใช่ตัวเลขที่ไม่ใช่ IPv4 สี่ส่วน (`127.1`, `2130706433`, `0x7f000001`); `links.clip_id` (YouTube 11 ตัว, `{site}-{id}` คงตัวพิมพ์, แทนตัวนอก `A-Za-z0-9_-` แล้วต่อ sha1 8 ตัว, ตัดที่ 64); `CLIP_ID` ใน `check_known` (spoil_maker ใช้ผ่านตัวนี้) และการล้างตอน start ลบเฉพาะชื่อที่แอปสร้าง (`notes.txt` อยู่)
- Download job: id และเช็คซ้ำหลัง `fetch_info` (`failed` `duplicate` พร้อม `error.clip_id`), `playlist`, `unsupported`, `unsupported_format`, `download_error` (เดิม `youtube_error`), ข้อความ `login_required` ชี้ปุ่มเลือกไฟล์; `DownloadJob.id` เป็น `null` จนรู้; ขนาดภาพจากไฟล์ (หมุนแล้ว)
- adapter: `select_formats` (callable) h264 `yuv420p` ≤ 1080 + aac หรือ format รวม ใหญ่สุดก่อน, ทางสำรองคือ format ที่ไม่บอก codec; `allowed_extractors: ["default", "-generic"]`, `socket_timeout` 30, `outtmpl` จาก `clip_id`
- `backend/spoil/mp4check.py`: ตัวตรวจ mp4 เดียวที่ ticket 09 ใช้ซ้ำ (container mp4, h264 `yuv420p`, ข้าม `attached_pic`, rotation ±90, ด้านสั้น ≤ 1080, เสียงทุก track aac); `ffmpeg.describe` ใช้ร่วมกับ `probe`; `Downloads(check_mp4=…)`
- `TempClip`: `site` (json เดิม → `Youtube`), `source_url`/`yt_dlp_version` เป็น `null` ได้; thumbnail ที่นามสกุลไม่บอกชนิด (TikTok `.image`) ตอบ media type จาก byte แรก
- หน้าเว็บ: ป้าย "ลิงก์คลิป", placeholder "วางลิงก์คลิป (YouTube, Facebook, TikTok …)", รายการว่าง "ยังไม่มีคลิป วางลิงก์หรือเลือกไฟล์ด้านบน", ข้อความ `invalid_url`/`busy` ใหม่, งาน `failed` `duplicate` highlight แถว `error.clip_id`, แถวเว็บอื่น "{ช่อง} · {เว็บ} · {ความยาว}"
- test: `test_spoil_mp4_check.py` (stderr จริงของ ffmpeg 7.1 + ffmpeg จริงบน lavfi), seam 1 ของลิงก์ id selector (รวม YoutubeDL จริงรัน selector บน info ปลอม ไม่ใช้ network) ไฟล์ไม่ใช่ mp4 การล้างตอน start; คลิป `facebook-123` ถอด ตัด บรรยายฉาก เล่น ลบได้; seam 4 ข้อลิงก์และแถวชื่อเว็บ
- ลองก่อนเขียน: callable selector กับ YouTube จริง → combined format (240p) และ merge `312+258` ได้ mp4 h264 1920×1080 + aac
- เช็คมือบน Mac ผ่าน API (root ชั่วคราว ไม่แตะ `media/temp/` ของผู้ใช้): TikTok NASA → `tiktok-7679483952507276558` 720×1280 h264 ตั้ง (เลือก h264 720p แทน HEVC 1080p), ซ้ำ → `duplicate`; Facebook NASA Langley → 1920×1080 h264/aac 136 วินาที (ผ่าน `hd` ที่ไม่บอก codec); Facebook CNN และ NASA Perseverance → `unsupported_format` ("ภาพเป็น vp9") `.partial/` ว่าง; `example.com` และ Facebook ที่ไม่ใช่วิดีโอ → `unsupported`; YouTube "Me at the zoo" ยัง `done`. ข้อความจริงจดใน `docs/library-notes/yt-dlp.md`

**Decided:**
- D56 — "No suitable extractor" เป็น `unsupported`, คำ login ของเว็บอื่น, format ไม่บอก codec ให้ตัวตรวจไฟล์ตัดสิน, ไฟล์ไม่ใช่ mp4, ขนาดภาพจากไฟล์, thumbnail `.image`, host hex, ข้อความ API ตรงหน้าเว็บ

**For the next ticket:**
- ไม่เจอ TikTok ที่มีแต่ HEVC ให้ลองจริง; TikTok มี format `download` ที่บอก `h264` แต่ไม่บอกขนาด จึงอาจถูกเลือกและได้ผลหลังโหลดแทน "ก่อนโหลด" ของ seam 2 — selector ครอบด้วย test
- ไฟล์ของผู้ใช้ใน `media/temp/` ที่ชื่อมี `-` และไม่มี json ถูกลบตอน start (กฎของ D55); id คงตัวพิมพ์ (`BVabc`/`bvabc`) ชนกันบนดิสก์ที่ไม่สนตัวพิมพ์ของ Mac/Windows — feature review
- TikTok โพสต์เก่าได้ "Your IP address is blocked" จากไทย แม้มี `curl_cffi`; ไม่ได้เพิ่ม dependency
- review ที่ไม่ได้แก้: `site` เป็น string ที่มีค่าพิเศษ `Youtube`/`local` (frontend `YOUTUBE_SITE` ซ้ำกับ `links.YOUTUBE_KEY`); `links.py` ทั้งตรวจ host และสร้าง id; การ duplicate มีสองทาง (`409` และงาน `failed`) ตาม D51
- ticket 10: แถว `site` `local` ยังแสดง "local" จนกว่าจะทำ "ไฟล์ในเครื่อง"

**Checks:** `uv run pytest` — 760 passed; `npm --prefix frontend test` — 323 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### Feature review (ตัดช่วง) — done 2026-11-05

**Built:**
- review สามแกนบน ticket 06–07 (`ffaab9c..8456ee5`) แก้ทุกข้อที่ผู้ใช้เลือกใน `aacca74`
- backend: `ffmpeg_failed` แสดงบรรทัดท้ายของ stderr (`FfmpegFailed.last_line`); พื้น bitrate 300 kbps; `has_derived` เป็นคำถามเต็มด้วยคำของหน้าเว็บ; `GET /api/spoil/clips/{id}`; `clips.files_lock` แทน lock ของ Transcribe job; `TrimPlan`, ending และ `ErrorCode` มี type; `trimmed_clip_swap` แทน flag `trimming=True`
- bug: render ที่เสียงครบไม่จองช่อง GPU จึงไม่ถูกปฏิเสธระหว่างตัดคลิปนั้น และ Trim ไม่เห็น render — เพิ่ม `begin_render`/`end_render` ให้สองฝั่งได้ `clip_busy` (test แดงก่อนแก้ทั้งสองทาง)
- test: ffmpeg และ probe จริงบนคลิป lavfi ผ่าน API; `FakeFfmpeg` ใช้ `pause_at`/`wait_until`/`release` และ render ใช้ตัวเดียวกัน; `clip_busy` ผ่าน route จริงของ describe, draft pick, voice, render; deadlock test เริ่ม Draft pick จริง; probe ล้ม → `500`; shutdown ผ่าน lifespan
- frontend: ตัดคลิปส่ง `POST` ก่อนแล้วถาม `message` แบบงานถอดผ่าน `postConfirming` ตัวเดียว (`lib/confirm.ts`); Alert ของงานตัดหายเมื่อเลือกคลิปอื่น; เลือกคลิปของงานที่ค้างที่เดียวใน `ClipsPage`; ปลด player ทางเดียว (state + `flushSync`); `ClipsChanged` type เดียว; `allSettled` (`lib/settled.ts`) แทนเช็คห้า hook; Shot picker อ่าน `GET /clips/{id}`; ชื่อ `releasedClipId`, `IndexedRange`
- docs: spec ตามโค้ด (`busy` ก่อน `clip_busy`, ลูกศรขึ้น/ลง, marker ที่ไม่มี json, `TrimSection`); ลำดับ lock ใน `fastapi-api/SKILL.md`

**Decided:**
- D46 — สิ่งที่แก้จาก feature review ของงานตัดช่วง

**For the next ticket:**
- ไม่ได้แก้: `Trims.cancel`/`stop_on_shutdown` ไม่ย้ายไป `ModelJobSlot` — class นั้นถือว่ามี GPU kind และ child process ส่วน Trim ปฏิเสธยกเลิกใน `replacing` และ join thread ตอน shutdown
- ลบคลิปและ `PUT` การตัด EP ยังไม่เช็คเครื่องหมายของ render ระหว่างขั้น ffmpeg (มีมาก่อน feature นี้ ของ spoil-maker)
- เวลาตัดหนัง 2 ชั่วโมงยังเป็นค่าประมาณจากหนัง 69 นาที (~13 นาที) ไม่ได้วัดจริง
- test ของ spoil-maker สองตัว ("the failure's Alert stays…", "แทรกใต้ adds a sentence…") ล้มบางครั้งตอนเครื่องหนัก — ล้มบน HEAD เดิมด้วย; รันสามรอบหลังแก้ผ่านทั้งหมด

**Checks:** `uv run pytest` — 603 passed; `npm --prefix frontend test` — 266 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 07: ส่วนตัดช่วงใน tab คลิป — done 2026-11-05

**Built:**
- `TrimSection` และ `TrimTimeline` ในกล่องถอดบทพูดตาม Figma D44: ปุ่ม "ตัดช่วง", timeline ที่หัวลากเป็น `role="slider"` (เป้า 44px, ลูกศร ±1 วินาที, Shift ±10, ไม่ข้ามหัวอีกข้างหรือช่วงข้างเคียง, ลากด้วย pointer แล้วเห็นเวลา), รายการช่วงที่พิมพ์ `h:mm:ss.s`/`m:ss`/`ss` ได้ พร้อม "= ตอนนี้" และ ✕, "เพิ่มช่วง", "ตัดออก · เหลือ", "ตัดคลิป"/"ยกเลิก"; กำลังตัด (%), กำลังยกเลิก…, กำลังแทนไฟล์… (ไม่มียกเลิก), คลิปอื่นกำลังตัด
- `useTrim`: ช่วงเก็บใน memory แยกตามคลิป, `GET /trims/current` ตอนเปิด tab (งานยังไม่จบ → เลือกคลิปนั้น), poll ทุก 1 วินาที, `confirm()` จาก `transcribed`/`described`/`in_draft` แล้วจาก `derived` ของ `409 has_derived`, ปลด player ก่อนทุก `POST` และระหว่างงาน, error ของ `POST` เป็น Alert แล้วคืน player, Alert ผลหลังงานจบ
- `?v={trimmed_at ?? downloaded_at}` ใน `src` ของ player ทุกที่ (`videoUrl` ใน `lib/clips.ts`) รวม Shot picker ของ spoil-maker; Badge "ตัดแล้ว" ก่อน "ถอดแล้ว"; `409 trimming` ของลบคลิปและของถอดบทพูด
- ของร่วมใหม่: `SECONDARY_BUTTON`, `plus.svg` ย้ายไป `components/ui/assets/`; test ของ seam 4 ข้อตัดช่วงครบ (25 test ใหม่ใน `ClipsPage.test.tsx`, 1 ใน `ScriptReview.test.tsx`)
- bug ที่เจอตอนเช็คมือ: ความยาวคลิป 893.178 วินาทีปัดเป็น 0.1 ได้ 893.2 เกินไฟล์ → backend จะตอบ `invalid_ranges`; แก้ให้ปัดลง (test แดงก่อนแก้). bug จาก review: หลังงาน `done` player โหลด `?v=` เดิมก่อนรายการใหม่มา (ไฟล์เก่าจาก cache) และลบคลิปที่กำลังตัดขณะคลิปอื่นถอดอยู่ทำให้กล่องว่าง (test แดงก่อนแก้ทั้งสอง)
- เช็คมือบน Mac ผ่าน Vite proxy (backend :8010 บน root ชั่วคราวที่สำเนาสองคลิป ไม่แตะ `media/temp/` ของผู้ใช้): โคนัน 14:53 ที่ถอดและบรรยายฉากแล้ว ตัด 0:00–0:30 และ 14:23.1–14:53.1 → คำยืนยัน "ตัดคลิปจะลบ Transcript (รวมบรรทัดที่แก้ไว้), ภาพฉากและการตัด EP ของคลิปนี้ ตัดต่อไหม?", % เดิน 0→99 ใน 122 วินาที, "ตัดคลิปเสร็จ", player เล่นไฟล์ใหม่ 833.18 วินาทีที่ฉากแรกหลังโฆษณา, แถวมี "ตัดแล้ว" ไม่มี "ถอดแล้ว"/"บรรยายฉากแล้ว"; โทริโกะ 23:03 ตัดแล้วกดยกเลิกที่ 2% → "ยกเลิกแล้ว" ใน 0.4 วินาที, ช่วงยังอยู่, player เล่นไฟล์เดิม (readyState 4), Transcript ยังอยู่, `.partial/` ว่าง ไม่มี ffmpeg ค้าง; 375px หัวลาก 44×44 ไม่มี scroll แนวนอน, ลากหัวจบด้วย pointer และกด track แล้ว seek ได้; หน้าตาตรง frame desktop และ mobile

**Decided:**
- D45 — ความยาวจาก `video.duration` ปัดลง 0.1 วินาที, ช่วง < 0.5 วินาทีเป็น error, `busy` ติดตามงาน, player ว่างจนรายการใหม่มา, `?v=` ของ Shot picker, `SECONDARY_BUTTON`

**For the next ticket:**
- feature review: ไฟล์คลิป bitrate ต่ำโตขึ้นหลังตัด (โคนัน 100.1 → 125.4 MB ทั้งที่สั้นลง 1 นาที) ตามพื้น `MIN_VIDEO_BPS` ของ D41 — ข้อเดิมจาก 06
- review ที่ไม่ได้แก้: การเช็ค offline/loading ของห้า hook ใน `ClipsPage` เขียนทีละตัว (loop ทำให้ TypeScript ไม่ narrow state); `startTrim` กับ `startTranscribe` ถามยืนยันแล้วส่งซ้ำคล้ายกันแต่รูปต่าง; Shot picker อ่าน `/api/spoil/clips` ทั้งรายการเพื่อใช้ `trimmed_at` คลิปเดียว
- ตอนเช็คมือไม่เห็น state "กำลังแทนไฟล์…" กับ "กำลังยกเลิก…" ในหน้าจริง (สั้นกว่า poll) — test ครอบไว้
- backend เก่าที่เปิดค้างบน :8000 (เริ่ม 2026-11-04 18:44) ยังเป็นโค้ดก่อน 06 — เปิด `npm run dev` ใหม่ก่อนลองตัดจริง

**Checks:** `uv run pytest` — 594 passed; `npm --prefix frontend test` — 265 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 06: Backend Trim job และ API — done 2026-11-05

**Built:**
- `backend/spoil/trim.py`: `POST /api/spoil/trims`, `GET`/`DELETE /trims/current`; ตรวจตามลำดับ spec › Trim ข้อ 1 (gate ffmpeg, รูปร่าง body, `404`, ความยาวจริงจาก `probe`, `invalid_ranges`, `transcribing`, `busy`, `clip_busy`, `has_derived` พร้อม `derived`) แล้ว encode ช่วงที่เหลือเข้า `.partial/`, ตรวจความยาวกับเสียงของไฟล์ผล, เขียน marker `{id}.trimming.json`, แทน mp4 (ลองซ้ำ 0.5 วินาที × 20 โดยไม่ถือ lock ระหว่างรอ), ลบ Transcript, Shot, การตัด EP แล้ว Spoil draft นอก lock ของ slot; argv, การรวมช่วงและสูตร bitrate เป็น pure function
- `gpu.slot.begin_trim`/`end_trim`: `take()` ทุกชนิดและ `clip_untouched` ไม่ว่า `by` ได้ `clip_busy` ของคลิปที่กำลังตัด; Transcribe start, แก้บรรทัด และลบคลิปได้ `409` `trimming`; start ใหม่อ่าน marker แล้วทำต่อหรือย้อน (`recover_on_start` ก่อนล้าง `.partial/`); shutdown ระหว่าง `replacing` รอให้แทนเสร็จ
- `TempClip` มี `trimmed` และ `trimmed_at` (json เก่าอ่านเป็น `[]`/`null`); `list_clips` ข้าม marker
- prefactor: `spoil_maker/ffmpeg.py` → `backend/ffmpeg.py` พร้อม `run`/`Runner` ที่ย้ายจาก `compose` (render ใช้ตัวเดียวกัน)
- bug ที่ test เจอ: `begin_trim` ถือ lock ของ slot ซ้ำใน `clip_untouched` → ค้าง; `.partial/` ไม่ถูกสร้างก่อน ffmpeg เขียน
- เช็คจริงบน Mac (seam 3a, สำเนาคลิปใน root ชั่วคราว): หนัง 69:10 ตัดสองช่วง → 64:20 ภาพ 3860.13 วินาที เสียง 3860.21 วินาที, encode 450 วินาที (`h264_videotoolbox`; หนัง 2 ชั่วโมงประมาณ 13 นาที), ขนาดต่อนาที 1.08 เท่า; คลิป 14:53 ที่ถอดแล้ว → `has_derived` แล้ว confirm → `done` 109 วินาที, ความยาวต่าง 0.04 วินาที, `transcribed: false` และ `trimmed` สองช่วง; ยกเลิกที่ 30% → `cancelled` 0.5 วินาที ไม่มี ffmpeg ค้าง Transcript อยู่ครบ; คลิปไม่มีเสียง → `done`; ถอดใหม่ → ไม่มีบรรทัดของช่วงที่ตัด; บรรยายฉาก → Shot 10 เริ่ม 60.03 และ Shot 105 เริ่ม 540.37 ตรงรอยตัด

**Decided:**
- D43 — ตัวปลอมของ test ผ่าน `Trims(…)` ตาม `rules/testing.md`, ffmpeg ขึ้นเป็น `backend/ffmpeg.py`, ลอง `os.replace` ซ้ำโดยไม่ถือ lock

**For the next ticket:**
- 07: `POST` ซ้ำขณะตัดคลิปเดียวกันได้ `busy` (ไม่ใช่ `clip_busy`); `GET /trims/current` มี `kept_s` ให้หน้าเว็บแสดง
- คลิป bitrate ต่ำกว่า 1 Mbps (คลิป 14:53 ที่ 0.9 Mbps) ได้ไฟล์ต่อนาที 1.34 เท่าเพราะพื้น `MIN_VIDEO_BPS` (D41); หนังยาวกว่า 1 ชั่วโมงตาม seam 3a ได้ 1.08 เท่า — ถ้าผู้ใช้ว่าไฟล์โตเกิน ให้ใช้ bitrate เดิมเมื่อต่ำกว่าพื้น
- review ที่ไม่ได้แก้: Describe job ระหว่างตัดทดสอบที่ `gpu.slot.take` ไม่ผ่าน `POST /describes` (gate ของ Qwen หนัก) — ทุก GPU job เริ่มผ่าน `take`; `clip_untouched(trimming=True)` เป็น flag argument; `(project, clip, mp4, media, cut, spans)` ส่งต่อกันสามชั้น
- ข้อ Windows ของ seam 3a อยู่ใน `windows-check` 02 แล้ว

**Checks:** `uv run pytest` — 594 passed; `npm --prefix frontend test` — 239 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### Feature review — done 2026-10-30

**Built:**
- review สามแกนบนโค้ดทั้ง feature (aee14b7..31fb79c ซึ่งอยู่บน `develop` แล้ว) แก้ทุกข้อที่ผู้ใช้เลือกใน `24c6c9b` บน `feat/spoil`
- bug: งานถอดได้ `503` และ status ใหม่ขาดแถวที่งานโหลดใช้ → งานโหลดที่ยังวิ่งถูกทิ้งและหยุด poll ทั้งที่ backend ยังโหลด; ตอนนี้ยังติดตามต่อ (test ใหม่ แดงก่อนแก้)
- backend: gate สองงานผ่าน `require_rows`, `JobFailed` ตัวเดียว, `write_atomic` ตัวเดียว, `jobs.py` → `downloads.py`, `DownloadJobError`/`TranscribeJobError`, `WorkerError.code` เป็น `Literal`
- frontend: `gate.ts`/`notice.ts`/`refusal.ts` ไป `features/spoil/lib/`, ของร่วมของสอง hook ใน `lib/job.ts`, `getReply`
- comment และ test ชัดขึ้น (`Segment`, device probe, ลำดับ gate, test สองช่วง); กฎ test ให้นับ `<video>` ทั้งหน้าได้เพื่อพิสูจน์ว่าไม่มีตัวอื่น
- เช็คจริงบน Mac: gate สองงานกับ probe จริงผ่าน; tab สปอยผ่าน Vite โหลด module ใหม่และแสดงรายการ 5 คลิป

**Decided:**
- D35 — สิ่งที่แก้จาก feature review

**For the next ticket:**
- ทิ้งตามที่ผู้ใช้เลือก: `.txt` สร้างสองที่ (backend `to_txt` กับ Copy ของหน้าเว็บ), state ของหน้าเป็น union เดียว, `deno` ใช้สองโมดูล, `ProjectPaths(paths.ROOT)` สร้างหลายที่, ลบคลิปผ่าน `transcriptions.delete_clip`, สอง Alert หลัง `done`, `404` ใน console, fake backend ใน test ตอบตามลำดับ, cue `.srt` สั้น, ชื่อ `statusTypes.ts`, test ชน POST พิสูจน์ lock ไม่ได้
- `npm run dev` ที่เปิดค้างอยู่ใช้ backend เก่าจนกว่าจะเปิดใหม่ (`jobs.py` เปลี่ยนชื่อ)

**Checks:** `uv run pytest` — 169 passed; `npm --prefix frontend test` — 68 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

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
| 6 | 07 | design: ส่วนตัดช่วง | `/warroom spoil` พร้อมลิงก์ Figma frame (ทำจาก `docs/features/spoil/ui-prompt.md`) | done ([Figma 8094-49867](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8094-49867), D44) |
| 7 | 10 | design: tab คลิป — ช่องลิงก์และการเลือกไฟล์ | `/warroom spoil` พร้อมลิงก์ Figma frame (จาก `docs/features/spoil/ui-prompt.md`) | open |
