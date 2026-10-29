# 03: Windows NVIDIA

**What to build:** ผู้ใช้ Windows ที่มีการ์ด NVIDIA รัน `setup.cmd` ได้แม้ execution policy เป็น `Restricted` และ project อยู่ใน path ที่มีช่องว่างและภาษาไทย. ได้ทุกอย่างเหมือน Mac และหน้า Setup status แสดง 9/9 กับ Device `cuda`.

**Blocked by:** 02: หน้า Setup status และ npm run dev

**Covers:**
- Decisions: D5, D8, D13
- ADR: 0006
- User stories: 6

**Status:** ready-for-agent

## Acceptance criteria

- `setup.cmd` เรียก `setup.ps1` ตาม spec › Setup script → ทำงานบนเครื่องที่ execution policy เป็น `Restricted`
- `setup.ps1` → มีแต่ตัวอักษร ASCII
- Windows ที่ไม่มี uv รัน `setup.cmd` → จบด้วย exit 0, checklist ไม่มี `missing`, Device เป็น `cuda` (เช็คมือบนเครื่องจริง)
- project อยู่ที่ `C:\Users\{user}\งาน ทดสอบ\framecraft` → ข้อบนยังผ่าน และข้อความไทยใน terminal อ่านออก (เช็คมือ)
- `npm run dev` แล้วเปิด `http://localhost:5173` → หน้าแสดง "พร้อมใช้งาน" และ 9/9 (เช็คมือ)
- แถว `fix` บน Windows → แสดง `setup.cmd` ไม่ใช่ `./setup.sh`
- backend เปิดอยู่แล้วรัน `setup.cmd` → พิมพ์ "ปิด npm run dev ก่อนรัน setup" และ exit 1
