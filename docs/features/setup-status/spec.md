# Spec: setup-status

ผู้ใช้รัน setup script คำสั่งเดียวเพื่อติดตั้ง Python env, OmniVoice, Whisper large v3 turbo และ ffmpeg แล้วเปิดหน้าเว็บดู checklist ว่าติดตั้งครบหรือยัง.

**Status:** ready-to-build

## Problem

จะทำเครื่องมือ generate video ที่ใช้ React เป็น UI และเรียก Python กับเครื่องมือ AI. ตอนนี้ยังไม่มีอะไรติดตั้งเลย และไม่มีทางรู้ว่าเครื่องไหนพร้อมใช้หรือขาดอะไร โดยเฉพาะเมื่อย้ายไปเครื่อง Windows.

## Solution

- รัน setup คำสั่งเดียว ได้ venv, package, ffmpeg และโมเดลครบ (D3, D8)
  - Mac: `./setup.sh`
  - Windows: `setup.cmd` (D13)
- รัน setup ซ้ำได้ปลอดภัย: ข้ามสิ่งที่มีแล้ว และโหลดโมเดลต่อจากที่ค้าง
- เปิดหน้าเว็บ เห็น checklist 9 รายการ พร้อมคำตัดสินว่าเครื่องพร้อมหรือยัง (D7, D13)
- กด Refresh แล้วเช็คใหม่ โดยไม่โหลดโมเดลและไม่ใช้ network (D7)
- ย้ายเครื่องที่ OS เดียวกัน: ก๊อป folder แล้วรัน setup ซ้ำ โมเดลไม่ต้องโหลดใหม่ (D12)

## User Stories

**ผู้ใช้ (เจ้าของเครื่อง)**
1. As a ผู้ใช้, I want รันคำสั่งเดียวแล้วติดตั้งทุกอย่าง, so that ไม่ต้องจำขั้นตอนติดตั้งเอง (D3, D8)
2. As a ผู้ใช้, I want เห็น checklist และคำตัดสินว่าพร้อมหรือยัง, so that รู้ว่าเครื่องพร้อมสำหรับ generate video (D7)
3. As a ผู้ใช้, I want กด Refresh หลังรัน setup ใหม่, so that เห็นสถานะล่าสุดโดยไม่ต้อง reload หน้า (D7)
4. As a ผู้ใช้, I want เห็นคำสั่งที่ต้องรันเมื่อรายการไหนขาด, so that แก้เองได้ (D3)
5. As a ผู้ใช้, I want เห็นว่า backend ไม่ทำงาน แยกจากรายการขาด, so that ไม่สับสนว่าติดตั้งพังหรือแค่ยังไม่ได้ start (D1)
6. As a ผู้ใช้ Windows, I want ทำข้อ 1–5 ได้เหมือน Mac, so that ใช้ได้ทั้งสองเครื่อง (D5)
7. As a ผู้ใช้, I want ก๊อป folder ไปอีกเครื่องแล้วรัน setup โดยไม่ต้องโหลดโมเดลใหม่, so that ย้ายเครื่องได้เร็ว (D12)

## Design

| Screen | User stories | Must show | Source |
|---|---|---|---|
| Setup status | 2, 3, 4, 5 | ชื่อ app; ปุ่ม Refresh (disabled ระหว่างเช็ค); เวลาเช็คล่าสุด; คำตัดสินจาก `ready` (D13); 9 แถวตามลำดับใน Status check แต่ละแถวมี icon ตาม `status`, label, `detail`, และ `fix` เมื่อไม่ `ok` (D7); แถวโมเดลแสดง license, ผู้สร้าง, ลิงก์ license และลิงก์โมเดล (D11); state loading, result, refreshing, offline ตาม Frontend; brief: [checklist-sketch.md](checklist-sketch.md); คำสั่งแก้แสดงแค่ `fix` จาก API ค่าเดียว ไม่ใช่ chip Mac และ Windows คู่กันใน frame (D15) | [Figma: framecraft — Setup status](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8004-7488) — frames: 1 loading, 2 result not ready, 3 ready with warning, 4 all ready, 5 refreshing, 6 offline, 7 mobile 375px |

## Expected Outcome

