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
| รองรับ Mac Apple Silicon (MPS) และ Windows NVIDIA (CUDA 12.8), torch 2.8.0 | [setup-status](features/setup-status/decisions.md) | D5 | — | [0006](adr/0006-supported-platforms.md) | active |

## การติดตั้ง

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| Portable = ก๊อป folder แล้วรัน setup ซ้ำ, ทุกอย่างอยู่ใน project | [setup-status](features/setup-status/decisions.md) | D12 | — | [0003](adr/0003-everything-inside-project.md) | active |
| กฎ red team: `setup.cmd` สำหรับ Windows, pin revision โมเดล, `cache_dir` ชัดเจน, lock และเช็คดิสก์, torchaudio cu128 | [setup-status](features/setup-status/decisions.md) | D13 | — | [0003](adr/0003-everything-inside-project.md), [0004](adr/0004-pinned-model-registry.md) | active |
| ติดตั้งด้วย script บน terminal, เว็บแค่แสดงสถานะ | [setup-status](features/setup-status/decisions.md) | D3 | — | [0002](adr/0002-install-only-in-setup.md) superseded by [0008](adr/0008-runtime-media-download.md) | active |
| `setup.sh` กับ `setup.ps1` บางๆ เรียก `backend.setup` ตัวเดียว | [setup-status](features/setup-status/decisions.md) | D8 | — | [0002](adr/0002-install-only-in-setup.md) superseded by [0008](adr/0008-runtime-media-download.md) | active |
| เช็ค PID ของ setup lock: `os.kill(pid, 0)` บน Mac, `OpenProcess` บน Windows | [setup-status](features/setup-status/decisions.md) | D17 | — | — | active |
| จุด inject สำหรับ test: probe, `download`, `backend_running`, `free_bytes`, `DeviceProbe` | [setup-status](features/setup-status/decisions.md) | D18 | spoil | — | active |
| `setup.cmd` หยุดรอเมื่อดับเบิลคลิกและคืน code page, `setup.ps1` เช็ค `$LASTEXITCODE` ไม่ใช้ `Stop`, ติดตั้ง uv ใน PowerShell ลูกที่ Bypass, CRLF, `run_checks` รับ `sys_platform` | [setup-status](features/setup-status/decisions.md) | D23 | — | — | active |
| `npm run dev` start backend ด้วย Python ใน `.venv` ผ่าน `scripts/dev-api.mjs` ไม่พึ่ง uv ใน PATH; README ติดตั้งและใช้งานเป็นไทย | [setup-status](features/setup-status/decisions.md) | D24 | — | — | active |
| Status check เป็น checklist 9 รายการ ไม่โหลดโมเดล ไม่ใช้ network | [setup-status](features/setup-status/decisions.md) | D7 | spoil | [0004](adr/0004-pinned-model-registry.md) | extended by spoil D9 |
| Status check เพิ่มแถว `yt_dlp` และ `deno` เป็น 11 แถว; tab สปอย gate ด้วยแถว `yt_dlp`, `deno`, `ffmpeg` ไม่ใช้ `ready` | [spoil](features/spoil/decisions.md) | D9 | — | [0009](adr/0009-status-check-single-place.md) | active |

## ffmpeg

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ffmpeg มาจาก `imageio-ffmpeg` ใน venv, หา path ด้วย `get_ffmpeg_exe()` ไม่พึ่ง PATH | [setup-status](features/setup-status/decisions.md) | D4 | — | [0005](adr/0005-ffmpeg-from-imageio.md) | active |

## โมเดล AI

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| เก็บโมเดลใน `models/` ของ project ผ่าน `HF_HOME` | [setup-status](features/setup-status/decisions.md) | D6 | — | [0003](adr/0003-everything-inside-project.md) | changed by D13 |
| ใช้ OmniVoice แบบไม่หารายได้เท่านั้น, แสดง license | [setup-status](features/setup-status/decisions.md) | D11 | — | [0007](adr/0007-non-commercial-use.md) | active |
| revision ที่ pin และ `allow_patterns` ของ OmniVoice และ Whisper | [setup-status](features/setup-status/decisions.md) | D16 | spoil | [0004](adr/0004-pinned-model-registry.md) | active |

