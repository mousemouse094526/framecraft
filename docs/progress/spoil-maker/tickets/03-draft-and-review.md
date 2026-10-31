# 03: ร่างบทและหน้าตรวจแก้

**What to build:** ผู้ใช้เปิด `#/spoil/maker` เลือก Temp clip ที่ถอดและดูภาพแล้วหลาย EP เรียงลำดับ ตั้งสไตล์ layout ความยาว และ Saved voice เห็น token รวมก่อนกด แล้วกดร่างบท: AI เขียนบทไทยและเลือก 2 Shot ต่อประโยค. หน้าตรวจแก้ให้แก้ hook หรือชื่อตอน แก้ ลบ แทรกประโยค เปลี่ยน Shot จากตัวเลือกหรือให้ AI เลือกใหม่ และตั้งเสียงต้นฉบับ; ทุกอย่างอยู่ข้าม restart. ถอดใหม่ ดูภาพใหม่ หรือลบคลิปใน Spoil draft เตือนก่อนว่าจะลบ Spoil draft.

**Blocked by:** 02: Saved voice

**Covers:**
- Decisions: D4, D5, D7, D8, D11, D18, D19, D25, D26, D27, D28, D29, D39, D40 (`original_volume` ใน draft และ settings), D43 (`voice_in_use`), D46, D49, D51
- ADR: 0010, 0012, 0013, 0015, 0018
- Screens: ตั้งค่าคลิปสปอย, หน้าตรวจแก้ (ยกเว้นเสียง ลายน้ำ และ render), ตัวเลือก Shot, แถว Temp clip ใน tab สปอย (คำเตือนของคลิปใน Spoil draft)
- Seams: 1 (Draft, แก้ draft ยกเว้นข้อ Voice job, คลิปใน Spoil draft, ลบคลิปและ start ข้อ Spoil draft, `voice_in_use`, `POST /draft-jobs` `not_ready`), 2 (หน้าตั้งค่า, หน้าตรวจแก้ข้อบทและ Shot, ตัวเลือก Shot, คำเตือน `in_draft`, `voice_in_use`), 3 (ร่างบท)
- User stories: 3, 5, 6, 7, 8, 12

**Status:** ready-for-agent

## Acceptance criteria

### Draft job

- คลิปถอดแล้วแต่ไม่ได้ดูภาพ → `400` `clip_not_ready` พร้อม id นั้น
- `target_s` 29, 181, 60.5 → `400` `invalid_target`; `style` `x` → `400` `invalid_request`
- token ปลอมรวม 32,001 → `400` `transcript_too_long`; `GET /tokens` คืน `total` 32,001 และ `per_clip`
- LLM ปลอมคืนบท 2 EP ที่อ้าง `1-0` และ `2-1` → `done`, `GET /draft` มี `refs` เป็น `clip_id` ของแต่ละ EP และ Shot อยู่ใน `window`; ประโยคที่อ้างทั้งสองพร้อมกัน → `window` ของคลิป EP 1 เท่านั้น
- LLM ปลอมคืน JSON พัง 3 ครั้ง → `failed` `draft_failed` และ Spoil draft เดิมไม่เปลี่ยน; พัง 2 ครั้งแล้วถูก → `done` และ LLM ถูกเรียก 3 ครั้ง; ค้างเกิน timeout → นับเป็นครั้งที่ไม่ผ่าน
- LLM ปลอมคืนข้อความที่มี `現場` และ ref `9-999` → ไม่มีอักษรจีน, `refs` ว่าง, `shots` `[null, null]`, สถานะ `no_shot`
- LLM ปลอมขั้นสองคืน Shot นอกช่วง → ใช้ 2 Shot ที่ใกล้เวลาของ ref ที่สุด
- มี Spoil draft แล้วไม่มี `replace` → `409` `draft_exists`; `replace: true` → `202`
- marker ของ Qwen หาย → `POST /draft-jobs` `503` `not_ready`; ระหว่าง Describe job → `409` `gpu_busy`

### แก้ Spoil draft

- สร้าง app ใหม่บน root เดิม → `GET /draft` เหมือนเดิม; `draft.json` อ่านไม่ได้ → `GET /draft` เป็น `null`
- แก้ `text` ของประโยคที่มีเสียง (เขียน `audio` ปลอมใน test) → `stale_audio`; แก้กลับเป็นข้อความเดิม → `ready`; `PATCH /draft` เปลี่ยน `voice_id` → ทุกประโยคที่มีเสียงเป็น `stale_audio`
- `POST /draft/sentences` `after_id` ของประโยคแรก → ประโยคใหม่อยู่ลำดับสอง สถานะ `no_shot`; `kind: "pick"` กับประโยคนั้น → `400` `no_refs`
- `PATCH /draft/sentences/{sid}` `shots` ที่ `n` ไม่มี → `400` `invalid_shot`
- `PATCH` ระหว่าง Draft job `pick` → `409` `draft_locked`; `GET /draft` มี `locked: true`
- `PATCH /draft` `original_volume` 35 → `GET /settings` มี 35; ร่างใหม่ → draft ใหม่มี 35
- `estimated_total_s` ของ draft ที่มีประโยค `ready` 2.0 วินาที และประโยคยังไม่มีเสียง 30 ตัวอักษรกับ `chars_per_s` 15 → 4.0
- `DELETE /voices/{id}` ที่ Spoil draft ใช้ → `409` `voice_in_use`

