# Decisions: setup-status

## D1: React เรียก Python ผ่าน FastAPI

**Chosen:** Backend เป็น FastAPI รันใน venv ของ project. Frontend เป็น React (Vite) เรียก backend ผ่าน HTTP JSON.

**Why:** งาน AI ทั้งหมด (TTS, Whisper, ffmpeg) อยู่ฝั่ง Python ที่เดียว และต่อยอดไป feature generate video ได้ตรงๆ.

**Rejected:**
- Node server แล้ว spawn python script ทีละงาน — มีสองภาษาฝั่ง server และต้องโหลดโมเดลซ้ำทุกครั้ง
- Electron หรือ Tauri desktop — หนักเกินไปสำหรับขั้นแรก

**From:** interview · **Status:** active

## D2: ใช้ uv และ pin Python 3.12

**Chosen:** ใช้ uv จัดการ `.venv` ใน project ด้วย Python 3.12 (uv ดาวน์โหลดให้เอง). Dependency lock อยู่ใน `uv.lock`.

**Why:** เครื่องมี Python 3.14 ซึ่ง torch และ OmniVoice อาจยังไม่มี wheel ให้. uv แยก Python ของ project ออกจาก Python ของเครื่อง.

**Rejected:**
- `python -m venv` กับ pip บน Python 3.14 — เสี่ยงไม่มี wheel ของ torch หรือ omnivoice
- conda หรือ miniforge — env อยู่นอก project และหนักกว่า

**From:** interview · **Status:** active

## D3: ติดตั้งด้วย script บน terminal, เว็บแค่แสดงสถานะ

**Chosen:** การติดตั้งทั้งหมดทำผ่าน setup script คำสั่งเดียว. หน้าเว็บอ่านสถานะอย่างเดียว มีปุ่ม Refresh และบอกคำสั่งที่ต้องรันเมื่อมีรายการขาด.

**Why:** ง่ายที่สุดสำหรับขั้นแรก ผู้ใช้ขอ "เอาง่ายก่อน". ไม่ต้องมี background job, progress stream หรือการกันกดซ้ำ.

**Rejected:**
- ปุ่ม Install บนเว็บ — ต้องมี background job และ progress stream, งานเยอะกว่ามาก
- ทั้งสองแบบ — ยังไม่จำเป็นในขั้นนี้

**From:** interview · **Status:** active

## D4: ffmpeg มาจาก imageio-ffmpeg ใน venv

**Chosen:** ใช้ package `imageio-ffmpeg` ใน venv ซึ่งมี ffmpeg binary สำหรับ macOS arm64 และ Windows x64. App หา path ของ ffmpeg ผ่าน `imageio_ffmpeg.get_ffmpeg_exe()` ไม่พึ่ง PATH.

**Why:** ต้องใช้บน Windows ได้และต้อง portable.

**Rejected:**
- Homebrew ของเครื่อง — ใช้บน Windows ไม่ได้และไม่ portable
- เช็ค PATH ก่อนแล้ว fallback — สองทาง ต้องทดสอบสองแบบ

**Details:**
- `get_ffmpeg_exe()` ดู env `IMAGEIO_FFMPEG_EXE` ก่อน แล้วจึง binary ที่มากับ package แล้วจึง ffmpeg ของระบบ
- ไม่มี ffprobe มาด้วย

**Sources:** [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)

**From:** interview · **Status:** active

## D5: รองรับ Mac Apple Silicon และ Windows NVIDIA

**Chosen:** Mac ใช้ torch ปกติ (device `mps`). Windows ใช้ torch CUDA 12.8 wheel (device `cuda`). หน้าสถานะแสดง device ที่ใช้ได้.

**Why:** rationale not recorded

**Rejected:**
- รองรับ Windows CPU-only ด้วย — ช้ามากตอน generate
- Mac ก่อน Windows ทีหลัง — ผู้ใช้ต้องการ Windows ตั้งแต่ขั้นนี้ (D4)

**Details:**
- torch pin `2.8.0` ตามที่ OmniVoice แนะนำ
- เลือก index ของ torch ตาม OS ผ่าน `[tool.uv.sources]` กับ marker `sys_platform`
- Linux, AMD และ Intel GPU ไม่อยู่ในขั้นนี้

