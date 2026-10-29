# Progress: setup-status

**Now:** 02 done; 03 next — waits on a Windows NVIDIA machine (Blocked #2)

**Next:**

```
/warroom-build setup-status 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | Setup บน Mac และ Status API | done |
| 02 | หน้า Setup status และ npm run dev | done |
| 03 | Windows NVIDIA | ready |

## Log

### 02: หน้า Setup status และ npm run dev — done 2026-10-29

**Built:**
- `npm run dev` start backend (`[api]`) และหน้าเว็บ (`[web]`); เปิด `http://localhost:5173` เห็นหน้า Setup status: คำตัดสิน, checklist 9 แถว พร้อม license ของโมเดล, คำสั่งแก้เป็น chip กดคัดลอกได้, ปุ่ม Refresh และข้อความ offline (ตาม Figma ทั้ง 7 frame รวม mobile 375px)
- เช็คมือผ่าน Vite proxy แล้ว: หยุด backend → หน้าแสดง Backend offline; start backend แล้วกด Refresh → ได้ checklist 9/9
- `./setup.sh` รัน `npm install` ที่ root และ `frontend` หลังโหลดโมเดล; รันซ้ำบนเครื่องนี้ exit 0 และพิมพ์ "ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173"

**Decided:**
- D19 — font มากับ `@fontsource` ใน project ไม่โหลดจาก CDN
- D20 — `fix` ไม่มีช่องว่าง = คำสั่ง (chip กับปุ่ม copy), มีช่องว่าง = ข้อความ
- D21 — Refresh จาก offline กลับไป loading, เวลาเช็คล่าสุดตัดจาก `checked_at`, pill คำเตือน, icon SVG จาก Figma, timeout แบบ race
- D22 — ต้องใช้ Node.js 22+ (ผู้ใช้เลือก): `concurrently` 10 ต้องการ Node 22 และ Node 20 หมดอายุแล้ว

**For the next ticket:**
- 03: `setup.ps1` ต้องเช็ค `node`/`npm` และพิมพ์ "Node.js 22+ required: https://nodejs.org" เหมือน `setup.sh`; `_npm_install` ใช้ `shutil.which("npm")` เพื่อให้ได้ `npm.cmd` บน Windows แต่ยังไม่เคยรันจริง
- 03: `concurrently` ใน `npm run dev` ต้องลองบน Windows ว่า Ctrl+C ปิดทั้ง `[api]` และ `[web]`
- npm 11 เตือน `allow-scripts` สำหรับ `fsevents` (install script ถูกข้าม) ตอน `npm install`; ใช้งานได้ปกติ ไม่ต้องทำอะไรจนกว่าจะมีปัญหา
- ticket 01 ข้อ acceptance ยังเขียน "Node.js 20+" — เป็นประวัติ ไม่แก้; ค่าที่ใช้จริงคือ D22
- Review เสนอแต่ยังไม่ทำ: ถ้า `fix` เป็นคำสั่งที่มีช่องว่างเมื่อไร ให้ API ส่ง field บอกชนิดแทนการดูช่องว่าง (D20)

**Checks:** `uv run pytest` — 25 passed; `npm --prefix frontend test` — 12 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 01: Setup บน Mac และ Status API — done 2026-10-29

**Built:**
- Mac ที่ไม่มี uv และ ffmpeg รัน `./setup.sh` ครั้งเดียว ได้ uv, Python 3.12, package, ffmpeg และโมเดลสองตัว แล้วเห็น checklist 9/9 กับ Device `mps` (รันจริงบนเครื่องนี้ exit 0, รันซ้ำไม่โหลดซ้ำ exit 0)
- `GET /api/setup/status` คืน checklist เดียวกันเป็น JSON; เรียกซ้ำได้ผลใน 0.05 วินาที
- `NOTICE.md` กับ `README.md` (setup, ย้ายเครื่อง, Uninstall) และ library notes ใน `docs/library-notes/`

**Decided:**
- D16 — revision ที่ pin (`c5fdb5c`, `41f01f3`) และ `allow_patterns` ของสองโมเดล
- D17 — เช็ค PID ของ lock: `os.kill(pid, 0)` บน Mac, `OpenProcess` บน Windows
- D18 — จุด inject สำหรับ test ของ checks และ setup

**For the next ticket:**
- 02 เพิ่ม `npm install` ใน `run_setup` ระหว่างโหลดโมเดลกับลบ lock (spec › Setup script ขั้น 5) และ `package.json` กับ `npm run dev`; ข้อความ "ขั้นต่อไป" ของ setup อ้าง `npm run dev` อยู่แล้ว
- Schema ของ API (`StatusResponse`, `ChecklistItem`, `License`) อยู่ใน `backend.checks`; frontend ใช้ field ตาม spec › API
- 03: ทาง Windows ของ `_windows_pid_alive` และ `IS_WINDOWS` (fix เป็น `setup.cmd`) ยังไม่เคยรันจริง; `setup.ps1` ต้องติดตั้ง uv แบบ pin `0.13.6` เหมือน `setup.sh`
- Review เสนอแต่ยังไม่ทำ (ทำเมื่อมีผู้ใช้คนที่สอง): รวม `device_probe` กับ `ffmpeg_probe` เป็น type เดียว, ทำ Model marker เป็น type แทน dict, แยก schema ของ API ออกจาก `checks.py`
- เช็คมือที่เหลือให้ผู้ใช้: ก๊อป folder ไป Mac อีกเครื่องแล้วรัน `./setup.sh` ต้องไม่โหลดโมเดลซ้ำ; ปิด internet แล้วเรียก API ต้องได้ผลเหมือนเดิม

**Checks:** `uv run pytest` — 22 passed

- 2026-10-29: ได้ Figma design หน้า Setup status ใส่ใน spec › Design แล้ว (D15). Blocked #1 done

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 02 | design: Setup status | `/warroom setup-status` พร้อมลิงก์ Figma frame | done |
| 2 | 03 | เครื่อง Windows ที่มีการ์ด NVIDIA สำหรับทดสอบ (spec Open Question 1) | ผู้ใช้ยืนยันว่ามีเครื่อง แล้ว `/warroom-build setup-status 03` | open |
