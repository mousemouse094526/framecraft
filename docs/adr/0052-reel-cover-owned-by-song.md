# reel cover เป็นข้อมูลของ Song: อยู่ใน folder ของเพลง ตาม `analysis` ปัจจุบัน และหายพร้อมเพลง

การตั้งค่า reel หนึ่งชุดต่อเพลงและผล render อยู่ใน folder ของ Song ใต้ lock ของเพลง drum-notes ไม่รู้ schema ของมันและลบไปกับ folder; `drum_cover` import drum-notes และ video-gen ได้ ไม่มีทางกลับ. ต่างจากบทเรียนที่เป็นสำเนาทางเดียว (ADR-0047) เพราะ reel ไม่มีหน้าแก้โน้ต มันคือการตีของเพลงนั้นเสมอ: แกะใหม่แล้วช่วงที่เก็บถูกดึงเข้าช่วงตอนอ่าน และผล render บันทึกช่วงกับเวลาแกะของตัวเอง (ADR-0034).

**Status:** accepted

Source: drum-cover D1, D2, D6
