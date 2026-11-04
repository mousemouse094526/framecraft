# 06: Backend Trim job และ API

**What to build:** ส่ง `POST /api/spoil/trims` พร้อมช่วงเวลาแล้ว backend encode `{id}.mp4` ใหม่ที่ไม่มีช่วงเหล่านั้นแทนไฟล์เดิม เห็น % ผ่าน `GET /trims/current` และยกเลิกได้จนถึงขั้นแทนไฟล์. คลิปที่มี Transcript, Shot, การตัด EP หรือ Spoil draft ต้องยืนยันก่อน แล้วข้อมูลเหล่านั้นถูกลบเมื่อแทนไฟล์สำเร็จ; ระหว่างตัด งานอื่นของคลิปนั้นถูกปฏิเสธ และ restart กลางการแทนไฟล์ทำต่อจนครบ.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D36, D37, D41, D42, spoil-maker D49
- ADR: 0020, 0021
- Seams: 1 (ข้อของ Trim), 3a
- User stories: 12, 13 (ฝั่ง API)
- Legal: 6

**Status:** ready-for-agent

## Acceptance criteria

### งานตัด

- test ของ seam 1 ทุกข้อของ Trim ผ่าน; test เดิมทั้งหมดผ่าน
- ลองก่อนเขียนต่อตาม spec › Library assumptions (ข้อของงานตัด): `trim` กับ `concat` ของหนังจริงยาวกว่า 1 ชั่วโมงสองช่วงได้ภาพเสียงตรงกันที่รอยตัด; ไม่ตรง → หยุดแล้วถามผู้ใช้
- ทุกขั้นของ spec › Trim และทุก `code` ในตาราง error ของ Trim job ทำตาม spec
- argv ของ ffmpeg, การรวมช่วงและสูตร bitrate เป็น pure function ที่ test เรียกได้โดยไม่รัน ffmpeg

### คลิปเดียวกัน

- ระหว่าง Trim job: ถอด แก้บรรทัด ลบคลิป → `409` `trimming`; Describe, Draft, Voice, Render job และ `PUT` การตัด EP ของคลิปนั้น → `409` `clip_busy` (D42)
- Draft job เริ่มพร้อมขั้น `replacing` ไม่ค้าง (D42)
- start backend ขณะมี `{id}.trimming.json` → ทำต่อหรือย้อนตาม spec › Trim

### เช็คมือบน Mac

- seam 3a ทุกข้อของ Mac ผ่าน; เวลาที่ใช้ตัดหนัง 2 ชั่วโมงจดลง progress.md
- ตัดหนังที่ถอดไว้แล้วผ่าน `curl` → ได้ `409` `has_derived`; ส่งซ้ำพร้อม `confirm_derived_loss: true` → `done` และ `GET /clips` มี `transcribed: false`, `trimmed` สองช่วง
- ข้อ Windows ของ seam 3a เพิ่มเข้า `windows-check` 02 (Open Question 5)