**Sources:** [OmniVoice install](https://github.com/k2-fsa/OmniVoice) · [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/)

**From:** interview · **Status:** active

## D6: เก็บโมเดลใน `models/` ของ project

**Chosen:** ตั้ง `HF_HOME` ชี้ไป `./models` (อยู่ใน `.gitignore`). ทั้ง setup และ backend ใช้ค่าเดียวกัน.

**Why:** portable — ก๊อปทั้ง folder ไปเครื่องอื่นได้. ลบ project แล้วโมเดลหายไปด้วย. เช็คสถานะง่าย.

**Rejected:**
- HF cache กลางของเครื่อง (`~/.cache/huggingface`) — ไม่ portable

**From:** interview · **Status:** changed by D13

## D7: Status check เป็น checklist แบบเบา

**Chosen:** Refresh แสดง checklist 9 รายการ แต่ละรายการมีสถานะ `ok`, `missing` หรือ `warning` พร้อมเวอร์ชันและคำแนะนำถ้าขาด. ไม่โหลดโมเดลเข้า RAM และไม่ใช้ network.

**Why:** ผู้ใช้ต้องการดูว่าหลังรัน setup แล้วติดตั้งครบหรือยัง แบบ checklist.

**Rejected:**
- เช็คเบาบวกปุ่ม Smoke test — ยังไม่จำเป็น
- โหลดโมเดลจริงทุก Refresh — ช้ามากทุกครั้ง

**Details:**
- หน้าตาตาม sketch ใน [checklist-sketch.md](checklist-sketch.md)
- รายการทั้ง 9 อยู่ใน spec.md › Implementation › Status check

**From:** interview · **Status:** extended by spoil D9

## D8: setup.sh และ setup.ps1 บางๆ เรียก Python ตัวเดียว

**Chosen:** `setup.sh` (Mac) และ `setup.ps1` (Windows) ทำแค่ติดตั้ง uv ถ้ายังไม่มี แล้วเรียก `uv run python -m backend.setup` ซึ่งทำงานจริงทั้งหมด.

**Why:** logic อยู่ที่เดียว แก้ที่เดียว ทั้งสอง OS.

**Rejected:**
- เขียน script เต็มสองชุดแยก OS — ทำงานซ้ำกัน ต้องแก้สองที่ทุกครั้ง
- `npm run setup` — ให้ Node เป็นตัวสั่ง Python, ข้ามภาษาโดยไม่จำเป็น

**From:** interview · **Status:** active

## D9: ออกแบบหน้าจอใน Figma หลัง plan

**Chosen:** หน้าจอ Setup status ออกแบบใน Figma หลัง plan นี้ผ่าน gate. ระหว่างนี้ Source เป็น `pending` และ sketch ใน D7 เป็น brief.

**Why:** ผู้ใช้ขอให้ทำ design ใน Figma.

**Rejected:**
- ไม่ทำ design ใช้ sketch ตรงๆ — ผู้ใช้อยากได้ Figma
- ตั้ง shadcn/ui ตั้งแต่แรก — ยังไม่ได้เลือก

**From:** interview · **Status:** active

## D10: ค่าเริ่มต้นที่ planner เลือกให้

**Chosen:** ชุดค่าเริ่มต้นด้านโครงสร้างและการรัน ที่ผู้ใช้ไม่ได้ระบุ.

**Details:**
- **Layout:** `backend/` (Python package) กับ `frontend/` (Vite React TypeScript) ใต้ root เดียว — แยกสองภาษาชัด
- **Port:** backend `127.0.0.1:8000`, frontend `5173` — ค่า default ของ uvicorn และ Vite
- **Bind:** backend ฟังแค่ `127.0.0.1` — เครื่องมือใช้ในเครื่องเดียว ไม่เปิดให้เครื่องอื่นในวงแลน
- **Proxy:** Vite proxy `/api` ไป backend — ไม่ต้องตั้ง CORS
- **Run:** `npm run dev` ที่ root รัน backend และ frontend พร้อมกันด้วย `concurrently` — ทำงานบน Windows ได้
- **Tests:** pytest สำหรับ backend, Vitest กับ React Testing Library สำหรับ frontend — ตัวมาตรฐานของแต่ละฝั่ง
- **Styling:** Tailwind CSS — เบา, ตามแบบ Figma ได้ง่าย

**From:** gate · **Status:** active

## D11: ใช้ OmniVoice แบบไม่หารายได้เท่านั้น

**Chosen:** วิดีโอที่สร้างใช้ส่วนตัวหรือทดลองเท่านั้น. หน้าสถานะแสดง license ของแต่ละโมเดล.

**Why:** โมเดล OmniVoice เป็น CC-BY-NC และผู้ใช้ตอบว่าใช้ส่วนตัว ไม่หารายได้.

**Rejected:**
- เอาไปหารายได้ — ขัดเงื่อนไข NonCommercial ของ license

**Details:**
- จะใช้เชิงพาณิชย์เมื่อไร ต้องเปลี่ยน TTS ก่อน (ดู legal.md ข้อ 1)

**Sources:** [OmniVoice model card](https://huggingface.co/k2-fsa/OmniVoice) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

**From:** legal · **Status:** active

## D12: Portable คือก๊อป folder แล้วรัน setup ซ้ำ

**Chosen:** ทุกอย่างที่ project ใช้อยู่ใน folder ของ project ไม่พึ่งของที่ลงไว้ในเครื่อง. ย้ายเครื่องที่ OS เดียวกัน = ก๊อป folder แล้วรัน setup อีกครั้ง: โมเดลใน `models/` ใช้ต่อได้ ส่วน `.venv` สร้างใหม่ (ต้องมี internet).

**Why:** `.venv` ของ uv มี path แบบ absolute และ Python 3.12 อยู่นอก project จึงก๊อปข้ามเครื่องตรงๆ ไม่ได้. ผู้ใช้เลือกแบบที่เรียบง่ายกว่า.

**Rejected:**
- ก๊อปแล้วรันได้เลย offline — ต้องเก็บ Python และ cache ของ uv ใน project, folder ใหญ่ขึ้นมากและซับซ้อนกว่า
- ไม่สนการก๊อป folder — ผู้ใช้ต้องการ portable (D4)

**Details:**
- refine D4 และ D6: "portable" ใน feature นี้หมายถึงตาม D12

**From:** red team · **Status:** active

## D13: แก้ตาม red team

**Chosen:** ชุดกฎที่เพิ่มจาก red team เรื่อง Windows, การโหลดโมเดล, ความปลอดภัยของ setup และหน้าเว็บ.

**Details:**
- **Windows entry:** ใช้ `setup.cmd` ที่เรียก `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"` และ `setup.ps1` เป็น ASCII ล้วน — Windows ตั้ง execution policy เป็น `Restricted` และ PowerShell 5.1 อ่าน UTF-8 ไม่มี BOM ผิด
- **Pin โมเดล:** แต่ละโมเดล pin commit hash ไว้ใน `backend.models`. ข้ามการโหลดเมื่อ marker มี revision ตรงและไฟล์ครบ — กันโหลดหลาย GB ซ้ำเมื่อ upstream เปลี่ยน
- **Cache path:** ส่ง `cache_dir` ชัดเจนทุกครั้ง ไม่พึ่ง env `HF_HOME` — env ของเครื่องหรือ import ก่อนหน้าอาจชี้ที่อื่น
- **Marker เก็บรายการไฟล์:** check เทียบชื่อและขนาดไฟล์ — จับ snapshot ที่ถูกลบบางส่วน
- **Setup กันพัง:** lock กันรันซ้อน, เช็คที่ว่างดิสก์, ไม่รันถ้า backend เปิดอยู่ — Windows ล็อกไฟล์ `.pyd` ของ torch ที่ backend ใช้อยู่
- **torchaudio:** map ไป index `cu128` บน Windows เหมือน torch — ไม่งั้นได้ torchaudio CPU คู่กับ torch CUDA
- **หน้าเว็บ:** แสดงคำตัดสิน "พร้อม" จาก `ready`, timeout 30 วินาที, Refresh ล้มแล้วแทนด้วย offline, ข้อความ offline บอกทางแก้ทั้งสองกรณี — red team พบว่าผู้ใช้อ่านผลผิดได้
- **Test:** `backend.checks` รับ root และตัว probe แบบ inject ได้, มี test ของ `backend.setup` ที่ mock การโหลด — ให้ผล test ไม่ขึ้นกับเครื่อง

**From:** red team · **Status:** active

## D14: Conventions ของ backend และ frontend

**Chosen:** ใช้ conventions skill สองชุดใน project: `fastapi-api` สำหรับ `backend/` และ `vite-react-web` สำหรับ `frontend/` ตามโครงที่เสนอตอนตัด ticket.

**Why:** project ยังไม่มี code และ ticket ต้องตัดตามโครงที่ตกลงแล้ว. ผู้ใช้ยอมรับโครงที่เสนอ.

**Details:**
- backend แบน: `app`, `paths`, `models`, `checks`, `setup` และ `routes/` ต่อ feature — ตรงกับชื่อ module ใน spec
- frontend: `features/{feature}/components` กับ `hooks`, `lib/api.ts` — ยังไม่มี router จนกว่าจะมีหน้าที่สอง
- ยังไม่มี browser e2e tool — spec ใช้ Vitest และเช็คมือ

**From:** tickets · **Status:** active

## D15: คำสั่งแก้แสดงตาม OS ที่ backend รันอยู่ ไม่ใช่ทั้งสอง OS

**Chosen:** แถวที่ไม่ `ok` แสดงค่า `fix` จาก API ค่าเดียว เป็น chip พร้อมปุ่ม copy. ไม่แสดง chip Mac และ Windows คู่กันแบบใน Figma frame.

**Why:** ผู้ใช้เลือกตาม spec: API ส่ง `fix` ตาม OS ที่ backend รันอยู่แล้ว ไม่ต้องเปลี่ยน API และผู้ใช้ไม่สับสนว่าต้องรันอันไหน.

**Rejected:**
- แสดงทั้ง Mac และ Windows ตาม design — ต้องเปลี่ยน `fix` ใน API เป็นสองค่า และผู้ใช้เห็นคำสั่งที่ใช้กับเครื่องตัวเองไม่ได้

**Details:**
- ปุ่ม copy ข้าง chip มาจาก design. ไม่มี label `Mac` หรือ `Windows` นำหน้า
- `fix` ที่เป็นข้อความ ไม่ใช่คำสั่ง (เช่นแถว Device) แสดงเป็นข้อความธรรมดา ไม่มีปุ่ม copy

**From:** design link · **Status:** active

## D16: ไฟล์ที่โหลดและ revision ที่ pin ของโมเดล

**Chosen:** OmniVoice pin `c5fdb5c` โหลดแค่ `*.json`, `*.safetensors`, `*.jinja`. Whisper pin `41f01f3` โหลดแค่ `*.json`, `*.safetensors`, `*.txt`. ไม่โหลด README, LICENSE หรือ `.gitattributes`.

**Why:** ได้ไฟล์ที่ `transformers` และ `omnivoice` ต้องใช้ครบ (config, weights, tokenizer, chat template) โดยไม่มีไฟล์เกิน. commit hash คือล่าสุดของแต่ละ repo ณ 2026-10-29 ตาม spec.

**From:** build ticket 01 · **Status:** active

## D17: เช็คว่า PID ของ lock ยังทำงานแยกตาม OS

**Chosen:** Mac ใช้ `os.kill(pid, 0)`. Windows ใช้ `OpenProcess` กับ `GetExitCodeProcess` ผ่าน `ctypes`.

**Why:** บน Windows `os.kill(pid, 0)` เรียก `TerminateProcess` จึงฆ่า setup อีกหน้าต่างแทนการเช็ค.

**Details:**
- lock ที่อ่านเป็นเลขไม่ได้ถือว่าค้าง เขียนทับได้
- ทางของ Windows ยังไม่ได้รันจริง ticket 03 ต้องทดสอบ

**From:** build ticket 01 · **Status:** active

## D18: จุด inject สำหรับ test ของ checks และ setup

**Chosen:** `run_checks(root, device_probe, ffmpeg_probe)` ใช้ค่า default ตอนเรียก (ไม่ใช่ตอนประกาศ) จึง monkeypatch `backend.paths.ROOT` และ probe ใน test ของ API ได้. `run_setup` รับ `download`, `backend_running`, `free_bytes` และ probe ทั้งสอง. Cache ของ device อยู่ใน class `DeviceProbe` ที่ห่อตัว detect.

**Why:** ให้ test ผ่าน seam 1 ได้ทุกข้อโดยไม่โหลดโมเดล, ไม่ import torch และไม่ขึ้นกับเครื่อง. แยก cache ออกจาก torch ทำให้พิสูจน์กฎ "cpu ไม่ cache" ได้.

**From:** build ticket 01 · **Status:** active

## D19: font ของหน้าเว็บมากับ package ใน project

**Chosen:** ใช้ `@fontsource/ibm-plex-sans-thai`, `@fontsource/ibm-plex-mono`, `@fontsource/geist` และ `@fontsource/manrope` import ใน `frontend/src/index.css`. ไม่โหลดจาก Google Fonts.

**Why:** หน้าเว็บต้องหน้าตาเหมือน Figma แม้ปิด internet และทุกอย่างอยู่ใน project ตาม ADR 0003.

**Rejected:**
- Google Fonts CDN — ปิด internet แล้ว font หาย

**From:** build ticket 02 · **Status:** active

## D20: แยก `fix` ที่เป็นคำสั่งกับที่เป็นข้อความด้วยช่องว่าง

**Chosen:** `fix` ที่ไม่มีช่องว่าง (`./setup.sh`, `setup.cmd`) เป็นคำสั่ง แสดงเป็น chip พร้อมปุ่ม copy. `fix` ที่มีช่องว่างเป็นประโยค แสดงเป็นข้อความธรรมดา.

**Why:** ทำตาม D15 ได้โดยไม่ต้องเพิ่ม field ใน API. คำสั่งทั้งหมดที่ `backend.checks` ส่งเป็นคำเดียว ส่วนประโยคภาษาไทยมีช่องว่างเสมอ.

**Details:**
- ถ้าวันหนึ่ง `fix` เป็นคำสั่งที่มีช่องว่าง ให้เพิ่ม field บอกชนิดใน API แทน

**From:** build ticket 02 · **Status:** active

## D21: รายละเอียดหน้า Setup status ที่ spec ไม่ได้บอก

**Chosen:** ค่าที่ build ticket 02 เลือกเองตาม Figma และ conventions.

**Details:**
- **Refresh จาก offline:** ไม่มี checklist เดิมให้ค้าง จึงกลับไป state loading ("กำลังเช็ค…")
- **เวลาเช็คล่าสุด:** ตัด `HH:MM:SS` จาก `checked_at` ตรงๆ — backend อยู่เครื่องเดียวกัน และ test ไม่ขึ้นกับ timezone
- **คำตัดสินที่มีคำเตือน:** แสดง pill label ของแถว `warning` ข้างคำตัดสิน ตาม frame 3
- **Icon:** ใช้ SVG ที่ export จาก Figma ใน `features/setup-status/assets/` ไม่เพิ่ม `lucide-react`
- **Timeout:** `lib/api.ts` race ตัวจับเวลา 30 วินาทีกับ fetch แล้ว abort — fetch ที่ไม่สน signal ก็ยังจบ
- **ป้ายปุ่ม copy:** `คัดลอก {คำสั่ง}` สำหรับ screen reader
- **ข้อความ offline บรรทัดสาม:** ถ้อยคำตาม spec › Frontend ส่วนคำที่เป็น font mono (`error`, `terminal`, `npm run dev`, `setup`) ตาม frame 6
- **ปุ่ม Refresh ที่ disabled:** opacity 60% ทั้งตอน loading และ refreshing (Figma 55% กับ 60% ต่างกันจนมองไม่ออก)

**From:** build ticket 02 · **Status:** active

## D22: ต้องใช้ Node.js 22 ขึ้นไป

**Chosen:** setup, README และ spec บอก "Node.js 22+". ใช้ `concurrently` 10 และ Vite 8 รุ่นล่าสุดตามที่ spec ให้ติดตั้ง.

**Why:** `concurrently` 10 ต้องใช้ Node 22 ขึ้นไป และ Node 20 หมดอายุ (end-of-life) ตั้งแต่เดือนเมษายน 2026. ผู้ใช้เลือกตอน build ticket 02.

**Rejected:**
- คง "Node.js 20+" แล้ว pin `concurrently` 9 — Vite 8 ก็ยังต้องใช้ 20.19 ขึ้นไป และ Node 20 ไม่ได้รับ security fix แล้ว

**Details:**
- wrapper ยังเช็คแค่ว่ามี `node` กับ `npm` ไม่เช็คเวอร์ชัน

**Sources:** [docs/library-notes/concurrently.md](../../library-notes/concurrently.md) · [docs/library-notes/vite.md](../../library-notes/vite.md)

**From:** build ticket 02 · **Status:** active

## D23: รายละเอียดของ setup.cmd และ setup.ps1 ที่ spec ไม่ได้บอก

**Chosen:** ค่าที่ build ticket 03 เลือกเองตาม spec › Setup script และ conventions.

**Details:**
- **pause:** `setup.cmd` หยุดรอกดปุ่มก่อนจบเฉพาะเมื่อถูกรันแบบ `cmd.exe /c` (ดับเบิลคลิก, หรือ `.\setup.cmd` จาก PowerShell) — ดับเบิลคลิกแล้วหน้าต่างไม่ปิดก่อนอ่าน checklist. รันใน Command Prompt ไม่หยุด. exit ด้วย code ของ `setup.ps1` เสมอ
- **code page:** `setup.cmd` จำ code page เดิมจาก `chcp` แล้วคืนให้ก่อนจบ — `setlocal` ไม่คืน code page ให้
- **ไม่ใช้ `$ErrorActionPreference = 'Stop'`:** PowerShell 5.1 ที่ stderr ถูก redirect เปลี่ยน progress ของ uv เป็น error. เช็ค `$LASTEXITCODE` หลังทุกคำสั่งแทน
- **ติดตั้ง uv:** รัน installer ทางการ `0.13.6` ใน `powershell -ExecutionPolicy Bypass` ลูก (เปิด TLS 1.2 ก่อน) เพราะ installer ปฏิเสธ policy อื่นและจบด้วย `exit`. แล้วเพิ่ม `XDG_BIN_HOME`, `XDG_DATA_HOME\..\bin` หรือ `%USERPROFILE%\.local\bin` (ตัวแรกที่มี เหมือน installer) ใน PATH ของ session
- **CRLF:** `.gitattributes` บังคับ `*.cmd` และ `*.ps1` เป็น CRLF — `cmd.exe` อ่าน batch file ที่เป็น LF ผิด
- **ทดสอบ fix ตาม OS:** `run_checks` รับ `sys_platform` (default `sys.platform`) — test ข้อ "แถว fix บน Windows แสดง `setup.cmd`" ได้บน Mac. `IS_WINDOWS` ย้ายไป `backend.setup` ที่เดียวที่ใช้
- **Test ของ wrapper:** `backend/tests/test_wrappers.py` เช็คแค่ ASCII ของ `setup.ps1` และบรรทัด `chcp` กับ `powershell` ของ `setup.cmd` ตาม spec. การทำงานจริงเช็คมือบน Windows

**Sources:** [docs/library-notes/powershell.md](../../library-notes/powershell.md)

**From:** build ticket 03 · **Status:** active

## D24: `npm run dev` start backend ด้วย Python ใน `.venv` ไม่ใช่ `uv run`

**Chosen:** `[api]` ของ `npm run dev` เป็น `node scripts/dev-api.mjs` ที่เรียก `.venv/bin/python` (Windows: `.venv\Scripts\python.exe`) `-m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. ไม่มี `.venv` → พิมพ์ "ยังไม่ได้ติดตั้ง: รัน ./setup.sh ก่อน" (Windows: `setup.cmd`) และ exit 1.

**Why:** installer ของ uv เพิ่ม uv ใน PATH ให้ terminal ใหม่เท่านั้น. ผู้ใช้รัน setup แล้ว `npm run dev` ใน terminal เดิมได้ `uv: command not found` และหน้าเว็บขึ้น Backend offline (เจอบน Mac ของผู้ใช้). `.venv` มีทุกอย่างหลัง `uv sync` แล้ว จึงไม่ต้องพึ่ง uv ตอนรัน. ใช้ Node เพราะ `npm run dev` ต้องเลือก path ตาม OS.

**Details:**
- script ไม่ส่ง signal ต่อให้ uvicorn: concurrently ฆ่าทั้ง process tree อยู่แล้ว
- Ctrl+C ใต้ `npm run` ทำให้ uvicorn ได้ SIGINT สองครั้งและพิมพ์ traceback `CancelledError` ตอนปิด (มีตั้งแต่ใช้ `uv run`); ยังปิดครบและคืน port 8000 — ไม่แก้จนกว่าจะเป็นปัญหา
- README ส่วนติดตั้งและใช้งานเป็นภาษาไทยทีละขั้น สำหรับคนที่ไม่เคยใช้ terminal (ผู้ใช้เลือก)

**Sources:** [docs/library-notes/concurrently.md](../../library-notes/concurrently.md)

**From:** build ticket 03 · **Status:** active

## Sources

- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — `get_ffmpeg_exe()` และ binary ที่มากับ wheel (accessed 2026-10-28)
- [OmniVoice GitHub](https://github.com/k2-fsa/OmniVoice) — คำสั่งติดตั้ง torch และ MPS support (accessed 2026-10-28)
- [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) — เลือก torch index ตาม platform (accessed 2026-10-28)
- [OmniVoice model card](https://huggingface.co/k2-fsa/OmniVoice) — license CC-BY-NC (accessed 2026-10-28)
- [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — นิยาม NonCommercial และ attribution (accessed 2026-10-28)
