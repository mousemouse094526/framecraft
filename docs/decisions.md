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
| ใช้ OmniVoice แบบไม่หารายได้เท่านั้น, แสดง license | [setup-status](features/setup-status/decisions.md) | D11 | spoil-maker | [0007](adr/0007-non-commercial-use.md), [0017](adr/0017-non-commercial-no-forced-credit.md) | active |
| revision ที่ pin และ `allow_patterns` ของ OmniVoice และ Whisper | [setup-status](features/setup-status/decisions.md) | D16 | spoil | [0004](adr/0004-pinned-model-registry.md) | active |
| ยังไม่คิดเรื่อง license รอบแรก ใช้ OmniVoice ไปก่อน แล้วค่อยเปลี่ยนตัวแทนเมื่อจะหารายได้ | [spoil-maker](features/spoil-maker/decisions.md) | D3 | — | [0007](adr/0007-non-commercial-use.md), [0019](adr/0019-saved-voice-tied-to-tts-model.md) | changed by spoil-maker D41 |

## UI design

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| แถบ tab บน: สปอย (`#/spoil`), Setup status (`#/setup`), default Setup status, ไม่ใช้ router library | [spoil](features/spoil/decisions.md) | D10 | — | — | active |
| ออกแบบหน้าจอใน Figma หลัง plan | [setup-status](features/setup-status/decisions.md) | D9 | spoil | — | active |
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
| รับคลิป YouTube ทุกแนว, temp ด้านสั้น ≤ 1080 px mp4; output แนวตั้งเลือก p ได้ถึง 1080 (รอบหน้า) | [spoil](features/spoil/decisions.md) | D5 | — | — | active |
| โหลดทีละคลิปเป็นงานเบื้องหลัง, poll % ทุก 1 วินาที, ยกเลิกได้, ไม่มีคิว | [spoil](features/spoil/decisions.md) | D6 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| หน้าต่างรายการ temp clip: thumbnail, ชื่อ, ช่อง, ความยาว, ขนาดภาพ/แนว, ขนาดไฟล์, เวลาโหลด, ลบ, เล่นในหน้าเว็บ | [spoil](features/spoil/decisions.md) | D7 | — | — | extended by D25 |
| ยอมรับความเสี่ยงลิขสิทธิ์และ ToS ของ YouTube; หารายได้ขัด ADR-0007 ต้องเปลี่ยน TTS ก่อน feature เสียง | [spoil](features/spoil/decisions.md) | D13 | — | — | active |
| red team: ยกเลิกต่อ state (merging ยกเลิกไม่ได้), lock กัน POST ซ้อน, ลบ mp4 ก่อน json, `in_use`, แยก error `login_required`, `TrustedHostMiddleware` | [spoil](features/spoil/decisions.md) | D15 | spoil-maker | [0011](adr/0011-trusted-host-only.md) | active |
| แยก error ของ yt-dlp ตามข้อความจริง: live ที่ยังไม่เริ่ม = "This live event will begin", ไม่ใช้คำ "age" เดี่ยวๆ | [spoil](features/spoil/decisions.md) | D16 | — | — | active |
| ทางเลือกเล็กของงานโหลด: gate เรียก probe ใน `backend.checks`, adapter รับ `ProjectPaths`, busy เช็คจาก state | [spoil](features/spoil/decisions.md) | D17 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | active |
| ของบนจอที่ design เพิ่ม: หัวรายการพร้อมจำนวน, badge "กำลังเล่น", ข้อความแทนปุ่มยกเลิกตอน merging | [spoil](features/spoil/decisions.md) | D18 | — | — | active |
| ทางเลือกเล็กของ tab: tab เป็นลิงก์ hash, `PageLayout` ร่วม, `useCopy`, tone ของข้อความ, code ที่ไม่รู้จัก = offline, ปุ่ม "Copy" ตาม Figma | [spoil](features/spoil/decisions.md) | D19 | — | — | active |
| ซับ layout A ทีละท่อนราว 2–4 คำ (ตัดคำไทย) เวลาแบ่งตามจำนวนตัวอักษรของเสียงประโยค | [spoil-maker](features/spoil-maker/decisions.md) | D20 | — | — | active |
| ข้อความบนวิดีโอใช้ font Kanit (OFL) ตัวเดียว ไฟล์ ttf ใน project โหลดผ่าน Setup script มีแถว Status check | [spoil-maker](features/spoil-maker/decisions.md) | D21 | — | [0003](adr/0003-everything-inside-project.md), [0009](adr/0009-status-check-single-place.md) | active |
| สี ขนาด และตำแหน่งของข้อความตายตัวต่อ layout ตามคลิปตัวอย่าง ไม่มีตัวเลือกในรอบแรก | [spoil-maker](features/spoil-maker/decisions.md) | D22 | — | — | active |
| watermark เป็นข้อความชื่อช่องพิมพ์ครั้งเดียว แอปจำไว้ ว่าง = ไม่แสดง | [spoil-maker](features/spoil-maker/decisions.md) | D23 | — | — | superseded by spoil-maker D41 |
| ลายน้ำข้อความหลายอัน เลือก 6 ตำแหน่งและขนาดเล็กหรือกลาง แอปจำไว้; ไม่บังคับเครดิตโมเดล (Accepted risk) | [spoil-maker](features/spoil-maker/decisions.md) | D41 | — | [0017](adr/0017-non-commercial-no-forced-credit.md) | changed by spoil-maker D51 |
| ภาพเปลี่ยนแบบตัดตรงทุก layout ไม่มี transition หรือภาพเลื่อน ซ้อน เอียง | [spoil-maker](features/spoil-maker/decisions.md) | D24 | — | — | active |
| ทางเลือกเล็กของรายการ Temp clip: คลิปมีอยู่ = มี json, ลบ json ที่ mp4 หาย, เรียงตามเวลาจริง, ลบได้ 404 = แถวหาย, highlight มาจากข้อความ, `useMountedState`, `autoPlay` | [spoil](features/spoil/decisions.md) | D20 | — | — | active |
| ลิงก์ซ้ำ (video id เดิม) ไม่โหลดใหม่ ชี้แถวเดิม | [spoil](features/spoil/decisions.md) | D12 | — | — | active |
| ไม่จำกัดความยาว, ปฏิเสธ live, เช็คดิสก์ว่าง ≥ ขนาดประมาณ + 1 GB ก่อนโหลด | [spoil](features/spoil/decisions.md) | D11 | — | — | active |
| `yt-dlp[default]` และ `deno` (PyPI wheel) pin ใน `uv.lock`; โหลดพังแสดงเวอร์ชันและคำสั่งอัปเดต | [spoil](features/spoil/decisions.md) | D8 | — | — | active |

