# reel ของแต่ละเครื่องดนตรีมี timeline ชนิดของตัวเอง ไม่ขยาย `Timeline` ของกลอง

reel คาลิมบาใช้ `KalimbaTimeline` ที่ปัดโน้ตที่จัดแล้วเป็น sample ครั้งเดียว และเสียง ภาพ ตัวหนังสือของคาลิมบาอ่านเวลาจากมันเท่านั้น; กติกาเลขจังหวะเรียก function เดียวกับ `drum_cover.timeline`. เลือกแทนการใช้ `Timeline` เดิมที่ `piece` เป็นคีย์ เพราะ `assemble` ผูกกับลำดับชุดกลองและ round-robin ของ sample กลอง ซึ่งต้องแก้ของ video-gen ที่ใช้ร่วม. หลักโน้ตชุดเดียวขับเสียงและภาพของ ADR-0041 และเวลาจริงของ ADR-0051 จึงเป็นกติกาต่อคลิป ไม่ใช่ต่อชนิดของ timeline.

**Status:** accepted — extends ADR-0041, ADR-0051

Source: kalimba-cover D6, D8
