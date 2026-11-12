# 02: EP, พล็อต และเส้นเรื่อง

**What to build:** ผู้ใช้สร้าง EP ใหม่ใน Series ด้วยไอเดียสั้นๆ ได้พล็อตต่อองก์ ชื่อตอน และรายชื่อตัวละครกับฉากหลังที่ต้องใช้ แก้แล้วยืนยันให้ AI แตกเป็นช่วงและการ์ด. แก้ เพิ่ม ลบ องก์ ช่วง การ์ดได้ เห็นความยาวรวมเทียบเป้า และแก้พล็อตแล้วแตกใหม่เฉพาะองก์ที่เปลี่ยนโดยถามก่อนทับงานที่แก้เอง.

**Blocked by:** 01: ติดตั้ง klein, Series และภาพอ้างอิง

**Covers:**
- Decisions: D8 (`voice_id` ของ EP), D9, D10, D12, D13, D14, D15, D20, D21, D24, D25 (ตัวละคร ฉากหลัง Saved voice ที่ EP ใช้), D26 (ลบ EP), D30, D40, D41, D43, spoil-maker D74
- ADR: 0010, 0012, 0015, 0024, 0026, 0033
- Screens: รายการ EP ใน Series, พล็อต, เส้นเรื่อง (การ์ด) ส่วนข้อความ องก์ ช่วง การ์ด ความยาวรวม และการล็อก
- Seams: 1 (Plot job, Cards job, แตกใหม่, เลข EP, `ep_locked`, `in_use` ของตัวละคร), 3 (ช่องแก้ปิดระหว่าง Cards job, ความยาวเกินเป้า, `cards_will_be_lost`)
- User stories: 4, 5, 6, 7, 12 (ลบ EP)

**Status:** done

## Acceptance criteria

### EP และ Plot job

- สร้าง EP แรก → `n` 1; ลบ EP แล้วสร้างใหม่ → `n` เท่ากับ `max_ep` + 1 (D40)
- `PATCH` EP `n` ซ้ำใน Series หรือ 0 → `400` `invalid_ep_number`
- Plot job ด้วย `FakeLlm` → EP มี `title` และ `summary` ทุกองก์; ของใหม่อยู่ใน `plot` `new: true` ไม่อยู่ใน Series
- `FakeLlm` ตอบ JSON พังสามครั้ง → `failed` `write_failed`
- Plot job บน EP `stage` `cards` → `409` `plot_confirmed`
- `plot` ไม่เหลือฉากหลัง → `400` `invalid_request`

### Cards job

- Cards job ครั้งแรก → ของใหม่เข้า Series `ref_rev` 0; การ์ดที่ใช้มันสถานะภาพ `no_ref`; `stage` `cards`
- ตัวละครเกิน 2 ใน `FakeLlm`, `motion` นอกรายการ, `sound` ที่ไม่มีในคลัง → เก็บ 2 ตัวแรก, `still`, `null`
- แก้ `summary` หนึ่งองก์ → Cards job แตกเฉพาะองก์นั้น การ์ดองก์อื่น id เดิม
- องก์ที่จะแตกมีการ์ด `edited` หรือมีภาพ ไม่ส่ง `confirm_loss` → `409` `cards_will_be_lost` พร้อมจำนวนต่อองก์
- ไม่มีองก์ที่เปลี่ยน → `400` `nothing_to_split`; องก์ที่เพิ่มหลังยืนยัน → นับเป็นองก์ที่เปลี่ยน
- ยกเลิกหรือ crash ระหว่าง Cards job → `ep.json` ไม่เปลี่ยน
- `gpu.Kind` มี `toon_write` ใน `RUNNING_NAMES` ("ร่างการ์ตูนเล่า"); Plot job และ Cards job จองช่องนี้แล้วคืนเมื่อจบทุกแบบ
- ชื่อเสียงในคลังเสียงพื้นอยู่ในคำสั่งของ Cards job (คลังว่างได้จนกว่า ticket 04)

### แก้เส้นเรื่อง

- `PATCH` การ์ดเปลี่ยน `text` → `edited` `true`; การ์ดเงียบ `hold_s` 0 → `400` `invalid_card`
- ลบการ์ดใบสุดท้ายของช่วง → ช่วงหาย; เพิ่มช่วงโดยไม่มี `background_id` → `400` `invalid_request`
- `GET` EP → สถานะภาพ สถานะเสียง ความยาวต่อการ์ด และความยาวรวมตามสูตรใน spec › สถานะการ์ด
- แก้การ์ดระหว่าง Cards job → `409` `ep_locked`; ลบ EP ระหว่าง Cards job ของ EP นั้น → `409` `ep_busy`
- ลบตัวละครที่การ์ดหรือ `plot` ใช้ → `409` `in_use` พร้อม `eps`; ลบ Saved voice ที่ EP ใช้ → `409` `voice_in_use`
- `PATCH` EP `voice_id` ถือ `gpu.slot.draft_lock` ก่อน `toon.store.lock` แบบ Series

### หน้าเว็บ

- `#/toon/eps/{eid}` เปิดหน้า EP
- ระหว่าง Cards job ของ EP ที่เปิดอยู่ → ช่องแก้การ์ดถูกปิด (e2e)
- เส้นเรื่องที่ความยาวรวม 130 วินาที → เห็นคำบอกว่าเกินเป้า 60–120 (e2e)
- Cards job ได้ `409` `cards_will_be_lost` → เห็นจำนวนการ์ดแก้เอง ภาพ และเสียงที่จะหายต่อองก์ ก่อนกดยืนยัน (e2e)
- พล็อตที่มีตัวละครใหม่ → เห็นป้าย "ใหม่" และสลับเป็นตัวละครใน Series ได้ (e2e)
- หน้าตาตรงแบบของสามจอใน Covers (Source ยัง `pending`: Blocked #5–7)
