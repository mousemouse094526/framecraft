# ความสามารถที่ใช้โมเดลหรือตัวรันต่างกันต่อ OS มี spec ต่อ OS ใน registry แต่ใช้ id แถว Status check เดียว

เมื่อความสามารถหนึ่ง (เช่น Qwen) ใช้โมเดลหรือตัวรันต่างกันบน Mac กับ Windows แต่ละ OS มี spec ที่ pin ของตัวเองใน `backend.models` ใต้ id แถวเดียวกัน และโค้ดทุกจุดหา spec จาก OS ที่รันอยู่ ไม่อ้าง spec ของ OS ใด OS หนึ่งตรงๆ. Status check แสดงเฉพาะแถวตัวรันของ OS นั้นเมื่อพอร์ตเสร็จ (ก่อนพอร์ตยังเป็น `missing` ตาม ADR-0016). เลือกแบบนี้เพราะหน้าเว็บ gate และ `not_ready.rows` ผูกกับ id ของแถว; id ต่อ OS หรือแถวกลางต้องแก้ทุกจุดนั้น.

Source: windows-launch D3, D6

**Status:** accepted
