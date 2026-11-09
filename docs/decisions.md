# Decisions

Every decision in the project, by subject. Check here before asking a
question; the full entry is in the feature's decisions.md.

## สถาปัตยกรรม

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| React (Vite) เรียก Python ผ่าน FastAPI | [setup-status](features/setup-status/decisions.md) | D1 | — | [0001](adr/0001-one-python-backend.md) | active |
| โครงสร้าง `backend/` กับ `frontend/`, port 8000 และ 5173, bind `127.0.0.1`, Vite proxy `/api`, `npm run dev`, pytest และ Vitest, Tailwind | [setup-status](features/setup-status/decisions.md) | D10 | — | — | active |
| Conventions skill `fastapi-api` (backend) และ `vite-react-web` (frontend) | [setup-status](features/setup-status/decisions.md) | D14 | — | — | active |

## Python environment

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ต้องใช้ Node.js 22+ (`concurrently` 10, Vite 8) | [setup-status](features/setup-status/decisions.md) | D22 | — | — | active |
| ใช้ uv และ pin Python 3.12 ใน `.venv` ของ project | [setup-status](features/setup-status/decisions.md) | D2 | — | — | active |
| รองรับ Mac Apple Silicon (MPS) และ Windows NVIDIA (CUDA 12.8), torch 2.8.0 | [setup-status](features/setup-status/decisions.md) | D5 | — | [0006](adr/0006-supported-platforms.md) | changed by setup-status D25 |
| feature จบได้เมื่อผ่านบน Mac; เช็คมือบน Windows เป็น ticket ใน `windows-check` | [setup-status](features/setup-status/decisions.md) | D25 | spoil, windows-check, spoil-maker | [0014](adr/0014-mac-first-windows-check.md), [0016](adr/0016-single-os-library-ports-separately.md) | active |

## การติดตั้ง

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| Portable = ก๊อป folder แล้วรัน setup ซ้ำ, ทุกอย่างอยู่ใน project | [setup-status](features/setup-status/decisions.md) | D12 | — | [0003](adr/0003-everything-inside-project.md) | active |
| กฎ red team: `setup.cmd` สำหรับ Windows, pin revision โมเดล, `cache_dir` ชัดเจน, lock และเช็คดิสก์, torchaudio cu128 | [setup-status](features/setup-status/decisions.md) | D13 | — | [0003](adr/0003-everything-inside-project.md), [0004](adr/0004-pinned-model-registry.md) | active |
| ติดตั้งด้วย script บน terminal, เว็บแค่แสดงสถานะ | [setup-status](features/setup-status/decisions.md) | D3 | — | [0002](adr/0002-install-only-in-setup.md) superseded by [0008](adr/0008-runtime-media-download.md) | active |
| `setup.sh` กับ `setup.ps1` บางๆ เรียก `backend.setup` ตัวเดียว | [setup-status](features/setup-status/decisions.md) | D8 | — | [0002](adr/0002-install-only-in-setup.md) superseded by [0008](adr/0008-runtime-media-download.md) | active |
| เช็ค PID ของ setup lock: `os.kill(pid, 0)` บน Mac, `OpenProcess` บน Windows | [setup-status](features/setup-status/decisions.md) | D17 | — | — | active |
| จุด inject สำหรับ test: probe, `download`, `backend_running`, `free_bytes`, `DeviceProbe` | [setup-status](features/setup-status/decisions.md) | D18 | spoil, windows-launch | — | active |
| `setup.cmd` หยุดรอเมื่อดับเบิลคลิกและคืน code page, `setup.ps1` เช็ค `$LASTEXITCODE` ไม่ใช้ `Stop`, ติดตั้ง uv ใน PowerShell ลูกที่ Bypass, CRLF, `run_checks` รับ `sys_platform` | [setup-status](features/setup-status/decisions.md) | D23 | — | — | active |
| `npm run dev` start backend ด้วย Python ใน `.venv` ผ่าน `scripts/dev-api.mjs` ไม่พึ่ง uv ใน PATH; README ติดตั้งและใช้งานเป็นไทย | [setup-status](features/setup-status/decisions.md) | D24 | — | — | active |
| Status check เป็น checklist 9 รายการ ไม่โหลดโมเดล ไม่ใช้ network | [setup-status](features/setup-status/decisions.md) | D7 | spoil, windows-launch | [0004](adr/0004-pinned-model-registry.md) | extended by spoil D9 |
| Status check เพิ่มแถว `yt_dlp` และ `deno` เป็น 11 แถว; tab คลิป gate งานโหลดด้วยแถว `yt_dlp`, `deno`, `ffmpeg` ไม่ใช้ `ready` (แต่ละ tab gate เฉพาะแถวที่ใช้, spoil-maker D53) | [spoil](features/spoil/decisions.md) | D9 | — | [0009](adr/0009-status-check-single-place.md) | active |

## ffmpeg

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ffmpeg มาจาก `imageio-ffmpeg` ใน venv, หา path ด้วย `get_ffmpeg_exe()` ไม่พึ่ง PATH | [setup-status](features/setup-status/decisions.md) | D4 | — | [0005](adr/0005-ffmpeg-from-imageio.md) | active |

## โมเดล AI

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| เก็บโมเดลใน `models/` ของ project ผ่าน `HF_HOME` | [setup-status](features/setup-status/decisions.md) | D6 | — | [0003](adr/0003-everything-inside-project.md) | changed by D13 |
| ใช้ OmniVoice แบบไม่หารายได้เท่านั้น, แสดง license | [setup-status](features/setup-status/decisions.md) | D11 | spoil-maker | [0007](adr/0007-non-commercial-use.md), [0017](adr/0017-non-commercial-no-forced-credit.md) | active |
| revision ที่ pin และ `allow_patterns` ของ OmniVoice และ Whisper | [setup-status](features/setup-status/decisions.md) | D16 | spoil | [0004](adr/0004-pinned-model-registry.md) | active |
| ยังไม่คิดเรื่อง license รอบแรก ใช้ OmniVoice ไปก่อน แล้วค่อยเปลี่ยนตัวแทนเมื่อจะหารายได้ | [spoil-maker](features/spoil-maker/decisions.md) | D3 | — | [0007](adr/0007-non-commercial-use.md), [0019](adr/0019-saved-voice-tied-to-tts-model.md) | changed by spoil-maker D41 |

## UI design

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| แถบ tab บน: สปอย (`#/spoil`), Setup status (`#/setup`), default Setup status, ไม่ใช้ router library | [spoil](features/spoil/decisions.md) | D10 | — | — | changed by spoil-maker D53 |
| แถบ tab บน 3 tab: ติดตั้ง (`#/setup`) · คลิป (`#/clips`) · สปอย (`#/spoil`) default ติดตั้ง; tab สปอยเป็น 3 ขั้น `#/spoil` → `#/spoil/review` → `#/spoil/renders`; แต่ละ tab gate เฉพาะแถว Status check ที่ใช้ | [spoil-maker](features/spoil-maker/decisions.md) | D53 | story-kb | — | changed by spoil-maker D68; changed by story-kb D9 |
| ออกแบบหน้าจอใน Figma หลัง plan | [setup-status](features/setup-status/decisions.md) | D9 | spoil, story-kb, windows-launch | — | active |
| แถวที่ไม่ `ok` แสดง `fix` จาก API ค่าเดียวเป็น chip พร้อมปุ่ม copy ไม่แสดงคำสั่งทั้งสอง OS | [setup-status](features/setup-status/decisions.md) | D15 | — | — | active |
| font มากับ `@fontsource` ใน project ไม่โหลดจาก CDN | [setup-status](features/setup-status/decisions.md) | D19 | — | [0003](adr/0003-everything-inside-project.md) | active |
| `fix` ไม่มีช่องว่าง = คำสั่ง (chip กับปุ่ม copy), มีช่องว่าง = ข้อความ | [setup-status](features/setup-status/decisions.md) | D20 | spoil | — | changed by setup-status D26 |
| API ส่ง `fix_kind` (`command`/`hint`) คู่ `fix`; probe รวมเป็น `Probes`; แถว Python บอกสาเหตุให้ตรง | [setup-status](features/setup-status/decisions.md) | D26 | spoil | — | active |
| รายละเอียดหน้า Setup status: Refresh จาก offline, เวลาเช็คล่าสุด, pill คำเตือน, icon จาก Figma, timeout | [setup-status](features/setup-status/decisions.md) | D21 | spoil | — | active |

