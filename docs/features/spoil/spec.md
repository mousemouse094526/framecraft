# Spec: spoil

ผู้ใช้วางลิงก์ YouTube ใน tab สปอย แล้วแอปโหลดคลิปมาเก็บเป็น Temp clip พร้อมหน้าต่างบอกว่าโหลดอะไรมา. จากนั้นเลือกคลิปเข้ากล่องถอดบทพูด แล้วกดให้ Whisper ถอดคำพูดเป็น Transcript ที่อ่าน คัดลอก และโหลดเป็นไฟล์ได้.

**Status:** ready-to-build

## Problem

ผู้ใช้ทำคลิปสปอยหนังจากคลิปบน YouTube แต่ framecraft ยังไม่มีทางเอาคลิปต้นทางเข้ามาในแอป. ต้องโหลดด้วยเครื่องมืออื่นแล้วจัดไฟล์เอง.

## Solution

- tab ด้านบนของแอปสลับระหว่าง สปอย กับ Setup status (D10)
- วางลิงก์ YouTube คลิปเดียว แล้วโหลดคลิปทุกแนวที่ด้านสั้นไม่เกิน 1080 px เป็น mp4 (D5)
- เห็น % ระหว่างโหลด และกดยกเลิกได้ (D6)
- เห็นรายการ Temp clip ที่โหลดมา เล่นดูในหน้าเว็บ และกดลบได้ (D3, D7)
- Setup script ติดตั้ง yt-dlp กับ Deno และ Status check บอกว่าติดตั้งครบไหม (D1, D8, D9)
- เลือก Temp clip เข้ากล่องถอดบทพูดทางขวาของรายการ มีลูกศรคั่นกลาง (D25)
- กดถอด → Whisper large-v3-turbo ถอดคำพูดทุกภาษาเป็น Transcript พร้อมเวลา เห็น % และยกเลิกได้ (D21, D24, D26)
- Transcript เก็บคู่คลิป แถวแสดง "ถอดแล้ว", Copy ทั้งหมด, โหลด `.txt` และ `.srt` (D22, D23)

## User Stories

**ผู้ทำคลิปสปอย**
1. As a ผู้ทำคลิปสปอย, I want สลับ tab สปอยกับ Setup status ได้จากด้านบน, so that ใช้งานและเช็คการติดตั้งในแอปเดียว (D10)
2. As a ผู้ทำคลิปสปอย, I want วางลิงก์ YouTube แล้วกดโหลด, so that คลิปต้นทางมาอยู่ในเครื่องพร้อมทำต่อ (D2, D5)
3. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างโหลดและยกเลิกได้, so that รู้ว่าคลิปยาวยังเดินอยู่ และหยุดเมื่อวางลิงก์ผิด (D6)
4. As a ผู้ทำคลิปสปอย, I want เห็นรายการคลิปที่โหลดมาและเล่นดูได้, so that เช็คว่าได้คลิปถูกตัว (D7)
5. As a ผู้ทำคลิปสปอย, I want ลบคลิปที่ไม่ใช้, so that ดิสก์ไม่เต็ม (D3)
6. As a ผู้ทำคลิปสปอย, I want รู้ทันทีเมื่อวางลิงก์ที่โหลดไปแล้ว, so that ไม่โหลดซ้ำ (D12)
7. As a ผู้ทำคลิปสปอย, I want รู้ว่าทำไมโหลดไม่ได้และต้องแก้ยังไง, so that แก้เองได้ (D8, D11)
8. As a ผู้ทำคลิปสปอย, I want เลือกคลิปแล้วกดถอดบทพูด, so that ได้คำพูดทั้งเรื่องไปวิเคราะห์เขียนบทสปอย (D21, D23, D25)
9. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างถอดและยกเลิกได้ ระหว่างที่โหลดคลิปอื่นอยู่ก็ได้, so that รู้ว่าหนังยาวยังเดิน และไม่ต้องรอกัน (D24, D26)
10. As a ผู้ทำคลิปสปอย, I want อ่าน Transcript พร้อมเวลา กดบรรทัดแล้วกระโดดไปฉากนั้น, Copy และโหลด `.txt`/`.srt`, so that เอาไปใช้ที่อื่นได้ทันที (D22)
11. As a ผู้ทำคลิปสปอย, I want เห็นว่าคลิปไหนถอดแล้ว และเปิดแอปใหม่ก็ยังอยู่, so that ไม่ต้องถอดซ้ำ (D23)

## Design

| Screen | User stories | Must show | Source |
|---|---|---|---|
| แถบ tab | 1 | tab "สปอย" และ "Setup status" ตามลำดับนี้, tab ที่เปิดอยู่เด่นกว่า (D10) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frame "Tab bar / Setup status active" และ header ของทุก frame สปอย; component `Tab` |
| tab สปอย | 2, 3, 6, 7 | ช่องลิงก์กับปุ่ม "โหลด"; ระหว่างโหลด: ชื่อคลิปเมื่อรู้แล้ว, แถบ % (ไม่รู้ขนาด → แถบไม่มีตัวเลข), ปุ่ม "ยกเลิก" (ซ่อนตอนรวมไฟล์), ปุ่มโหลด disabled (D6, D15); ข้อความ error ตาราง Frontend รวมเวอร์ชัน yt-dlp และคำสั่งอัปเดต (D8); ลิงก์ซ้ำ → highlight แถวเดิม (D12); ติดตั้งไม่ครบ → ข้อความกับลิงก์ไป Setup status แทนช่องลิงก์ (D9, D10); backend offline → ข้อความเดียวกับหน้า Setup status (setup-status D21) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 1 loading, 2–3 idle, 4 downloading, 5 progress states, 6 done, 7 failed with fix, 8 messages, 9 duplicate, 11 not ready, 12 offline, 13 mobile 375px; component `Download progress` |
| หน้าต่างรายการ Temp clip | 4, 5 | ใน tab สปอยใต้ช่องลิงก์; แถวใหม่สุดก่อน: thumbnail, ชื่อคลิป, ชื่อช่อง, ความยาว, ขนาดภาพกับแนว "ตั้ง" หรือ "นอน", ขนาดไฟล์, เวลาโหลด, ปุ่มลบพร้อมยืนยัน และ error เมื่อลบไม่ได้ (D7, D15); กดแถว → player เล่นคลิปนั้น (D7); state ว่าง: "ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน" | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 2 empty, 3 list, 6 and 9 highlight, 10 playing and delete error; component `Clip row` (D18) |
| layout สองคอลัมน์ | 8 | จอกว้าง: รายการคลิปซ้าย, ลูกศร → กลาง, กล่องถอดบทพูดขวา; 375px เรียงบนลงล่างพร้อมลูกศร ↓ (D25); แถวที่เลือกเด่นกว่า; แถวที่ถอดแล้วมีสถานะ "ถอดแล้ว" (D23); ช่องลิงก์กับแถบโหลดอยู่คอลัมน์ซ้ายเหนือรายการ (D33) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — frames: 14 nothing selected, 15 selected, 16 transcribing while downloading, 17 transcribed, 19 mobile 375 stacked; component `Clip row` (property `Show transcribed`), icon `icon/arrow-right`, `icon/arrow-down` |
| กล่องถอดบทพูด | 8–11 | ยังไม่เลือก: "เลือกคลิปจากรายการ"; เลือกแล้ว: player, ชื่อคลิป, ความยาว, ปุ่ม "ถอดบทพูด" (ถอดแล้ว → "ถอดใหม่" พร้อม alert "คลิปนี้ถอดแล้ว"); ระหว่างถอด: "กำลังเตรียมเสียง…" หรือ "กำลังถอด {n}%" กับแถบ % และปุ่ม "ยกเลิก"; Transcript: บรรทัด `[hh:mm:ss] ข้อความ` กดได้, ภาษาที่ตรวจได้, ปุ่ม Copy, `.txt`, `.srt`; ว่าง: "ไม่พบคำพูดในคลิปนี้"; error ของงานถอด; ติดตั้งไม่ครบ: ข้อความกับลิงก์ไป Setup status แทนปุ่มถอด (D22–D27); ข้อความหลังงานจบเป็น Alert ในกล่อง (D33) | [Figma: framecraft — สปอย](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8013-281) — component `Transcript panel` (ทุก state), `Transcript line`, `Player`; frames: 14–17, 18 messages, 19 mobile |

