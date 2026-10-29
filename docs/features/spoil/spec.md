# Spec: spoil

ผู้ใช้วางลิงก์ YouTube ใน tab สปอย แล้วแอปโหลดคลิปมาเก็บเป็น Temp clip พร้อมหน้าต่างบอกว่าโหลดอะไรมา.

**Status:** ready-to-build

## Problem

ผู้ใช้ทำคลิปสปอยหนังจากคลิปบน YouTube แต่ framecraft ยังไม่มีทางเอาคลิปต้นทางเข้ามาในแอป. ต้องโหลดด้วยเครื่องมืออื่นแล้วจัดไฟล์เอง.

## Solution

- tab ด้านบนของแอปสลับระหว่าง สปอย กับ Setup status (D10)
- วางลิงก์ YouTube คลิปเดียว แล้วโหลดคลิปทุกแนวที่ด้านสั้นไม่เกิน 1080 px เป็น mp4 (D5)
- เห็น % ระหว่างโหลด และกดยกเลิกได้ (D6)
- เห็นรายการ Temp clip ที่โหลดมา เล่นดูในหน้าเว็บ และกดลบได้ (D3, D7)
- Setup script ติดตั้ง yt-dlp กับ Deno และ Status check บอกว่าติดตั้งครบไหม (D1, D8, D9)

## User Stories

**ผู้ทำคลิปสปอย**
1. As a ผู้ทำคลิปสปอย, I want สลับ tab สปอยกับ Setup status ได้จากด้านบน, so that ใช้งานและเช็คการติดตั้งในแอปเดียว (D10)
2. As a ผู้ทำคลิปสปอย, I want วางลิงก์ YouTube แล้วกดโหลด, so that คลิปต้นทางมาอยู่ในเครื่องพร้อมทำต่อ (D2, D5)
3. As a ผู้ทำคลิปสปอย, I want เห็น % ระหว่างโหลดและยกเลิกได้, so that รู้ว่าคลิปยาวยังเดินอยู่ และหยุดเมื่อวางลิงก์ผิด (D6)
4. As a ผู้ทำคลิปสปอย, I want เห็นรายการคลิปที่โหลดมาและเล่นดูได้, so that เช็คว่าได้คลิปถูกตัว (D7)
5. As a ผู้ทำคลิปสปอย, I want ลบคลิปที่ไม่ใช้, so that ดิสก์ไม่เต็ม (D3)
6. As a ผู้ทำคลิปสปอย, I want รู้ทันทีเมื่อวางลิงก์ที่โหลดไปแล้ว, so that ไม่โหลดซ้ำ (D12)
7. As a ผู้ทำคลิปสปอย, I want รู้ว่าทำไมโหลดไม่ได้และต้องแก้ยังไง, so that แก้เองได้ (D8, D11)

## Design

| Screen | User stories | Must show | Source |
|---|---|---|---|
| แถบ tab | 1 | tab "สปอย" และ "Setup status" ตามลำดับนี้, tab ที่เปิดอยู่เด่นกว่า (D10) | pending |
| tab สปอย | 2, 3, 6, 7 | ช่องลิงก์กับปุ่ม "โหลด"; ระหว่างโหลด: ชื่อคลิปเมื่อรู้แล้ว, แถบ % (ไม่รู้ขนาด → แถบไม่มีตัวเลข), ปุ่ม "ยกเลิก" (ซ่อนตอนรวมไฟล์), ปุ่มโหลด disabled (D6, D15); ข้อความ error ตาราง Frontend รวมเวอร์ชัน yt-dlp และคำสั่งอัปเดต (D8); ลิงก์ซ้ำ → highlight แถวเดิม (D12); ติดตั้งไม่ครบ → ข้อความกับลิงก์ไป Setup status แทนช่องลิงก์ (D9, D10); backend offline → ข้อความเดียวกับหน้า Setup status (setup-status D21) | pending |
| หน้าต่างรายการ Temp clip | 4, 5 | ใน tab สปอยใต้ช่องลิงก์; แถวใหม่สุดก่อน: thumbnail, ชื่อคลิป, ชื่อช่อง, ความยาว, ขนาดภาพกับแนว "ตั้ง" หรือ "นอน", ขนาดไฟล์, เวลาโหลด, ปุ่มลบพร้อมยืนยัน และ error เมื่อลบไม่ได้ (D7, D15); กดแถว → player เล่นคลิปนั้น (D7); state ว่าง: "ยังไม่มีคลิป วางลิงก์ YouTube ด้านบน" | pending |