## ดาวน์โหลดสื่อ

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| Backend โหลดสื่อตามลิงก์ที่ผู้ใช้ใส่ได้ตอนรัน, package และโมเดลยังผ่าน Setup script เท่านั้น (แคบ ADR-0002) | [spoil](features/spoil/decisions.md) | D1 | — | [0008](adr/0008-runtime-media-download.md) | active |
| รอบแรกของสปอยทำแค่โหลดคลิป YouTube เป็น temp; ปลายทางคือคลิปสปอยหนังพร้อมเสียงเล่า OmniVoice | [spoil](features/spoil/decisions.md) | D2 | — | — | active |
| Temp clip เก็บใน `media/temp/` ของ project จนผู้ใช้กดลบเอง | [spoil](features/spoil/decisions.md) | D3 | — | — | active |
| Temp clip = `{id}.mp4` + `{id}.json` (เขียนสุดท้าย) + thumbnail; ไฟล์ค้างใน `.partial/` ล้างตอน start; Download job อยู่ใน memory | [spoil](features/spoil/decisions.md) | D14 | spoil-maker | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| คลิปแนวตั้งแบบ reels เท่านั้น, ด้านสั้น ≤ 720 px, mp4 | [spoil](features/spoil/decisions.md) | D4 | — | — | superseded by spoil D5 |
| รับคลิป YouTube ทุกแนว, temp ด้านสั้น ≤ 1080 px mp4; output แนวตั้งเลือก p ได้ถึง 1080 (รอบหน้า) | [spoil](features/spoil/decisions.md) | D5 | — | — | changed by spoil D47 |
| ลิงก์คลิปเดียวจากทุกเว็บที่ yt-dlp โหลดได้แบบสาธารณะ ไม่ใช้ cookies; ที่เหลือผู้ใช้โหลดเองแล้วเลือกไฟล์ในเครื่อง | [spoil](features/spoil/decisions.md) | D47 | — | [0029](adr/0029-media-links-dedicated-extractors-only.md) | active |
| ไฟล์ในเครื่องรับทุกชนิดที่ ffmpeg อ่านได้, copy เข้า Temp clip; mp4 h264/aac ≤ 1080 copy ตรง นอกนั้นแปลง (มี %, ยกเลิกได้) | [spoil](features/spoil/decisions.md) | D48 | — | [0005](adr/0005-ffmpeg-from-imageio.md) | superseded by spoil D49 |
| ไฟล์ในเครื่องรับแค่ mp4 h264/aac ≤ 1080 copy ตรง ไม่แปลง; ไม่ตรง → error ให้ผู้ใช้แปลงเอง | [spoil](features/spoil/decisions.md) | D49 | — | [0027](adr/0027-temp-clip-one-format-owned-copy.md) | active |
| เลือกไฟล์/ลากวางในเว็บ ส่ง body ดิบ `application/octet-stream`; ADR-0013 ขยายรับ octet-stream | [spoil](features/spoil/decisions.md) | D50 | — | [0013](adr/0013-post-requires-json.md), [0028](adr/0028-raw-file-upload-per-route.md) | active |
| คลิปซ้ำชี้แถวเดิม: ลิงก์ = เว็บ+id, ไฟล์ = ชื่อ+ขนาด; id: YouTube 11 ตัวเดิม, `{extractor}-{id}`, `local-{sha1}` ตรง `[A-Za-z0-9_-]{1,64}` | [spoil](features/spoil/decisions.md) | D51 | — | — | active |
| ทางเลือกเล็ก: กันลิงก์ localhost/private, error `unsupported`/`playlist`/`download_error`, File import เป็น request เดียวส่งไฟล์ดิบ, ทีละงานกับ Download job, แถว "ไฟล์ในเครื่อง" | [spoil](features/spoil/decisions.md) | D52 | — | — | active |
| ยอมรับความเสี่ยงลิขสิทธิ์และ ToS ของเว็บอื่นและไฟล์ในเครื่องแบบ D13 (Accepted risk) | [spoil](features/spoil/decisions.md) | D53 | — | — | active |
| คลิปจากเว็บต้อง h264/aac ด้านสั้น ≤ 1080 (format selector + ตรวจหลัง merge) ไม่งั้น `unsupported_format` | [spoil](features/spoil/decisions.md) | D54 | — | [0027](adr/0027-temp-clip-one-format-owned-copy.md) | active |
| red team: ปิด generic extractor, id+hash (ตัวพิมพ์และการล้างตอน start แก้ใน D59), upload ค้าง 60 วิ, thread, yuv420p/rotation, `CLIP_ID` ทุกที่, model nullable | [spoil](features/spoil/decisions.md) | D55 | — | [0028](adr/0028-raw-file-upload-per-route.md), [0029](adr/0029-media-links-dedicated-extractors-only.md) | active |
| ทางเลือกเล็กตอน build โหลดหลายเว็บ: "No suitable extractor" เป็น `unsupported`, คำ login ของเว็บอื่น, format ไม่บอก codec ให้ตัวตรวจไฟล์ตัดสิน, ขนาดภาพจากไฟล์, thumbnail `.image` | [spoil](features/spoil/decisions.md) | D56 | — | [0027](adr/0027-temp-clip-one-format-owned-copy.md) | active |
| ทางเลือกเล็กตอน build เอาไฟล์ mp4 เข้า: ข้อความของ API, `name`/`size` ที่ไม่ถูก, `require_json` ข้าม route ที่มี `require_octet_stream` (`backend/body_types.py`), `ClientDisconnect` ตอบเงียบ, flag ใน `Downloads`, เขียนทีละ 1 MiB, thumbnail ว่างเป็น `null` | [spoil](features/spoil/decisions.md) | D57 | — | [0013](adr/0013-post-requires-json.md), [0028](adr/0028-raw-file-upload-per-route.md) | active |
| ทางเลือกเล็กตอน build ปุ่มเลือกไฟล์: ทั้งกล่องเป็นปุ่ม "เลือกไฟล์ในเครื่อง", วางไฟล์ได้ทั้งกล่องลิงก์ กัน browser เปิดไฟล์, ข้อความช่องเดียว, `emphasis` หลัง `unsupported`/`login_required`/`unsupported_format`, `sendFile` ไม่มี timeout | [spoil](features/spoil/decisions.md) | D58 | — | [0028](adr/0028-raw-file-upload-per-route.md) | active |
| feature review หลายเว็บและเอาไฟล์เข้า: id เว็บอื่นตัวเล็ก + hash เมื่อมีตัวใหญ่, ล้างตอน start เฉพาะ `{site}` ที่ yt-dlp รู้จัก, ชื่อ `ffmpeg.input_info`/`NOT_MP4_CONTAINER`/`ONLY_MP4`/`clip_id` | [spoil](features/spoil/decisions.md) | D59 | — | — | active |
| โหลดทีละคลิปเป็นงานเบื้องหลัง, poll % ทุก 1 วินาที, ยกเลิกได้, ไม่มีคิว | [spoil](features/spoil/decisions.md) | D6 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| หน้าต่างรายการ temp clip: thumbnail, ชื่อ, ช่อง, ความยาว, ขนาดภาพ/แนว, ขนาดไฟล์, เวลาโหลด, ลบ, เล่นในหน้าเว็บ | [spoil](features/spoil/decisions.md) | D7 | — | — | extended by D25 |
| ยอมรับความเสี่ยงลิขสิทธิ์และ ToS ของ YouTube; หารายได้ขัด ADR-0007 ต้องเปลี่ยน TTS ก่อน feature เสียง | [spoil](features/spoil/decisions.md) | D13 | — | — | active |
| red team: ยกเลิกต่อ state (merging ยกเลิกไม่ได้), lock กัน POST ซ้อน, ลบ mp4 ก่อน json, `in_use`, แยก error `login_required`, `TrustedHostMiddleware` | [spoil](features/spoil/decisions.md) | D15 | spoil-maker | [0011](adr/0011-trusted-host-only.md) | active |
| แยก error ของ yt-dlp ตามข้อความจริง: live ที่ยังไม่เริ่ม = "This live event will begin", ไม่ใช้คำ "age" เดี่ยวๆ | [spoil](features/spoil/decisions.md) | D16 | — | — | active |
| ทางเลือกเล็กของงานโหลด: gate เรียก probe ใน `backend.checks`, adapter รับ `ProjectPaths`, busy เช็คจาก state | [spoil](features/spoil/decisions.md) | D17 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| ของบนจอที่ design เพิ่ม: หัวรายการพร้อมจำนวน, badge "กำลังเล่น", ข้อความแทนปุ่มยกเลิกตอน merging | [spoil](features/spoil/decisions.md) | D18 | — | — | active |
| ทางเลือกเล็กของ tab: tab เป็นลิงก์ hash, `PageLayout` ร่วม, `useCopy`, tone ของข้อความ, code ที่ไม่รู้จัก = offline, ปุ่ม "Copy" ตาม Figma | [spoil](features/spoil/decisions.md) | D19 | — | — | changed by spoil-maker D53 |
| ซับ layout A ทีละท่อนราว 2–4 คำ (ตัดคำไทย) เวลาแบ่งตามจำนวนตัวอักษรของเสียงประโยค | [spoil-maker](features/spoil-maker/decisions.md) | D20 | toon | — | active |
| ข้อความบนวิดีโอใช้ font Kanit (OFL) ตัวเดียว ไฟล์ ttf ใน project โหลดผ่าน Setup script มีแถว Status check | [spoil-maker](features/spoil-maker/decisions.md) | D21 | toon | [0003](adr/0003-everything-inside-project.md), [0009](adr/0009-status-check-single-place.md) | active |
| สี ขนาด และตำแหน่งของข้อความตายตัวต่อ layout ตามคลิปตัวอย่าง ไม่มีตัวเลือกในรอบแรก | [spoil-maker](features/spoil-maker/decisions.md) | D22 | — | — | active |
| watermark เป็นข้อความชื่อช่องพิมพ์ครั้งเดียว แอปจำไว้ ว่าง = ไม่แสดง | [spoil-maker](features/spoil-maker/decisions.md) | D23 | — | — | superseded by spoil-maker D41 |
| ลายน้ำข้อความหลายอัน เลือก 6 ตำแหน่งและขนาดเล็กหรือกลาง แอปจำไว้; ไม่บังคับเครดิตโมเดล (Accepted risk) | [spoil-maker](features/spoil-maker/decisions.md) | D41 | — | [0017](adr/0017-non-commercial-no-forced-credit.md) | changed by spoil-maker D51, D64 |
| ภาพเปลี่ยนแบบตัดตรงทุก layout ไม่มี transition หรือภาพเลื่อน ซ้อน เอียง | [spoil-maker](features/spoil-maker/decisions.md) | D24 | — | — | active |
| ทางเลือกเล็กของรายการ Temp clip: คลิปมีอยู่ = มี json, ลบ json ที่ mp4 หาย, เรียงตามเวลาจริง, ลบได้ 404 = แถวหาย, highlight มาจากข้อความ, `useMountedState`, `autoPlay` | [spoil](features/spoil/decisions.md) | D20 | — | — | active |
| ลิงก์ซ้ำ (video id เดิม) ไม่โหลดใหม่ ชี้แถวเดิม | [spoil](features/spoil/decisions.md) | D12 | — | — | extended by spoil D51 |
| ไม่จำกัดความยาว, ปฏิเสธ live, เช็คดิสก์ว่าง ≥ ขนาดประมาณ + 1 GB ก่อนโหลด | [spoil](features/spoil/decisions.md) | D11 | — | — | active |
| `yt-dlp[default]` และ `deno` (PyPI wheel) pin ใน `uv.lock`; โหลดพังแสดงเวอร์ชันและคำสั่งอัปเดต | [spoil](features/spoil/decisions.md) | D8 | — | — | active |

