# 01: Setup บน Mac และ Status API

**What to build:** บน Mac Apple Silicon ผู้ใช้รัน `./setup.sh` ครั้งเดียว ได้ uv, Python 3.12, package ทั้งหมด, ffmpeg และโมเดลสองตัวที่ pin revision พร้อม Model marker แล้วเห็น checklist 9 รายการใน terminal. Backend รันด้วย `uv run --no-sync uvicorn backend.app:app --host 127.0.0.1 --port 8000` แล้ว `GET /api/setup/status` คืน checklist เดียวกันเป็น JSON. ขั้น `npm install` ของ setup ยังไม่อยู่ใน ticket นี้ (ticket 02).

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D4, D5, D6, D7, D8, D11, D12, D13, D14
- ADR: 0001, 0002, 0003, 0004, 0005, 0006, 0007
- Seams: 1
- User stories: 1, 4, 7
- Legal: 1

**Status:** ready-for-agent

## Acceptance criteria

### Project และ dependency

- `pyproject.toml` ตาม spec › pyproject → `uv lock` สำเร็จ และ lock มี torch กับ torchaudio `2.8.0+cu128` สำหรับ `win32` และ `2.8.0` จาก PyPI สำหรับ `darwin`
- `.gitignore` มี `.venv/`, `models/`, `node_modules/`
- `NOTICE.md` มีผู้สร้าง, ลิงก์ license และลิงก์โมเดลของ OmniVoice (CC BY-NC 4.0) และ Whisper (MIT)
- `README.md` มีคำสั่ง setup, วิธีย้ายเครื่อง (D12) และ Uninstall ตาม spec › Ops

### Setup

- Mac ที่ไม่มี uv และ ffmpeg รัน `./setup.sh` → จบด้วย exit 0, checklist ใน terminal ไม่มี `missing`, Device เป็น `mps`
- รัน `./setup.sh` ซ้ำทันที → ไม่มีการโหลดโมเดลซ้ำ และจบด้วย exit 0
- ไม่มี `node` บนเครื่อง → พิมพ์ "Node.js 20+ required: https://nodejs.org" และ exit 1
- backend เปิดอยู่ที่ `127.0.0.1:8000` แล้วรัน setup → พิมพ์ "ปิด npm run dev ก่อนรัน setup" และ exit 1
- `snapshot_download` ปลอมที่สำเร็จ → marker ถูกเขียน, แถวโมเดลเป็น `ok`, exit 0
- `snapshot_download` ปลอมที่ raise → ไม่มี marker, lock ถูกลบ, exit 1
- มี lock ของ PID ที่ยังทำงาน → exit 1 โดยไม่โหลดอะไร
- ที่ว่างดิสก์ปลอมน้อยกว่า 15 GB และมีโมเดลที่ยังไม่ `ok` → พิมพ์ที่ว่างที่มีกับที่ต้องการ และ exit 1
- ก๊อป folder ไป Mac อีกเครื่องแล้วรัน `./setup.sh` → ไม่มีการโหลดโมเดลซ้ำ (เช็คมือ)

### Status API

- root ปลอมครบ, device probe `cuda`, ffmpeg probe exit 0 → `ready: true`, `ok_count: 9`
- เหมือนบน แต่ device probe `cpu` → `ok_count: 8`, `warning_count: 1`, `ready: true`
- ไม่มี marker ของ OmniVoice → `model_omnivoice` เป็น `missing`, `ready: false`
- marker มีแต่ไฟล์หนึ่งหายหรือขนาดไม่ตรง → `model_omnivoice` เป็น `missing`
- marker `revision` ไม่ตรง `backend.models` → `model_omnivoice` เป็น `missing`
- ffmpeg probe raise → `ffmpeg` เป็น `missing` และ response ยังมีครบ 9 รายการ
- device probe คืน `cpu` แล้วครั้งถัดไปคืน `cuda` → ครั้งที่สองได้ `cuda`
- แถวโมเดลมี `license` ครบ `name`, `url`, `author`, `model_url`. แถวอื่น `license` เป็น `null`
- ปิด internet แล้วเรียก API → ผลเหมือนเดิม (เช็คมือ)
- เรียก API ซ้ำหลังครั้งแรก → ได้ผลภายใน 3 วินาที (เช็คมือ)
