# 01: เช็ค setup-status บน Windows NVIDIA

**What to build:** ผู้ใช้ Windows ที่มีการ์ด NVIDIA รัน `setup.cmd` ได้แม้ execution policy เป็น `Restricted` และ project อยู่ใน path ที่มีช่องว่างและภาษาไทย. ได้ทุกอย่างเหมือน Mac และหน้า Setup status แสดงทุกแถว `ok` กับ Device `cuda`.

**Blocked by:** setup-status 03: Windows NVIDIA

**Covers:**
- Decisions: setup-status D5, setup-status D13, setup-status D17, setup-status D22, setup-status D23, setup-status D24, setup-status D25
- ADR: 0014
- Seams: 1

**Status:** ready-for-agent

## Acceptance criteria

### setup.cmd

- ทำตามขั้น Windows ใน README ทีละขั้น → ติดตั้งได้โดยไม่ต้องถาม
- policy `Restricted` และไม่มี uv รัน `setup.cmd` → ติดตั้ง uv `0.13.6`, exit 0, checklist ไม่มี `missing`, Device เป็น `cuda`
- ดับเบิลคลิก `setup.cmd` → จบแล้วหยุดรอกดปุ่ม และ code page ของ terminal กลับเป็นค่าเดิม
- ไม่มี Node.js → พิมพ์ "Node.js 22+ required: https://nodejs.org" และ exit ไม่เป็น 0
- `npm install` ของ setup → หา `npm.cmd` เจอ และ `node_modules` ทั้ง root กับ `frontend` ครบ
- project อยู่ที่ `C:\Users\{user}\งาน ทดสอบ\framecraft` → ข้อบนยังผ่าน และข้อความไทยใน terminal อ่านออก
- torch โหลด DLL จาก `.venv` ใน path ภาษาไทยได้ → แถว torch และ Device `ok`
- backend เปิดอยู่แล้วรัน `setup.cmd` → พิมพ์ "ปิด npm run dev ก่อนรัน setup" และ exit 1
- setup ค้าง lock ไว้แล้วรันใหม่ → เช็ค PID ด้วย `OpenProcess` แล้วรันต่อได้

### npm run dev

- `npm run dev` แล้วเปิด `http://localhost:5173` → "พร้อมใช้งาน" และทุกแถว `ok`
- `scripts/dev-api.mjs` → หา `.venv\Scripts\python.exe` เจอ และข้อความไทยของ script ใน Command Prompt อ่านออก
- Ctrl+C → ปิดทั้ง `[api]` และ `[web]` และ port 8000 กับ 5173 ว่าง
- ปิด internet แล้วกด Refresh → ได้ผลเหมือนเดิม