## ถอดบทพูด

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ถอดคำพูดของ Temp clip ด้วย Whisper large-v3-turbo ที่ติดตั้งแล้ว ตรวจภาษาเอง; ได้ Transcript อย่างเดียว ไม่แยกไฟล์เสียงให้ผู้ใช้ | [spoil](features/spoil/decisions.md) | D21 | spoil-maker | — | active |
| แสดง Transcript ทีละบรรทัดพร้อมเวลา กดแล้ว player กระโดด, Copy ทั้งหมด, โหลด `.txt` และ `.srt` | [spoil](features/spoil/decisions.md) | D22 | — | — | active |
| ถอดเมื่อผู้ใช้กดเท่านั้น, Transcript เก็บคู่ Temp clip ข้าม restart, แถวแสดง "ถอดแล้ว", ลบคลิปลบ Transcript | [spoil](features/spoil/decisions.md) | D23 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| Transcribe job ทีละงาน ไม่มีคิว, รันพร้อม Download job ได้, poll % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D24 | spoil-maker | [0015](adr/0015-one-gpu-slot.md) | changed by spoil-maker D45 |
| tab คลิปสองคอลัมน์ (เดิม tab สปอย): รายการคลิป → ลูกศร → กล่องถอดบทพูด (player ย้ายเข้ากล่อง), 375px เรียงบนลงล่าง | [spoil](features/spoil/decisions.md) | D25 | — | — | changed by spoil-maker D53 |
| ไม่จำกัดเวลาถอด ต้องเห็น % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D26 | — | — | active |
| กติกางานถอด: ดึงเสียงด้วย ffmpeg ของ imageio เข้า memory, โหลด Whisper จาก snapshot แล้วปล่อยหลังงาน, ช่วงละ 5 นาที, gate 5 แถว, ลบคลิประหว่างถอด `409`, `{id}.transcript.json` | [spoil](features/spoil/decisions.md) | D27 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | changed by D28, D29 |
| งานถอดรันใน process ลูก `spawn`, thread ใน backend ถือสถานะ, ยกเลิก = terminate, ตายไม่ส่งผล = `crashed` | [spoil](features/spoil/decisions.md) | D28 | — | [0012](adr/0012-gpu-jobs-in-child-process.md) | active |
| red team งานถอด: `internal` + `finally`, ffmpeg ทีละช่วง, long-form ไม่ใช้ `chunk_length_s`, ช่วงท้าย < 30 วินาทีรวม, `language` null ได้, lock ร่วมกับลบ, ข้าม `*.transcript.json`, POST ต้อง JSON (`415`) | [spoil](features/spoil/decisions.md) | D29 | — | [0013](adr/0013-post-requires-json.md) | active |
| ทางเลือกเล็กตอน build งานถอด: `float32` บน `mps`, ชื่อภาษา → code, ตัดเวลาจบที่จบช่วง, gate ใช้ check เดียวกับ Status check, `415` เป็น router dependency, terminate → kill หลัง 5 วินาที | [spoil](features/spoil/decisions.md) | D30 | — | [0012](adr/0012-gpu-jobs-in-child-process.md), [0013](adr/0013-post-requires-json.md) | active |
| ไม่กรองบรรทัดที่ Whisper แต่งในช่วงไม่มีคำพูด ผู้ใช้ลบเอง | [spoil](features/spoil/decisions.md) | D31 | — | — | active |
| ยอมรับเวลาบรรทัดตาม Whisper long-form แม้บางบรรทัดคลาด 2–3 วินาที | [spoil](features/spoil/decisions.md) | D32 | — | — | active |
| ของบนจอที่ design ของกล่องถอดเพิ่ม: ช่องลิงก์อยู่คอลัมน์ซ้าย, ข้อความหลังงานถอดเป็น Alert ในกล่อง, แถบ % แบบ Download progress, Transcript ว่างไม่มีปุ่ม Copy/ไฟล์; อยู่ใน tab คลิป | [spoil](features/spoil/decisions.md) | D33 | — | — | changed by spoil-maker D53 |
| ทางเลือกเล็กตอน build กล่องถอด: คลิปที่เลือกอยู่กับ `useTranscribe`, status GET ครั้งเดียว, `busy` → GET current, ลบคลิปที่กำลังถอดไม่ปลด player, ซ่อน Transcript ระหว่างถอดใหม่, ไม่ autoPlay เมื่อเลือกเพราะงาน, `PageLayout wide` | [spoil](features/spoil/decisions.md) | D34 | — | — | changed by spoil-maker D53 |
| แก้จาก feature review: gate สองงานผ่าน `require_rows`, `JobFailed`, `write_atomic`, `jobs.py` → `downloads.py`, `features/spoil/lib/`, งานโหลดไม่หลุดเมื่องานถอดได้ 503 | [spoil](features/spoil/decisions.md) | D35 | — | — | active |
| แก้ข้อความ Transcript ทีละบรรทัดใน tab คลิป (เวลาและจำนวนบรรทัดไม่เปลี่ยน), `edited: true`, `PATCH .../transcript/lines/{n}`; ถอดใหม่ต้องยืนยัน (`has_edits`); `.txt` `.srt` token Draft job ใช้ข้อความที่แก้ | [spoil-maker](features/spoil-maker/decisions.md) | D54 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| ทางเลือกเล็กตอน build แถบ 3 tab และแก้ Transcript: `ClipsPage`/`SpoilMakerPage`, `useHash.ts`, `#/spoil/…` ไม่รู้จัก = ขั้น 1, `clip_users` ของ `clip_busy`, `PATCH` ต้องเป็น JSON, ข้อความแก้เป็นบรรทัดเดียว, ปุ่ม "แก้" แสดงตลอดบนจอสัมผัส, error ใต้ช่องแก้ | [spoil-maker](features/spoil-maker/decisions.md) | D55 | — | [0013](adr/0013-post-requires-json.md) | active |
| ทางเลือกเล็กตอน build ติดตั้ง Qwen, ช่อง GPU และดูภาพ: แถว `model_qwen`/`mlx_vlm` หลัง `device`, `ModelSpec.platforms`, `not_ready` มี `rows` (id), `ApiError`/`backend.jobs` ใช้ร่วม, `GpuSlot.clip_untouched`, ลำดับการเช็ค, ไฟล์ของ `spoil_maker`, ภาพเล็ก ffmpeg `-q:v 5`, `404` `not_found` ทั้งแอป, ยืนยันดูภาพใหม่ในแถว | [spoil-maker](features/spoil-maker/decisions.md) | D56 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| เฟรมที่ Qwen บรรยายกว้าง 448 (เดิม 640): หนัง 96 นาทีจบใน 52.7 นาทีแทน 64 นาทีบน M2 | [spoil-maker](features/spoil-maker/decisions.md) | D57 | — | — | active |
| คำบนจอ "ดูภาพ" → "บรรยายฉาก", "กำลังแบ่งฉาก", บรรทัดอธิบายใต้ปุ่ม | [spoil-maker](features/spoil-maker/decisions.md) | D58 | — | — | active |
| ทางเลือกเล็กตอน build Saved voice: env `PYTHAINLP_DATA`, แถว `pythainlp` หลัง `mlx_vlm`, นับตัวอักษรไม่นับช่องว่างและวรรคตอน, ประโยคล็อกใช้ประโยคตัวอย่าง, process ลูกส่งเสียงและ prompt เป็น bytes, state `voicing`, `gpu.Kind` `voice`, `#/spoil/voices` ไม่มีตัวบอกขั้น, `lib/` ใช้ร่วมของหน้าเว็บ | [spoil-maker](features/spoil-maker/decisions.md) | D59 | — | [0012](adr/0012-gpu-jobs-in-child-process.md) | active |
| ทางเลือกเล็กตอน build ร่างบทและหน้าตรวจแก้: `draft_file` แยกจาก `draft`, `gpu.slot.draft_lock` และ `take(locks_draft=True)`, `jobs.ModelJobSlot`, ลำดับการเช็คของ Draft job, เลือก Shot ใกล้ ref แรก, `components/ui/Alert`, `lib/clips`, ลิงก์จัดการเสียง, แทรก "ประโยคใหม่", คำเตือน Spoil draft ในแถวคลิป | [spoil-maker](features/spoil-maker/decisions.md) | D60 | — | [0012](adr/0012-gpu-jobs-in-child-process.md), [0015](adr/0015-one-gpu-slot.md) | active |
| เลือก Shot ส่งให้ AI ไม่เกิน 40 Shot ที่ใกล้ ref แรก; temperature ร่างบท 0.3; คำสั่งร่างบทบอกกฎซ้ำหลัง Transcript พร้อมตัวอักษรต่อประโยค, ครั้งที่ 2–3 บอกว่าครั้งก่อนพลาดตรงไหน, ประโยคเก็บ ref 3 ตัวแรก | [spoil-maker](features/spoil-maker/decisions.md) | D61 | — | — | active |
| ทางเลือกเล็กตอน build เสียงต่อประโยคและ render: `backend.fonts` และ marker `font_kanit`, ลำดับการเช็คของ Voice job `sentences` และ Render job, `SentenceVoicer`, ไฟล์กลาง mkv และจุดตัดตามเฟรม, `spoil_maker.ffmpeg`, style ของ ASS, ซับ A คำเดียวได้, render เสร็จเปิดผล render, ภาพเล็กจาก mp4, player panel ≥ 1024 | [spoil-maker](features/spoil-maker/decisions.md) | D62 | — | [0005](adr/0005-ffmpeg-from-imageio.md), [0015](adr/0015-one-gpu-slot.md) | active |
| แก้จาก feature review: `10:30 น.` อ่านเป็นนาฬิกา, `audio.wav` `no-store`, พื้นเบลอ A ย่อ-เบลอ-ขยาย, error ของ framework เป็น `{code, message}`, `ModelJobSlot._run_job`, `backend.gate_rows`, `RefusalLine` | [spoil-maker](features/spoil-maker/decisions.md) | D63 | — | [0013](adr/0013-post-requires-json.md) | active |
| ลายน้ำเปิดปิดได้ทีละอัน (`enabled`, ปิดแล้วจำไว้); หน้าตรวจแก้เตือนเมื่อลายน้ำ `top_center` ที่เปิดอยู่ทับ hook (A) หรือชื่อตอน (C) | [spoil-maker](features/spoil-maker/decisions.md) | D64 | — | — | active |
| ทางเลือกเล็กตอน build ลายน้ำเปิดปิดและงานค้างจาก review: `PATCH` ไม่มี `enabled` = เปิด, สวิตช์ `role="switch"`, คำเตือนใต้ช่อง hook ตามที่พิมพ์, `RenderJobs(run_ffmpeg=...)`, `JOB_HOLDERS`, icon ใช้ร่วมใน `components/ui/assets/` | [spoil-maker](features/spoil-maker/decisions.md) | D65 | — | — | active |