ผู้ใช้รู้ได้ในหน้าเดียวว่าเครื่องพร้อมสำหรับ feature generate video หรือยัง และต้องทำอะไรถ้ายังไม่พร้อม.
- **เครื่องใหม่ ยังไม่ติดตั้ง:** รัน setup จนจบ, setup บอกให้รัน `npm run dev` แล้วเปิด `http://localhost:5173`, หน้าเว็บแสดง "พร้อมใช้งาน"
- **โมเดลโหลดค้าง:** แถวโมเดลเป็น `missing` พร้อมคำสั่ง setup. รันใหม่แล้วโหลดต่อ
- **backend ไม่ได้ start หรือ start ไม่ขึ้น:** หน้าแสดง "Backend offline" พร้อมทางแก้ทั้งสองกรณี

**How success is judged:**
- Mac Apple Silicon ที่ไม่มี uv และ ffmpeg: `./setup.sh` จบด้วย exit 0 โดยไม่มีขั้นตอนมือนอกจากติดตั้ง Node.js. หน้าเว็บแสดง 9/9 และ Device `mps`
- Windows ที่มีการ์ด NVIDIA และ execution policy เป็น `Restricted`: ดับเบิลคลิกหรือรัน `setup.cmd` จบด้วย exit 0. หน้าเว็บแสดง 9/9 และ Device `cuda`
- Windows: project อยู่ใน path ที่มีช่องว่างและภาษาไทย (เช่น `C:\Users\me\งาน ทดสอบ\framecraft`) ยังผ่านข้อบน
- Refresh ได้ผลภายใน 3 วินาทีหลังครั้งแรก. ครั้งแรกหลัง backend start ไม่เกิน 20 วินาที (import torch)
- ปิด internet แล้ว Refresh ได้ผลเหมือนเดิม
- ลบไฟล์ `*.safetensors` หนึ่งไฟล์ใน snapshot ของ OmniVoice แล้ว Refresh: แถว OmniVoice model เป็น `missing`
- ก๊อป folder ไปเครื่อง Mac อีกเครื่องแล้วรัน `./setup.sh`: ไม่มีการโหลดโมเดลซ้ำ
- `npm run dev` กับ backend ที่หยุดอยู่: หน้าเว็บแสดง offline. start backend แล้วกด Refresh: ได้ checklist (เช็คมือ ผ่าน Vite proxy จริง)

## Implementation

### Modules touched
- **root**
  - `pyproject.toml` กับ `uv.lock` (D2, D5, D13)
  - `package.json` กับ script `dev` (D10)
  - `setup.sh`, `setup.ps1` และ `setup.cmd` (D8, D13)
  - `.gitignore`: `.venv/`, `models/`, `node_modules/`
  - `NOTICE.md`: attribution ของ OmniVoice (CC BY-NC 4.0) และ Whisper (MIT) (D11)
  - `README.md`: คำสั่ง setup, `npm run dev`, การย้ายเครื่อง (D12), Uninstall (Ops)
- **backend** (Python package, D10)
  - `backend.paths`: หา root ของ project จากตำแหน่ง package. ค่า `models_dir` = `{root}/models`, `hub_dir` = `{root}/models/hub`, `markers_dir` = `{root}/models/.setup` (D6)
  - `backend.models`: รายการโมเดลที่เดียว: `repo_id`, `revision` (commit hash ที่ pin), `allow_patterns`, `license`, `license_url`, `author`, `model_url` (D13)
  - `backend.checks`: สร้าง checklist 9 รายการ. ใช้ร่วมกันทั้ง API และ setup (D7)
  - `backend.setup`: ขั้นตอนติดตั้งทั้งหมด (D8)
  - `backend.app`: FastAPI app กับ route ใน API (D1)
- **frontend** (Vite React TypeScript กับ Tailwind, D10)
  - หน้า Setup status หน้าเดียว
  - Vite proxy `/api` ไป `http://127.0.0.1:8000`

### Dependencies

| Package | Version | ใช้ทำอะไร |
|---|---|---|
| `torch`, `torchaudio` | `==2.8.0` | runtime ของ OmniVoice และ Whisper (D5) |
| `omnivoice` | latest ตอน lock (0.2.x) | TTS |
| `transformers`, `accelerate` | latest ตอน lock, `transformers>=5.3` ตาม omnivoice | โหลด Whisper large v3 turbo (feature ถัดไป) |
| `huggingface_hub` | latest ตอน lock | ดาวน์โหลดโมเดล (D6) |
| `imageio-ffmpeg` | `==0.7.0` | ffmpeg binary (D4) |
| `fastapi`, `uvicorn` | latest ตอน lock | backend (D1) |
| `pytest`, `httpx` | dev group | test backend (D10) |
| `react`, `vite`, `tailwindcss`, `vitest`, `@testing-library/react`, `concurrently` | latest ตอนติดตั้ง | frontend (D10) |