ออกแบบใน Figma หลัง plan (setup-status D9) ในไฟล์เดียวกับหน้า Setup status.

## Expected Outcome

ผู้ใช้เอาคลิป YouTube เข้า framecraft ได้ในแอปเดียว โดยไม่ต้องใช้เครื่องมือโหลดอื่น.

- **วางลิงก์คลิปแนวตั้ง:** เห็น % เดินจนครบ แล้วคลิปขึ้นบนสุดของรายการ ขนาดภาพเป็นขนาดใหญ่สุดของต้นทางที่ด้านสั้นไม่เกิน 1080 (เช่น "1080×1920 ตั้ง" หรือ "720×1280 ตั้ง") (D5)
- **วางลิงก์หนังแนวนอนยาว 2 ชั่วโมง:** โหลดได้ ได้แถว "นอน" ที่ด้านสั้นไม่เกิน 1080
- **วางลิงก์ซ้ำ:** ไม่โหลด แถวเดิมถูก highlight
- **กดยกเลิกกลางทาง:** งานหยุด ไม่มีแถวใหม่ ไม่มีไฟล์ค้างใน `media/temp/.partial/`

**How success is judged:**
- บน Mac หลังรัน `./setup.sh`: หน้า Setup status มี 11 แถว รวม `yt_dlp` และ `deno` เป็น `ok`
- โหลด YouTube Shorts หนึ่งคลิปและคลิปแนวนอนยาวกว่า 1 ชั่วโมงหนึ่งคลิปได้จริง แต่ละไฟล์เล่นได้ใน player ของหน้าเว็บ
- ไฟล์ที่ได้เป็น mp4 และด้านสั้นไม่เกิน 1080 px
- restart `npm run dev` แล้วรายการเดิมยังอยู่ครบ
- ทำซ้ำสามข้อบนบน Windows NVIDIA หลังรัน `setup.cmd` (ADR-0006)

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
  - `backend.app`: include router ของ spoil, lifespan ที่ล้างไฟล์ค้างตอน start และตั้ง flag ยกเลิกตอน shutdown, `TrustedHostMiddleware` (D14, D15)
- **frontend**
  - `App`: แถบ tab; hook `useHashTab` ใน `lib/` อ่านและเขียน hash. ไม่มี folder `routes/` เพราะไม่ใช้ router (D10). บันทึกเรื่องนี้ใน skill `vite-react-web`
  - `features/spoil/` (folder ใหม่): ช่องลิงก์, แถบความคืบหน้า, รายการ Temp clip และ player (D6, D7)
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

ข้อที่ ticket 01 ต้องลองกับ YouTube จริงก่อนเขียนต่อ: ยกเลิกด้วย `DownloadCancelled` จาก hook ได้, merge ด้วย ffmpeg ของ imageio ที่ไม่มี ffprobe (ADR-0005) ได้, ลิงก์ upcoming ได้ error ที่แยกเป็น `live` ได้, และข้อความ error ของ bot check หรือ login ที่ใช้แยก `login_required`. ยกเลิกไม่ได้ → ย้ายการโหลดไป `multiprocessing.Process` แล้ว terminate. merge ไม่ได้ → หยุดแล้วถามผู้ใช้ก่อน เพราะ format ไฟล์เดียวบน YouTube ส่วนใหญ่ไม่ถึง 1080 (ขัด D5); ทางเลือกคือหา ffprobe มาเพิ่ม (ขัด ADR-0005) หรือยอมความคมต่ำลง; ผลเป็น `D{n}` ใหม่.

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

แยก error ของ yt-dlp (D15):

