# 04: Backend งานถอดบทพูดและ API

**What to build:** ส่ง `POST /api/spoil/transcriptions` ด้วย `clip_id` ของ Temp clip แล้ว backend ถอดคำพูดทั้งคลิปด้วย Whisper large-v3-turbo ใน process ลูก; poll เห็น % จนจบ แล้วอ่าน Transcript เป็น JSON, `.txt` และ `.srt` ได้. ยกเลิกได้ทันที, crash ของ GPU ไม่ล้ม backend, ลบคลิปลบ Transcript ด้วย. ทุก `POST` ของสปอยต้องเป็น JSON.

**Blocked by:** 03: รายการ Temp clip

**Covers:**
- User stories: 8, 9, 11 (ฝั่ง API)
- Decisions: D21, D23, D24, D26, D27, D28, D29
- ADR: 0004, 0005, 0010, 0012, 0013
- Seams: 1 (ข้อของงานถอด), 3 (บน Mac)

**Status:** ready-for-agent

## Acceptance criteria

- ก่อนเขียนต่อ ลองกับโมเดลจริงตาม spec › Library assumptions (ข้อที่ ticket ของงานถอดต้องลอง): `float16` บน `mps`, long-form 300 วินาทีโดยไม่มี `chunk_length_s`, timestamp ภายในช่วง, process ลูก `spawn` import `backend` ได้ — ไม่ได้ข้อไหน หยุดแล้วถามตามที่ spec บอก
- test ของ seam 1 ทุกข้อที่เกี่ยวกับงานถอด, `415`, `transcribed`, `409` `transcribing` และการล้าง `*.tmp` ผ่านด้วย `start_worker` ปลอม ไม่โหลดโมเดลจริง
- `GET /clips` มี `transcribed` และไม่มีแถวของ `*.transcript.json`; รายการคลิปเดิมและงานโหลดทำงานเหมือนเดิม (test เดิมผ่านหมด)
- `POST /downloads` ที่ไม่ใช่ `application/json` → `415`; หน้าเว็บเดิมยังโหลดคลิปได้
- เช็คมือบน Mac ผ่าน `curl`: ถอดหนังภาษาอังกฤษยาวกว่า 1 ชั่วโมงที่โหลดไว้แล้วจน `done`, `language` เป็น `en`, สุ่ม 5 บรรทัดเวลาตรงเสียงภายใน 2 วินาที; ถอด Shorts ภาษาไทยได้ภาษา `th`
- เช็คมือ: ยกเลิกกลางหนัง → process ลูกหายภายใน 5 วินาที; ฆ่า process ลูกระหว่างถอดขณะมีงานโหลด → งานถอด `crashed` และงานโหลด `done`; ถอดพร้อมโหลดคลิปอื่น → ทั้งสอง `done`
- `.srt` ที่ได้เปิดใน VLC กับ mp4 แล้ว subtitle ตรงเวลา
- บันทึกผล Open Question 4 (รอยต่อช่วงตัดคำ) ใน progress
- README บอกเรื่องถอดบทพูดและที่เก็บ `{id}.transcript.json`