### pyproject

ส่วนที่เป็น decision (D2, D5, D13):

```toml
[project]
requires-python = "==3.12.*"
dependencies = ["torch==2.8.0", "torchaudio==2.8.0", "..."]

[tool.uv.sources]
torch = [{ index = "pytorch-cu128", marker = "sys_platform == 'win32'" }]
torchaudio = [{ index = "pytorch-cu128", marker = "sys_platform == 'win32'" }]

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```

### Run

Script `dev` ใน `package.json` ที่ root (D10):

```text
concurrently -n api,web "uv run --no-sync uvicorn backend.app:app --host 127.0.0.1 --port 8000" "npm --prefix frontend run dev"
```

- `--no-sync`: `npm run dev` ไม่ติดตั้งอะไรเอง การติดตั้งเป็นงานของ setup เท่านั้น (D3)
- ไม่ใช้ `--reload`

### Setup script

Entry ตาม OS (D8, D13):

| OS | ผู้ใช้รัน | ทำอะไร |
|---|---|---|
| Mac | `./setup.sh` | ขั้น 1–4 ด้านล่าง |
| Windows | `setup.cmd` | `chcp 65001` แล้วเรียก `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"` |
| Windows | `setup.ps1` | ขั้น 1–4 ด้านล่าง. ไฟล์เป็น ASCII ล้วน ข้อความภาษาไทยทั้งหมดพิมพ์จาก Python |

ขั้นของ wrapper:
1. ถ้าไม่มีคำสั่ง `uv` → ติดตั้งด้วย installer ทางการของ uv แล้วเพิ่ม path ใน session ปัจจุบัน. installer เพิ่ม uv ใน PATH ของผู้ใช้ถาวร
2. ถ้าไม่มี `node` หรือ `npm` → พิมพ์ "Node.js 22+ required: https://nodejs.org" แล้ว exit 1 (D22)
3. `uv sync`
4. `uv run --no-sync python -m backend.setup` โดยตั้ง `PYTHONUTF8=1`

ถ้าขั้น 3 ล้มเพราะไฟล์ถูกล็อก (backend เปิดอยู่บน Windows) ผู้ใช้เห็น error ของ uv. ขั้น 1 ของ `backend.setup` กันกรณีนี้ในการรันครั้งถัดไป.

`backend.setup` ทำตามลำดับ:
1. ถ้า `127.0.0.1:8000` ตอบ → พิมพ์ "ปิด npm run dev ก่อนรัน setup" แล้ว exit 1
2. สร้าง lock `models/.setup/setup.lock` (เก็บ PID). มี lock อยู่และ PID นั้นยังทำงาน → พิมพ์ "setup กำลังรันอยู่อีกหน้าต่าง" แล้ว exit 1. PID ไม่ทำงานแล้ว → เขียนทับ
3. โมเดลไหนยังไม่ `ok` → ต้องมีที่ว่างบนดิสก์ของ project อย่างน้อย 15 GB ไม่งั้นพิมพ์ที่ว่างที่มีกับที่ต้องการ แล้ว exit 1
4. สำหรับแต่ละโมเดลใน `backend.models` (OmniVoice ก่อน, Whisper ทีหลัง):
   1. แถวของโมเดลนั้นเป็น `ok` อยู่แล้ว → ข้าม
   2. `snapshot_download(repo_id, revision=..., cache_dir=hub_dir, allow_patterns=...)`
   3. เขียน marker `models/.setup/{owner}--{name}.json`
5. `npm install` ที่ root และ `npm install --prefix frontend`
6. ลบ lock
7. พิมพ์ checklist จาก `backend.checks`
8. ไม่มี `missing` → พิมพ์ "ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173" แล้ว exit 0. มี `missing` → พิมพ์รายการที่ขาด แล้ว exit 1

Marker (JSON):

| Field | ค่า |
|---|---|
| `repo_id` | เช่น `k2-fsa/OmniVoice` |
| `revision` | commit hash ที่โหลด |
| `files` | รายการ `{ "path": ชื่อไฟล์ใน snapshot, "size": bytes }` |
| `size_bytes` | ผลรวมขนาด |
| `finished_at` | เวลา ISO 8601 |

