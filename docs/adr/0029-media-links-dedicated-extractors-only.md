# Backend โหลดสื่อจากลิงก์เฉพาะเว็บที่ yt-dlp มีตัวโหลดเฉพาะ ไม่ใช้ generic extractor และ cookies

ลิงก์ที่ผู้ใช้วางไปถึง yt-dlp ด้วย `allowed_extractors: ["default", "-generic"]`, ไม่มี cookies หรือ login, และ host ที่เป็น loopback, private, link-local ถูกปฏิเสธก่อนยิง request. เพราะ generic extractor ทำให้ backend ยิง URL อะไรก็ได้ตาม redirect และลิงก์ในหน้า (การเช็ค host ไม่ resolve DNS จึงกันได้ไม่หมด) และ cookies ของผู้ใช้เปลี่ยนความเสี่ยงทางกฎหมาย; เว็บที่โหลดแบบนี้ไม่ได้ ผู้ใช้โหลดเองแล้วเอาไฟล์เข้าแทน. feature ต่อไปที่ยิง request ตามลิงก์ที่ผู้ใช้พิมพ์ใช้การเช็ค host ตัวเดียวกัน.

**Status:** accepted — extends ADR-0008

Source: spoil D47, D52, D55 · legal 7