### คลิปใน Spoil draft (D49)

- `POST /describes` ไม่มี `confirm_draft_loss` → `409` `in_draft`; มี → `202` แล้วหลัง `done` `GET /draft` เป็น `null`; ยกเลิกแทน → `GET /draft` ยังอยู่
- `POST /api/spoil/transcriptions` ของคลิปใน Spoil draft ไม่มี `confirm_draft_loss` → `409` `in_draft`
- `DELETE /api/spoil/clips/{id}` ของคลิปใน Spoil draft → `204`, Shot ของคลิปหาย, `GET /draft` เป็น `null`; ลบ mp4 ไม่ได้ → `409` `in_use` และ Spoil draft ยังอยู่
- `GET /api/spoil/clips` มี `in_draft`; start app ขณะมี `draft.json.tmp` → หาย

### หน้าเว็บ

- `#/spoil/maker` เปิด tab สปอยที่หน้าตั้งค่า; ไม่มี Spoil draft ที่หน้าตรวจแก้ → ลิงก์ไปหน้าตั้งค่า
- เลือก 2 คลิป `GET /tokens` คืน `total` 40,000 → ปุ่มร่างกดไม่ได้ และเห็น 40,000 / 32,000
- คลิปที่ยังไม่ดูภาพเลือกไม่ได้และเห็น "ยังไม่ดูภาพ"; ไม่มีคลิปพร้อมเลย → เห็นข้อความว่างพร้อมลิงก์
- เลือกสไตล์ `drama` → layout เป็น B; เปลี่ยน layout เป็น A ได้
- ไม่มี Saved voice → เห็นลิงก์ไปหน้า Saved voice และปุ่มร่างกดไม่ได้
- มี Spoil draft แล้วกดร่าง → เห็นคำยืนยันก่อนส่ง `replace: true`; ระหว่างร่าง → "กำลังเขียนบท" แล้ว "กำลังเลือกภาพ x/y" กับปุ่มยกเลิก
- หน้าตรวจแก้: ประโยค `no_shot` เห็น "เลือก" แทนภาพ; แก้ข้อความแล้ว blur → ส่ง `PATCH` และสถานะเป็น "ต้องสร้างเสียงใหม่"; กดลบประโยค → คำยืนยันก่อนส่ง `DELETE`
- กดภาพ Shot → ตัวเลือกแสดงภาพของ Shot ใน `window`; "ดูทั้งคลิป" → ทุก Shot ของ EP; ประโยคที่แทรกเปิดที่ทั้งคลิปของ EP แรก
- `GET /draft` มี `locked: true` และ current ของ Draft job `pick` → ช่องแก้ทุกช่องกดไม่ได้
- ลบ ถอดใหม่ หรือดูภาพใหม่ของคลิปที่ `in_draft: true` → เห็นคำเตือนก่อนส่ง; ยืนยันดูภาพ → ส่ง `confirm_draft_loss: true`
- ลบเสียงที่ใช้อยู่ได้ `409` `voice_in_use` → เห็น "เสียงนี้ใช้อยู่ใน Spoil draft"
- หน้าตาตรงแบบของจอ "ตั้งค่าคลิปสปอย", "หน้าตรวจแก้", "ตัวเลือก Shot" (Source ยัง `pending`: Blocked #3, #4, #5)

### เช็คมือบน Mac M2 (Seam 3)

- ก่อนเขียนตัวนับ token จริง ลอง `AutoTokenizer.from_pretrained` จาก snapshot ของ Qwen โดยไม่โหลดโมเดล — ไม่ได้ หยุดแล้วถาม
- ร่างบท 60 วินาที style `drama` จากหนัง 96 นาที → ครั้งแรกผ่านภายใน 8 นาที, ความยาวประมาณใน ±25%, Shot ตรงเนื้อหา ≥ 5 จาก 10 ประโยคที่สุ่ม
- 3 EP อนิเมะ token รวมใต้ 32,000 → ร่างจบโดย memory ของ process ลูกไม่เกิน 13 GB
- ยกเลิกระหว่าง `writing` → process ลูกหายภายใน 5 วินาที
- แก้บทแล้วปิด backend, เปิดใหม่ → หน้าตรวจแก้มีบทและ Shot เหมือนก่อนปิด
