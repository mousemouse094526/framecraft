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
| ติดตั้งด้วย script บน terminal, เว็บแค่แสดงสถานะ | [setup-status](features/setup-status/decisions.md) | D3 | — | [0002](adr/0002-install-only-in-setup.md) | active |
| `setup.sh` กับ `setup.ps1` บางๆ เรียก `backend.setup` ตัวเดียว | [setup-status](features/setup-status/decisions.md) | D8 | — | [0002](adr/0002-install-only-in-setup.md) | active |
| เช็ค PID ของ setup lock: `os.kill(pid, 0)` บน Mac, `OpenProcess` บน Windows | [setup-status](features/setup-status/decisions.md) | D17 | — | — | active |
| จุด inject สำหรับ test: probe, `download`, `backend_running`, `free_bytes`, `DeviceProbe` | [setup-status](features/setup-status/decisions.md) | D18 | — | — | active |
| `setup.cmd` หยุดรอเมื่อดับเบิลคลิกและคืน code page, `setup.ps1` เช็ค `$LASTEXITCODE` ไม่ใช้ `Stop`, ติดตั้ง uv ใน PowerShell ลูกที่ Bypass, CRLF, `run_checks` รับ `sys_platform` | [setup-status](features/setup-status/decisions.md) | D23 | — | — | active |
| `npm run dev` start backend ด้วย Python ใน `.venv` ผ่าน `scripts/dev-api.mjs` ไม่พึ่ง uv ใน PATH; README ติดตั้งและใช้งานเป็นไทย | [setup-status](features/setup-status/decisions.md) | D24 | — | — | active |
| Status check เป็น checklist 9 รายการ ไม่โหลดโมเดล ไม่ใช้ network | [setup-status](features/setup-status/decisions.md) | D7 | — | [0004](adr/0004-pinned-model-registry.md) | active |

## ffmpeg

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ffmpeg มาจาก `imageio-ffmpeg` ใน venv, หา path ด้วย `get_ffmpeg_exe()` ไม่พึ่ง PATH | [setup-status](features/setup-status/decisions.md) | D4 | — | [0005](adr/0005-ffmpeg-from-imageio.md) | active |

## โมเดล AI

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| เก็บโมเดลใน `models/` ของ project ผ่าน `HF_HOME` | [setup-status](features/setup-status/decisions.md) | D6 | — | [0003](adr/0003-everything-inside-project.md) | changed by D13 |
| ใช้ OmniVoice แบบไม่หารายได้เท่านั้น, แสดง license | [setup-status](features/setup-status/decisions.md) | D11 | — | [0007](adr/0007-non-commercial-use.md) | active |
| revision ที่ pin และ `allow_patterns` ของ OmniVoice และ Whisper | [setup-status](features/setup-status/decisions.md) | D16 | — | [0004](adr/0004-pinned-model-registry.md) | active |

## UI design

| Decision | Feature | D | Used by | ADR | Status |
|---|---|---|---|---|---|
| ออกแบบหน้าจอใน Figma หลัง plan | [setup-status](features/setup-status/decisions.md) | D9 | — | — | active |
| แถวที่ไม่ `ok` แสดง `fix` จาก API ค่าเดียวเป็น chip พร้อมปุ่ม copy ไม่แสดงคำสั่งทั้งสอง OS | [setup-status](features/setup-status/decisions.md) | D15 | — | — | active |
| font มากับ `@fontsource` ใน project ไม่โหลดจาก CDN | [setup-status](features/setup-status/decisions.md) | D19 | — | [0003](adr/0003-everything-inside-project.md) | active |
| `fix` ไม่มีช่องว่าง = คำสั่ง (chip กับปุ่ม copy), มีช่องว่าง = ข้อความ | [setup-status](features/setup-status/decisions.md) | D20 | — | — | active |
| รายละเอียดหน้า Setup status: Refresh จาก offline, เวลาเช็คล่าสุด, pill คำเตือน, icon จาก Figma, timeout | [setup-status](features/setup-status/decisions.md) | D21 | — | — | active |
