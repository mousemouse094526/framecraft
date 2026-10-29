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

**From:** interview · **Status:** active

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

## Sources

- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — `get_ffmpeg_exe()` และ binary ที่มากับ wheel (accessed 2026-10-28)
- [OmniVoice GitHub](https://github.com/k2-fsa/OmniVoice) — คำสั่งติดตั้ง torch และ MPS support (accessed 2026-10-28)
- [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) — เลือก torch index ตาม platform (accessed 2026-10-28)
- [OmniVoice model card](https://huggingface.co/k2-fsa/OmniVoice) — license CC-BY-NC (accessed 2026-10-28)
- [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — นิยาม NonCommercial และ attribution (accessed 2026-10-28)
