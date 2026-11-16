# เสียงคาลิมบาสังเคราะห์ในแอปด้วย numpy ไม่ใช้ sample

`kalimba_cover.sound.note(pitch, level)` สร้างเสียงแบบ additive ที่ seed ตายตัว จึงได้ทุก pitch ตรงเสียง ไม่มีไฟล์ให้ Setup script โหลด ไม่มีแถว Status check และ render ซ้ำได้ wav เดิมทุก byte. เลือกแทน VCSL "Kalimba, Tanzania" (CC0 แต่ตั้งเสียงแบบ mbira ไม่ตรง C major) และ sample ที่ไม่ชัดว่าเป็น CC0. เปลี่ยนเป็น sample ภายหลังทำที่ `sound.note` ได้โดยไม่แตะ timeline หรือภาพ แต่ sample นั้นต้องตามกติกาของ ADR-0042 (pin, Setup script, CC0, แถว Status check).

**Status:** accepted — extends ADR-0041, ADR-0042

Source: kalimba-cover D5, D12 · legal 3

Links: [VCSL](https://github.com/sgossner/VCSL)
