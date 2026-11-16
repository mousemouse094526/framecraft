# Progress: kalimba-cover

**Now:** วางแผนเสร็จ ticket 01–03 พร้อม build; ยังไม่เริ่ม

**Next:**

```
/warroom-build kalimba-cover 01
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI | ready |
| 02 | เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา | ready |
| 03 | render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง | ready |

## Log

ยังไม่มี.

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01, 02, 03 | design: หน้า reel — ส่วนที่เพิ่ม, หน้าเพลงและรายการเพลง — ส่วนที่เพิ่ม | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D10); แบบ Figma ภายหลัง → `/warroom kalimba-cover` พร้อมลิงก์ | open |
| 2 | 02 | เจ้าของฟังคาลิมบาของเพลงที่แกะจากเสียง (Yellow 11.5–30 แกะใหม่) ว่ายังจำทำนองได้ไหม (D12) | เจ้าของ: เปิด `#/songs/Ssz69tFTS7Y/cover` เลือก "คาลิมบา" กด "ฟัง" แล้วตอบ จำได้ / ไม่ได้ → `/warroom kalimba-cover` ถ้าไม่ได้ | open |
| 3 | 02 | เสียงสังเคราะห์พอไหม หรืออยากได้ sample จริง VCSL "Kalimba, Tanzania" (CC0, 27 คีย์ ~23 MB โหลดผ่าน Setup ต้องเลื่อน pitch เสียงออก mbira) (D5) | เจ้าของตอบหลังฟัง → `/warroom kalimba-cover` | open |
| 4 | 03 | อยากให้รับ MusicXML (`.musicxml`, `.mxl` จาก MuseScore) ด้วยไหม; PDF และภาพไม่ทำ (D3) | เจ้าของตอบ → `/warroom kalimba-cover` (ticket แยก) | open |
| 5 | 03 | เจ้าของ import MIDI ทำนองแล้วรับ reel คาลิมบาว่าเล่นทำนองถูก (D12) | เจ้าของ: import `.mid` ที่ `#/songs` เปิด reel แล้ว render | open |
