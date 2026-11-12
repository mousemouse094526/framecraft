# feature ที่อ้าง Saved voice ลงทะเบียนตัวเช็คกับ Saved voice และ Saved voice ที่ถูกอ้างลบไม่ได้

ทุก feature ที่เก็บ `voice_id` ของ Saved voice ลงทะเบียนตัวเช็คใน `backend.spoil_maker.voices` และการลบ Saved voice ที่ตัวเช็คใดบอกว่าใช้อยู่ได้ `409` `voice_in_use`. เลือกแบบนี้แทนการลบตามหรือซ่อน เพื่อไม่ให้ draft, Series หรือ EP ค้างกับเสียงที่หายไป และให้ `voices` ไม่ต้อง import feature ที่ใช้มัน. feature ใหม่ที่อ้าง Saved voice โดยไม่ลงทะเบียนทำให้กติกานี้พัง.

Source: spoil-maker D43, toon D25

**Status:** accepted
