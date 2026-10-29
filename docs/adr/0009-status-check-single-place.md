# Status check เป็นที่เดียวที่บอกว่าติดตั้งครบไหม

ทุก feature ที่ต้องใช้ package หรือ binary เพิ่ม เพิ่มแถวของตัวเองใน Status check (`backend.checks`) ไม่ทำหน้าเช็คแยก. Feature ตัดสินว่าพร้อมใช้จากแถวที่ตัวเองต้องใช้ ไม่ใช่จาก `ready` เพราะ `ready` เป็นเท็จเมื่อของที่ feature นั้นไม่ใช้ขาด (เช่นโมเดล). Check ทุกแถวไม่โหลดโมเดลและไม่ใช้ network.

Source: spoil D9 · setup-status D7