## ตัดช่วงคลิป

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ตัดช่วงออกจาก Temp clip ด้วย ffmpeg encode mp4 ใหม่แทนไฟล์เดิม ไม่เก็บต้นฉบับ; Mac `h264_videotoolbox`, Windows `libx264`, เสียง `aac`; ไม่จองช่อง GPU | [spoil](features/spoil/decisions.md) | D36 | — | [0020](adr/0020-temp-clip-mp4-replaced-by-trim.md) | active |
| ตัดคลิปที่มี Transcript, Shot, การตัด EP หรือ Spoil draft: เตือน ยืนยันครั้งเดียว (`confirm_derived_loss`) แล้วลบทั้งหมด | [spoil](features/spoil/decisions.md) | D37 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| เลือกช่วงตัดบน timeline ใต้ player ในกล่องขวาของ tab คลิป: ลากหัวท้าย, พิมพ์เวลา, ตั้งจากตำแหน่งเล่น, เพิ่มช่วง, ความยาวที่เหลือ | [spoil](features/spoil/decisions.md) | D38 | — | — | active |
| ตัดช่วงแทนการซ่อนบรรทัด Transcript (เลิก spoil-maker D90, D91, D94, D95 เลขของ branch `feat/spoil-maker-transcript-remove`); D92, D93 ยังทำ — D92 ลง develop เป็น spoil-maker D90 | [spoil](features/spoil/decisions.md) | D39 | — | — | active |
| ส่วนตัดช่วงออกแบบใน Figma หลังแผน (`pending`) | [spoil](features/spoil/decisions.md) | D40 | — | — | active |
| กติกาของ Trim job: ทีละงาน, `clip_busy` สองทาง, 1–20 ช่วง เหลือ ≥ 10 วินาที, bitrate จากไฟล์เดิม, marker `{id}.trimming.json`, `in_use` บน Windows, `?v=` ของ player, เช็คดิสก์ | [spoil](features/spoil/decisions.md) | D41 | — | [0020](adr/0020-temp-clip-mp4-replaced-by-trim.md) | active |
| ข้อแก้ Breaker ตัดช่วง: ความยาวจาก `probe`, ลบ draft หลัง lock ของ slot, `GpuSlot.trimming_clip`, ตรวจไฟล์ผลก่อนแทน, `os.replace` ลองซ้ำ 10 วินาที | [spoil](features/spoil/decisions.md) | D42 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| Trim job รับตัวปลอมผ่าน `Trims(…)`; ffmpeg เป็น `backend/ffmpeg.py`; ลอง `os.replace` ซ้ำโดยไม่ถือ lock | [spoil](features/spoil/decisions.md) | D43 | — | — | active |
| แบบส่วนตัดช่วงใน Figma: ปุ่ม "= ตอนนี้" ใต้ช่องเวลา, Badge "ตัดแล้ว", Alert ใต้ชื่อคลิป, `confirm()` ของ browser | [spoil](features/spoil/decisions.md) | D44 | — | — | active |
| ส่วนตัดช่วงในหน้าเว็บ: ความยาวจาก `video.duration` ปัดลง 0.1 วินาที, ช่วงสั้นกว่า 0.5 วินาทีเป็น error, `busy` ติดตามงาน, `?v=` ของ Shot picker, `SECONDARY_BUTTON` | [spoil](features/spoil/decisions.md) | D45 | — | — | active |
| feature review ของงานตัดช่วง: พื้น bitrate 300 kbps, `has_derived` เป็นคำถามเต็มและถามหลัง `POST`, `busy` ก่อน `clip_busy`, `GET /clips/{id}` | [spoil](features/spoil/decisions.md) | D46 | — | [0020](adr/0020-temp-clip-mp4-replaced-by-trim.md) | active |

