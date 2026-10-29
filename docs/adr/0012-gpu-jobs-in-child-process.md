# งานที่ใช้ GPU รันใน process ลูก สถานะยังอยู่ใน thread ของ backend

งานที่โหลดโมเดลและใช้ GPU (ถอดเสียง และต่อไปคือ TTS) รันใน `multiprocessing` process ลูกแบบ `spawn` ที่ส่งความคืบหน้าและผลกลับผ่าน queue; thread ใน backend ยังถือสถานะใน memory และเป็นผู้เขียนไฟล์ผลคนเดียว ตาม ADR-0010. เพราะ Metal หรือ CUDA crash ฆ่าทั้ง process ไม่ใช่ exception และจะล้มงานอื่นที่รันพร้อมกัน; process ลูกยังให้ยกเลิกได้ทันทีด้วย `terminate()` และคืน memory ครบเมื่อออก. งานที่ไม่ใช้ GPU (โหลดคลิป) ยังเป็น thread ตาม ADR-0010.

Source: spoil D28
