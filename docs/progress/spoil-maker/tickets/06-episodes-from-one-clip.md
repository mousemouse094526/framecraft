# 06: ตัด EP จากคลิปเดียว

**What to build:** ขั้น 1 ของ tab สปอยเลือก Temp clip ได้คลิปเดียว แอปตัดคลิปเป็น EP ตามความยาวต่อ EP (5–60 นาที ตั้งต้น 30) ที่ขอบ Shot ผู้ใช้เลื่อนจุดตัดเองได้ แล้วเลือก EP เดียวเพื่อร่างบท. บทอ้างเฉพาะบรรทัดของ EP, Shot มาจากช่วงของ EP, และผล render บอกว่าเป็น EP ไหน. แทนการเลือกหลาย Temp clip เรียงเป็น EP แบบเดิม (D5).

**Blocked by:** —

**Covers:**
- Decisions: D66, D67, D69, D70, D71 (ยกเว้นข้อตัวบอกขั้น)
- Screens: ตั้งค่าคลิปสปอย — `pending` (Blocked 13), current [Figma: Spoiler setup](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681); ตัวเลือก Shot ("ดูทั้ง EP"); ผล render ("EP {n}")
- Seams: 1 (EP, Draft, Render, ลบคลิปและ start), 2 (หน้าตั้งค่า, ตัวเลือก Shot)
- User stories: 5, 6, 14

**Status:** ready

## Acceptance criteria

### การตัด EP (spec › EP)

- `GET /clips/{id}/episodes` ของคลิปที่ไม่มีไฟล์การตัด → ตัดตาม `ep_minutes` ที่ขอบ Shot แล้วเขียน `media/temp/episodes/{id}.json` ทันที; `PUT` คลิปอื่นภายหลังไม่เปลี่ยนการตัดของคลิปนี้
- `PUT` `{minutes}` ตัดใหม่ `custom: false` และเขียน `ep_minutes`; `PUT` พร้อม `cuts` → จุดตัดขยับไปเวลาเริ่มของ Shot ที่ใกล้สุด (เท่ากันเลือกก่อน) `custom: true`
- กฎและรูป request ตาม spec › EP → ไม่ผ่าน `400` `invalid_episodes`; EP เดียวทั้งคลิปใช้ได้แม้สั้นกว่า 60 วินาที
- ไฟล์การตัดอยู่ใต้ lock ของ `backend.gpu`; `PUT` ระหว่าง Describe, Transcribe, Draft job ของคลิปหรือระหว่างลบคลิป → `409` `clip_busy`; tmp ชื่อไม่ซ้ำ
- ไฟล์การตัดเสีย → `GET` `200` ตัดตาม `ep_minutes` และ log เหตุผล
- Describe job ลบไฟล์การตัดตอนสลับ folder Shot; ลบ Temp clip ลบไฟล์การตัด; start ลบ `*.tmp` และไฟล์ของคลิปที่ไม่มีแล้ว
- `GET` คืน `lines`, `tokens` (ไม่มี tokenizer → `null` ไม่ใช่ `503`), `renders`, `in_draft` ต่อ EP ที่เทียบด้วยช่วง
- `settings.json` อ่าน-แก้-เขียนใต้ lock เดียวผ่าน `.tmp` แล้ว rename
- ทุก test ใน spec › Seams 1 › EP ผ่าน

### Spoil draft และ Draft job

- `draft.json` `version` 2 มี `clip_id` และ `ep {n, start_s, end_s}`; `version` 1 → `GET /draft` เป็น `null`
- `POST /draft-jobs` `{clip_id, ep: {n, start_s, end_s}, …}`: เลข `n` ไม่มี `400` `invalid_episodes`; ช่วงไม่ตรง `409` `episodes_changed`; EP ไม่มีบรรทัด `400` `ep_empty`; token ของ EP เกิน 32,000 `400` `transcript_too_long`
- LLM ได้เฉพาะบรรทัดที่เริ่มในช่วง EP เป็น `[{line} {hh:mm:ss}]`; ref นอก EP ถูกตัดออก; ช่วง ±30 วินาที (`window`) ตัดให้อยู่ใน EP
- `PATCH /draft/sentences/{sid}` `shots` นอกช่วง EP → `400` `invalid_shot`
- `GET /draft` มี `clip_title`
- route `GET /tokens` เดิมลบออก; test เดิมของหลาย EP (`1-0`, `2-1`) เปลี่ยนเป็น test ของ EP เดียวตาม spec › Seams

### ผล render

- `.json` ของผล render มี `clip_id`, `ep`, `start_s`, `end_s`; `GET /renders` คืน `clip_id` และ `ep` (ไฟล์เก่าเป็น `null`)

### หน้าเว็บขั้น 1, ตัวเลือก Shot, ผล render

- เลือก Temp clip ได้ทีละคลิป; คลิปที่ยังไม่ถอดหรือยังไม่บรรยายฉากยังมีปุ่มไปทำ
- รายการ EP: เลข, ช่วงเวลา, ภาพเล็ก, token / 32,000, "render แล้ว {k}", ป้าย EP ที่อยู่ใน Spoil draft; เลือกได้ทีละ EP
- ความยาวต่อ EP 5–60 นาที; เปลี่ยนตอน `custom: true` ยืนยันก่อน; เวลาจุดตัดแก้ได้บันทึกเมื่อ blur; "ตัดใหม่ตามความยาว"
- กดร่างรอ `PUT` ที่ค้างก่อน; `409` `episodes_changed` → ข้อความและอ่านรายการ EP ใหม่; EP `lines` 0 หรือ `tokens` `null` → ปุ่มร่างกดไม่ได้พร้อมเหตุผล
- มี Spoil draft → ขั้น 1 เลือกคลิปของ draft ไว้
- ตัวเลือก Shot ไม่มีตัวเลือก EP; ปุ่ม "ดูทั้ง EP" แสดงทุก Shot ในช่วง EP
- รายการผล render แสดง "EP {n}" เมื่อมี
- ข้อความ error ของ `invalid_episodes`, `episodes_changed`, `ep_empty`, `transcript_too_long` ตาม spec › Frontend
- หน้าตาขั้น 1 ตามแบบใหม่เมื่อ Blocked 13 เป็น `done`; ก่อนหน้านั้นใช้ component เดิมของ Spoiler setup ที่ 375 และ 1440
- ทุก test ใน spec › Seams 2 ที่เกี่ยวกับหน้าตั้งค่าและตัวเลือก Shot ผ่าน