## สร้างคลิปสปอย

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| สร้างคลิปสปอยเป็น feature ใหม่ `spoil-maker` ใน tab สปอย ใช้ Temp clip กับ Transcript ของ spoil | [spoil-maker](features/spoil-maker/decisions.md) | D1 | — | — | changed by spoil-maker D53 |
| ทุกอย่างต้องฟรี: โมเดลและโปรแกรมในเครื่อง ไม่มี API ที่ต้องจ่าย | [spoil-maker](features/spoil-maker/decisions.md) | D2 | — | — | active |
| AI ในเครื่องร่างบทสปอยจาก Transcript แล้วผู้ใช้แก้ทุกประโยคได้ก่อนสร้างเสียง | [spoil-maker](features/spoil-maker/decisions.md) | D4 | — | — | active |
| คลิปสปอยหนึ่งคลิปทำจาก Temp clip ที่ถอดแล้วได้หลาย EP เรียงลำดับเอง | [spoil-maker](features/spoil-maker/decisions.md) | D5 | — | — | superseded by spoil-maker D66 |
| เสียงบรรยายจาก OmniVoice เลือกเสียงตัวอย่างหรือ clone จากไฟล์เสียงสั้นได้ ใช้ซ้ำทุกคลิป | [spoil-maker](features/spoil-maker/decisions.md) | D6 | — | [0007](adr/0007-non-commercial-use.md) | changed by spoil-maker D48 |
| เลือก preset สไตล์ 3 แบบตามคลิปตัวอย่าง แล้วใส่ความยาวเป้าหมายเป็นวินาที | [spoil-maker](features/spoil-maker/decisions.md) | D7 | — | — | active |
| layout 3 แบบตามคลิปตัวอย่าง เลือกแยกจากสไตล์ ทุกแบบได้ 1080×1920 | [spoil-maker](features/spoil-maker/decisions.md) | D8 | — | — | changed by spoil-maker D90 |
| เสียงต้นฉบับลดเบาไว้ใต้เสียงบรรยาย ตั้งระดับได้ (0 = ปิด) ไม่มีเพลงพื้นหลัง | [spoil-maker](features/spoil-maker/decisions.md) | D9 | — | — | active |
| ผลลัพธ์เป็น mp4 1080×1920 กับ `.srt` ของบทบรรยาย แก้ในแอปแล้ว render ใหม่ | [spoil-maker](features/spoil-maker/decisions.md) | D10 | — | — | active |
| บทบรรยายและเสียงบรรยายเป็นภาษาไทยอย่างเดียว ต้นฉบับภาษาอะไรก็ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D11 | — | — | active |
| LLM รันด้วย library ใน `.venv`, โมเดล pin จาก Hugging Face ลง `models/` ผ่าน Setup script, ไม่ใช้ Ollama | [spoil-maker](features/spoil-maker/decisions.md) | D12 | — | [0003](adr/0003-everything-inside-project.md), [0004](adr/0004-pinned-model-registry.md), [0008](adr/0008-runtime-media-download.md) | active |
| LLM คือ Qwen3.5 9B 4-bit (`mlx-community/Qwen3.5-9B-MLX-4bit`) Apache-2.0, ใช้ memory ราว 10 GB รันทีละงาน GPU | [spoil-maker](features/spoil-maker/decisions.md) | D13 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| LLM รันด้วย mlx-vlm บน Mac หลัง interface ที่เปลี่ยน backend ได้; backend บน Windows ตัดสินใน `windows-check` | [spoil-maker](features/spoil-maker/decisions.md) | D14 | — | [0016](adr/0016-single-os-library-ports-separately.md) | changed by spoil-maker D50 |
| LLM เลือก shot ให้ประโยคจาก Transcript กับคำบรรยายภาพของทุก shot ที่ทำครั้งเดียวต่อ Temp clip | [spoil-maker](features/spoil-maker/decisions.md) | D15 | — | — | active |
| Describe job เริ่มเมื่อผู้ใช้กดต่อคลิป เห็น % ยกเลิกได้; คลิปที่ใช้ทำสปอยต้องถอดแล้วและดูภาพแล้ว | [spoil-maker](features/spoil-maker/decisions.md) | D16 | — | — | active |
| ตัด Shot ด้วย ffmpeg scene filter 0.3, แบ่ง Shot ยาวเกิน 10 วินาที, รวม Shot สั้นกว่า 1 วินาที, บรรยายเฟรมกลาง | [spoil-maker](features/spoil-maker/decisions.md) | D17 | — | — | active |
| ร่างบทสองขั้น: บทจาก Transcript (สั่งใหม่ได้ 3 ครั้ง) แล้วเลือก 2 Shot ต่อประโยคจากช่วง ±30 วินาทีรอบบรรทัดที่อ้าง | [spoil-maker](features/spoil-maker/decisions.md) | D18 | — | — | active |
| hook (layout A) และชื่อตอน (layout C) ให้ LLM ร่างพร้อมบท ผู้ใช้แก้ได้ ว่าง = ไม่แสดง | [spoil-maker](features/spoil-maker/decisions.md) | D19 | — | — | active |
| กดร่างบทครั้งเดียวได้ทั้งบทและ Shot; แก้ประโยคแล้ว Shot เดิมอยู่ มีปุ่มให้ AI เลือก Shot ใหม่ต่อประโยค | [spoil-maker](features/spoil-maker/decisions.md) | D25 | — | — | active |
| ตัวเลือก Shot เปิดที่ ±30 วินาทีรอบบรรทัดที่อ้าง ขยายดูทั้งคลิปทีละ EP ได้; เก็บเฟรมกลางเป็นภาพเล็ก | [spoil-maker](features/spoil-maker/decisions.md) | D26 | — | — | active |
| หน้าตรวจแก้: แก้ ลบ แทรกประโยคได้ (ประโยคแทรกเลือก Shot เอง) ไม่มีลากสลับลำดับ | [spoil-maker](features/spoil-maker/decisions.md) | D27 | — | — | active |
| Spoil draft (บท, Shot, เสียง, ค่าตั้ง) เก็บเป็นไฟล์ใน `media/` งานเดียว ร่างใหม่ทับหลังยืนยัน | [spoil-maker](features/spoil-maker/decisions.md) | D28 | — | — | active |
| ลบ Temp clip ที่ Spoil draft ใช้: เตือน ยืนยันแล้วลบทั้งคลิปและ Spoil draft | [spoil-maker](features/spoil-maker/decisions.md) | D29 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| เสียง: ปุ่มสร้างทั้งหมด (เฉพาะที่ขาด) + ฟังและสร้างใหม่ทีละประโยค; แก้ข้อความ = ต้องสร้างใหม่; render สร้างส่วนที่ขาดให้ | [spoil-maker](features/spoil-maker/decisions.md) | D30 | toon | — | active |
| render: เสียงประโยคแบ่งครึ่งให้ 2 Shot เล่นจากต้น Shot, Shot สั้นเล่นเลยท้ายต่อในต้นฉบับ | [spoil-maker](features/spoil-maker/decisions.md) | D31 | — | — | active |
| เสียงตัวอย่าง = Saved voice ที่ผู้ใช้ออกแบบ (เพศ วัย ระดับเสียง → สุ่ม → ฟัง → บันทึก) เก็บเป็น clone prompt อยู่รายการเดียวกับเสียง clone | [spoil-maker](features/spoil-maker/decisions.md) | D32 | toon | [0019](adr/0019-saved-voice-tied-to-tts-model.md) | changed by spoil-maker D48 |
| clone: สร้างประโยคตัวอย่างให้ฟังก่อนบันทึกเป็น Saved voice ไม่มีตรวจอัตโนมัติ | [spoil-maker](features/spoil-maker/decisions.md) | D33 | — | — | superseded by spoil-maker D48 |
| ไฟล์ clone: สั้นกว่า 3 วินาทีไม่รับ ยาวกว่า 10 วินาทีใช้ 10 วินาทีแรก, Whisper ถอดข้อความ ผู้ใช้แก้ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D34 | — | — | superseded by spoil-maker D48 |
| Saved voice มี speed 0.8–1.2 ของตัวเอง; ความเร็วพูดที่วัดจากประโยคตัวอย่างใช้ประมาณความยาวบทแทน 9–11 ตัวอักษรต่อวินาที | [spoil-maker](features/spoil-maker/decisions.md) | D35 | toon | [0019](adr/0019-saved-voice-tied-to-tts-model.md) | active |
| ตัวเลขแปลงเป็นคำไทยเฉพาะข้อความที่ส่งให้ OmniVoice; บท ซับ และ `.srt` ยังเป็นตัวเลข | [spoil-maker](features/spoil-maker/decisions.md) | D36 | — | — | active |
| OmniVoice สร้างเสียงด้วย `num_step` 16 (ราว 9 วินาทีต่อประโยคบน M2) | [spoil-maker](features/spoil-maker/decisions.md) | D37 | — | — | active |
| แบบหน้าจอของ spoil-maker ออกแบบหลังจบ plan (Source `pending`) | [spoil-maker](features/spoil-maker/decisions.md) | D38 | — | — | active |
| ความยาวเป้าหมาย 30–180 วินาที ค่าตั้งต้น 60 | [spoil-maker](features/spoil-maker/decisions.md) | D39 | — | — | active |
| เสียงต้นฉบับ 0–100% ทีละ 5 ตั้งต้น 20% จำค่าล่าสุด | [spoil-maker](features/spoil-maker/decisions.md) | D40 | — | — | active |
| ผล render เก็บทุกครั้งใน `media/spoil-maker/renders/` มีรายการเล่น โหลด ลบ | [spoil-maker](features/spoil-maker/decisions.md) | D42 | — | — | active |
| Saved voice เปลี่ยนชื่อและลบได้ (ยกเว้นที่ Spoil draft ใช้) speed แก้ไม่ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D43 | toon | — | changed by toon D25 |
| อ่านตัวเลข: เลขไทยเป็นอารบิก, ทศนิยม `จุด`, เวลา `นาฬิกา…นาที`, `%` เปอร์เซ็นต์, อื่นๆ อ่านทีละกลุ่ม; เขียนเอง | [spoil-maker](features/spoil-maker/decisions.md) | D44 | — | — | active |
| ข้อตัดสินทางเทคนิค: งาน GPU ทีละงานทั้ง project (`gpu_busy`), Kanit Bold pin commit, ภาพเล็ก Shot 320 px, ค่าที่จำไว้ใน `settings.json`, clone เป็น base64 ≤ 20 MB, `pythainlp` newmm | [spoil-maker](features/spoil-maker/decisions.md) | D45 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| Transcript รวมของ EP ที่เลือกไม่เกิน 32,000 token (tokenizer ของ Qwen นับข้อความที่แก้แล้ว D54) เกินไม่ให้ร่าง `transcript_too_long` | [spoil-maker](features/spoil-maker/decisions.md) | D46 | story-kb, windows-launch | — | active |
| test: API กับ worker ปลอมของโมเดลแต่ ffmpeg จริง, หน้าเว็บกับ fetch ปลอม; adapter จริงเช็คมือ | [spoil-maker](features/spoil-maker/decisions.md) | D47 | story-kb, windows-launch | — | changed by spoil-maker D51 |
| ตัด clone เสียงออกจากรอบนี้ ออกแบบเสียงอย่างเดียว; `kind` เก็บไว้ให้เพิ่ม clone ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D48 | — | — | active |
| ถอดหรือดูภาพใหม่ของคลิปใน Spoil draft ลบ draft หลังยืนยัน; คลิปที่งาน spoil-maker ใช้อยู่ `409` `clip_busy` | [spoil-maker](features/spoil-maker/decisions.md) | D49 | spoil | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| spoil-maker ทำบน Mac อย่างเดียว; Windows เป็น feature แยก `windows-launch` | [spoil-maker](features/spoil-maker/decisions.md) | D50 | windows-launch | [0016](adr/0016-single-os-library-ports-separately.md) | active |
| Qwen บน Windows NVIDIA เป็น feature `windows-launch` (ตัวรัน CUDA + โมเดล pin); ช่องวางลิงก์โมเดล HF เองเป็นอีก feature ทีหลัง | [windows-launch](features/windows-launch/decisions.md) | D1 | — | — | active |
| Windows เป้าหมาย RTX (sm_75+) VRAM ≥ 8 GB, คง CUDA 12.8 ตาม ADR-0016; GTX 10xx (Pascal) ไม่อยู่ใน scope | [windows-launch](features/windows-launch/decisions.md) | D2 | — | [0026](adr/0026-device-row-gates-every-gpu-job.md) | changed by D10 |
| Windows รัน Qwen ด้วย transformers + `Qwen/Qwen3.5-9B` pin commit ย่อ 4-bit nf4 ด้วย bitsandbytes ตอนโหลด; Mac คง mlx-vlm | [windows-launch](features/windows-launch/decisions.md) | D3 | — | [0025](adr/0025-per-os-model-spec-one-row-id.md) | active |
| Status check แถว `gpu` (ชื่อการ์ด, VRAM); Windows ต่ำกว่า sm_75 หรือ < 8 GB ไม่ ok และ gate Describe/Draft job; Mac ok เสมอ | [windows-launch](features/windows-launch/decisions.md) | D4 | — | — | changed by D8, D9 |
| Windows ผ่านเมื่อ Describe, Draft (ใกล้ 32,000 token) และเรียบเรียงใหม่จบ `done` บน `f7jkZXvaB4g` และผู้ใช้รับบทไทย; ไม่มีเพดานเวลา | [windows-launch](features/windows-launch/decisions.md) | D5 | — | — | active |
| Status check แสดงแถวตัวรันของ OS นั้น: Mac `mlx_vlm`, Windows `bitsandbytes`; `model_qwen` ชื่อเดิม เช็ค repo ของ OS | [windows-launch](features/windows-launch/decisions.md) | D6 | — | [0025](adr/0025-per-os-model-spec-one-row-id.md) | active |
| timeout งาน Qwen ต่อ OS: Mac คงเดิม, Windows ตั้งต้น Mac × 5 แล้วเปลี่ยนเป็นเวลานานสุดที่ลองวัด × 3 (ไม่ต่ำกว่า Mac) | [windows-launch](features/windows-launch/decisions.md) | D7 | — | — | changed by D12 |
| แถว `device` ไม่ ok เมื่อ capability ไม่อยู่ใน arch list ของ torch (gate ทุกงาน GPU); แถว `gpu` เฉพาะ Windows gate งาน Qwen; การ์ด index 0 | [windows-launch](features/windows-launch/decisions.md) | D8 | — | [0026](adr/0026-device-row-gates-every-gpu-job.md) | active |
| การ์ดต่ำกว่าเป้า Qwen = `warning` ที่ยังกันงาน Qwen; Setup script ข้ามโหลด Qwen และจบปกติ | [windows-launch](features/windows-launch/decisions.md) | D9 | — | — | active |
| Qwen บน Windows ต้อง RTX 30xx ขึ้นไป (sm_80) VRAM ≥ 8 GB, bfloat16 ทางเดียว | [windows-launch](features/windows-launch/decisions.md) | D10 | — | — | active |
| เขียนโค้ดและ test บน Mac ก่อน ลองบน Windows เมื่อได้เครื่อง; ไม่พอ = change request | [windows-launch](features/windows-launch/decisions.md) | D11 | — | — | active |
| ข้อแก้ red team: ดิสก์ Windows 30 GB, ไม่ย่อ `visual` กับ `lm_head`, timeout หลังลองไม่ต่ำกว่าก่อนลอง, probe พังเป็น warning, `bitsandbytes` ใช้ `check_package`, token ต่างกัน = change request | [windows-launch](features/windows-launch/decisions.md) | D12 | — | — | active |
| แถว `device` บน Windows ผ่านเมื่อ arch list ของ torch มี `sm_` major เดียวกับการ์ด (กฎของ torch; RTX 40xx ผ่าน) | [windows-launch](features/windows-launch/decisions.md) | D13 | — | [0026](adr/0026-device-row-gates-every-gpu-job.md) | active |
| แถว Qwen บน Windows: "ดูแถว GPU" เมื่อการ์ดไม่ผ่าน, probe พังไม่ทำให้ `device` แดง, VRAM GiB ปัดเต็ม, อ่านการ์ดครั้งเดียว, probe `bitsandbytes`, gate token มีแถว `gpu`, ข้าม Qwen = ดิสก์ 15 GB | [windows-launch](features/windows-launch/decisions.md) | D14 | — | — | changed by D15 |
| ค่าแถว Windows ตาม Figma: แถว Qwen/bitsandbytes บนการ์ดไม่ผ่านแสดงค่าของตัวเอง, probe `gpu` พังไม่แสดง error, `device` เก่าเกินแสดง `{การ์ด} · sm_xy`, ค่า `warning` เป็นตัว mono | [windows-launch](features/windows-launch/decisions.md) | D15 | — | — | active |
| worker Qwen Windows: skip `model.visual` + `lm_head` (ชื่อเต็ม), dtype bfloat16, log module ที่ไม่ย่อและ VRAM; ตาราง `Timeouts` ใน `spoil_maker.llm`; เขียน/เรียบเรียงเกินเวลา = ลองไม่สำเร็จ | [windows-launch](features/windows-launch/decisions.md) | D16 | — | — | active |
| ข้อแก้ red team: ไฟล์ Shot ใน `media/temp/shots/` สลับตอนจบ, lock ของ draft, render คืน GPU หลัง voicing, ค่า LLM, escape ASS, error แบบ spoil, ลายน้ำขาวขอบดำ, 3 seam | [spoil-maker](features/spoil-maker/decisions.md) | D51 | story-kb | [0015](adr/0015-one-gpu-slot.md) | active |
| รับความเสี่ยงลิขสิทธิ์ของภาพและเสียงต้นฉบับในคลิปสปอยที่เผยแพร่ (legal 1 UNVERIFIED) | [spoil-maker](features/spoil-maker/decisions.md) | D52 | — | — | active |
| คลิปสปอยทำจาก Temp clip เดียว: ใส่ความยาวต่อ EP (นาที) แอปตัดเท่ากันจากต้นคลิปที่ขอบ Shot, เลื่อนจุดตัดเองได้, 1 EP = 1 คลิปสปอย | [spoil-maker](features/spoil-maker/decisions.md) | D66 | — | — | active |
| ทำสปอยทีละ EP: เลือก EP เดียวต่อ Spoil draft (draft งานเดียวตาม D28), หน้าเลือก EP แสดงเลข ช่วงเวลา ภาพเล็ก เลือกง่าย | [spoil-maker](features/spoil-maker/decisions.md) | D67 | — | — | active |
| ตัวบอกขั้นของ tab สปอย: ไม่มีเครื่องหมายถูกตามตำแหน่ง ทุกขั้นกดได้ บรรทัดสถานะจริงใต้แต่ละขั้น (EP ที่เลือก, กำลังร่าง/สร้างเสียง x/y/จำนวนประโยค, render %/จำนวนคลิป) จุดหมุนเมื่องานรัน | [spoil-maker](features/spoil-maker/decisions.md) | D68 | — | — | active |
| ความยาวต่อ EP 5–60 นาที ทีละ 5 ตั้งต้น 30 จำค่าล่าสุด | [spoil-maker](features/spoil-maker/decisions.md) | D69 | — | — | active |
| ทางเลือกเล็กตัด EP: `media/temp/episodes/{id}.json` ของคลิป, จุดตัดที่ขอบ Shot, draft `version` 2 `clip_id` + `ep`, Transcript และ Shot เฉพาะช่วง EP, ผล render มี EP, ตัวบอกขั้นใช้ route เดิม | [spoil-maker](features/spoil-maker/decisions.md) | D70 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | changed by spoil-maker D71 |
| ข้อแก้ Breaker ตัด EP: draft อ้าง EP ด้วยช่วง (`episodes_changed`), ไฟล์การตัดเขียนตอน GET แรกและอยู่ใต้ lock, ไฟล์เสียตัดใหม่, EP เดียวสั้นได้, `ep_empty`, ตัวบอกขั้นอ่านใหม่เมื่องานจบ, lock ของ settings | [spoil-maker](features/spoil-maker/decisions.md) | D71 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| Draft job เรียบเรียงทั้งบทให้ประโยคเชื่อมกันหลังร่างก่อนเลือก Shot; หน้าตรวจแก้มีปุ่ม "เรียบเรียงใหม่"; คำสั่งร่างขอเรื่องที่ต่อกัน | [spoil-maker](features/spoil-maker/decisions.md) | D72 | story-kb | — | active |
| เรียบเรียงแก้เฉพาะข้อความ: จำนวน ลำดับ `refs` และ Shot คงเดิม; ข้อความเปลี่ยนแล้วเสียงเป็น `stale_audio` | [spoil-maker](features/spoil-maker/decisions.md) | D73 | — | — | active |
| เรียบเรียงใหม่ไม่แตะประโยคที่ผู้ใช้แก้หรือแทรกเอง (ป้าย "แก้เอง") | [spoil-maker](features/spoil-maker/decisions.md) | D74 | toon | — | changed by spoil-maker D75 |
| กดเรียบเรียงใหม่แล้วเลือกได้: ช่องติ๊ก "เรียบเรียงประโยคที่แก้เองด้วย" (ตั้งต้นไม่ติ๊ก); ติ๊กแล้วเขียนทับที่แก้เองและล้างป้าย | [spoil-maker](features/spoil-maker/decisions.md) | D75 | toon | — | active |
| ข้อแก้ Breaker เรียบเรียง: จับคู่ด้วย `i`, `polish_failed`, คุมความยาวรวม, สั่งใหม่ 2 ครั้ง, `edited` เมื่อข้อความต่างจริง, ปุ่มรอบันทึกค้างและเตือนเขียนทับ, ตัวบอกขั้นของ polish | [spoil-maker](features/spoil-maker/decisions.md) | D76 | — | — | active |
| ทางเลือกเล็กตอน build ตัด EP: `spoil_maker.episodes`, `GpuSlot.clip_files`, `PUT` กันเฉพาะงานที่อ่านคลิป, ลำดับเช็คและเช็คช่วงซ้ำหลังจอง GPU, ref เป็น index บรรทัด, หน้าเว็บขั้น 1 ใช้ component เดิมจนแบบใหม่มา | [spoil-maker](features/spoil-maker/decisions.md) | D77 | — | [0021](adr/0021-derived-data-follows-current-mp4.md) | active |
| ทางเลือกเล็กตอน build ตัวบอกขั้น: `useStepStatus` ใน `SpoilMakerPage` กับ `StepsRefreshContext`, งานล่าสุดของขั้น 2 ตาม `started_at`, poll ล้มเลิกตามจน refresh, หน้าตาต่อจาก `Spoil steps` เดิมจนแบบใหม่มา | [spoil-maker](features/spoil-maker/decisions.md) | D78 | — | — | active |
| ทางเลือกเล็กตอน build เรียบเรียงบท: รูปคำสั่ง `[i]`/`(fixed)`, `i` ซ้ำทิ้งทุกอัน, `edited` `false` เมื่อข้อความเปลี่ยนเท่านั้น, `busy` เช็คก่อน, รอ change ที่ค้างก่อนส่ง, กล่องเลือกแบบ Shot picker จนแบบใหม่มา | [spoil-maker](features/spoil-maker/decisions.md) | D79 | — | — | changed by spoil-maker D82 |
| แก้จาก feature review รอบสาม: ADR-0013 รวม `PUT`, `tokens_not_ready`, ลำดับลบคลิปใน spec ตามโค้ด, `ModalDialog`, `useJobCalls`, test ผ่าน API แทน `gpu.slot.take` | [spoil-maker](features/spoil-maker/decisions.md) | D80 | — | [0013](adr/0013-post-requires-json.md) | active |
| ร่างบทแล้วเปิดขั้น 2 ทันที ระหว่างร่างขั้น 2 แสดงการ์ดความคืบหน้า 3 ขั้น (เขียนบท, เรียบเรียง, เลือกภาพ) กับปุ่มยกเลิก | [spoil-maker](features/spoil-maker/decisions.md) | D81 | story-kb | — | active |
| ระหว่างร่างบท ขั้น 1 อ่านอย่างเดียวด้วยค่าของงาน (`order` ใน Draft job) พร้อม Alert ให้ไปยกเลิกที่ขั้น 2 | [spoil-maker](features/spoil-maker/decisions.md) | D82 | story-kb | — | active |
| ร่างบทล้ม: ขั้น 2 แสดง error พร้อม "ลองอีกครั้ง" ด้วย `order` เดิมและ "กลับไปแก้ตั้งค่า"; ยกเลิก: กลับขั้น 1 ที่ค่าเดิม | [spoil-maker](features/spoil-maker/decisions.md) | D83 | — | — | changed by spoil-maker D86 |
| การ์ดสไตล์มีบรรทัดอธิบายใต้ชื่อทั้ง 3 ใบ ตามตารางสไตล์ใน spec | [spoil-maker](features/spoil-maker/decisions.md) | D84 | — | — | active |
| ยกเลิกร่างบท: "กำลังยกเลิก" จนเห็น `cancelled` แล้วกลับขั้น 1; จบ `done` ก่อนหยุด → บทใหม่พร้อม "ยกเลิกไม่ทัน บทร่างเสร็จแล้ว" | [spoil-maker](features/spoil-maker/decisions.md) | D85 | — | — | active |
| "ลองอีกครั้ง" หลังร่างล้มถามยืนยันร่างทับ (D28) ทุกครั้งเมื่อมี Spoil draft | [spoil-maker](features/spoil-maker/decisions.md) | D86 | — | — | active |
| ข้อแก้ The Breaker ร่างบทไปขั้น 2: error ของลองอีกครั้ง, ค่าของขั้น 1 จาก `order`, restart, `voice_in_use` ของงาน, state ก่อนเปลี่ยน hash, `busy` | [spoil-maker](features/spoil-maker/decisions.md) | D87 | — | — | active |
| ทางเลือกเล็กตอน build ร่างบทไปขั้น 2: การ์ดแทนทั้งขั้น, ซ่อนลองอีกครั้งเมื่อต้องแก้ตั้งค่า, offline เฉพาะงานร่างทั้งบท, `voice_in_use` ถามงานก่อน lock | [spoil-maker](features/spoil-maker/decisions.md) | D88 | — | — | changed by spoil-maker D89 |
| แก้จาก feature review รอบสี่: GPU ไม่ค้างเมื่ออ่านชื่อคลิปพลาด, เช็คเสียงซ้ำใต้ lock ของ draft, ขั้น 1 เริ่มใหม่จาก `order`, `ReplaceConfirm`, `runningDraft`, flow.md | [spoil-maker](features/spoil-maker/decisions.md) | D89 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| เลือกสไตล์ไม่เปลี่ยน layout; ฟอร์มใหม่ตั้งต้น B | [spoil-maker](features/spoil-maker/decisions.md) | D90 | — | — | active |

