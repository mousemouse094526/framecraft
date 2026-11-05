# 02: ร่างบทด้วย Story

**What to build:** ในขั้น 1 ของ tab สปอย ผู้ใช้เลือก Story ของคลิป (หรือ "ไม่ใช้") เห็นตัวนับ token รวม EP กับ Story แล้วกดร่าง; คำสั่งเขียนบทและเรียบเรียงตอนร่างมีบล็อก Story และคลิปจำเรื่องนั้นให้ทุก EP. คลิปที่ "ไม่ใช้" ได้คำสั่งเหมือนก่อนมี feature นี้ทุกตัวอักษร.

**Blocked by:** 01: คลังความรู้ — เพิ่ม แก้ ลบ Story

**Covers:**
- Decisions: D3, D4, D5, D8, D14, D15, D16 (ตำแหน่งบล็อก, เพิ่มเรื่องจากขั้น 1, spoil-maker spec), spoil-maker D46, spoil-maker D72, spoil-maker D81, spoil-maker D82, spoil-maker D86, spoil-maker D87
- ADR: 0024
- Screens: ขั้น 1 ตั้งค่าคลิปสปอย: ช่อง Story
- Seams: 1 (`kind: "draft"` กับ `story_id`, token รวม, คำสั่งเขียนบทและเรียบเรียง, คำสั่งเลือก Shot, คลิป "ไม่ใช้"), 2 (ขั้น 1, ระหว่างร่าง)
- User stories: 5

**Status:** ready-for-agent

## Acceptance criteria

### คำสั่ง LLM

- คลิปจำ Story → คำสั่งเขียนบทมีบล็อกตาม spec › คำสั่ง LLM ครั้งเดียว ก่อน `Transcript, one line each` และกฎท้ายมีบรรทัด `เขียนชื่อตัวละครตาม Story: …`
- คำสั่งเรียบเรียงตอนร่าง → บล็อกอยู่หลัง `top_text` ก่อน `The script, one sentence each`
- `article` ว่าง → ไม่มีบรรทัด `บทความ:`; ไม่มีตัวละคร → ไม่มีส่วนตัวละครและไม่มีบรรทัดชื่อในกฎท้าย; `description` ว่าง → `- {name}`
- คำสั่งเลือก Shot → ไม่มีบล็อก Story
- `story_id` `null` → คำสั่งเขียนบทและเรียบเรียงเท่ากับข้อความคาดหวังที่เก็บจากก่อน feature นี้ทุกตัวอักษร

### Draft job `kind: "draft"`

- `story_id` ของ Story → `202`, `GET /api/story-clips` มี key, `order.story_id` และ `order.story_title` ตรง
- `story_id` `null` หรือไม่ส่ง → `202` และ key ของคลิปหาย
- `story_id` ที่ไม่มีไฟล์หรืออ่านไม่ได้ → `400` `story_not_found` และ key ไม่เปลี่ยน
- token ปลอม EP 30,000 + Story 2,001 → `400` `transcript_too_long` `tokens` 32,001 `story_tokens` 2,001; Story "ไม่ใช้" → `202`
- คำขอถูกปฏิเสธข้อใดหลังเช็ค Story (รวม `gpu_busy`, `draft_exists`) → key ไม่เปลี่ยน
- `PUT` Story ระหว่าง Draft job → งานนั้นใช้ค่าตอนเริ่ม

### ขั้น 1

- เลือกคลิปที่จำ Story → ช่อง Story ตั้งที่เรื่องนั้น และตัวนับเป็น "{EP + Story} / 32,000 · เรื่อง {n} token" (e2e)
- คลิปที่จำ Story ที่ถูกลบ → ช่องเป็น "ไม่ใช้" (e2e)
- ตัวเลือกคือ "ไม่ใช้" กับทุก Story เรียงตามชื่อ; เปลี่ยนช่อง → ไม่ส่ง request (e2e)
- Story `tokens` `null` → ตัวนับ "— / —" และปุ่มร่างกดไม่ได้ (e2e)
- รวมเกิน 32,000 → ปุ่มร่างกดไม่ได้ (e2e)
- กดร่าง → `POST /draft-jobs` มี `story_id` ของช่อง; `400` `story_not_found` → อ่านรายการใหม่ ช่องเป็น "ไม่ใช้" พร้อม Alert "ไม่พบเรื่องนี้ในคลังความรู้แล้ว" (e2e)
- ลิงก์ "เพิ่มเรื่องในคลังความรู้" และ "แก้เรื่องนี้" → เปิดแท็บใหม่; หน้ากลับมา focus → อ่านรายการ Story ใหม่ ค่าอื่นในขั้น 1 ไม่หาย (e2e)
- ร่างบทด้วย Story แล้วเปิดขั้น 1 ของคลิปเดิมใหม่ → ช่อง Story เป็นเรื่องนั้น (e2e)

### ระหว่างร่างและลองอีกครั้ง

- ระหว่าง Draft job ยังไม่จบ → ช่อง Story เป็นข้อความ `order.story_title` หรือ "ไม่ใช้"; การ์ดความคืบหน้ามี "เรื่อง: {story_title}" (e2e)
- "ลองอีกครั้ง" หลังร่างล้ม → ส่ง `order.story_id` เดิม (e2e)
- spoil-maker spec มีโน้ตชี้มาที่ story-kb ในแถวขั้น 1, Draft job ข้อ 1, `order`
- หน้าตาของช่อง Story ตรง Figma ทั้ง desktop และ 375px
