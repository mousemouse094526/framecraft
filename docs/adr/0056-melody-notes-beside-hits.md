# โน้ตทำนองเป็น `analysis.notes` แยกจาก `hits` และทุก Pick job ถอด Basic Pitch

`analysis` ของ Song มี `notes` (`t`, `pitch`, `level`) แยกจาก `hits`; ทุก Pick job ทั้งสองโหมดรัน Basic Pitch ครั้งเดียว โดย `null` = แกะก่อนมีโน้ตทำนอง, `[]` = ไม่พบ และในโหมดกลอง Basic Pitch ที่ไม่มีหรือพังให้ `null` โดยงานกลองจบตามเดิม. เลือกแทนการใส่ `pitch` ใน `Hit` (การตีของ ADTOF ไม่มี pitch และทุกที่ที่อ่าน `hits` ต้องกรอง) และแทนการถอดเฉพาะโหมดทำนอง เพราะเพลงมีผลแกะชุดเดียวที่ reel ทุกเครื่องดนตรีอ่าน (ADR-0052).

**Status:** accepted — extends ADR-0044, ADR-0052

Source: kalimba-cover D2, D14
