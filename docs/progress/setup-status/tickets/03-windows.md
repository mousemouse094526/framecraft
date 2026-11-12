# 03: Windows NVIDIA

**What to build:** ผู้ใช้ Windows ที่มีการ์ด NVIDIA รัน `setup.cmd` ได้แม้ execution policy เป็น `Restricted` และ project อยู่ใน path ที่มีช่องว่างและภาษาไทย. ได้ทุกอย่างเหมือน Mac และหน้า Setup status แสดง 9/9 กับ Device `cuda`.

**Blocked by:** 02: หน้า Setup status และ npm run dev

**Covers:**
- Decisions: D5, D8, D13, D25
- ADR: 0014
- User stories: 6

**Status:** done

## Acceptance criteria

- `setup.cmd` เรียก `setup.ps1` ตาม spec › Setup script ด้วย `-ExecutionPolicy Bypass` → test ของ wrapper ผ่าน
- `setup.ps1` → มีแต่ตัวอักษร ASCII
- แถว `fix` บน Windows → แสดง `setup.cmd` ไม่ใช่ `./setup.sh`
- backend เปิดอยู่แล้วรัน setup → พิมพ์ "ปิด npm run dev ก่อนรัน setup" และ exit 1
- เช็คมือบนเครื่อง Windows จริงทุกข้อ → ย้ายไป `windows-check` 01 (D25)