## ถอดบทพูด

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ถอดคำพูดของ Temp clip ด้วย Whisper large-v3-turbo ที่ติดตั้งแล้ว ตรวจภาษาเอง; ได้ Transcript อย่างเดียว ไม่แยกไฟล์เสียงให้ผู้ใช้ | [spoil](features/spoil/decisions.md) | D21 | spoil-maker | — | active |
| แสดง Transcript ทีละบรรทัดพร้อมเวลา กดแล้ว player กระโดด, Copy ทั้งหมด, โหลด `.txt` และ `.srt` | [spoil](features/spoil/decisions.md) | D22 | — | — | active |
| ถอดเมื่อผู้ใช้กดเท่านั้น, Transcript เก็บคู่ Temp clip ข้าม restart, แถวแสดง "ถอดแล้ว", ลบคลิปลบ Transcript | [spoil](features/spoil/decisions.md) | D23 | — | [0018](adr/0018-temp-clip-owns-derived-data.md) | active |
| Transcribe job ทีละงาน ไม่มีคิว, รันพร้อม Download job ได้, poll % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D24 | spoil-maker | [0015](adr/0015-one-gpu-slot.md) | changed by spoil-maker D45 |
| tab สปอยสองคอลัมน์: รายการคลิป → ลูกศร → กล่องถอดบทพูด (player ย้ายเข้ากล่อง), 375px เรียงบนลงล่าง | [spoil](features/spoil/decisions.md) | D25 | — | — | active |
| ไม่จำกัดเวลาถอด ต้องเห็น % และยกเลิกได้ | [spoil](features/spoil/decisions.md) | D26 | — | — | active |
| กติกางานถอด: ดึงเสียงด้วย ffmpeg ของ imageio เข้า memory, โหลด Whisper จาก snapshot แล้วปล่อยหลังงาน, ช่วงละ 5 นาที, gate 5 แถว, ลบคลิประหว่างถอด `409`, `{id}.transcript.json` | [spoil](features/spoil/decisions.md) | D27 | — | [0010](adr/0010-long-jobs-in-process-thread.md) | changed by D28, D29 |
| งานถอดรันใน process ลูก `spawn`, thread ใน backend ถือสถานะ, ยกเลิก = terminate, ตายไม่ส่งผล = `crashed` | [spoil](features/spoil/decisions.md) | D28 | — | [0012](adr/0012-gpu-jobs-in-child-process.md) | active |
| red team งานถอด: `internal` + `finally`, ffmpeg ทีละช่วง, long-form ไม่ใช้ `chunk_length_s`, ช่วงท้าย < 30 วินาทีรวม, `language` null ได้, lock ร่วมกับลบ, ข้าม `*.transcript.json`, POST ต้อง JSON (`415`) | [spoil](features/spoil/decisions.md) | D29 | — | [0013](adr/0013-post-requires-json.md) | active |
| ทางเลือกเล็กตอน build งานถอด: `float32` บน `mps`, ชื่อภาษา → code, ตัดเวลาจบที่จบช่วง, gate ใช้ check เดียวกับ Status check, `415` เป็น router dependency, terminate → kill หลัง 5 วินาที | [spoil](features/spoil/decisions.md) | D30 | — | [0012](adr/0012-gpu-jobs-in-child-process.md), [0013](adr/0013-post-requires-json.md) | active |
| ไม่กรองบรรทัดที่ Whisper แต่งในช่วงไม่มีคำพูด ผู้ใช้ลบเอง | [spoil](features/spoil/decisions.md) | D31 | — | — | active |
| ยอมรับเวลาบรรทัดตาม Whisper long-form แม้บางบรรทัดคลาด 2–3 วินาที | [spoil](features/spoil/decisions.md) | D32 | — | — | active |
| ของบนจอที่ design ของกล่องถอดเพิ่ม: ช่องลิงก์อยู่คอลัมน์ซ้าย, ข้อความหลังงานถอดเป็น Alert ในกล่อง, แถบ % แบบ Download progress, Transcript ว่างไม่มีปุ่ม Copy/ไฟล์ | [spoil](features/spoil/decisions.md) | D33 | — | — | active |
| ทางเลือกเล็กตอน build กล่องถอด: คลิปที่เลือกอยู่กับ `useTranscribe`, status GET ครั้งเดียว, `busy` → GET current, ลบคลิปที่กำลังถอดไม่ปลด player, ซ่อน Transcript ระหว่างถอดใหม่, ไม่ autoPlay เมื่อเลือกเพราะงาน, `PageLayout wide` | [spoil](features/spoil/decisions.md) | D34 | — | — | active |
| แก้จาก feature review: gate สองงานผ่าน `require_rows`, `JobFailed`, `write_atomic`, `jobs.py` → `downloads.py`, `features/spoil/lib/`, งานโหลดไม่หลุดเมื่องานถอดได้ 503 | [spoil](features/spoil/decisions.md) | D35 | — | — | active |

