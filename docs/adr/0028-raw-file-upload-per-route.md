# ไฟล์จาก browser ส่งเป็น body ดิบ application/octet-stream ใน request เดียว เฉพาะ route ในรายการ

route ที่รับไฟล์จากหน้าเว็บรับ body ดิบ `application/octet-stream` เขียนลง `.partial/` ทีละก้อนใน thread ไม่ใช่ `multipart/form-data` และไม่ใช่ Download job แบบ ADR-0010: % มาจาก upload progress ของ browser, ยกเลิกด้วยการตัดการเชื่อมต่อ, หยุดเมื่อไม่ได้ byte นาน 60 วินาที, และหน้าเว็บส่ง JSON `check` ก่อนเพราะ server ที่ตอบ error ก่อนรับ body ครบทำให้ browser เห็นแค่ network error. ข้อยกเว้นของ ADR-0013 เป็นราย route (ตอนนี้ `POST /api/spoil/imports` และ `POST /api/toon/series/{sid}/{kind}/{id}/ref/upload` ของ toon) route อื่นยังได้ `415`; type ที่จะเพิ่มต้องไม่อยู่ใน CORS-safelisted เพื่อให้ preflight ยังกันเว็บอื่นได้. ไม่ใช้ multipart เพราะเว็บอื่นส่ง form แบบนั้นได้โดยไม่ preflight.

Source: spoil D50, D52, D55

Links: [Fetch standard › CORS-safelisted request-header](https://fetch.spec.whatwg.org/#cors-safelisted-request-header)
