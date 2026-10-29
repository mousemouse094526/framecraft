# งานยาวรันเป็น daemon thread ใน backend, สถานะอยู่ใน memory และหน้าเว็บ poll

งานที่ใช้เวลานาน (โหลดคลิป และต่อไปคือ render หรือ TTS) รันเป็น daemon thread ใน FastAPI process เดียว (ADR-0001). สถานะงานอยู่ใน memory หน้าเว็บ poll สถานะ และงานหายเมื่อ backend restart; ไฟล์ค้างถูกล้างตอน start. ไม่ใช้ job queue หรือ worker process แยก เพราะเป็นแอปผู้ใช้คนเดียวบนเครื่องเดียว และ request เดียวรอจนเสร็จไม่บอกความคืบหน้า.

Source: spoil D6, D14
