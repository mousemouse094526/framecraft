# reel cover สร้าง `Timeline` จากการตีที่แกะได้ตามเวลาจริง ไม่ผ่าน Groove

`Timeline` มีผู้สร้างสองทาง: `build` ของบทเรียน และ `timeline.assemble` ที่รับเวลาจริงของการตีแล้วปัดเป็น sample ครั้งเดียว; `mixer`, `frame_at` และ `captions` ยังอ่านเวลาจาก `Timeline` เท่านั้น. เลือกแทนการสร้างบทเรียนหนึ่งท่อนจาก Groove เพราะการ quantize ลง 16 ช่องทำให้ feel ของ fill จริงหาย. การปัดลงช่องเหลือแค่ขั้นเลือกมือ ซึ่งไม่เปลี่ยนเวลาที่เล่นหรือวาด.

**Status:** accepted — extends ADR-0041

Source: drum-cover D3, D4, D5

**Extended by:** ADR-0057 (kalimba-cover)