## คลังความรู้

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| คลังความรู้เป็น feature ใหม่ `story-kb` มี tab และข้อมูลของตัวเอง | [story-kb](features/story-kb/decisions.md) | D1 | — | [0023](adr/0023-story-owned-by-story-kb.md) | active |
| ตัวละครของ Story: ชื่อ (ต้องมี) กับคำอธิบายสั้น กดบวกเพิ่มได้ | [story-kb](features/story-kb/decisions.md) | D2 | — | — | active |
| Temp clip จำ Story ที่เลือกในขั้น 1 ของ tab สปอย ทุก EP ใช้เรื่องเดิม มี "ไม่ใช้" | [story-kb](features/story-kb/decisions.md) | D3 | — | — | changed by story-kb D15 |
| AI ใช้ Story ตอนเขียนบทและเรียบเรียง ไม่ใช้ตอนเลือก Shot | [story-kb](features/story-kb/decisions.md) | D4 | — | — | active |
| ทุกงานอ่าน Story ตอนนี้ของคลิปตอนเริ่มงาน Spoil draft ไม่เก็บสำเนา | [story-kb](features/story-kb/decisions.md) | D5 | — | [0024](adr/0024-llm-jobs-read-story-at-start.md) | active |
| Story: ชื่อเรื่อง ≤ 100, บทความ ≤ 5,000 ตัวอักษร, ตัวละคร ≤ 30 (ชื่อ ≤ 40, คำอธิบาย ≤ 200); ไม่นับในเพดาน token ของ Transcript | [story-kb](features/story-kb/decisions.md) | D6 | — | — | changed by story-kb D14 |
| Story ที่คลิปจำลบพร้อมคลิป แต่ไม่หมดอายุเมื่อถอดใหม่ บรรยายฉากใหม่ หรือตัดช่วง (ข้อยกเว้นของ ADR-0021) | [story-kb](features/story-kb/decisions.md) | D7 | — | [0022](adr/0022-user-bound-clip-data-never-expires.md) | active |
| Story เป็นพื้นหลังและตัวสะกดชื่อ เหตุการณ์ต้องมาจากบรรทัดของ EP เท่านั้น | [story-kb](features/story-kb/decisions.md) | D8 | — | — | active |
| แถบ tab: ติดตั้ง · คลิป · คลังความรู้ (`#/stories`) · สปอย | [story-kb](features/story-kb/decisions.md) | D9 | — | — | active |
| ลบ Story ได้หลังยืนยันที่บอกจำนวนคลิป คลิปเหล่านั้นเป็น "ไม่ใช้" | [story-kb](features/story-kb/decisions.md) | D10 | — | — | active |
| หน้าแก้ Story บันทึกด้วยปุ่ม ถามก่อนออกเมื่อยังไม่บันทึก | [story-kb](features/story-kb/decisions.md) | D11 | — | — | active |
| ทางเลือกเล็ก: `media/stories/` ไฟล์ละเรื่อง + `clip-stories.json`, lock เดียว, API `/api/stories`, บันทึกหลังทับก่อน, ชื่อตัวละครห้ามซ้ำ, นับ code point | [story-kb](features/story-kb/decisions.md) | D12 | — | [0023](adr/0023-story-owned-by-story-kb.md) | active |
| seam: API กับ LLM ปลอมที่จดคำสั่ง และหน้าเว็บกับ fetch ปลอม | [story-kb](features/story-kb/decisions.md) | D13 | — | — | active |
| token ของ EP + บล็อก Story ≤ 32,000 (`transcript_too_long`); ตัวนับขั้น 1 แสดงผลรวม | [story-kb](features/story-kb/decisions.md) | D14 | windows-launch | — | active |
| คลิปจำ Story ตอนกดร่าง: `kind: "draft"` ส่ง `story_id`; ไม่มี route บันทึกแยก | [story-kb](features/story-kb/decisions.md) | D15 | — | — | active |
| ข้อแก้ red team: ตำแหน่งบล็อก Story, lock ในสุด, ขึ้นบรรทัดเป็นช่องว่าง, บันทึกซ้ำ, ตัวกันออกใน `useHash`, เพิ่มเรื่องในแท็บใหม่, กล่องเรียบเรียงบอกเรื่อง | [story-kb](features/story-kb/decisions.md) | D16 | — | — | active |
| ทางเลือกเล็กของการเช็คค่า Story: ไม่ส่งชื่อ = ว่าง, ช่องบรรทัดเดียวรวมช่องว่าง, ชื่อซ้ำเทียบ casefold, ไม่สนฟิลด์ที่ไม่รู้จัก, Story อ่านไม่ได้เป็น `404` | [story-kb](features/story-kb/decisions.md) | D17 | — | — | active |
| ทางเลือกเล็กของหน้าคลังความรู้: ข้อ e2e ด้วย Vitest ผ่าน `App`, ตัวกันออกลงทะเบียนตอนโหลด module, บันทึกครั้งแรกไม่ remount, Alert เมื่อบันทึกไม่ได้, วันเวลาจากข้อความ `updated_at`, ของใช้ร่วมย้ายไป `components/ui` และ `src/testing` | [story-kb](features/story-kb/decisions.md) | D18 | — | — | active |
| ทางเลือกเล็กของการร่างบทด้วย Story: ค่าคาดหวังของคำสั่งเป็นไฟล์ golden, อ่าน Story ครั้งเดียวตอนเช็ค, `backend.qwen_tokens` ที่เดียว, ช่อง Story เป็นการ์ดของตัวเอง, ชื่อตัวนับตาม Figma | [story-kb](features/story-kb/decisions.md) | D19 | — | — | active |
| ทางเลือกเล็กของเรียบเรียงใหม่ด้วย Story: อ่าน Story ของคลิปแบบไม่ raise, golden ของ "ไม่ใช้", ไม่เช็ค token, กล่องไม่บอกเรื่องเมื่ออ่านไม่ได้, `readStoryLinks` ใช้ร่วม | [story-kb](features/story-kb/decisions.md) | D20 | — | — | active |
| ข้อแก้จาก feature review ของ story-kb: กล่องเรียบเรียงใหม่ตาม Figma, `story-clips` ไม่ห่อ RootModel, `#/stories/` เปิดรายการ, badge ใช้อยู่เมื่อ n > 0, `grouped` ใน `lib/format` | [story-kb](features/story-kb/decisions.md) | D21 | — | — | active |
| ข้อถาม designer ของ story-kb: `ModalDialog` มุม 24px คงเดิม, แถวปุ่มหน้าแก้ Story สูงตามปุ่ม, ไอคอน external-link คงสองแบบ | [story-kb](features/story-kb/decisions.md) | D22 | — | — | active |
| ค่าเลือกของช่อง Story ขั้น 1 เป็น union สี่แบบ (`followsClip`, `story`, `none`, `gone`) ไม่มีธงเรื่องถูกลบแยก | [story-kb](features/story-kb/decisions.md) | D23 | — | — | active |
| ลองอีกครั้งที่ถูกปฏิเสธเป็น `story_not_found` พาไปแก้ตั้งค่าเท่านั้น; ข้อความเรื่องถูกลบในช่อง Story มาจาก API | [story-kb](features/story-kb/decisions.md) | D24 | — | — | active |