| เมื่อ | `code` |
|---|---|
| ข้อความ error มี "Sign in to confirm", "not a bot" หรือ "age" | `login_required` |
| `GeoRestrictedError` หรือข้อความมี "Private video", "unavailable", "removed" | `unavailable` |
| upcoming (ข้อ 3) | `live` |
| อื่นๆ ทั้งหมด รวม error ของ ffmpeg | `youtube_error` |

ticket 01 ยืนยันข้อความจริงกับ YouTube แล้วแก้ตารางนี้ถ้าต่าง.

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
- ลบ = ลบ `{id}.mp4` และ thumbnail ก่อน แล้ว `{id}.json` สุดท้าย; ลบ mp4 ไม่ได้ (Windows ที่ไฟล์ยังเปิดอยู่) → `409` `in_use` และไม่แตะ json (D15)
- backend start → ลบ `.partial/` ทั้งหมด และไฟล์ `{id}.*` ใน `media/temp/` ที่ไม่มี `{id}.json` (D15)

### API

ทุก path อยู่ใต้ `/api/spoil`. error body เป็น `{"code": "...", "message": "..."}`; `message` เป็นภาษาไทยพร้อมแสดงในหน้าเว็บ.

| Method | Path | Response |
|---|---|---|
| `GET` | `/clips` | `200` `{"clips": [Temp clip, ...]}` |
| `GET` | `/clips/{id}/video` | `200` หรือ `206` ไฟล์ `video/mp4` รองรับ Range; ไม่มี → `404` `not_found` |
| `GET` | `/clips/{id}/thumbnail` | `200` ไฟล์ thumbnail; ไม่มี → `404` `not_found` |
| `DELETE` | `/clips/{id}` | `204`; ไม่มี → `404` `not_found`; ไฟล์ถูกเปิดอยู่ → `409` `in_use` "ลบไม่ได้เพราะไฟล์ยังเปิดอยู่ ปิด player แล้วลองอีกครั้ง" |
| `POST` | `/downloads` | body `{"url": "..."}`. `202` กับ Download job. error: `503` `not_ready`, `400` `invalid_url`, `409` `duplicate` (body มี `clip_id` เพิ่ม), `409` `busy` |
| `GET` | `/downloads/current` | `200` Download job ล่าสุด หรือ `null` ถ้ายังไม่เคยมีตั้งแต่ backend start |
| `DELETE` | `/downloads/current` | `202` ตั้ง flag ยกเลิก; state เป็น `cancelled` เมื่อ thread หยุด (รอบ progress ถัดไป หรือหลัง `fetch_info` คืน); state `merging` → `409` `merging`; ไม่มีงานที่ยังไม่จบ → `404` `not_found` |

`{id}` ใน path ต้องตรงรูปแบบ id 11 ตัว ไม่งั้น `404` — กัน path traversal.

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

error ของงาน (`failed`):

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
| downloading | งานเป็น `checking`, `downloading` หรือ `merging` | "กำลังเช็คลิงก์…", "กำลังโหลด {title}" กับแถบ % หรือ "กำลังรวมไฟล์…"; ปุ่ม "ยกเลิก" ยกเว้นตอน `merging`; ปุ่มโหลด disabled (D6, D15) |
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
- ความยาวแสดงเป็น `h:mm:ss` หรือ `m:ss`; ขนาดไฟล์เป็น MB หรือ GB ทศนิยมหนึ่งตำแหน่ง; เวลาโหลดเป็นเวลาท้องถิ่น
- ข้อความในหน้าเป็นภาษาไทย

### Ops

- ที่ดิสก์: wheel `deno` ประมาณ 80 MB ใน `.venv`; คลิป 1080p ประมาณ 0.5–1.5 GB ต่อชั่วโมง ใน `media/temp/`
- ลบคลิปทั้งหมดด้วยมือได้โดยลบ folder `media/temp/` ตอน backend ไม่ได้รัน (README)
- YouTube เปลี่ยนแล้วโหลดไม่ได้ทุกคลิป → `uv lock --upgrade-package yt-dlp` แล้วรัน Setup script (D8, README)

## Seams

