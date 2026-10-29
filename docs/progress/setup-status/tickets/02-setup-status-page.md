# 02: หน้า Setup status และ npm run dev

**What to build:** ผู้ใช้รัน `npm run dev` แล้วเปิด `http://localhost:5173` เห็นหน้า Setup status: คำตัดสินว่าพร้อมหรือยัง, checklist 9 แถวพร้อมคำสั่งแก้และ license ของโมเดล, ปุ่ม Refresh และข้อความ offline เมื่อ backend ไม่ตอบ. Setup เพิ่มขั้น `npm install` และพิมพ์ขั้นต่อไปตอนจบ.

**Blocked by:** 01: Setup บน Mac และ Status API

**Covers:**
- Decisions: D3, D7, D9, D10, D11, D13, D14
- ADR: 0001, 0007
- Screens: Setup status
- Seams: 2
- User stories: 2, 3, 4, 5
- Legal: 1

**Status:** ready-for-agent

## Acceptance criteria

### Run และ setup

- root `package.json` มี script `dev` ตาม spec › Run → `npm run dev` start ทั้ง backend และ frontend
- setup ขั้น 5 รัน `npm install` ที่ root และ `frontend` → รัน setup ซ้ำแล้วยังจบด้วย exit 0
- setup จบโดยไม่มี `missing` → พิมพ์ "ขั้นต่อไป: รัน npm run dev แล้วเปิด http://localhost:5173"

### หน้า Setup status

- response ครบ → เห็น 9 แถว, "พร้อมใช้งาน" และ "9/9"
- response มี `warning` หนึ่งแถว → เห็น "พร้อมใช้งาน (มีคำเตือน 1 รายการ)"
- response มี `missing` หนึ่งแถว → เห็น "ยังไม่พร้อม: ขาด 1 รายการ" และแถวนั้นแสดงข้อความ `fix`
- แถวโมเดล → เห็นชื่อ license, ผู้สร้าง, ลิงก์ license และลิงก์โมเดล
- เปิดหน้า ยังไม่ได้ response → เห็น "กำลังเช็ค…"
- กด Refresh → ปุ่ม disabled จนได้ผล แล้ว `checked_at` ใหม่แสดง
- fetch ล้มหรือเกิน 30 วินาที → เห็นข้อความ offline ทั้งสามบรรทัดตาม spec › Frontend
- ได้ผลแล้ว Refresh ล้ม → checklist หาย เห็นข้อความ offline
- หน้าตาตาม Figma frame ของ Setup status เมื่อ spec › Design มีลิงก์แล้ว
- `npm run dev` กับ backend ที่หยุด → หน้าแสดง offline. start backend แล้วกด Refresh → ได้ checklist (เช็คมือผ่าน Vite proxy)