## UI design

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| แถบ tab บน: สปอย (`#/spoil`), Setup status (`#/setup`), default Setup status, ไม่ใช้ router library | [spoil](features/spoil/decisions.md) | D10 | — | — | active |
| ออกแบบหน้าจอใน Figma หลัง plan | [setup-status](features/setup-status/decisions.md) | D9 | spoil | — | active |
| แถวที่ไม่ `ok` แสดง `fix` จาก API ค่าเดียวเป็น chip พร้อมปุ่ม copy ไม่แสดงคำสั่งทั้งสอง OS | [setup-status](features/setup-status/decisions.md) | D15 | — | — | active |
| font มากับ `@fontsource` ใน project ไม่โหลดจาก CDN | [setup-status](features/setup-status/decisions.md) | D19 | — | [0003](adr/0003-everything-inside-project.md) | active |
| `fix` ไม่มีช่องว่าง = คำสั่ง (chip กับปุ่ม copy), มีช่องว่าง = ข้อความ | [setup-status](features/setup-status/decisions.md) | D20 | spoil | — | active |
| รายละเอียดหน้า Setup status: Refresh จาก offline, เวลาเช็คล่าสุด, pill คำเตือน, icon จาก Figma, timeout | [setup-status](features/setup-status/decisions.md) | D21 | spoil | — | active |

## ดาวน์โหลดสื่อ

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| Backend โหลดสื่อตามลิงก์ที่ผู้ใช้ใส่ได้ตอนรัน, package และโมเดลยังผ่าน Setup script เท่านั้น (แคบ ADR-0002) | [spoil](features/spoil/decisions.md) | D1 | — | [0008](adr/0008-runtime-media-download.md) | active |
| รอบแรกของสปอยทำแค่โหลดคลิป YouTube เป็น temp; ปลายทางคือคลิปสปอยหนังพร้อมเสียงเล่า OmniVoice | [spoil](features/spoil/decisions.md) | D2 | — | — | active |
| Temp clip เก็บใน `media/temp/` ของ project จนผู้ใช้กดลบเอง | [spoil](features/spoil/decisions.md) | D3 | — | — | active |
| Temp clip = `{id}.mp4` + `{id}.json` (เขียนสุดท้าย) + thumbnail; ไฟล์ค้างใน `.partial/` ล้างตอน start; Download job อยู่ใน memory | [spoil](features/spoil/decisions.md) | D14 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| คลิปแนวตั้งแบบ reels เท่านั้น, ด้านสั้น ≤ 720 px, mp4 | [spoil](features/spoil/decisions.md) | D4 | — | — | superseded by spoil D5 |
| รับคลิป YouTube ทุกแนว, temp ด้านสั้น ≤ 1080 px mp4; output แนวตั้งเลือก p ได้ถึง 1080 (รอบหน้า) | [spoil](features/spoil/decisions.md) | D5 | — | — | active |
| โหลดทีละคลิปเป็นงานเบื้องหลัง, poll % ทุก 1 วินาที, ยกเลิกได้, ไม่มีคิว | [spoil](features/spoil/decisions.md) | D6 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| หน้าต่างรายการ temp clip: thumbnail, ชื่อ, ช่อง, ความยาว, ขนาดภาพ/แนว, ขนาดไฟล์, เวลาโหลด, ลบ, เล่นในหน้าเว็บ | [spoil](features/spoil/decisions.md) | D7 | — | — | extended by D25 |
| ยอมรับความเสี่ยงลิขสิทธิ์และ ToS ของ YouTube; หารายได้ขัด ADR-0007 ต้องเปลี่ยน TTS ก่อน feature เสียง | [spoil](features/spoil/decisions.md) | D13 | — | — | active |
| red team: ยกเลิกต่อ state (merging ยกเลิกไม่ได้), lock กัน POST ซ้อน, ลบ mp4 ก่อน json, `in_use`, แยก error `login_required`, `TrustedHostMiddleware` | [spoil](features/spoil/decisions.md) | D15 | — | [0011](adr/0011-trusted-host-only.md) | active |
| แยก error ของ yt-dlp ตามข้อความจริง: live ที่ยังไม่เริ่ม = "This live event will begin", ไม่ใช้คำ "age" เดี่ยวๆ | [spoil](features/spoil/decisions.md) | D16 | — | — | active |
| ทางเลือกเล็กของงานโหลด: gate เรียก probe ใน `backend.checks`, adapter รับ `ProjectPaths`, busy เช็คจาก state | [spoil](features/spoil/decisions.md) | D17 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| ของบนจอที่ design เพิ่ม: หัวรายการพร้อมจำนวน, badge "กำลังเล่น", ข้อความแทนปุ่มยกเลิกตอน merging | [spoil](features/spoil/decisions.md) | D18 | — | — | active |
| ทางเลือกเล็กของ tab: tab เป็นลิงก์ hash, `PageLayout` ร่วม, `useCopy`, tone ของข้อความ, code ที่ไม่รู้จัก = offline, ปุ่ม "Copy" ตาม Figma | [spoil](features/spoil/decisions.md) | D19 | — | — | active |
| ทางเลือกเล็กของรายการ Temp clip: คลิปมีอยู่ = มี json, ลบ json ที่ mp4 หาย, เรียงตามเวลาจริง, ลบได้ 404 = แถวหาย, highlight มาจากข้อความ, `useMountedState`, `autoPlay` | [spoil](features/spoil/decisions.md) | D20 | — | — | active |
| ลิงก์ซ้ำ (video id เดิม) ไม่โหลดใหม่ ชี้แถวเดิม | [spoil](features/spoil/decisions.md) | D12 | — | — | active |
| ไม่จำกัดความยาว, ปฏิเสธ live, เช็คดิสก์ว่าง ≥ ขนาดประมาณ + 1 GB ก่อนโหลด | [spoil](features/spoil/decisions.md) | D11 | — | — | active |
| `yt-dlp[default]` และ `deno` (PyPI wheel) pin ใน `uv.lock`; โหลดพังแสดงเวอร์ชันและคำสั่งอัปเดต | [spoil](features/spoil/decisions.md) | D8 | — | — | active |