ออกแบบใน Figma หลัง plan (setup-status D9) ในไฟล์เดียวกับหน้า Setup status. Section "framecraft — สปอย" มี component `Tab`, `Clip row`, `Download progress` และ frame ทุก state; ใช้ token และ component ของหน้า `:: Token` (Button, Field, Alert, Badge, icon).

## Expected Outcome

ผู้ใช้เอาคลิป YouTube เข้า framecraft ได้ในแอปเดียว โดยไม่ต้องใช้เครื่องมือโหลดอื่น.

- **วางลิงก์คลิปแนวตั้ง:** เห็น % เดินจนครบ แล้วคลิปขึ้นบนสุดของรายการ ขนาดภาพเป็นขนาดใหญ่สุดของต้นทางที่ด้านสั้นไม่เกิน 1080 (เช่น "1080×1920 ตั้ง" หรือ "720×1280 ตั้ง") (D5)
- **วางลิงก์หนังแนวนอนยาว 2 ชั่วโมง:** โหลดได้ ได้แถว "นอน" ที่ด้านสั้นไม่เกิน 1080
- **วางลิงก์ซ้ำ:** ไม่โหลด แถวเดิมถูก highlight
- **กดยกเลิกกลางทาง:** งานหยุด ไม่มีแถวใหม่ ไม่มีไฟล์ค้างใน `media/temp/.partial/`
- **เลือกหนังภาษาอังกฤษ 1:35 ชม. แล้วกดถอด:** % เดินจนครบ เห็น Transcript ทีละบรรทัดพร้อมเวลา ภาษา "en"; กดบรรทัดแล้ว player กระโดดไปเวลานั้น; แถวในรายการขึ้น "ถอดแล้ว" (D22, D23)
- **ถอดระหว่างโหลดคลิปอื่น:** ทั้งสองงานเดินไปพร้อมกันจนจบ (D24)
- **ลบคลิปที่ถอดแล้ว:** `{id}.transcript.json` หายพร้อมคลิป (D23)

**How success is judged:**
- บน Mac หลังรัน `./setup.sh`: หน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด YouTube Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิปได้จริง แต่ละไฟล์เล่นได้ใน player ของหน้าเว็บ
- ไฟล์ที่ได้เป็น mp4 และด้านสั้นไม่เกิน 1080 px
- restart `npm run dev` แล้วรายการเดิมยังอยู่ครบ
- ถอด Shorts ภาษาไทยหนึ่งคลิปและหนังแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิปได้จริง; Copy แล้ววางได้ข้อความครบ; `.srt` เปิดใน VLC แล้ว subtitle ตรงเวลา; restart `npm run dev` แล้วยังเห็น Transcript
- ยกเลิกงานถอดแล้ว process ลูกหยุดภายใน 5 วินาที และ Transcript เดิม (ถ้ามี) ยังอยู่
- ทำซ้ำข้อบนทั้งหมดบน Windows NVIDIA หลังรัน `setup.cmd` — เช็คใน `windows-check` 02 ไม่ขวางการจบ feature (ADR-0014)

## Implementation

### Modules touched

- **root**
  - `pyproject.toml` กับ `uv.lock`: เพิ่ม `yt-dlp[default,deno]` (extra `deno` ดึง package `deno` มาด้วย) (D8)
  - `.gitignore`: เพิ่ม `media/` (D14)
  - `README.md`: tab สปอย, ที่เก็บ `media/temp/` และวิธีอัปเดต yt-dlp (D3, D8)
- **backend**
  - `backend.paths`: เพิ่ม `media_temp_dir` = `{root}/media/temp` และ `partial_dir` = `{root}/media/temp/.partial` (D3, D14)
  - `backend.checks`: เพิ่มแถว `yt_dlp` และ `deno` (D9)
  - `backend.spoil` (package ใหม่): ตรวจลิงก์, Download job, คลังของ Temp clip และ adapter ที่คุยกับ yt-dlp ตัวเดียว (D6, D14)
  - `backend.routes.spoil`: route ใน ตาราง API (D6, D7)
  - `backend.app`: include router ของ spoil, lifespan ที่ล้างไฟล์ค้างตอน start และตั้ง flag ยกเลิกตอน shutdown, `TrustedHostMiddleware` (D14, D15); ตั้ง flag ยกเลิกของ Transcribe job ตอน shutdown ด้วย
  - `backend.spoil.transcribe` (ใหม่): Transcribe job, ไฟล์ Transcript, `.txt` และ `.srt` (D23, D24, D27)
  - `backend.spoil.whisper` (ใหม่): adapter ตัวเดียวที่ import `transformers` และ `torch` สำหรับถอด, เรียก ffmpeg ดึงเสียง และ `worker` ที่รันใน process ลูก (D27, D28)
  - `backend.routes.spoil`: `POST` ต้อง `Content-Type: application/json` (D29)
  - `backend.spoil.clips`: ลบ `{id}.transcript.json` พร้อมคลิป, field `transcribed` ในรายการ, `409` `transcribing` (D23, D27)
- **frontend**
  - `App`: แถบ tab; hook `useHashTab` ใน `lib/` อ่านและเขียน hash. ไม่มี folder `routes/` เพราะไม่ใช้ router (D10). บันทึกเรื่องนี้ใน skill `vite-react-web`
  - `features/spoil/` (folder ใหม่): ช่องลิงก์, แถบความคืบหน้า, รายการ Temp clip และ player (D6, D7); layout สองคอลัมน์และกล่องถอดบทพูด `TranscriptPanel` กับ hook `useTranscribe` (D22, D25). player ย้ายจากเหนือรายการเข้ากล่อง
  - `lib/api`: เพิ่ม `sendJson<T>(method, path, body?)` คืน `{ status, body }` ที่ body เป็น JSON หรือ `null` เมื่อไม่มี body; throw เฉพาะ network ล้มหรือเกิน 30 วินาที. timeout เดียวกับ `getJson`
  - `components/ui/`: ย้าย `OfflinePanel` จาก `features/setup-status` มาที่นี่ เพราะ tab สปอยใช้ด้วย
  - `lib/statusTypes`: ย้าย type ของ `/api/setup/status` ออกจาก `features/setup-status` เพราะ tab สปอยอ่านด้วย

### Dependencies

