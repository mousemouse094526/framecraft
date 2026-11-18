# ชื่อ `lesson` ในโค้ด ข้อมูล และ API คงไว้ เปลี่ยนแค่คำบนจอ

identifier `lesson`/`chapters`, folder `media/drums/lessons/` และ path `/api/drums/lessons` เป็นชื่อภายในของ reel กลองที่ผู้ใช้ไม่เห็น และไม่เปลี่ยนโดยไม่มีงาน rename ที่ย้ายไฟล์ของเจ้าของด้วย; ข้อความที่ผู้ใช้เห็นต้องใช้คำของ reel (ADR-0065). เลือกแทนการเปลี่ยนชื่อทั้งระบบเพราะ `drum_cover` ใช้ `video_gen.lessons` ข้างใน และไฟล์เก่าต้อง migrate ซึ่งเสี่ยงทำทางทำ reel พัง.

Source: reels-only D4, D8