## สร้างคลิปสปอย

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| สร้างคลิปสปอยเป็น feature ใหม่ `spoil-maker` ใน tab สปอย ใช้ Temp clip กับ Transcript ของ spoil | [spoil-maker](features/spoil-maker/decisions.md) | D1 | — | — | active |
| ทุกอย่างต้องฟรี: โมเดลและโปรแกรมในเครื่อง ไม่มี API ที่ต้องจ่าย | [spoil-maker](features/spoil-maker/decisions.md) | D2 | — | — | active |
| AI ในเครื่องร่างบทสปอยจาก Transcript แล้วผู้ใช้แก้ทุกประโยคได้ก่อนสร้างเสียง | [spoil-maker](features/spoil-maker/decisions.md) | D4 | — | — | active |
| คลิปสปอยหนึ่งคลิปทำจาก Temp clip ที่ถอดแล้วได้หลาย EP เรียงลำดับเอง | [spoil-maker](features/spoil-maker/decisions.md) | D5 | — | — | active |
| เสียงบรรยายจาก OmniVoice เลือกเสียงตัวอย่างหรือ clone จากไฟล์เสียงสั้นได้ ใช้ซ้ำทุกคลิป | [spoil-maker](features/spoil-maker/decisions.md) | D6 | — | [0007](adr/0007-non-commercial-use.md) | changed by spoil-maker D48 |
| เลือก preset สไตล์ 3 แบบตามคลิปตัวอย่าง แล้วใส่ความยาวเป้าหมายเป็นวินาที | [spoil-maker](features/spoil-maker/decisions.md) | D7 | — | — | active |
| layout 3 แบบตามคลิปตัวอย่าง เลือกแยกจากสไตล์ ทุกแบบได้ 1080×1920 | [spoil-maker](features/spoil-maker/decisions.md) | D8 | — | — | active |
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
| ลบ Temp clip ที่ Spoil draft ใช้: เตือน ยืนยันแล้วลบทั้งคลิปและ Spoil draft | [spoil-maker](features/spoil-maker/decisions.md) | D29 | — | [0018](adr/0018-temp-clip-owns-derived-data.md) | active |
| เสียง: ปุ่มสร้างทั้งหมด (เฉพาะที่ขาด) + ฟังและสร้างใหม่ทีละประโยค; แก้ข้อความ = ต้องสร้างใหม่; render สร้างส่วนที่ขาดให้ | [spoil-maker](features/spoil-maker/decisions.md) | D30 | — | — | active |
| render: เสียงประโยคแบ่งครึ่งให้ 2 Shot เล่นจากต้น Shot, Shot สั้นเล่นเลยท้ายต่อในต้นฉบับ | [spoil-maker](features/spoil-maker/decisions.md) | D31 | — | — | active |
| เสียงตัวอย่าง = Saved voice ที่ผู้ใช้ออกแบบ (เพศ วัย ระดับเสียง → สุ่ม → ฟัง → บันทึก) เก็บเป็น clone prompt อยู่รายการเดียวกับเสียง clone | [spoil-maker](features/spoil-maker/decisions.md) | D32 | — | [0019](adr/0019-saved-voice-tied-to-tts-model.md) | changed by spoil-maker D48 |
| clone: สร้างประโยคตัวอย่างให้ฟังก่อนบันทึกเป็น Saved voice ไม่มีตรวจอัตโนมัติ | [spoil-maker](features/spoil-maker/decisions.md) | D33 | — | — | superseded by spoil-maker D48 |
| ไฟล์ clone: สั้นกว่า 3 วินาทีไม่รับ ยาวกว่า 10 วินาทีใช้ 10 วินาทีแรก, Whisper ถอดข้อความ ผู้ใช้แก้ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D34 | — | — | superseded by spoil-maker D48 |
| Saved voice มี speed 0.8–1.2 ของตัวเอง; ความเร็วพูดที่วัดจากประโยคตัวอย่างใช้ประมาณความยาวบทแทน 9–11 ตัวอักษรต่อวินาที | [spoil-maker](features/spoil-maker/decisions.md) | D35 | — | [0019](adr/0019-saved-voice-tied-to-tts-model.md) | active |
| ตัวเลขแปลงเป็นคำไทยเฉพาะข้อความที่ส่งให้ OmniVoice; บท ซับ และ `.srt` ยังเป็นตัวเลข | [spoil-maker](features/spoil-maker/decisions.md) | D36 | — | — | active |
| OmniVoice สร้างเสียงด้วย `num_step` 16 (ราว 9 วินาทีต่อประโยคบน M2) | [spoil-maker](features/spoil-maker/decisions.md) | D37 | — | — | active |
| แบบหน้าจอของ spoil-maker ออกแบบหลังจบ plan (Source `pending`) | [spoil-maker](features/spoil-maker/decisions.md) | D38 | — | — | active |
| ความยาวเป้าหมาย 30–180 วินาที ค่าตั้งต้น 60 | [spoil-maker](features/spoil-maker/decisions.md) | D39 | — | — | active |
| เสียงต้นฉบับ 0–100% ทีละ 5 ตั้งต้น 20% จำค่าล่าสุด | [spoil-maker](features/spoil-maker/decisions.md) | D40 | — | — | active |
| ผล render เก็บทุกครั้งใน `media/spoil-maker/renders/` มีรายการเล่น โหลด ลบ | [spoil-maker](features/spoil-maker/decisions.md) | D42 | — | — | active |
| Saved voice เปลี่ยนชื่อและลบได้ (ยกเว้นที่ Spoil draft ใช้) speed แก้ไม่ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D43 | — | — | active |
| อ่านตัวเลข: เลขไทยเป็นอารบิก, ทศนิยม `จุด`, เวลา `นาฬิกา…นาที`, `%` เปอร์เซ็นต์, อื่นๆ อ่านทีละกลุ่ม; เขียนเอง | [spoil-maker](features/spoil-maker/decisions.md) | D44 | — | — | active |
| ข้อตัดสินทางเทคนิค: งาน GPU ทีละงานทั้ง project (`gpu_busy`), Kanit Bold pin commit, ภาพเล็ก Shot 320 px, ค่าที่จำไว้ใน `settings.json`, clone เป็น base64 ≤ 20 MB, `pythainlp` newmm | [spoil-maker](features/spoil-maker/decisions.md) | D45 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| Transcript รวมของ EP ที่เลือกไม่เกิน 32,000 token (tokenizer ของ Qwen) เกินไม่ให้ร่าง `transcript_too_long` | [spoil-maker](features/spoil-maker/decisions.md) | D46 | — | — | active |
| test: API กับ worker ปลอมของโมเดลแต่ ffmpeg จริง, หน้าเว็บกับ fetch ปลอม; adapter จริงเช็คมือ | [spoil-maker](features/spoil-maker/decisions.md) | D47 | — | — | changed by spoil-maker D51 |
| ตัด clone เสียงออกจากรอบนี้ ออกแบบเสียงอย่างเดียว; `kind` เก็บไว้ให้เพิ่ม clone ได้ | [spoil-maker](features/spoil-maker/decisions.md) | D48 | — | — | active |
| ถอดหรือดูภาพใหม่ของคลิปใน Spoil draft ลบ draft หลังยืนยัน; คลิปที่งาน spoil-maker ใช้อยู่ `409` `clip_busy` | [spoil-maker](features/spoil-maker/decisions.md) | D49 | — | [0018](adr/0018-temp-clip-owns-derived-data.md) | active |
| spoil-maker ทำบน Mac อย่างเดียว; Windows เป็น feature แยก `windows-launch` | [spoil-maker](features/spoil-maker/decisions.md) | D50 | — | [0016](adr/0016-single-os-library-ports-separately.md) | active |
| ข้อแก้ red team: ไฟล์ Shot ใน `media/temp/shots/` สลับตอนจบ, lock ของ draft, render คืน GPU หลัง voicing, ค่า LLM, escape ASS, error แบบ spoil, ลายน้ำขาวขอบดำ, 3 seam | [spoil-maker](features/spoil-maker/decisions.md) | D51 | — | [0015](adr/0015-one-gpu-slot.md) | active |
| รับความเสี่ยงลิขสิทธิ์ของภาพและเสียงต้นฉบับในคลิปสปอยที่เผยแพร่ (legal 1 UNVERIFIED) | [spoil-maker](features/spoil-maker/decisions.md) | D52 | — | — | active |