| Package | Version | ใช้ทำอะไร |
|---|---|---|
| `yt-dlp[default,deno]` | latest ตอน lock แล้ว pin ใน `uv.lock` | โหลดคลิป YouTube; extra `default` มี `yt-dlp-ejs`, extra `deno` มี package `deno` ที่เป็น JavaScript runtime (D8) |

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| yt-dlp | latest ตอน lock (2026.10.26 ตอนเขียน) | `YoutubeDL(params).extract_info(url, download=False)` คืน metadata โดยไม่โหลด แล้ว `process_ie_result` หรือ `download` โหลดตาม format ที่เลือก | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `format_sort: ["res:1080", "vcodec:h264", "acodec:aac"]`: `res` คือด้านสั้นของภาพ, `res:1080` เลือกตัวใหญ่สุดที่ไม่เกิน 1080 และถ้าไม่มีเอาตัวเล็กสุด | [README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) |
| yt-dlp | เดียวกัน | `merge_output_format: "mp4"` และ `ffmpeg_location` รับ path ของ binary ตรงๆ (ชื่อ binary ของ imageio ขึ้นต้นด้วย `ffmpeg`) | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `js_runtimes: {"deno": {"path": ...}}` ชี้ Deno ที่ไม่อยู่บน PATH | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `progress_hooks` ได้ dict ที่มี `status`, `downloaded_bytes`, `total_bytes`, `total_bytes_estimate`; raise `yt_dlp.utils.DownloadCancelled` ใน hook หยุดการโหลด | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | `paths: {"home": ..., "temp": ...}` แยกไฟล์ระหว่างโหลดออกจากไฟล์ผลลัพธ์, `noplaylist: True` โหลดคลิปเดียวเมื่อลิงก์มี `list=` | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| yt-dlp | เดียวกัน | YouTube ต้องมี JavaScript runtime; Deno ≥ 2.3.0 | [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS) |
| yt-dlp | เดียวกัน | error ตอนโหลดเป็น `yt_dlp.utils.DownloadError` ที่ `exc_info[1]` คือ exception ต้นทาง (`GeoRestrictedError`, `ExtractorError` ที่ `expected=True`); คลิป upcoming ทำให้ `extract_info` raise เพราะไม่มี format | [YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) |
| deno (PyPI) | latest ตอน lock (2.9.8 ตอนเขียน) | wheel macOS arm64 และ Windows amd64 มี binary, `deno.find_deno_bin()` คืน path | [deno on PyPI](https://pypi.org/project/deno/) |
| starlette | 1.10.0 (มากับ fastapi 0.162.0) | `FileResponse` ตอบ HTTP Range ให้ `<video>` seek ได้ | [Starlette responses](https://www.starlette.io/responses/#fileresponse) |
| imageio-ffmpeg | 0.7.0 | `get_ffmpeg_exe()` คืน path ffmpeg ที่ใช้ merge (ADR-0005) | [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |
| transformers | 5.21.0 | `pipeline("automatic-speech-recognition", model=<folder snapshot>, device=..., dtype=...)` โหลด Whisper จาก folder ในเครื่อง; รับ `numpy` float32 16 kHz ไม่ต้องใช้ ffmpeg บน PATH; ไม่ส่ง `chunk_length_s` (experimental สำหรับ Whisper ตาม `pipelines/automatic_speech_recognition.py:306`) ให้ Whisper ถอด long-form เอง; `return_timestamps=True` คืน `chunks` ที่มี `timestamp` (เริ่ม, จบ) และ `text`; `return_language=True` ใส่ `language` ใน `chunks[i]` ไม่มีค่าบนสุด และอ่านจาก batch item แรกเท่านั้น จึงใช้ `batch_size` 1 | [ASR pipeline](https://huggingface.co/docs/transformers/v5.21.0/en/main_classes/pipelines#transformers.AutomaticSpeechRecognitionPipeline), [Whisper](https://huggingface.co/docs/transformers/v5.21.0/en/model_doc/whisper) |
| ffmpeg (imageio) | เดียวกับบน | `ffmpeg -ss {start} -t {length} -i {id}.mp4 -vn -ac 1 -ar 16000 -f f32le -` ส่ง PCM float32 ของช่วงเดียวออก stdout; คลิปไม่มีเสียงได้ exit ไม่เป็น 0 | [ffmpeg docs](https://ffmpeg.org/ffmpeg.html) |
| Python `multiprocessing` | 3.12 | `get_context("spawn").Process` และ `Queue`; `terminate()` ส่ง SIGTERM บน Mac และ `TerminateProcess` บน Windows; `exitcode` ติดลบเมื่อตายด้วย signal | [multiprocessing](https://docs.python.org/3.12/library/multiprocessing.html) |

ข้อที่ ticket 01 ต้องลองกับ YouTube จริงก่อนเขียนต่อ: ยกเลิกด้วย `DownloadCancelled` จาก hook ได้, merge ด้วย ffmpeg ของ imageio ที่ไม่มี ffprobe (ADR-0005) ได้, ลิงก์ upcoming ได้ error ที่แยกเป็น `live` ได้, และข้อความ error ของ bot check หรือ login ที่ใช้แยก `login_required`. ยกเลิกไม่ได้ → ย้ายการโหลดไป `multiprocessing.Process` แล้ว terminate. merge ไม่ได้ → หยุดแล้วถามผู้ใช้ก่อน เพราะ format ไฟล์เดียวบน YouTube ส่วนใหญ่ไม่ถึง 1080 (ขัด D5); ทางเลือกคือหา ffprobe มาเพิ่ม (ขัด ADR-0005) หรือยอมความคมต่ำลง; ผลเป็น `D{n}` ใหม่.

ข้อที่ ticket ของงานถอดต้องลองก่อนเขียนต่อ: Whisper บน `mps` ด้วย `float16` ได้ผลถูก (ไม่ได้ → `float32` บน `mps`); pipeline รับ array 300 วินาทีโดยไม่มี `chunk_length_s` แล้วถอดแบบ long-form ได้ครบทั้งช่วง (ไม่ได้ → หยุดแล้วถาม เพราะทางเลือกคือ `chunk_length_s` ที่ library บอกว่า experimental); timestamp ของ `chunks` เป็นเวลาภายในช่วง; บรรทัดสุดท้ายที่ `timestamp` จบเป็น `None` → ใช้ความยาวของช่วงแทน; process ลูก `spawn` import `backend` ได้ทั้ง Mac และ Windows.

### Status check

เพิ่มสองแถวต่อจาก `ffmpeg` ใน `backend.checks.run_checks` รวมเป็น 11 แถว (D9). กฎของ check เดิมใช้ทั้งหมด (setup-status D7).

| `id` | `label` | `ok` เมื่อ | ไม่ `ok` | `fix` |
|---|---|---|---|---|
| `yt_dlp` | yt-dlp | `importlib.metadata.version("yt-dlp")` ได้. `detail` = เวอร์ชัน | `missing` | คำสั่ง setup |
| `deno` | Deno | `deno.find_deno_bin()` คืน path และ `{deno} --version` exit 0 ภายใน 5 วินาที. `detail` = เวอร์ชัน | `missing` | คำสั่ง setup |

- `run_checks` รับ `deno_probe` แบบเดียวกับ `ffmpeg_probe` ให้ test ส่งตัวปลอมได้
- probe ของ Deno ไม่ cache ผล
- tab สปอยและ `POST /downloads` ใช้แค่แถว `yt_dlp`, `deno` และ `ffmpeg` ไม่ใช้ `ready` (D9). `backend.spoil` เรียก probe สามตัวนี้เอง ไม่เรียก `run_checks` ทั้งชุด (ไม่ import torch)

### Download

ขั้นตอนของ Download job หนึ่งงาน (D5, D6, D11, D14, D15):

1. `POST /api/spoil/downloads` ตรวจตามลำดับ: probe `yt_dlp`, `deno` และ `ffmpeg` ผ่าน; ลิงก์ตรงรูปแบบ; แล้วภายใต้ lock เดียว: ไม่มี Temp clip ของ id นี้, ไม่มีงานที่ thread ยังไม่ออก, สร้างงาน. ไม่ผ่านข้อไหนตอบ error ของข้อนั้นทันที
2. เริ่ม daemon thread, state `checking`: `adapter.fetch_info(url)`
3. flag ยกเลิกถูกตั้ง → `cancelled`. `live_status` เป็น `is_live` หรือ `is_upcoming` หรือ error ของ upcoming → `failed` code `live` (D11)
4. ประมาณขนาด: ผลรวม `filesize` หรือ `filesize_approx` ของ `requested_formats`; ไม่มี → `tbr` (kbps) × `duration` × 125 bytes; ประมาณไม่ได้ → 0
5. `free_bytes(media/temp)` < ขนาดประมาณ + 1 GiB → `failed` code `disk_full` (D11)
6. state `downloading`: `adapter.download(info, on_progress)`. `percent` = byte ที่โหลดแล้วของทุก format ÷ ขนาดประมาณ × 100 ปัดลง ไม่เกิน 100; ขนาดประมาณเป็น 0 → `percent` เป็น `null`. hook raise `DownloadCancelled` เมื่อ flag ถูกตั้ง
7. state `merging` เมื่อ hook ของ format สุดท้ายได้ `finished`. ตั้งแต่นี้ยกเลิกไม่ได้ (D15)
8. อ่านขนาดภาพจาก metadata ของ format ที่เลือก, เขียน `{id}.json` แบบเขียนไฟล์ชั่วคราวแล้ว rename (D14), state `done` และ `clip_id` = id
9. ยกเลิกหรือ error ที่ขั้นไหนก็ตาม → ลบไฟล์ของ id นี้ใน `.partial/` และ `{id}.*` ที่ยังไม่มี json, state `cancelled` หรือ `failed`. งานนับว่าจบเมื่อ thread ออกจากขั้นนี้

Adapter (ตัวเดียวที่ import yt-dlp, test แทนด้วยตัวปลอม):

| ฟังก์ชัน | ทำอะไร |
|---|---|
| `fetch_info(url) -> dict` | `YoutubeDL(params).extract_info(url, download=False)` |
| `download(info, on_progress) -> Path` | `YoutubeDL(params พร้อม progress_hooks).process_ie_result(info, download=True)` ใช้ info เดิม ไม่ดึงจาก YouTube ซ้ำ; คืน path ของ mp4 |

จุด inject สำหรับ test (แบบเดียวกับ setup-status D18): `backend.spoil` มี module attribute `adapter` และ `free_bytes` ที่ test monkeypatch ได้ และ probe สามตัวที่ใช้ gate.

แยก error ของ yt-dlp (D15, D16):

| เมื่อ | `code` |
|---|---|
| upcoming (ข้อ 3): ข้อความ error มี "This live event will begin" หรือ "Premieres in" | `live` |
| ข้อความ error มี "Sign in to confirm" หรือ "not a bot" | `login_required` |
| `GeoRestrictedError` หรือข้อความมี "Private video", "unavailable", "removed" | `unavailable` |
| อื่นๆ ทั้งหมด รวม error ของ ffmpeg | `youtube_error` |

เช็คตามลำดับแถว. ข้อความยืนยันกับ YouTube จริงตอน build ticket 01 (D16).

params ของ yt-dlp (adapter เดียวใน `backend.spoil` สร้าง):

| Key | ค่า |
|---|---|
| `format_sort` | `["res:1080", "vcodec:h264", "acodec:aac"]` (D5) |
| `merge_output_format` | `"mp4"` (D5) |
| `ffmpeg_location` | `imageio_ffmpeg.get_ffmpeg_exe()` (ADR-0005) |
| `js_runtimes` | `{"deno": {"path": deno.find_deno_bin()}}` (D8) |
| `paths` | `{"home": media/temp, "temp": media/temp/.partial}` (D14) |
| `outtmpl` | `"%(id)s.%(ext)s"` (D14) |
| `writethumbnail` | `True`; thumbnail ได้นามสกุลตามที่ YouTube ให้ ไม่แปลง |
| `noplaylist` | `True` |
| `quiet`, `noprogress` | `True`; ความคืบหน้ามาจาก `progress_hooks` |

รูปแบบลิงก์ที่รับ (ตรวจโดยไม่ใช้ network, D14). id คือ 11 ตัวจาก `A-Z a-z 0-9 _ -`:

| Host | Path | id มาจาก |
|---|---|---|
| `youtube.com`, `www.youtube.com`, `m.youtube.com` | `/watch` | query `v` |
| เดียวกัน | `/shorts/{id}` | path |
| เดียวกัน | `/live/{id}` | path |
| `youtu.be` | `/{id}` | path |

- รับทั้ง `http` และ `https`, ตัดช่องว่างหัวท้าย
- query อื่น (`list`, `t`, `si`) ไม่สนใจ
- นอกตาราง → `invalid_url`

### Transcribe

ขั้นตอนของ Transcribe job หนึ่งงาน (D21, D23, D24, D26, D27, D28, D29):

1. `POST /api/spoil/transcriptions` ตรวจตามลำดับ: แถว `torch`, `transformers`, `ffmpeg`, `model_whisper` เป็น `ok` และ `device` ไม่ใช่ `cpu`; แล้วภายใต้ lock ของงานถอด (lock เดียวกับ `DELETE /clips/{id}`, D29): มี Temp clip ของ `clip_id` (มี json และ mp4), ไม่มี Transcribe job ที่ thread ยังไม่ออก, สร้างงาน. Download job ไม่มีผล (D24)
2. เริ่ม daemon thread ใน backend, state `preparing`: start process ลูก (`multiprocessing` context `spawn`) ที่รัน `backend.spoil.whisper.worker(mp4, duration_s, snapshot_dir, device, queue)` (D28)
3. process ลูก: โหลดโมเดล; ล้ม → ส่ง `("error", "model_failed", ข้อความ)`. แล้วแบ่งเวลา 0 ถึง `duration_s` เป็นช่วงละ 300 วินาที (ช่วงสุดท้ายสั้นกว่า 30 วินาทีรวมเข้าช่วงก่อน, D29); ทุกช่วง: `read_audio(mp4, start, length)` (ffmpeg ล้มที่ช่วงแรก → `("error", "no_audio", ...)`), `transcribe(model, audio)`, บวกเวลาเริ่มของช่วงให้ทุกบรรทัด แล้วส่ง `("segment", index, total, lines, language)`. จบครบ → ส่ง `("done",)` แล้ว exit
4. thread ใน backend อ่าน queue: ข้อความ `segment` แรกเปลี่ยน state เป็น `transcribing`; `percent` = ช่วงที่ได้ × 100 ÷ จำนวนช่วง ปัดลง; สะสมบรรทัดใน memory
5. flag ยกเลิกถูกตั้ง → `terminate()` process ลูก แล้ว `join`, state `cancelled`. process ลูกออกโดยไม่ได้ `done` หรือ `error` (Metal/CUDA crash, ถูก OS ฆ่า) → `failed` `crashed` (D28)
6. ได้ `done`: ตัดบรรทัดที่ข้อความว่างหลัง strip; `language` = ภาษาที่ช่วงส่วนใหญ่ตรวจได้ไม่นับ `null` (เสมอกัน → ช่วงแรก, ไม่มีเลย → `null`); เขียน `{id}.transcript.json` แบบไฟล์ `.tmp` แล้ว rename; state `done`
7. error ใดก็ตามที่ไม่อยู่ในข้อบน (รวมเขียนไฟล์ไม่ได้) → `failed` `internal`; thread ตั้ง state จบใน `finally` และ process ลูกที่ยังรันถูก `terminate()` (D29). `cancelled` และ `failed` ไม่แตะ `{id}.transcript.json` เดิม. งานนับว่าจบเมื่อ thread ออก
8. backend shutdown → ตั้ง flag ยกเลิกและ `terminate()` process ลูกที่ยังรัน (D28)

Adapter `backend.spoil.whisper` (ตัวเดียวที่ import `transformers` และ `torch` สำหรับถอด; import ภายในฟังก์ชันที่รันใน process ลูก ไม่ใช่ตอน import module):

| ฟังก์ชัน | ทำอะไร |
|---|---|
| `worker(mp4, duration_s, snapshot_dir, device, queue)` | จุดเริ่มของ process ลูก ทำขั้น 3 |
| `read_audio(mp4, start_s, length_s) -> ndarray` | ffmpeg ของ imageio ตาม Library assumptions ช่วงเดียว อ่าน stdout เป็น float32 |
| `load(snapshot_dir, device) -> Model` | `pipeline("automatic-speech-recognition", ...)` กับ `float16` บน `cuda` และ `float32` บน `mps` (D30) |
| `transcribe(model, audio, start_s, length_s) -> (lines, language)` | ส่ง array ทั้งช่วงโดยไม่ใช้ `chunk_length_s` ให้ Whisper ทำ long-form เอง, `return_timestamps=True`, `return_language=True`, `batch_size` 1; คืนบรรทัด `(start_s, end_s, text)` ที่ `to_lines` บวกเวลาเริ่มของช่วงแล้ว (จบเป็น `None` หรือเลยช่วง → จบช่วง) และภาษาจาก `chunks[0]["language"]` แปลงเป็น code (ไม่มี chunk → `null`) (D29, D30) |

จุด inject สำหรับ test: `backend.spoil` มี module attribute `start_worker` (สร้าง process ลูก) ที่ test แทนด้วยตัวปลอมที่รันใน thread และป้อนข้อความเข้า queue ตามลำดับที่ test กำหนด; probe และ status ของแถวที่ gate มาจาก `backend.checks` เหมือนงานโหลด. test ของ `worker` จริงอยู่ใน seam 3 (เช็คมือ).

`{id}.transcript.json`:

```json
{
  "clip_id": "dQw4w9WgXcQ",
  "language": "en",
  "duration_s": 5712,
  "model": "openai/whisper-large-v3-turbo",
  "revision": "41f01f3",
  "transcribed_at": "2026-10-30T10:12:00+07:00",
  "lines": [
    {"start_s": 12.4, "end_s": 15.0, "text": "Where are you going?"}
  ]
}
```

- `lines` เรียงตาม `start_s`; ว่างได้ (ไม่พบคำพูด)
- `language` เป็น `null` เมื่อไม่มีช่วงไหนตรวจภาษาได้ (D29)
- `.txt` = บรรทัดละ `[hh:mm:ss] ข้อความ`; `.srt` = มาตรฐาน SRT เลขลำดับจาก 1 เวลา `hh:mm:ss,mmm`; ทั้งสอง UTF-8 ไม่มี BOM, ขึ้นบรรทัด `\n`

### Temp clip

`{id}.json` (D7, D14):

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "ชื่อคลิป",
  "channel": "ชื่อช่อง",
  "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_s": 7212,
  "width": 1920,
  "height": 1080,
  "orientation": "landscape",
  "file_bytes": 1450000000,
  "thumbnail": "dQw4w9WgXcQ.webp",
  "downloaded_at": "2026-10-29T14:05:11+07:00",
  "yt_dlp_version": "2026.10.26"
}
```

- `orientation` เป็น `portrait` เมื่อ `height` > `width`, ไม่งั้น `landscape`
- `thumbnail` เป็น `null` เมื่อโหลด thumbnail ไม่ได้
- `file_bytes` อ่านจากไฟล์ mp4 จริงหลัง merge
- รายการ = ทุก `*.json` ใน `media/temp/` ที่มี `{id}.mp4` คู่กัน เรียง `downloaded_at` ใหม่สุดก่อน. json ที่อ่านไม่ได้หรือไม่มี mp4 คู่ → ข้าม
- ลบ = ลบ `{id}.mp4`, thumbnail และ `{id}.transcript.json` ก่อน แล้ว `{id}.json` สุดท้าย; ลบ mp4 ไม่ได้ (Windows ที่ไฟล์ยังเปิดอยู่) → `409` `in_use` และไม่แตะ json (D15, D23); คลิปที่ Transcribe job ยังไม่จบ → `409` `transcribing` ไม่ลบอะไร (D27)
- รายการมี field `transcribed`: `true` เมื่อมีไฟล์ `{id}.transcript.json` (ไม่ parse); รายการคลิปข้ามไฟล์ `*.transcript.json` (D23, D29)
- เช็คกับลบภายใต้ lock ของงานถอด (D29)
- backend start → ลบ `.partial/` ทั้งหมด, ไฟล์ `{id}.*` ใน `media/temp/` ที่ไม่มี `{id}.json` และไฟล์ `*.tmp` ทั้งหมด (D15, D29)

### API

ทุก path อยู่ใต้ `/api/spoil`. error body เป็น `{"code": "...", "message": "..."}`; `message` เป็นภาษาไทยพร้อมแสดงในหน้าเว็บ.

| Method | Path | Response |
|---|---|---|
| `GET` | `/clips` | `200` `{"clips": [Temp clip + `transcribed`, ...]}` |
| `GET` | `/clips/{id}/video` | `200` หรือ `206` ไฟล์ `video/mp4` รองรับ Range; ไม่มี → `404` `not_found` |
| `GET` | `/clips/{id}/thumbnail` | `200` ไฟล์ thumbnail; ไม่มี → `404` `not_found` |
| `DELETE` | `/clips/{id}` | `204`; ไม่มี → `404` `not_found`; ไฟล์ถูกเปิดอยู่ → `409` `in_use` "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง"; กำลังถอดคลิปนี้ → `409` `transcribing` "กำลังถอดคลิปนี้อยู่ ยกเลิกก่อนแล้วลบ" |
| `GET` | `/clips/{id}/transcript` | `200` เนื้อ `{id}.transcript.json`; ไม่มี → `404` `not_found` |
| `GET` | `/clips/{id}/transcript.txt`, `/clips/{id}/transcript.srt` | `200` `text/plain; charset=utf-8` หรือ `application/x-subrip`, `Content-Disposition: attachment; filename="{id}.txt"` หรือ `.srt`; ไม่มี → `404` `not_found` |
| `POST` | `/transcriptions` | body `{"clip_id": "..."}`. `202` กับ Transcribe job. error: `503` `not_ready`, `404` `not_found`, `409` `busy` "กำลังถอดคลิปอื่นอยู่" |
| `GET` | `/transcriptions/current` | `200` Transcribe job ล่าสุด หรือ `null` |
| `DELETE` | `/transcriptions/current` | `202` ตั้ง flag ยกเลิก; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |
| `POST` | `/downloads` | body `{"url": "..."}`. `202` กับ Download job. error: `503` `not_ready`, `400` `invalid_url`, `409` `duplicate` (body มี `clip_id` เพิ่ม), `409` `busy` |
| `GET` | `/downloads/current` | `200` Download job ล่าสุด หรือ `null` ถ้ายังไม่เคยมีตั้งแต่ backend start |
| `DELETE` | `/downloads/current` | `202` ตั้ง flag ยกเลิก; state เป็น `cancelled` เมื่อ thread หยุด (รอบ progress ถัดไป หรือหลัง `fetch_info` คืน); state `merging` → `409` `merging`; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |

`{id}` ใน path ต้องตรงรูปแบบ id 11 ตัว ไม่งั้น `404` — กัน path traversal.

ทุก `POST` ใต้ `/api/spoil` ที่ `Content-Type` ไม่ใช่ `application/json` ได้ `415` `unsupported_media_type` — บังคับ CORS preflight จึงไม่มีเว็บอื่นสั่งงานได้ (D29). `sendJson` ส่ง header นี้อยู่แล้ว.

ทุก request ที่ `Host` ไม่ใช่ `127.0.0.1`, `localhost` หรือ `[::1]` (port ใดก็ได้) ได้ `400` จาก `TrustedHostMiddleware` (D15). Vite proxy ส่ง `Host: localhost:5173` ต่อมาจึงผ่าน.

Download job:

```json
{
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "id": "dQw4w9WgXcQ",
  "state": "downloading",
  "title": "ชื่อคลิป",
  "percent": 42,
  "cancel_requested": false,
  "error": null,
  "clip_id": null
}
```

- `state` เป็นหนึ่งใน `checking`, `downloading`, `merging`, `done`, `failed`, `cancelled`
- งานยังไม่จบ = `checking`, `downloading`, `merging`
- `title` เป็น `null` ระหว่าง `checking`
- `percent` เป็น `null` นอก `downloading` หรือเมื่อประมาณขนาดไม่ได้
- `clip_id` มีค่าเมื่อ `done`
- `cancel_requested` เป็น `true` หลัง `DELETE /downloads/current` จนงานจบ
- `error` มีค่าเมื่อ `failed`: `{"code": "...", "message": "...", "yt_dlp_version": "...", "fix": "..."}`; `fix` มีค่าเฉพาะ `youtube_error`

Transcribe job:

```json
{
  "clip_id": "dQw4w9WgXcQ",
  "state": "transcribing",
  "percent": 35,
  "cancel_requested": false,
  "error": null
}
```

- `state` เป็นหนึ่งใน `preparing`, `transcribing`, `done`, `failed`, `cancelled`; งานยังไม่จบ = `preparing`, `transcribing`
- `percent` เป็น `null` นอก `transcribing`
- `error` มีค่าเมื่อ `failed`: `{"code", "message"}`

| `code` | เมื่อ | `message` |
|---|---|---|
| `no_audio` | ffmpeg อ่านเสียงช่วงแรกไม่ได้ | "คลิปนี้ไม่มีเสียง หรืออ่านเสียงไม่ได้" |
| `model_failed` | โหลดโมเดลหรือถอดช่วงไหนล้มเป็น exception | "ถอดไม่สำเร็จ: {ข้อความสั้นของ error}. ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง"; ข้อความเต็มอยู่ใน log ของ `[api]` |
| `crashed` | process ลูกตายโดยไม่ส่งผล (D28) | "ตัวถอดหยุดทำงานกลางทาง (exit {code}). ปิดโปรแกรมอื่นที่ใช้ GPU แล้วลองอีกครั้ง" |
| `internal` | error อื่นทั้งหมด รวมเขียนไฟล์ไม่ได้ (D29) | "ถอดไม่สำเร็จ: {ข้อความสั้นของ error}"; ข้อความเต็มอยู่ใน log ของ `[api]` |

error ของ Download job (`failed`):

| `code` | เมื่อ | `message` |
|---|---|---|
| `live` | `live_status` เป็น `is_live` หรือ `is_upcoming` | "คลิปนี้เป็น live หรือยังไม่เริ่มฉาย โหลดไม่ได้" |
| `disk_full` | ที่ว่างไม่พอตามขั้น 5 | "ที่ว่างไม่พอ: ต้องการ {ต้องการ} GB มี {ว่าง} GB" |
| `unavailable` | ตารางแยก error | "คลิปนี้เป็น private ถูกลบ หรือจำกัดประเทศ โหลดไม่ได้" |
| `login_required` | ตารางแยก error | "YouTube ขอให้ login หรือยืนยันว่าไม่ใช่ bot ยังไม่รองรับในรอบนี้ ลองใหม่ภายหลังหรือใช้คลิปอื่น" |
| `youtube_error` | ตารางแยก error | "โหลดไม่สำเร็จ (yt-dlp {version}). ถ้าเป็นทุกคลิป ให้อัปเดต yt-dlp ด้วยคำสั่งด้านล่างแล้วรัน Setup script"; `fix` = `uv lock --upgrade-package yt-dlp`; ข้อความเต็มจาก yt-dlp อยู่ใน log ของ `[api]` (D8) |

### Frontend

แถบ tab (D10):
- hash `#/spoil` → tab สปอย, `#/setup` → Setup status, อื่นหรือว่าง → Setup status
- กด tab → เปลี่ยน hash; ปุ่ม back ของ browser สลับ tab ตาม hash

tab สปอย:

| State | เมื่อไร | แสดง |
|---|---|---|
| loading | เปิด tab ยังไม่ได้ผลจาก `/api/setup/status` และ `/api/spoil/clips` | "กำลังโหลด…" |
| not ready | แถว `yt_dlp`, `deno` หรือ `ffmpeg` ไม่ `ok` | "ยังติดตั้งไม่ครบ: {label ที่ขาด}" กับลิงก์ "ไปหน้า Setup status" แทนช่องลิงก์; รายการยังแสดง (D9) |
| idle | พร้อม ไม่มีงานที่ยังไม่จบ | ช่องลิงก์, ปุ่ม "โหลด", รายการ |
| downloading | งานเป็น `checking`, `downloading` หรือ `merging` | "กำลังเช็คลิงก์…", "กำลังโหลด {title}" กับแถบ % หรือ "กำลังรวมไฟล์…"; ปุ่ม "ยกเลิก" ยกเว้นตอน `merging` ที่แสดง "ยกเลิกไม่ได้ระหว่างรวมไฟล์" แทน (D18); ปุ่มโหลด disabled (D6, D15) |
| cancelling | `cancel_requested` เป็น `true` และงานยังไม่จบ | "กำลังยกเลิก…", ปุ่มยกเลิก disabled |
| offline | fetch ล้ม, status ที่ไม่อยู่ในตาราง API หรือเกิน 30 วินาที | `OfflinePanel` ตัวเดียวกับหน้า Setup status พร้อมปุ่ม Refresh ที่โหลด tab ใหม่ทั้งหมด |

ข้อความหลังงานจบ (แสดงเหนือรายการจนกดโหลดครั้งถัดไป):

| ผล | แสดง |
|---|---|
| `done` | "โหลดเสร็จ: {title}" และ highlight แถวใหม่ |
| `cancelled` | "ยกเลิกแล้ว" |
| `failed` | `error.message`; มี `error.fix` → แสดงคำสั่งเป็นบรรทัดพร้อมปุ่ม copy; ไม่ใช้ chip เพราะคำสั่งมีช่องว่าง (setup-status D20) |
| poll ได้ `null` ระหว่างติดตามงาน | "งานโหลดหายเพราะ backend เริ่มใหม่ ลองโหลดอีกครั้ง" แล้วโหลดรายการใหม่ (D15) |
| `409` `merging` | "กำลังรวมไฟล์ ยกเลิกไม่ได้แล้ว" |
| ลบได้ `409` `in_use` | `message` จาก API ใต้แถวนั้น |
| `400` `invalid_url` | "ลิงก์นี้ไม่ใช่ลิงก์คลิป YouTube" |
| `409` `duplicate` | "คลิปนี้โหลดไว้แล้ว" และ highlight แถว `clip_id` พร้อมเลื่อนไปหา (D12) |
| `409` `busy` | "กำลังโหลดคลิปอื่นอยู่" |
| `503` `not_ready` | state not ready |

กฎอื่น:
- เปิด tab → `GET /api/spoil/downloads/current` ครั้งหนึ่ง; งานยังไม่จบ → เข้า state downloading; งานจบแล้ว → แสดงข้อความผลของงานนั้น (D15)
- poll `GET /api/spoil/downloads/current` ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ; จบแล้ว → `GET /api/spoil/clips` ครั้งเดียว (D6)
- ลบ → `window.confirm("ลบ {title}?")` ก่อน; แถวนั้นเล่นอยู่ → ปลด player (`src` ว่างแล้ว `load()`) ก่อน `DELETE` (D15); สำเร็จ → เอาแถวออก
- กดแถว → `<video controls>` ที่ `src` = `/api/spoil/clips/{id}/video` แสดงเหนือรายการ; แถวที่ถูกลบหายจาก player ด้วย
- รายการมีหัว "คลิปที่โหลดมา" พร้อมจำนวนคลิป; แถวที่เล่นอยู่มี badge "กำลังเล่น" (D18)
- ความยาวแสดงเป็น `h:mm:ss` หรือ `m:ss`; ขนาดไฟล์เป็น MB หรือ GB ทศนิยมหนึ่งตำแหน่ง; เวลาโหลดเป็นเวลาท้องถิ่น
- ข้อความในหน้าเป็นภาษาไทย

กล่องถอดบทพูด (D22–D25):

| State | เมื่อไร | แสดง |
|---|---|---|
| ยังไม่เลือก | ไม่มีคลิปที่เลือก | "เลือกคลิปจากรายการ" |
| not ready | แถว gate ของงานถอด (D27) ไม่ผ่าน | player และ "ยังติดตั้งไม่ครบ: {label ที่ขาด}" กับลิงก์ไป Setup status แทนปุ่มถอด |
| เลือกแล้ว | คลิปไม่มี Transcript | player, ชื่อ, ความยาว, ปุ่ม "ถอดบทพูด" |
| ถอดแล้ว | `transcribed` เป็น `true` | alert "คลิปนี้ถอดแล้ว", ปุ่ม "ถอดใหม่", Transcript; ไม่มีบรรทัด → "ไม่พบคำพูดในคลิปนี้" ไม่มีปุ่ม Copy, `.txt`, `.srt` (D33) |
| กำลังถอด | งานของคลิปนี้ยังไม่จบ | "กำลังเตรียมเสียง…" กับแถบไม่มีตัวเลข หรือ "กำลังถอด" กับแถบ % และ "{percent}%" ขวา (component `Download progress`, D33), ปุ่ม "ยกเลิก"; cancel_requested → "กำลังยกเลิก…" |
| คลิปอื่นกำลังถอด | งานของคลิปอื่นยังไม่จบ | ปุ่มถอด disabled กับ "กำลังถอด {ชื่อคลิปนั้น}" |

กฎอื่นของกล่อง:
- กดแถว = เลือกคลิปนั้นและเล่นใน player ของกล่อง (แทน player เหนือรายการ, D25); แถวที่เลือกมี badge "กำลังเล่น" (D18)
- เปิด tab → `GET /api/spoil/transcriptions/current` ครั้งหนึ่ง; งานยังไม่จบ → เลือกคลิปนั้นและเข้า state กำลังถอด
- poll `GET /api/spoil/transcriptions/current` ทุก 1 วินาทีเฉพาะตอนงานยังไม่จบ แยกจาก poll ของงานโหลด; จบ → `GET /api/spoil/clips` ครั้งเดียว และถ้า `done` โหลด Transcript ของคลิปที่เลือก
- ข้อความหลังงานถอดจบ: `done` → "ถอดเสร็จ"; `cancelled` → "ยกเลิกแล้ว"; `failed` → `error.message`; poll ได้ `null` → "งานถอดหายเพราะ backend เริ่มใหม่ ลองถอดอีกครั้ง". เป็น `Alert` ในกล่อง ใต้ชื่อคลิปและความยาว: `done` success, `cancelled` info, `failed` error, `null` warning; `404` ของ `POST` → "ไม่พบคลิปนี้" error (D33)
- บรรทัดของ Transcript: `[hh:mm:ss] ข้อความ`; กด → `video.currentTime = start_s` แล้วเล่น; ใต้หัวแสดง "ภาษา: {language}" หรือ "ภาษา: ไม่ทราบ" เมื่อ `null` (D29)
- ผลของ `POST /transcriptions`: `409` `busy` ที่งานเป็นของคลิปนี้ → เข้า state กำลังถอด; `busy` ของคลิปอื่น → "กำลังถอด {ชื่อคลิปนั้น}"; `404` `not_found` → "ไม่พบคลิปนี้" แล้วโหลดรายการใหม่; `503` `not_ready` → state not ready ของกล่อง; อื่น → offline (D29)
- Copy → คัดลอกเนื้อเดียวกับ `.txt` ด้วย `useCopy`; `.txt` และ `.srt` เป็นลิงก์ไป API (browser โหลดไฟล์เอง)
- ลบคลิปที่เลือกอยู่ → กล่องกลับเป็น "ยังไม่เลือก"; `409` `transcribing` → `message` ใต้แถว
- แถวที่ `transcribed` มี badge "ถอดแล้ว" (D23)
- จอกว้าง ≥ 1024px สองคอลัมน์มีลูกศร →; แคบกว่าเรียงบนลงล่างมีลูกศร ↓ (D25). คอลัมน์ซ้ายกว้าง 520px มีช่องลิงก์, แถบโหลด และรายการ; กล่องกินที่เหลือ (D33)

### Ops

- ที่ดิสก์: wheel `deno` ประมาณ 80 MB ใน `.venv`; คลิป 1080p ประมาณ 0.5–1.5 GB ต่อชั่วโมง ใน `media/temp/`
- ลบคลิปทั้งหมดด้วยมือได้โดยลบ folder `media/temp/` ตอน backend ไม่ได้รัน (README)
- YouTube เปลี่ยนแล้วโหลดไม่ได้ทุกคลิป → `uv lock --upgrade-package yt-dlp` แล้วรัน Setup script (D8, README)
- งานถอดใช้ memory ของ process ลูกประมาณ 2–4 GB (โมเดล 1.6 GB กับเสียงช่วงละ 300 วินาทีประมาณ 19 MB) ไม่โตตามความยาวคลิป และคืนทั้งหมดเมื่อ process ลูกออก (D28, D29)
- งานถอดมีปัญหา: กดยกเลิก หรือปิด `npm run dev` — process ลูกถูก terminate; ปิด feature ทั้งหมดไม่ได้นอกจากไม่กดถอด

## Seams

สี่ seam: API ของสปอยกับ adapter ปลอม, adapter จริงกับ YouTube, adapter จริงของ Whisper, และหน้าเว็บ — เพราะ yt-dlp กับ YouTube จริงช้าและเปลี่ยนตลอด จึงแยก adapter ไว้ตัวเดียวให้ส่วนอื่นทดสอบได้เร็ว (D14).

1. **Spoil API** `/api/spoil/*` และ `GET /api/setup/status` ด้วย `TestClient`, root ปลอมใน `tmp_path` และ adapter ปลอม
   - ลิงก์ทุกแบบในตารางลิงก์ → `202`; `https://vimeo.com/1`, `https://www.youtube.com/playlist?list=x` → `400` `invalid_url`
   - adapter ปลอมสำเร็จ → poll จน `done`, `GET /clips` มีคลิปนั้นพร้อมทุกฟิลด์ และ `/clips/{id}/video` ตอบ `206` เมื่อส่ง `Range: bytes=0-99`
   - ลิงก์ของ id ที่มี json แล้ว → `409` `duplicate` กับ `clip_id`
   - POST ระหว่างงานยังไม่จบ → `409` `busy`
   - adapter ปลอมคืน `live_status: is_live` → `failed` `live`
   - ที่ว่างปลอมน้อยกว่าขนาดประมาณ + 1 GiB → `failed` `disk_full` และ adapter ไม่ถูกเรียกโหลด
   - `DELETE /downloads/current` ระหว่าง `downloading` → `cancelled` และ `.partial/` ไม่มีไฟล์ของ id นั้น
   - json ที่ไม่มี mp4 คู่ หรือ json เสีย → ไม่อยู่ใน `GET /clips`
   - `DELETE /clips/{id}` → `204` และไฟล์ทั้งสามหาย; `/clips/../x/video` → `404`
   - start app ขณะ `.partial/` มีไฟล์ → ไฟล์หาย
   - deno probe raise → แถว `deno` เป็น `missing`, มี 11 แถว, และ `POST /downloads` → `503` `not_ready`
   - marker ของโมเดลหาย แต่ probe สามตัวผ่าน → `POST /downloads` → `202` (D9)
   - ยกเลิกระหว่าง `checking` (adapter ปลอมรอสัญญาณใน `fetch_info`) → `cancelled` และไม่มีไฟล์
   - `DELETE /downloads/current` ระหว่าง `merging` → `409` `merging` และงานจบเป็น `done`
   - POST สองครั้งพร้อมกันจากสอง thread → หนึ่ง `202` หนึ่ง `409` `busy`
   - adapter ปลอม raise error ที่มี "Sign in to confirm" → `failed` `login_required`
   - adapter ปลอม raise `GeoRestrictedError` → `failed` `unavailable`
   - adapter ปลอม raise error อื่น → `youtube_error` ที่มี `yt_dlp_version` และ `fix`
   - `DELETE /clips/{id}` ขณะลบ mp4 ไม่ได้ (monkeypatch ให้ raise `PermissionError`) → `409` `in_use` และ json ยังอยู่
   - start app ขณะมี `{id}.mp4` ที่ไม่มี json → ไฟล์หาย
   - request ที่ `Host: evil.example` → `400`
   - worker ปลอมส่งสองช่วง → poll จน `done`, `GET /clips/{id}/transcript` มีบรรทัดที่เวลาของช่วงสองบวก 300; `GET /clips` มี `transcribed: true`
   - `.txt` และ `.srt` ของ Transcript สองบรรทัด → เนื้อตรงตัวอย่างใน test; `Content-Disposition` มีชื่อไฟล์
   - POST ถอดระหว่าง Download job ยังไม่จบ → `202` (D24); POST ถอดระหว่าง Transcribe job ยังไม่จบ → `409` `busy`
   - `DELETE /transcriptions/current` ระหว่างช่วงแรก (worker ปลอมรอสัญญาณ) → `cancelled`, worker ปลอมถูก terminate และ Transcript เดิมยังอยู่
   - worker ปลอมส่ง `error` `no_audio` → `failed` `no_audio`; ส่ง `error` `model_failed` → `failed` `model_failed`
   - worker ปลอมออกโดยไม่ส่ง `done` → `failed` `crashed`; POST ถัดไป → `202`
   - เขียน Transcript ไม่ได้ (monkeypatch rename ให้ raise) → `failed` `internal` และ POST ถัดไป → `202`
   - `POST /transcriptions` และ `POST /downloads` ที่ `Content-Type: text/plain` → `415`
   - start app ขณะมี `{id}.transcript.json.tmp` → ไฟล์หาย; `GET /clips` ไม่มีแถวของ `*.transcript.json`
   - worker ปลอมส่งช่วงที่ภาษา `null` ทุกช่วง → `language` เป็น `null`
   - marker ของ Whisper หาย → `POST /transcriptions` → `503` `not_ready`; device `cpu` → `503`
   - `DELETE /clips/{id}` ระหว่างถอดคลิปนั้น → `409` `transcribing`; หลังงานจบ → `204` และ `{id}.transcript.json` หาย
   - worker ปลอมส่งช่วงที่ไม่มีบรรทัด → `done` และ `lines` ว่าง
2. **yt-dlp adapter** `backend.spoil` กับ YouTube จริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Shorts หนึ่งคลิป → mp4 ด้านสั้น ≤ 1080 และมีเสียง
   - คลิปแนวนอนยาวกว่า 1 ชั่วโมง → mp4 1920×1080 หรือเล็กกว่า
   - กดยกเลิกที่ประมาณ 30% → หยุดภายใน 5 วินาที ไม่มีไฟล์ค้าง
   - ลิงก์ live ที่ยังไม่เริ่ม → `live`
   - Ctrl+C ระหว่างโหลด แล้ว `npm run dev` ใหม่ → ไม่มี process ค้าง และ `.partial/` ว่าง
   - Windows: เล่นคลิปใน player แล้วกดลบ → ลบได้ หรือได้ `in_use` และแถวยังอยู่
3. **Whisper adapter** `backend.spoil.whisper` กับโมเดลจริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Shorts ภาษาไทยและหนังภาษาอังกฤษยาวกว่า 1 ชั่วโมง → Transcript อ่านรู้เรื่อง ภาษาตรง เวลาของบรรทัดตรงกับเสียงในคลิปภายใน 2 วินาที (สุ่มดู 5 บรรทัด)
   - ยกเลิกกลางหนัง → process ลูกหายภายใน 5 วินาที (`ps`) และ memory ของ backend ไม่โตขึ้น
   - ฆ่า process ลูกด้วยมือระหว่างถอดขณะมีงานโหลด → งานถอด `crashed`, งานโหลดเดินต่อจน `done`
   - ช่วงละ 300 วินาทีให้ timestamp ของ `chunks` เป็นเวลาภายในช่วง และบรรทัดสุดท้ายที่ `timestamp` จบเป็น `None` → ใช้ความยาวช่วงแทน
   - ถอดพร้อมโหลดคลิปอื่น → ทั้งสองงาน `done`
   - Windows NVIDIA: ถอดได้บน `cuda`
4. **tab สปอย** `frontend` ด้วย Vitest และ fetch ปลอม
   - hash ว่าง → เห็นหน้า Setup status; กด tab สปอย → hash เป็น `#/spoil`
   - status ที่ `deno` เป็น `missing` → "ยังติดตั้งไม่ครบ: Deno" และไม่มีช่องลิงก์
   - วางลิงก์ กดโหลด, current คืน `downloading` 40 แล้ว `done` → เห็น 40%, แล้ว "โหลดเสร็จ" และแถวใหม่
   - `409` `duplicate` → "คลิปนี้โหลดไว้แล้ว" และแถวนั้น highlight
   - งาน `failed` → เห็น `error.message`; มี `fix` → เห็นคำสั่งพร้อมปุ่ม copy
   - current คืน `downloading` ที่ `percent: null` → แถบไม่มีตัวเลข
   - กำลังติดตามงานแล้ว current คืน `null` → "งานโหลดหายเพราะ backend เริ่มใหม่"
   - เปิด tab แล้ว current เป็น `failed` → เห็น `error.message`
   - กดยกเลิก → ส่ง `DELETE /api/spoil/downloads/current`; current คืน `cancel_requested: true` → เห็น "กำลังยกเลิก…"
   - รายการว่าง → "ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน"
   - กดแถว → มี `<video>` ที่ `src` ถูก; กดลบและยืนยัน → แถวหาย
   - ยังไม่เลือก → "เลือกคลิปจากรายการ"; กดแถว → กล่องมีชื่อคลิปและปุ่ม "ถอดบทพูด"
   - กดถอด, current คืน `transcribing` 35 แล้ว `done` → เห็น "กำลังถอด 35%" แล้วบรรทัดของ Transcript และแถวมี "ถอดแล้ว"
   - กดบรรทัดเวลา 12.4 → `currentTime` ของ video เป็น 12.4
   - กด Copy → clipboard ได้บรรทัด `[00:00:12] ...`; ลิงก์ `.srt` ชี้ `/api/spoil/clips/{id}/transcript.srt`
   - เปิด tab ขณะ current ของงานถอดเป็น `transcribing` → คลิปนั้นถูกเลือกและเห็น %
   - status ที่ `model_whisper` เป็น `missing` → ไม่มีปุ่มถอด เห็นลิงก์ไป Setup status; ช่องลิงก์โหลดยังใช้ได้

## Testing decisions

- **Copy:** `backend/tests/test_app.py` — `TestClient` กับ root ปลอมใน `tmp_path`
- **Copy:** `backend/tests/fakes.py` — เพิ่ม adapter ปลอมของ yt-dlp และ deno probe ปลอมที่นี่; เพิ่ม `start_worker` ปลอมที่รันใน thread ป้อนข้อความเข้า queue และรอสัญญาณได้แบบเดียวกับ adapter ปลอมของ yt-dlp
- **Copy:** `backend/tests/test_spoil_api.py` — โครงของ test งานโหลด (poll จนจบ, ยกเลิกด้วยสัญญาณ) ใช้กับงานถอด
- **Copy:** `frontend/src/features/spoil/components/SpoilPage.test.tsx` — fake backend ที่ตอบตาม route; เพิ่ม route ของ `/transcriptions` และ `/transcript`
- **Copy:** `backend/tests/test_checks.py` — test แถวใหม่ของ Status check และนับ 11 แถว
- **Copy:** `frontend/src/features/setup-status/components/SetupStatusPage.test.tsx` — fetch ปลอมและการ assert ข้อความ
- test ที่มีอยู่ซึ่งนับ 9 แถวต้องแก้เป็น 11
- test ที่เช็คการล้างไฟล์ตอน start ใช้ `with TestClient(app)` เพื่อให้ lifespan รัน; การล้างอ่าน `paths.ROOT` ตอนรัน จึง monkeypatch ได้
- `TestClient` ทุกตัวใช้ `base_url="http://127.0.0.1"` เพราะ host default `testserver` ไม่ผ่าน `TrustedHostMiddleware`; แก้ `backend/tests/test_app.py` ด้วย
- adapter ปลอมเรียก progress hook เองตามลำดับที่ test กำหนด และรอสัญญาณจาก test ได้ เพื่อทดสอบ busy และยกเลิกแบบไม่ขึ้นกับเวลา
- seam 2 ไม่อยู่ใน test อัตโนมัติ: พิสูจน์ด้วย How success is judged บน Mac; ข้อ Windows เช็คใน `windows-check` 02 (ADR-0014)
- seam 3 ไม่อยู่ใน test อัตโนมัติ ยกเว้นฟังก์ชันที่ไม่แตะโมเดล: `backend/tests/test_whisper.py` ทดสอบ `plan_segments`, `to_lines` และว่า import adapter ไม่ import torch กับ transformers. การบวกเวลาของช่วงจึงพิสูจน์ที่นี่ ไม่ใช่ใน seam 1 ซึ่ง worker ปลอมส่งเวลาของคลิปมาแล้ว (D30)

## Out of Scope

- ตัดต่อ, ทำแนวตั้ง, เลือก p ของ output และ render (D2, D5)
- ใส่เสียงเล่าด้วย TTS และการเลือก TTS ที่ใช้เชิงพาณิชย์ได้ (D2, D13)
- แยกเสียงพูดออกจากดนตรี และให้ไฟล์เสียงหรือวิดีโอเงียบกับผู้ใช้ (D21)
- แปลภาษา, แก้ไข Transcript ในแอป, แยกผู้พูด, เลือกภาษาเอง (D21, D22)
- วิเคราะห์บทหรือเขียนบทสปอยด้วย AI ในแอป — ผู้ใช้ทำที่อื่น (D21)
- ถอดอัตโนมัติหลังโหลด และคิวถอดหลายคลิป (D23, D24)
- คิวหลายลิงก์ (D6)
- playlist และช่องทั้งช่อง (D5)
- ลบ Temp clip อัตโนมัติ (D3)
- คลิป live (D11)
- คลิปที่ต้อง login หรือ cookies — ได้ error `login_required` (D15)
- ยกเลิกระหว่างรวมไฟล์ (D15)
- เว็บอื่นนอกจาก YouTube (D5)

## Open Questions

1. TTS ตัวไหนพูดไทยและใช้เชิงพาณิชย์ได้ เพื่อ supersede ADR-0007 — non-blocking: รอบนี้ไม่ใช้ TTS (D13)
2. เรื่องลิขสิทธิ์และ ToS ของ YouTube ก่อนเผยแพร่คลิปสปอยหารายได้ — non-blocking: ผู้ใช้รับความเสี่ยงไว้แล้วและจะกลับมาดูก่อนเผยแพร่ (D13)
3. legal ข้อ 2 (yt-dlp แก้ challenge ของ YouTube ตาม ม.53/4) เป็น UNVERIFIED — non-blocking: ผู้ใช้รับความเสี่ยงนี้ใน D13

4. ช่วงละ 300 วินาทีตัดคำที่คร่อมรอยต่อได้ทุก 5 นาที — non-blocking: เช็คตอน build seam 3; ตัดจนอ่านไม่รู้เรื่อง → เพิ่ม overlap ระหว่างช่วงเป็น `D{n}` ใหม่

## Sources

- [yt-dlp YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) — params `format_sort`, `merge_output_format`, `ffmpeg_location`, `js_runtimes`, `progress_hooks`, `paths`, `noplaylist` (accessed 2026-10-29)
- [yt-dlp README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) — `res` คือด้านสั้นของภาพ, ความหมายของ `res:1080` (accessed 2026-10-29)
- [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS) — ต้องมี JavaScript runtime, Deno ≥ 2.3.0, extra `default` (accessed 2026-10-29)
- [deno on PyPI](https://pypi.org/project/deno/) — wheel macOS arm64 และ Windows amd64, `find_deno_bin` (accessed 2026-10-29)
- [Starlette responses](https://www.starlette.io/responses/#fileresponse) — `FileResponse` รองรับ Range (accessed 2026-10-29)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — `get_ffmpeg_exe()` (accessed 2026-10-29)
