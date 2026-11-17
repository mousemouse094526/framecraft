# ภาพของ reel cover เป็นของ `drum_cover` แยกจากภาพของคลิปสอนกลอง

reel วาดชุดกลอง ไม้ เลนโน้ต และตัวนับด้วย `drum_cover.frames` กับ `drum_cover.captions` ของตัวเอง ออกแบบเพื่อให้คนดูอ่านออกว่าตีชิ้นไหน มือไหน ห้องไหน; คลิปสอนกลองยังใช้ `video_gen.frames`/`kit`/`lane`/`captions` ที่ตามคลิปอ้างอิง. ใช้ร่วมแค่ส่วนที่ไม่ใช่หน้าตา (`Timeline`, `mixer`, `_command`, พื้นหลัง, จังหวะการขยับไม้, สไตล์ข้อความ) และ prefactor ของ video-gen ต้องให้ผลเดิม. เลือกแทนการแก้ภาพที่ใช้ร่วม เพราะจะเปลี่ยนคลิปสอนที่ไม่มีใครขอ; ภาพของ feature ใหม่ที่วาดกลองให้เลือกหนึ่งในสองชุดนี้ หรือทำของตัวเองตามกติกาเดียวกัน (Pillow + ASS ADR-0040, เวลาจาก `Timeline` ADR-0041).

**Status:** accepted

Source: drum-cover D25, D26

**Extended by:** ADR-0058 (kalimba-cover)
