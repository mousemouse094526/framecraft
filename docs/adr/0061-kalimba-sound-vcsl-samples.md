# เสียงคาลิมบาเป็น sample VCSL "Kalimba, Tanzania" (CC0) ที่ pin commit และย้ายเข้า C major ในแอป

`kalimba_cover.sound.note` เล่น sample ของ VCSL "Kalimba, Tanzania" ที่ commit `c1ea7bc` ซึ่ง Setup script โหลดพร้อม sha256 ลง `models/kalimba/` มี marker และแถว Status check `kalimba_kit` ตามกติกาของ ADR-0042 (CC0, pin, Setup, แถวของตัวเอง). mbira ชุดนี้ไม่ได้ตั้งเสียงตรง C major และชื่อไฟล์ต่ำไปหนึ่งอ็อกเทฟ จึงเก็บ pitch ที่วัดจากเสียงจริงต่อไฟล์ แล้วแอปย้ายทุกโน้ตเข้าคีย์ และกรองเสียงซ่ากับคีย์อื่นที่ดังตามออกเอง; timeline และภาพไม่รู้ว่าเสียงมาจาก sample. เปลี่ยนชุด sample ต้องตรวจ license ใหม่และวัด pitch ใหม่.

**Status:** accepted — supersedes ADR-0059, extends ADR-0042

Source: kalimba-cover D18, D5 · legal 3

Links: [VCSL LICENSE ที่ commit c1ea7bc](https://github.com/sgossner/VCSL/blob/c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e/LICENSE)