สาม seam: API ของสปอยกับ adapter ปลอม, adapter จริงกับ YouTube, และหน้าเว็บ — เพราะ yt-dlp กับ YouTube จริงช้าและเปลี่ยนตลอด จึงแยก adapter ไว้ตัวเดียวให้ส่วนอื่นทดสอบได้เร็ว (D14).

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
2. **yt-dlp adapter** `backend.spoil` กับ YouTube จริง (เช็คมือ ไม่อยู่ใน test ที่รันทุกครั้ง)
   - Shorts หนึ่งคลิป → mp4 ด้านสั้น ≤ 1080 และมีเสียง
   - คลิปแนวนอนยาวกว่า 1 ชั่วโมง → mp4 1920×1080 หรือเล็กกว่า
   - กดยกเลิกที่ประมาณ 30% → หยุดภายใน 5 วินาที ไม่มีไฟล์ค้าง
   - ลิงก์ live ที่ยังไม่เริ่ม → `live`
   - Ctrl+C ระหว่างโหลด แล้ว `npm run dev` ใหม่ → ไม่มี process ค้าง และ `.partial/` ว่าง
   - Windows: เล่นคลิปใน player แล้วกดลบ → ลบได้ หรือได้ `in_use` และแถวยังอยู่
3. **tab สปอย** `frontend` ด้วย Vitest และ fetch ปลอม
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

## Testing decisions

- **Copy:** `backend/tests/test_app.py` — `TestClient` กับ root ปลอมใน `tmp_path`
- **Copy:** `backend/tests/fakes.py` — เพิ่ม adapter ปลอมของ yt-dlp และ deno probe ปลอมที่นี่
- **Copy:** `backend/tests/test_checks.py` — test แถวใหม่ของ Status check และนับ 11 แถว
- **Copy:** `frontend/src/features/setup-status/components/SetupStatusPage.test.tsx` — fetch ปลอมและการ assert ข้อความ
- test ที่มีอยู่ซึ่งนับ 9 แถวต้องแก้เป็น 11
- test ที่เช็คการล้างไฟล์ตอน start ใช้ `with TestClient(app)` เพื่อให้ lifespan รัน; การล้างอ่าน `paths.ROOT` ตอนรัน จึง monkeypatch ได้
- `TestClient` ทุกตัวใช้ `base_url="http://127.0.0.1"` เพราะ host default `testserver` ไม่ผ่าน `TrustedHostMiddleware`; แก้ `backend/tests/test_app.py` ด้วย
- adapter ปลอมเรียก progress hook เองตามลำดับที่ test กำหนด และรอสัญญาณจาก test ได้ เพื่อทดสอบ busy และยกเลิกแบบไม่ขึ้นกับเวลา
- seam 2 ไม่อยู่ใน test อัตโนมัติ: พิสูจน์ด้วย How success is judged บน Mac และ Windows

## Out of Scope

- ตัดต่อ, ทำแนวตั้ง, เลือก p ของ output และ render (D2, D5)
- ใส่เสียงเล่าด้วย TTS และการเลือก TTS ที่ใช้เชิงพาณิชย์ได้ (D2, D13)
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

## Sources

- [yt-dlp YoutubeDL.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py) — params `format_sort`, `merge_output_format`, `ffmpeg_location`, `js_runtimes`, `progress_hooks`, `paths`, `noplaylist` (accessed 2026-10-29)
- [yt-dlp README › Sorting Formats](https://github.com/yt-dlp/yt-dlp#sorting-formats) — `res` คือด้านสั้นของภาพ, ความหมายของ `res:1080` (accessed 2026-10-29)
- [yt-dlp EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS) — ต้องมี JavaScript runtime, Deno ≥ 2.3.0, extra `default` (accessed 2026-10-29)
- [deno on PyPI](https://pypi.org/project/deno/) — wheel macOS arm64 และ Windows amd64, `find_deno_bin` (accessed 2026-10-29)
- [Starlette responses](https://www.starlette.io/responses/#fileresponse) — `FileResponse` รองรับ Range (accessed 2026-10-29)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — `get_ffmpeg_exe()` (accessed 2026-10-29)
