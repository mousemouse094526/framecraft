# 05: ลายน้ำเปิดปิดได้ และงานค้างจาก feature review

**What to build:** ในหน้าตรวจแก้ผู้ใช้ปิดลายน้ำทีละอันได้โดยแอปยังจำไว้ และเห็นคำเตือนเมื่อลายน้ำบนกลางที่เปิดอยู่จะทับ hook หรือชื่อตอน. ส่วนที่เหลือเป็นงานค้างจาก feature review ที่ผู้ใช้ไม่เห็น: test ของ render ไม่ผูกกับฟังก์ชันภายใน, spec ตรงกับลำดับเช็คของ Describe job, icon ที่ใช้สอง feature มีที่เดียว และงานใหม่ลงทะเบียนกับ lifespan ที่เดียว.

**Blocked by:** 04: เสียงต่อประโยคและ render

**Covers:**
- Decisions: D41, D60 (ลำดับเช็คของ Describe job), D64
- Screens: หน้าตรวจแก้ (ลายน้ำ) — [Figma: Script review](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390)
- Seams: 1 (ลายน้ำ, Render job, Describe job), 2 (หน้าตรวจแก้ข้อลายน้ำ)
- User stories: 10
- Blocked: 8, 9, 10, 11

**Status:** ready-for-agent

## Acceptance criteria

### ลายน้ำเปิดปิด (D64)

- `PATCH /settings` ลายน้ำที่มี `enabled: false` → `GET /settings` คืน `enabled: false` พร้อมข้อความ ตำแหน่ง และขนาดเดิม
- `settings.json` เดิมที่ลายน้ำไม่มี `enabled` → `GET /settings` คืน `enabled: true`
- `enabled` ที่ไม่ใช่ boolean → `400` `invalid_settings`
- ลายน้ำ 6 อันที่ปิดอยู่ 2 อัน แล้วเพิ่มอันที่ 7 → `400` `invalid_settings`
- render ที่มีลายน้ำเปิด 1 อันและปิด 1 อัน → ไฟล์ ASS มีข้อความของอันที่เปิดเท่านั้น
- spec › ค่าที่จำไว้ และ spec › API มี `enabled` ตาม D64

### คำเตือนลายน้ำทับ (D64)

- ลายน้ำ `top_center` ที่เปิดอยู่ กับ layout A ที่มี hook → หน้าตรวจแก้เห็นคำเตือนว่าลายน้ำทับ hook; ปุ่ม render ยังกดได้
- ลายน้ำ `top_center` ที่เปิดอยู่ กับ layout C ที่มีชื่อตอน → เห็นคำเตือนว่าลายน้ำทับชื่อตอน
- ปิดลายน้ำนั้น, เปลี่ยนเป็น `top_left`, ลบ hook จนว่าง หรือเปลี่ยนเป็น layout B → คำเตือนหายทันที
- กดสวิตช์ของลายน้ำแล้ว reload → สวิตช์ยังอยู่ที่ค่าที่ตั้งไว้ (จาก `GET /settings`)
- หน้าตาของสวิตช์และคำเตือนใช้ component เดิม และเข้ากับ Figma Script review ที่ 375 และ 1440

### Test ของ render (Blocked 8)

- test ที่หยุด render ระหว่าง `rendering` หยุดผ่าน runner ที่ holder ของ Render job รับเข้ามา ตาม `fastapi-api` › testing; ไม่มี test ไหน patch `compose.run`
- draft ที่ทุกประโยคมีเสียงแล้ว render → เข้า `rendering` โดยไม่ผ่าน `voicing`; ระหว่างนั้น `POST /describes` ของคลิปอื่น `202` (ticket 04 › Render job)
- test เดิมของ render ทั้งหมดยังผ่าน

### ลำดับเช็คของ Describe job (Blocked 9)

- spec › Describe job ข้อ 1–2 เรียงตาม D60: `404` `not_found` → แถว Status check → `409` `busy` → `409` `in_draft` → `409` `gpu_busy`
- คลิปใน Spoil draft ที่ Qwen ยังไม่ติดตั้ง ไม่ส่ง `confirm_draft_loss` → `503` `not_ready` ไม่ใช่ `in_draft` (มี test)

### ของใช้ร่วม (Blocked 10)

- icon ที่ซ้ำกันใน `spoil` และ `spoil-maker` ทั้ง 6 คู่ (`copy`, `trash`, `x` กับ `cancel-x`, `circle-alert` กับ `delete-error`, `file-text-24` กับ `panel-empty`, `play` กับ `thumb-play`) เหลือไฟล์เดียวในที่ของ icon ใช้ร่วม ตาม `vite-react-web` › components; หน้าตาไม่เปลี่ยน
- backend app มี `JOB_HOLDERS` รายการเดียว: lifespan ล้างของค้างตอน start และหยุดงานตอนปิดจากรายการนี้ ตาม `fastapi-api`; ลำดับล้างเดิมยังเหมือนเดิม (คลิปก่อน Shot)
- start app ขณะมี `renders/x.partial`, `.new-{id}/` ของ Shot และ voice ที่เขียนไม่จบ → หายทั้งหมดเหมือนเดิม