## สร้างคลิปการ์ตูนเล่า

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| การ์ตูนเล่าเป็น feature ใหม่ `toon` ใน tab "การ์ตูนเล่า" มีข้อมูลของตัวเอง ไม่ใช้ Temp clip | [toon](features/toon/decisions.md) | D1 | — | — | active |
| รอบแรกทำครบทางแต่บาง: บท → การ์ด → ภาพ → เสียงเล่า → ซับ → render mp4 | [toon](features/toon/decisions.md) | D2 | — | — | active |
| Series เก็บชื่อช่อง สไตล์ ตัวละคร ฉากหลัง; EP อยู่ใน Series เลข EP เดินต่อเอง | [toon](features/toon/decisions.md) | D3 | — | — | active |
| ภาพขยับต่อการ์ด: นิ่ง/ซูมเข้า/ซูมออก/เลื่อนซ้าย/ขวา + ไฟกะพริบทั้งภาพ, จางระหว่างการ์ด, ด้วย ffmpeg | [toon](features/toon/decisions.md) | D4 | — | — | active |
| คลังเสียง (ไฟล์หรือลิงก์) AI เลือกตามชื่อต่อฉาก ผู้ใช้ปรับได้; AI สร้างเสียงที่ขาดเป็นรอบสอง | [toon](features/toon/decisions.md) | D5 | — | — | active |
| สร้างภาพด้วย FLUX.2 klein 4B (Apache-2.0) ทั้งสอง OS พร้อมภาพอ้างอิง; ลองบน Mac ก่อนสร้าง tab | [toon](features/toon/decisions.md) | D6 | — | — | active |
| แบบจอสองแบบเลือกต่อ Series: กรอบดำ (ภาพแนวนอน + ชื่อเรื่อง EP ชื่อช่อง) หรือเต็มจอ (ภาพ 9:16 + ซับทับภาพ) | [toon](features/toon/decisions.md) | D7 | — | — | active |
| เสียงเล่าหลักหนึ่ง Saved voice ต่อ Series, EP เปลี่ยนเป็นเสียงอื่นได้; ไม่มีเสียงต่อตัวละคร | [toon](features/toon/decisions.md) | D8 | — | — | active |
| เส้นเรื่อง องก์ → ช่วง → การ์ด; ช่วง = การ์ดติดกันในฉากหลังเดียว เสียงพื้นต่อช่วง; ไม่ใช้คำ "ฉาก" | [toon](features/toon/decisions.md) | D9 | — | — | active |
| โครงองก์ตั้งต้นที่ Series (แบบหลอน / แบบตลก); AI ร่างตามโครง; EP เพิ่ม ลบ เปลี่ยนชื่อองก์ได้ | [toon](features/toon/decisions.md) | D10 | — | — | active |
| โครงแบบตลก ตั้งเรื่อง / ปั่น / พลิก / ตบมุก; แก้โครงของ Series ได้ มีผลกับ EP ใหม่เท่านั้น | [toon](features/toon/decisions.md) | D11 | — | — | active |
| AI ร่าง EP สองขั้น: ไอเดีย → พล็อต (สรุปต่อองก์ + ตัวละคร ฉากหลังที่ใช้) ผู้ใช้แก้ → ช่วงและการ์ด | [toon](features/toon/decisions.md) | D12 | — | — | active |
| ตัวละครและฉากหลังใหม่ที่พล็อตเสนอเข้า Series ตอนยืนยันพล็อต (ยังไม่มีภาพ); การ์ดที่ใช้ของไม่มีภาพอ้างอิงสร้างภาพไม่ได้ | [toon](features/toon/decisions.md) | D13 | — | — | active |
| ความยาวการ์ด = เสียงเล่าจริง + เว้นสั้น, ผู้ใช้เพิ่มวินาทีค้างได้, การ์ดไม่มีเสียงเล่าได้; ก่อนมีเสียงประมาณตาม spoil-maker D35 | [toon](features/toon/decisions.md) | D14 | — | — | active |
| แก้พล็อตแล้วแตกใหม่เฉพาะองก์ที่พล็อตเปลี่ยน; การ์ดป้าย "แก้เอง" ต้องยืนยันก่อนทับ; องก์ที่แตกใหม่เสียภาพการ์ด | [toon](features/toon/decisions.md) | D15 | — | — | active |
| คลังเสียงพื้นเป็นคลังกลางของ tab การ์ตูนเล่า ทุก Series ใช้ร่วม | [toon](features/toon/decisions.md) | D16 | — | — | active |
| เสียงพื้นเดียวกันข้ามช่วงเล่นต่อ; ต่างกันผสมทับราว 1 วินาที; สั้นกว่าช่วงวนซ้ำ | [toon](features/toon/decisions.md) | D17 | — | — | active |
| ไม่มีดูตัวอย่างทั้ง EP ก่อน render ในรอบแรก; render mp4 จริงแล้วดูผล | [toon](features/toon/decisions.md) | D18 | — | — | active |
| ข้อความบนภาพรอบแรกมีแค่ป้ายชื่อตัวละครตอนออกครั้งแรกใน EP เปิดปิดต่อ Series; ไม่มีกล่องข้อความอื่น | [toon](features/toon/decisions.md) | D19 | — | — | active |
| คำบรรยายภาพของการ์ดเป็นข้อความอิสระช่องเดียว (ท่าทาง สีหน้า มุมกล้อง แสง) | [toon](features/toon/decisions.md) | D20 | — | — | active |
| ช่องของการ์ด: ข้อความเล่า (ว่าง = การ์ดเงียบ), ตัวละคร, คำบรรยายภาพ, การขยับ, ไฟกะพริบ, ค้างเพิ่ม 0–5 วิ, เสียงทีละการ์ด, ภาพ; เว้นท้ายเสียง 0.3 วิ | [toon](features/toon/decisions.md) | D21 | — | — | active |
| ตำแหน่งแบบจอตาม layout-sketch: กรอบดำ (ชื่อตอน + ป้าย EP บน, ภาพ 1080×608 กลาง, ซับใต้ภาพ, ชื่อช่องล่าง), เต็มจอ (ซับขาวขอบดำ ~60%); Kanit; ไม่มีสีเน้นคำ | [toon](features/toon/decisions.md) | D22 | — | — | active |
| ป้ายชื่อ "ชื่อ / คำสั้น" (คำสั้นใส่หรือไม่ก็ได้) ขึ้นตลอดการ์ดแรกที่ตัวละครอยู่ในภาพ | [toon](features/toon/decisions.md) | D23 | — | — | active |
| ชื่อตอนของ EP AI เสนอพร้อมพล็อต ผู้ใช้แก้ได้ก่อน render; แสดงเฉพาะแบบกรอบดำ | [toon](features/toon/decisions.md) | D24 | — | — | active |
| ตัวละคร ฉากหลัง และ Saved voice ที่การ์ตูนเล่าใช้อยู่ลบไม่ได้ (ขยาย spoil-maker D43) | [toon](features/toon/decisions.md) | D25 | — | — | active |
| ลบ Series ลบทุก EP ตัวละคร ฉากหลัง ภาพ เสียง คลิป หลังยืนยัน; Saved voice และคลังเสียงพื้นคงอยู่ | [toon](features/toon/decisions.md) | D26 | — | — | active |
| ภาพการ์ดที่เสียแก้ด้วยการสร้างใหม่ทั้งภาพ; ไม่มีแก้เฉพาะจุดในรอบแรก | [toon](features/toon/decisions.md) | D27 | — | — | active |
