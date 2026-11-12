# 06: ส่วนที่ซ้ำและช่องโหว่เล็ก

**What to build:** render ของการ์ตูนเล่ากับของสปอยใช้ส่วนกลางชุดเดียว (ชื่อไฟล์ว่าง แถว gate ที่ต้องใช้ การลบผล) และหน้าเว็บของ tab poll Toon job ผ่าน hook เดียว. ผู้ใช้ที่ปิดหน้าเว็บระหว่างแปลงไฟล์เสียงจะไม่ได้เสียงนั้นเข้าคลัง, และ spec เขียน `409` `in_use` ตอนลบคลิปที่ player เปิดอยู่ตามที่ทำจริง.

**Blocked by:** 05: แยกงานของ toon ออกเป็นส่วน

**Covers:**
- Decisions: D45, spoil-maker D20, spoil-maker D21
- ADR: 0009, 0026, 0028
- Seams: 1 (Sound import)
- Blocked: #15, #16, #17, #18 (feature review)

**Status:** done

## Acceptance criteria

### backend

- ชื่อไฟล์ผลที่ว่าง, แถว gate ที่ render ต้องใช้ และการลบผล (mp4 ก่อน json ท้าย) อยู่ module กลางตามกติกา "Where shared code goes" ของ backend; `toon.render` และ `spoil_maker.render` เรียกตัวนั้น → test render ของทั้งสอง feature ผ่านเหมือนเดิม
- `episodes.list_for` ไม่ import `render` ในฟังก์ชัน; ไม่มี import วนระหว่าง module ของ `toon`
- แถว `diffusers` และ `gguf` เขียนที่เดียว: Status check และ `gate_rows.klein` ได้แถวเดียวกัน → test ของ Status check และ gate ของ klein ผ่าน
- Sound import ไฟล์ แล้วหน้าเว็บหายระหว่าง ffmpeg แปลง → ffmpeg หยุด, ไม่มีเสียงใหม่ใน `sounds.json`, ไม่มีไฟล์ค้างใน `.partial/`
- ลบคลิปที่ player เปิดอยู่ → `409` `in_use` (เหมือน spoil-maker spec › `DELETE /renders/{name}`); spec › Modules touched และตาราง route ของ toon เขียนรหัสนี้

### หน้าเว็บ

- `useCast`, `usePickRef`, `useEp` poll `JOB_PATH` ผ่าน hook เดียว → test ของทั้งสามผ่านเหมือนเดิม
- test เทียบ `GENRE_DEFAULTS` ของหน้าเว็บกับ `DEFAULTS` ของ backend → ค่าที่ต่างกันทำให้ test ตก
- กด "ฟัง" ของการ์ด → เล่นเสียงเล่าของการ์ดนั้น (test ใหม่; test เดิมแค่เห็นปุ่ม)
- กด "ฟัง" ของแถวในคลังเสียงพื้น → เล่นเสียงนั้น (test ใหม่)
- `npm test`, `npm run build` และ CI ทั้งหมดเขียว