## ถอดบทพูด

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ถอดคำพูดของ Temp clip ด้วย Whisper large-v3-turbo ที่ติดตั้งแล้ว ตรวจภาษาเอง; ได้ Transcript อย่างเดียว ไม่แยกไฟล์เสียงให้ผู้ใช้ | [spoil](features/spoil/decisions.md) | D21 | — | — | active |
| แสดง Transcript ทีละบรรทัดพร้อมเวลา กดแล้ว player กระโดด, Copy ทั้งหมด, โหลด `.txt` และ `.srt` | [spoil](features/spoil/decisions.md) | D22 | — | — | active |
| ถอดเมื่อผู้ใช้กดเท่านั้น, Transcript เก็บคู่ Temp clip ข้าม restart, แถวแสดง "ถอดแล้ว", ลบคลิปลบ Transcript | [spoil](features/spoil/decisions.md) | D23 | — | — | active |
| Transcribe job ทีละงาน ไม่มีคิว, รันพร้อม Download job ได้, poll % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D24 | — | — | active |
| tab สปอยสองคอลัมน์: รายการคลิป → ลูกศร → กล่องถอดบทพูด (player ย้ายเข้ากล่อง), 375px เรียงบนลงล่าง | [spoil](features/spoil/decisions.md) | D25 | — | — | active |
| ไม่จำกัดเวลาถอด ต้องเห็น % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D26 | — | — | active |
| กติกางานถอด: ดึงเสียงด้วย ffmpeg ของ imageio เข้า memory, โหลด Whisper จาก snapshot แล้วปล่อยหลังงาน, ช่วงละ 5 นาที, gate 5 แถว, ลบคลิประหว่างถอด `409`, `{id}.transcript.json` | [spoil](features/spoil/decisions.md) | D27 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | changed by D28, D29 |
| งานถอดรันใน process ลูก `spawn`, thread ใน backend ถือสถานะ, ยกเลิก = terminate, ตายไม่ส่งผล = `crashed` | [spoil](features/spoil/decisions.md) | D28 | — | [0012](adr/0012-gpu-jobs-in-child-process.md) | active |
| red team งานถอด: `internal` + `finally`, ffmpeg ทีละช่วง, long-form ไม่ใช้ `chunk_length_s`, ช่วงท้าย < 30 วินาทีรวม, `language` null ได้, lock ร่วมกับลบ, ข้าม `*.transcript.json`, POST ต้อง JSON (`415`) | [spoil](features/spoil/decisions.md) | D29 | — | [0013](adr/0013-post-requires-json.md) | active |

