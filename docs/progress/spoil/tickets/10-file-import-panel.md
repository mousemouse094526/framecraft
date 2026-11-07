# 10: ปุ่มเลือกไฟล์และลากไฟล์มาวางใน tab คลิป

**What to build:** ใน tab คลิป ผู้ใช้กด "เลือกไฟล์ในเครื่อง" หรือลากไฟล์ mp4 มาวาง เห็น % ระหว่างส่ง ยกเลิกได้ แล้วได้แถว "ไฟล์ในเครื่อง" ที่ถูก highlight; ไฟล์ไม่ตรงหรือซ้ำเห็นข้อความตาม spec; error ของลิงก์ที่ชี้ให้เอาไฟล์เข้าชี้ไปที่ปุ่มนี้. ตามแบบใน Figma.

**Blocked by:** 09

**Covers:**
- Decisions: D49, D50, D51, D52 (หน้าเว็บ), D55 (XHR error)
- ADR: 0028
- Seams: 4 (ข้อของการเอาไฟล์เข้า)
- User stories: 15
- Screens: tab คลิป — ช่องลิงก์และการเลือกไฟล์ ([Figma 8113-60644](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8113-60644))

**Status:** ready

## Acceptance criteria

- seam 4 ทุกข้อของการเอาไฟล์เข้าผ่าน; test เดิมทั้งหมดผ่าน
- ทุก state และข้อความของ spec › Frontend › เอาไฟล์เข้า ทำตาม spec และแบบใน Figma ทั้ง desktop และ 375px
- `useFileImport` ส่ง `/imports/check` ด้วย `sendJson` ก่อน แล้ว `XMLHttpRequest` ที่ไม่มี timeout; `abort()` เมื่อกดยกเลิกหรือ unmount
- พื้นที่ลากวางกดได้ด้วยคีย์บอร์ด และมี label
- เช็คมือในหน้าเว็บจริง: ลากไฟล์ mp4 ยาวกว่า 1 ชั่วโมงมาวาง → % เดิน แถวใหม่เล่นได้; ยกเลิกกลางทาง → `.partial/` ว่าง
