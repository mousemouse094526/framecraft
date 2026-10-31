# Feature ที่พึ่ง library ที่รันได้ OS เดียว ส่งบน Mac ก่อน และพอร์ตไป Windows เป็น feature แยก

ทุก feature เขียนโค้ดและ test สำหรับ Mac และ Windows และจบได้เมื่อเช็คบน Mac ผ่าน; การเช็คมือบน Windows เป็น ticket ใน `windows-check`. ยกเว้น feature ที่ต้องใช้ library หรือโมเดลที่รันได้แค่บน Mac (เช่น mlx-vlm): ส่วนนั้นทำบน Mac อย่างเดียว แถว Status check ของมันเป็น `missing` บน Windows และงานพอร์ตทั้งหมดเป็น feature ของตัวเอง เพราะการเลือก backend อีก OS ต้องลองโมเดลใหม่และไม่ควรขวาง feature ที่ใช้ได้แล้วบน Mac. ขอบเขต OS ที่รองรับยังเหมือน ADR-0014.

**Status:** accepted — supersedes ADR-0014

Source: spoil-maker D14, D50 · setup-status D5, D25
