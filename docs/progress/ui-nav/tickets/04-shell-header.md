# 04: แบรนด์อยู่หัวเมนู หัวหน้าเป็นหัวข้อของหน้า

**What to build:** หัวของเมนูหลัก (sidebar และ drawer) มี wordmark "framecraft" กับปุ่ม "ยุบเมนู" (sidebar) หรือ "ปิดเมนู" (drawer). หัวคอนเทนต์ของทุกหน้าเหลือ ☰ ไม่มีขอบ (เฉพาะตอนเมนูไม่เห็นบนจอนั้น) ชิดหัวข้อหน้า `<h1>` ที่เห็นได้ และ action ของหน้าทางขวา แถวเดียวกันทุกจอ. พฤติกรรมเดิมของเมนู (hash, `aria-current`, ค่ายุบ, drawer, `inert`, leave guard) ไม่เปลี่ยน.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D14 (changes D4, D10)
- Screens: เมนูหลักและหัวหน้า (ทุกหน้า)
- Seams: 1
- User stories: 1, 5, 6

**Status:** done

## Acceptance criteria

### หัวเมนู

- จอ ≥1280px sidebar เปิด: ในเมนูหลักมี wordmark และปุ่มธรรมดา "ยุบเมนู" (ไม่มี `aria-expanded`); หัวหน้าไม่มีปุ่ม ☰ (e2e)
- กด "ยุบเมนู" → เมนูซ่อน `framecraft.nav.collapsed` = `"true"` ☰ โผล่ในหัวหน้า (`aria-expanded="false"`) และได้โฟกัส; โหลดใหม่ยังยุบ (e2e)
- กด ☰ ตอนยุบ → เมนูกลับมา ค่ายุบถูกลบ โฟกัสไป "ยุบเมนู" (e2e)
- จอ <1280px drawer เปิด: ในเมนูมี wordmark และปุ่ม "ปิดเมนู"; กดแล้ว drawer ปิดและโฟกัสกลับ ☰ (e2e)

### หัวหน้า

- `<h1>` ที่เห็นได้ ข้อความ = ข้อความตำแหน่ง (D11) ทุกแถวของ spec › Implementation › Hash; `banner` ยังมีข้อความนั้น; ☰ ยังชื่อ "เมนู: {ข้อความตำแหน่ง}" (e2e)
- จอ <1280px: ☰ `aria-expanded` และ `aria-controls` เหมือนเดิม; drawer เปิดแล้ว action และเนื้อหา `inert` ส่วน ☰ กับปุ่มในเมนูไม่ (e2e)

### ข้าม 1280px

- โฟกัสบน ☰ แล้วจอกว้างขึ้น (sidebar เปิด) → โฟกัสไป "ยุบเมนู"; จอแคบลง → โฟกัสไป ☰ (e2e)
- จอแคบลงขณะ sidebar เปิด → ☰ โผล่ `aria-expanded="false"` และปุ่มในหัวเมนูชื่อ "ปิดเมนู"

### ไม่พังของเดิม

- เขียนใหม่ตั้งใจ (D8, D14): describe "menu from 1280px" ทั้งชุดหาปุ่ม "ยุบเมนู" ในเมนูแทน ☰ ตอน sidebar เปิด; test ที่เลือกคลังคลิปบน sidebar ตรวจ `<h1>` แทนชื่อ ☰
- test เดิมของ drawer (โฟกัสรายการที่เปิดอยู่, `Esc`, กดนอก, เลือกแล้วโฟกัสกลับ ☰, leave guard ยอม/ไม่ยอม, ข้าม 1280px) ผ่าน (e2e)
- `uv run pytest`, `typecheck`, `test`, `build` ผ่าน
- ภาพแคปจากของจริง (dev server พอร์ต 5174): 375px drawer ปิดและเปิด, 1280px sidebar เปิดและยุบ, 1440px — path ลง `progress.md`