กฎของ setup:
- รันซ้ำได้: `uv sync` ข้ามของที่มี, โมเดลที่ `ok` ถูกข้าม, `snapshot_download` โหลดต่อจากที่ค้าง
- ล้มกลางทาง → พิมพ์ขั้นที่ล้มกับ error, ลบ lock, exit 1. ไม่ลบสิ่งที่โหลดมาแล้ว
- marker เขียนหลังโหลดเสร็จเท่านั้น
- ไม่ใช้ env `HF_HOME` หรือ `HF_HUB_CACHE`. ส่ง `cache_dir` ทุกครั้ง (D13)
- `revision` ใน `backend.models` คือ commit hash ล่าสุดของแต่ละ repo ณ วันที่ build ticket. เปลี่ยนได้ด้วยการแก้ค่าแล้วรัน setup

### Status check

`backend.checks.run_checks(root, device_probe, ffmpeg_probe)` สร้าง 9 รายการตามลำดับนี้ (D7, D13). ค่า default ของ probe คือของจริง; test ส่งตัวปลอม.

| `id` | `label` | `ok` เมื่อ | ไม่ `ok` | `fix` |
|---|---|---|---|---|
| `python` | Python venv | Python `3.12.x` และ `sys.prefix` คือ `{root}/.venv` | `warning` ถ้ารันนอก `.venv` ของ project | รัน backend ด้วย `npm run dev` |
| `torch` | torch | `importlib.metadata.version("torch")` ได้ | `missing` | คำสั่ง setup |
| `transformers` | transformers | metadata version ได้ | `missing` | คำสั่ง setup |
| `omnivoice` | omnivoice | metadata version ได้ | `missing` | คำสั่ง setup |
| `fastapi` | fastapi | metadata version ได้ | `missing` | คำสั่ง setup |
| `ffmpeg` | ffmpeg | `get_ffmpeg_exe()` คืน path และ `{exe} -version` exit 0 ภายใน 5 วินาที. `detail` = เวอร์ชันและแหล่ง (`imageio-ffmpeg`, `IMAGEIO_FFMPEG_EXE` หรือ `system`) | `missing` | คำสั่ง setup |
| `model_omnivoice` | OmniVoice model | marker มี, `revision` ตรงกับ `backend.models`, ทุกไฟล์ใน `files` มีอยู่และขนาดตรง | `missing`. `detail` บอกว่าไม่มี marker, revision ไม่ตรง หรือไฟล์ไหนหาย | คำสั่ง setup |
| `model_whisper` | Whisper model | เหมือนแถวบน | `missing` | คำสั่ง setup |
| `device` | Device | `cuda` หรือ `mps` ใช้ได้ | `warning` ถ้าได้แค่ `cpu` | Mac: ต้องเป็น Apple Silicon. Windows: ติดตั้ง NVIDIA driver แล้วปิดและเปิด `npm run dev` ใหม่ |

"คำสั่ง setup" = `./setup.sh` บน Mac, `setup.cmd` บน Windows. เลือกตาม OS ที่ backend รันอยู่.

กฎของ check:
- ห้าม import `omnivoice` หรือ `transformers`. เช็ค package ด้วย `importlib.metadata` เท่านั้น
- device probe import `torch` ในครั้งแรกที่เช็ค. ผล `cuda` หรือ `mps` cache ไว้ตลอด process. ผล `cpu` หรือ error ไม่ cache
- ไม่ใช้ network
- อ่านแค่ชื่อและขนาดไฟล์ ไม่ hash
- รายการหนึ่งพังด้วย exception → รายการนั้นเป็น `missing` และ `detail` เป็นข้อความ error. รายการอื่นยังเช็คต่อ
- `ready` เป็น `true` เมื่อไม่มีรายการ `missing`. `warning` ไม่ทำให้ไม่พร้อม

### API

Backend ฟังที่ `127.0.0.1:8000` เท่านั้น (D10).

| Method | Path | Response |
|---|---|---|
| `GET` | `/api/setup/status` | `200` กับ JSON ด้านล่าง. ไม่มี error response อื่น เพราะทุก error อยู่ในรายการ |

```json
{
  "checked_at": "2026-10-28T17:42:10+07:00",
  "ready": false,
  "ok_count": 7,
  "warning_count": 1,
  "missing_count": 1,
  "total": 9,
  "items": [
    {
      "id": "model_omnivoice",
      "label": "OmniVoice model",
      "status": "missing",
      "detail": "ไม่พบ marker ใน models/.setup",
      "fix": "./setup.sh",
      "license": {
        "name": "CC BY-NC 4.0",
        "url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "author": "k2-fsa",
        "model_url": "https://huggingface.co/k2-fsa/OmniVoice"
      }
    }
  ]
}
```

- `status` เป็นหนึ่งใน `ok`, `missing`, `warning`
- `fix` เป็น `null` เมื่อ `ok`
- `license` มีเฉพาะแถวโมเดล แถวอื่นเป็น `null`

### Frontend

| State | เมื่อไร | แสดง |
|---|---|---|
| loading | เปิดหน้า ยังไม่ได้ response แรก | "กำลังเช็ค…" |
| result | ได้ `200` | คำตัดสิน, checklist, เวลา `checked_at`, "{ok_count}/{total}" |
| refreshing | กด Refresh | checklist เดิมค้างไว้, ปุ่ม Refresh disabled |
| offline | fetch ล้ม, ไม่ใช่ `200`, หรือเกิน 30 วินาที | แทน checklist ทั้งหมดด้วยข้อความ offline, ปุ่ม Refresh กดได้ |

คำตัดสิน:
- `ready` true และ `warning_count` 0 → "พร้อมใช้งาน"
- `ready` true และ `warning_count` > 0 → "พร้อมใช้งาน (มีคำเตือน {warning_count} รายการ)"
- `ready` false → "ยังไม่พร้อม: ขาด {missing_count} รายการ"

ข้อความ offline:
- "Backend offline"
- "ยังไม่ได้ start: รัน `npm run dev`"
- "รันอยู่แล้ว: ดู error ในบรรทัด `[api]` ของ terminal ที่รัน `npm run dev` หรือรัน setup ใหม่"

กฎอื่น:
- เช็คอัตโนมัติครั้งเดียวตอนเปิดหน้า. ไม่ poll
- ข้อความในหน้าเป็นภาษาไทย

### Library assumptions

| Library | Version | The plan needs | Docs |
|---|---|---|---|
| uv | latest | `[tool.uv.sources]` กับ marker `sys_platform` เลือก index `cu128` บน Windows และ PyPI บน Mac; `uv sync` ดาวน์โหลด Python ตาม `requires-python` | [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) |
| torch, torchaudio | 2.8.0 | มี wheel `cu128` cp312 `win_amd64` และ wheel cp312 macOS arm64 บน PyPI | [PyTorch install](https://pytorch.org/get-started/locally/) |
| omnivoice | 0.2.x | pure-Python wheel ติดตั้งได้ทุก OS, ใช้ repo `k2-fsa/OmniVoice`, รองรับ `mps` | [OmniVoice GitHub](https://github.com/k2-fsa/OmniVoice) |
| huggingface_hub | latest ตอน lock | `snapshot_download` รับ `revision`, `cache_dir`, `allow_patterns` และโหลดต่อจากที่ค้าง. Windows ไม่มี symlink → เก็บไฟล์จริงใน `snapshots/` | [HF download guide](https://huggingface.co/docs/huggingface_hub/guides/download) |
| imageio-ffmpeg | 0.7.0 | wheel macOS arm64 และ Windows x64 มี ffmpeg binary, `get_ffmpeg_exe()` คืน path | [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |

### Ops

- ใช้แค่ในเครื่อง ไม่ deploy
- ที่ดิสก์: project ประมาณ 10 GB (`.venv`, โมเดลสองตัว, `node_modules`) บวก cache ของ uv นอก project อีกหลาย GB

Uninstall (เขียนใน `README.md`):
- ลบ folder ของ project (`.venv`, `models/`, `node_modules/` อยู่ข้างในทั้งหมด)
- cache และ Python ของ uv: `uv cache clean` และ `uv python uninstall 3.12`
- ตัว uv เอง: ตามคู่มือ uninstall ของ uv

## Seams

สอง seam: API คืน checklist ที่ถูก และหน้าเว็บแสดงสิ่งที่ API คืน. Setup พิสูจน์ผ่าน seam 1 เพราะ setup กับ API ใช้ `backend.checks` ตัวเดียวกัน (D7).

1. **Status API** `GET /api/setup/status` และ `backend.setup` ที่ mock การโหลด
   - root ปลอมครบ (`.venv` ปลอมเป็น `sys.prefix`, marker กับไฟล์ครบ), device probe คืน `cuda`, ffmpeg probe คืน exit 0 → `ready: true`, `ok_count: 9`
   - เหมือนบน แต่ device probe คืน `cpu` → `ok_count: 8`, `warning_count: 1`, `ready: true`
   - ไม่มี marker ของ OmniVoice → `model_omnivoice` เป็น `missing`, `ready: false`
   - marker มีแต่ไฟล์หนึ่งหายหรือขนาดไม่ตรง → `model_omnivoice` เป็น `missing`
   - marker `revision` ไม่ตรง `backend.models` → `model_omnivoice` เป็น `missing`
   - ffmpeg probe raise → `ffmpeg` เป็น `missing` และยังมีครบ 9 รายการ
   - device probe คืน `cpu` แล้วครั้งถัดไปคืน `cuda` → ครั้งที่สองได้ `cuda`
   - `backend.setup` กับ `snapshot_download` ปลอมที่สำเร็จ → marker ถูกเขียน, แถวโมเดลเป็น `ok`, exit 0
   - `backend.setup` กับ `snapshot_download` ปลอมที่ raise → ไม่มี marker, lock ถูกลบ, exit 1
   - `backend.setup` ขณะมี lock ของ PID ที่ยังทำงาน → exit 1 โดยไม่โหลดอะไร
2. **หน้า Setup status** `frontend` หน้าแรก (Vitest กับ fetch ปลอม)
   - response ครบ → เห็น 9 แถว, "พร้อมใช้งาน" และ "9/9"
   - response มี `warning` หนึ่งแถว → "พร้อมใช้งาน (มีคำเตือน 1 รายการ)"
   - response มี `missing` → "ยังไม่พร้อม: ขาด 1 รายการ" และแถวนั้นแสดงข้อความ `fix`
   - แถวโมเดลแสดงชื่อ license, ผู้สร้าง, ลิงก์ license และลิงก์โมเดล
   - กด Refresh → ปุ่ม disabled จนได้ผล แล้ว `checked_at` ใหม่แสดง
   - fetch ล้ม → เห็นข้อความ offline ทั้งสามบรรทัด
   - ได้ผลแล้ว Refresh ล้ม → checklist หาย เห็นข้อความ offline

## Testing decisions

- **Copy:** ยังไม่มี test ใน project. Ticket แรกสร้าง pattern: `backend/tests/` ใช้ pytest กับ FastAPI `TestClient`, `frontend/src/**/*.test.tsx` ใช้ Vitest กับ React Testing Library (D10)
- Seam 1 สร้าง root ปลอมใน `tmp_path` และส่ง probe ปลอมเข้า `run_checks`. ไม่โหลดโมเดลจริงใน test
- Seam 2 ใช้ fetch ปลอม. Vite proxy พิสูจน์ด้วยการเช็คมือใน How success is judged
- การโหลดจริงและ Windows พิสูจน์ด้วยการรันจริงตาม How success is judged

## Out of Scope

- ปุ่ม Install หรือ progress การติดตั้งบนเว็บ (D3)
- Smoke test ที่โหลดโมเดลจริง (D7)
- ffprobe (D4)
- Linux, AMD GPU, Intel GPU และ Windows CPU-only (D5)
- ก๊อป folder แล้วรัน offline โดยไม่รัน setup (D12)
- การใช้เชิงพาณิชย์ (D11)
- generate video, TTS และ transcribe จริง — feature ถัดไป

## Open Questions

1. มีเครื่อง Windows ที่มีการ์ด NVIDIA ให้ทดสอบหรือไม่ — non-blocking: งาน Windows อยู่ ticket แยก ปิดได้เมื่อทดสอบบนเครื่องจริงผ่านเท่านั้น
2. feature ถัดไปที่ส่งไฟล์เสียงให้ Whisper ผ่าน `transformers` pipeline อาจต้องมี `ffmpeg` บน PATH — non-blocking: ขั้นนี้ไม่ transcribe

## Sources

- [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) — เลือก torch index ตาม OS (accessed 2026-10-28)
- [PyTorch install](https://pytorch.org/get-started/locally/) — wheel CUDA และ MPS (accessed 2026-10-28)
- [OmniVoice GitHub](https://github.com/k2-fsa/OmniVoice) — ติดตั้งและ MPS support (accessed 2026-10-28)
- [OmniVoice model card](https://huggingface.co/k2-fsa/OmniVoice) — repo id และ license (accessed 2026-10-28)
- [Whisper large v3 turbo model card](https://huggingface.co/openai/whisper-large-v3-turbo) — repo id และ license MIT (accessed 2026-10-28)
- [HF download guide](https://huggingface.co/docs/huggingface_hub/guides/download) — `snapshot_download`, `cache_dir`, `allow_patterns` (accessed 2026-10-28)
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — binary ใน wheel และ `get_ffmpeg_exe()` (accessed 2026-10-28)
