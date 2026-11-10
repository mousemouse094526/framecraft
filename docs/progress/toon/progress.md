# Progress: toon

**Now:** 02 done (EP, Plot job, Cards job, แตกใหม่, หน้ารายการ EP พล็อต เส้นเรื่อง). ต่อ 03 ภาพการ์ดและเสียงเล่า

**Next:**

```
/warroom-build toon 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้ง klein, Series และภาพอ้างอิง | done |
| 02 | EP, พล็อต และเส้นเรื่อง | done |
| 03 | ภาพการ์ดและเสียงเล่า | ready |
| 04 | คลังเสียงพื้นและ render | ready |

## Log

### 02: EP, พล็อต และเส้นเรื่อง — done 2026-11-10

**Built:**
- backend: `toon/episodes.py` (EP สร้าง แก้ ลบ, เลข EP ตาม `max_ep` D40, `invalid_ep_number`, องก์ ช่วง การ์ด, สถานะภาพ เสียง ความยาวต่อการ์ดและรวม, `ep_locked` / `ep_busy` ผ่าน `ep_jobs`, `in_use` ของตัวละครและฉากหลังที่การ์ดหรือ `plot` ใช้, `voice_in_use` ของ EP), `toon/writer.py` (คำสั่งและการอ่านคำตอบของ Plot job กับ Cards job), `ToonJobs` มี `plot` และ `cards` บน `toon_write` ("ร่างการ์ตูนเล่า"); Cards job เขียน Series กับ `ep.json` พร้อมกันตอนจบ (ยกเลิกหรือ crash แล้วไม่เปลี่ยน), แตกใหม่เฉพาะองก์ที่ `summary` ≠ `cards_from`, `cards_will_be_lost` ต่อองก์, `nothing_to_split`
- `backend/llm_reply.py` ใหม่: `json_object` และ `clean` ย้ายจาก `spoil_maker.script` (ผู้ใช้คนที่สองคือ `toon.writer`); `store.ep_ids` ให้ id ของ EP ไม่ซ้ำทั้ง tab
- หน้าเว็บ: รายการ EP (`#/toon/series/{sid}`, EP ใหม่ส่ง Plot job ทันที), ตัวละครย้ายไป `/cast`, หน้า EP (`#/toon/eps/{eid}`, `/plot`): พล็อต (ชื่อตอน สรุปต่อองก์ ป้าย "ใหม่" สลับเป็นของใน Series, องก์ที่จะแตกใหม่, dialog ของที่จะหาย), เส้นเรื่อง (องก์ แก้ชื่อที่หัวองก์, ช่วงพร้อมฉากหลัง, `CardEditor`, `LengthMeter` เทียบเป้า 60–120), ช่องแก้ปิดระหว่าง Plot/Cards job ของ EP; `NoticeLine` เป็น component ของตัวเอง
- test: `backend/tests/test_toon_eps_api.py` (33), `features/toon/components/EpPage.test.tsx`

**Decided:**
- D53 — hash ใหม่ (`/cast`, `/eps/{eid}`, `/plot`), EP ใหม่เริ่ม Plot job ทันที, `PATCH` องก์, Cards job เขียนตอนจบ, ขีดจำกัดข้อความ, ค่าตั้งต้นของช่วงใหม่
- D54 — พล็อตที่ยืนยันแล้วไม่รับของใหม่ (`invalid_request`), id ของ EP ไม่ซ้ำทั้ง tab, ชื่อองก์แก้ที่หัวองก์

**For the next ticket:**
- ticket 03: การ์ดมี `has_previous_image` และ `previous_image` รอแล้ว; ภาพการ์ด ปุ่มเสียงเล่า และสถานะบน `CardEditor` ยังไม่ขึ้น (D53)
- ticket 04: `PATCH` ช่วง `sound` / `volume` (`episodes._sound`) และ `ListedEp.rendered_at` มีแล้วแต่หน้าเว็บยังไม่ใช้; Render slot ต้องเพิ่มตัวเองใน `episodes.ep_jobs` (ตอนนี้มีแค่ `toon_jobs.ep_use`)
- smell ที่ไม่ได้แก้: `writer._plot_items` (อ่านคำตอบ Qwen แบบทิ้งของเสีย) กับ `episodes._plot_items` (API ปฏิเสธ) คล้ายกันแต่กติกาต่างกัน; แตกกิ่ง `characters` / `backgrounds` เพิ่มใน `_cards`, `_plot_items` — รวมเป็นตารางต่อ kind พร้อมที่ ticket 01 บอกไว้
- test backend บางตัวผูกกับถ้อยคำในคำสั่ง (`Writer.respond` แยกด้วย "เขียนพล็อต" และ "องก์นี้ ("); `edit_stored` เขียน `ep.json` ตรงเพื่อใส่ภาพและเสียง จนกว่า ticket 03 จะมี API
- `GENRE_DEFAULTS` ซ้ำ `DEFAULTS`, `lib/voices.ts` และ smell ของ `useCast` / `usePickRef` จาก ticket 01 ยังค้าง; `useEp` poll `JOB_PATH` เป็นตัวที่สาม → ticket 03 รวมเป็น hook เดียว

**Checks:** `uv run pytest` 973 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 382 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e = Vitest ผ่าน `App`; หน้าตาเทียบ Figma ด้วยมือยังไม่ได้ทำ

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — done 2026-11-10

**Built:**
- tab ที่ห้า "การ์ตูนเล่า" (`#/toon/…`, `ToonPage` เลือกหน้าจาก `pageOf`): รายการ Series (ว่าง, กำลังโหลด, ลบพร้อมยืนยันจำนวน EP, `series_busy`), ตั้งค่า Series (สร้างและแก้, แนวเติมสไตล์ น้ำเสียง โครงองก์, แบบจอล็อกหลังสร้าง, ไม่มี Saved voice → ลิงก์ `#/spoil/voices`), ตัวละครและฉากหลัง (เพิ่ม ลบ, tile ทุกสถานะ, Ref job banner, upload พร้อม %, คำเตือน legal ข้อ 2 ก่อนเลือกไฟล์ตัวละคร, `gpu_busy` / `not_ready` เป็น Alert), เลือกภาพอ้างอิง (ติดตามงาน, เลือก 1 ใน 3, ล้ม / หยุด / ลองอีกครั้ง)
- `GPU_JOB_PATHS` และ `RUNNING_NAMES` มี `toon_image`; `Alert` มี `title`; icon ที่สอง feature ใช้ (`chevron-down`, `radio-selected`, `plus-white`) ย้ายไป `components/ui/assets`
- backend: `POST /series` รับ `style`, `tone`, `acts` (กติกาเดียวกับ `PATCH`, D52)
- test: `features/toon/components/ToonPage.test.tsx` (16, ผ่าน `App` กับ `testBackend`), backend test ใหม่ 1

**Decided:**
- D52 — hash ของหน้า tab, `POST /series` ส่งครั้งเดียว, Ref job ล้มหรือหยุดไม่มีภาพให้เลือก, ปุ่มคลังเสียงพื้นรอ 04, ลบตัวละครไม่ถามก่อน

**For the next ticket:**
- ticket 02: `#/toon/series/{sid}` เป็นรายการ EP ตามแบบ → ย้ายหน้าตัวละครและฉากหลังไป hash ใหม่ (เช่น `/cast`) และปุ่ม "กลับไปที่ชุด" ชี้รายการ EP; ลิงก์ "ตั้งค่า Series" บนหน้า cast ย้ายตามแบบรายการ EP
- ticket 04: ปุ่ม "คลังเสียงพื้น" บนรายการ Series (`assets/music.svg` เตรียมไว้แล้ว)
- `GENRE_DEFAULTS` (frontend) ซ้ำ `DEFAULTS` (backend) ไม่มี test เทียบ: เปลี่ยนที่หนึ่งต้องเปลี่ยนอีกที่
- shared ใหม่: `lib/voices.ts` (`VOICES_PATH`, `SavedVoice`) แทนค่าที่ซ้ำใน spoil-maker
- build มีคำเตือน chunk > 500 kB ของ Vite (ไม่ใช่ error)
- review ไม่ได้แก้ (smell): `useCast` กับ `usePickRef` ซ้ำ `update` และการ poll `JOB_PATH` — ถ้า ticket 03 เพิ่ม hook ที่ poll Toon job อีก ให้รวมเป็น hook เดียว; `(sid, kind, id)` เดินด้วยกันหลายที่ (อาจเป็น type `ItemRef`)

**Checks:** `uv run pytest` 940 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 371 passed; `npm --prefix frontend run build` ผ่าน (คำเตือน chunk > 500 kB). e2e ตาม testing rules = Vitest ผ่าน `App`; หน้าตาเทียบ Figma ด้วยมือยังไม่ได้ทำ

### design — 2026-11-10

- แบบ 9 จอจาก Figma (Blocked #1–9 done); spec › Design Source เป็นลิงก์ section ของแต่ละจอ; `ui-prompt.md` ลบ; spec › Design ไม่มีจอ `pending`

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — stopped 2026-11-09 (รอบ 2)

**Done:** ทุกกลุ่มยกเว้นหน้าเว็บ; โค้ดจาก `wip/toon-01` เข้า `feat/toon` แล้ว (`wip/toon-01` ไม่ใช้อีก)
- ลด memory ตาม D49 → ใช้ขั้น 3: transformer Q4_K_M + ภาพอ้างอิง ≤ 512 + `empty_cache` หลังทุกภาพ (D51); `allow_patterns`, `GGUF_FILE`, ที่ว่าง 32/42/27 GB, spec, `NOTICE.md`
- Status check: marker ของ Q8_0 กับ spec Q4_K_M → `model_klein_gguf` `missing` (D50); setup ตรวจทุก pattern ที่ระบุไฟล์หรือ folder หลังโหลดด้วยกฎเดียวกัน
- Ref job และเอาไฟล์เข้า: test ครบกลุ่มใน `backend/tests/test_toon_ref_api.py` (translating → drawing 3/3, `pending` 3, `busy`, `gpu_busy`, `not_ready`, ทุกทางออกคืน GPU, pick, `no_pending`, upload, start ใหม่ล้าง `.pending`, shutdown หยุด process ลูก); `FakeKlein` ใน `fakes.py`
- review: ลำดับเช็ค `busy` → `gpu_busy` → `disk_full`; ลบ Series กับเริ่มงานไม่แข่งกันแล้ว (`ToonJobs.delete_series` ถือ lock ของ slot); `RefPlan` อยู่ใน `series`; upload ใช้ไฟล์ `.partial` ต่อ request; `check` ตอบเป็น model; `json_values` ย้ายเป็น `backend/json_values.py` (ผู้ใช้คนที่สอง); SKILL.md มี `toon/`, `uploads.py`, adapter ของ diffusers, ลำดับ lock ของ `toon.store.lock`; ADR-0028 มี route upload ของ toon

**Left:** กลุ่มหน้าเว็บ (รอแบบ: Blocked #1–4)

**ลองจริง D49** (Mac M1 16 GB, torch 2.8.0, กรณีหนักสุด 576×1024 + 3 ภาพอ้างอิง, 5 ภาพต่อ process, seed และคำสั่งตายตัว, ผ่าน `backend.toon.klein` จริง; ปิดแอปอื่นไม่ได้: swap 4–7 GB ก่อนเริ่มทุกรอบ)

| ขั้น | รอบ | peak MPS ภาพ 1–5 | เวลา/ภาพ | swap ก่อน → peak |
|---|---|---|---|---|
| 1: Q8_0 + ref 512 + `empty_cache` | 1 | 13.08 ทุกภาพ | 185–236 วิ | 4.3 → 10.7 GB |
| 2: Q6_K + ref 512 + `empty_cache` | 1 (2 ภาพ) | 12.88, 12.88 | 197–199 วิ | 5.7 → 8.4 GB |
| 3: Q4_K_M + ref 512 + `empty_cache` | 1 | 11.83 ทุกภาพ | 192–197 วิ | 6.4 → 7.6 GB |
| 3 | 2 | 11.83 ทุกภาพ | 194–201 วิ | 6.5 → 7.6 GB |
| 3 | 3 | 11.83 ทุกภาพ | 194–198 วิ | 6.8 → 7.1 GB |

- ขั้น 1 และ 2 เกิน 12 GB ตั้งแต่ภาพแรก จึงหยุดที่รอบเดียว; ขั้น 3 ผ่านทั้ง 3 รอบ และภาพ 3–5 ไม่สูงกว่าภาพ 2
- encode 1 คำสั่ง 19–33 วิ peak 9.4–9.8 GB; โหลด transformer + vae 5–11 วิ
- วัดแยกของขั้น 1 ไม่ครบ: Q8_0 + ref 768 + `empty_cache` thrash (swap 11 GB, 10 นาทีต่อ step) จึงหยุด; เทียบกับรอบก่อนแทน: ref 768 ไม่มี `empty_cache` ได้ 13.09 → 13.98 GB (ไต่ขึ้นภาพที่ 2) ส่วน ref 512 + `empty_cache` ได้ 13.08 คงที่ → `empty_cache` ตัดการไต่, ขนาดภาพอ้างอิงแทบไม่มีผลต่อ peak
- **คงตัวละคร 10 ภาพ (Q4_K_M, ref 1 ภาพ):** ✅ ผมดำ หัวกลม ตาจุด เสื้อโปโลกรมท่าปกดำ กางเกงดำ ครบทุกภาพ ไม่มีหน้าบิดหรือตัวซ้ำ ([consistency-10-q4km.png](../../features/toon/trial-images/consistency-10-q4km.png)); peak 10.6–11.2 GB, 142–145 วิ/ภาพ
- **ไทยตรงเข้า klein (ข้อมูลให้ D36):** ได้ภาพรวมถูก (ผู้ชายข้างกองไฟ, ผู้หญิงตกใจหน้าห้องน้ำแสงฟ้า, เด็กวิ่งตอนกลางคืนป้ายเขียว) แต่รายละเอียดหลุด: เสื้อฮาวายเป็นเสื้อยืด, ทางเดินโรงเรียนเป็นถนนนอกอาคาร, สไตล์หัวกลมตาจุดไม่ติด, ป้ายเป็นตัวหนังสือมั่ว → ยืนยัน D36 (Qwen แปลก่อน); 119–121 วิ/ภาพ 1024×576

**Decided:**
- D50 — Status check และ setup เทียบ pattern ที่ระบุไฟล์หรือ folder กับไฟล์จริง; pattern ชนิดไฟล์ไม่เทียบ
- D51 — transformer Q4_K_M (ขั้น 3 ของ D49), ที่ว่าง 32/42/27 GB

**For the next ticket:**
- `series.delete_item` ยังไม่มี `409` `in_use` ของ D25 (การ์ดหรือ `plot` ของ EP อ้างอยู่): ticket 02 สร้าง EP และ `plot` ต้องเพิ่มพร้อม test
- เครื่องที่โหลด Q8_0 ไว้ setup โหลด Q4_K_M ใหม่ แต่ไฟล์ Q8_0 (4.3 GB) ค้างใน `models/hub`; ยังไม่มีอะไรลบ
- smell จาก review ที่ไม่ได้แก้: ตัวละคร/ฉากหลังแตกกิ่ง `kind == "characters"` หลายที่ (`add_item`, `change_item`, `picture_size`, `_take_upload`, `prompts`) — ถ้า Image job เพิ่มอีกที่ ให้รวมเป็นตารางต่อ kind; แถว `diffusers`/`gguf` เขียนทั้งใน `checks.run_checks` และ `gate_rows.klein`
- ภาพการ์ดกับ 3 ภาพอ้างอิง 576×1024 ใช้ ~195 วิ/ภาพบน M1 (ref 1 ภาพ ~143 วิ, ไม่มี ref ~120 วิ): ใช้ตั้งความคาดหวังของ "สร้างภาพที่ขาดทั้งหมด"

**Checks:** `uv run pytest` 938 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 355 passed (รอบหนึ่งระหว่าง klein รัน `DraftProgress.test.tsx` ตก 1 เพราะเครื่องโหลดหนัก, รันซ้ำผ่าน; ticket ไม่แตะ frontend); `npm --prefix frontend run build` ผ่าน

### 01: ติดตั้ง klein, Series และภาพอ้างอิง — stopped 2026-11-09

**Done:** (โค้ดอยู่บน `wip/toon-01`, test backend 897 ผ่าน)
- ติดตั้งและ Status check: `KLEIN` และ `KLEIN_GGUF` ใน `MODELS` (GGUF pin `a09d5bb51ac4000ccd9643d10e9db3ed14200508`), setup ตรวจทุก folder ใน `allow_patterns` หลังโหลด, ที่ว่างที่ต้องการ 33/43/28 GB, แถว `model_klein` `model_klein_gguf` `diffusers` `gguf` ต่อจาก `font_kanit`, `NOTICE.md`
- Series ตัวละคร ฉากหลัง: สร้าง แก้ ลบ (`confirm_needed`, `series_busy`), `voice_in_use` ของ Series, ข้าม `series.json` ที่อ่านไม่ได้; test ใน `backend/tests/test_toon_series_api.py`
- เริ่มแล้วแต่ยังไม่มี test: Ref job (`backend/toon/jobs.py`), worker ของ klein (`backend/toon/klein.py`), pick และ upload ภาพอ้างอิง

**Left:** กลุ่ม Ref job และเอาไฟล์เข้า (test ทั้งกลุ่ม), กลุ่มหน้าเว็บ (รอแบบ: Blocked #1–4)

**ลองจริง (Open Question 1):** Mac M1 16 GB, torch 2.8.0, diffusers 0.42.1, gguf 0.19.0, GGUF Q8_0, 4 steps

| ขั้น | เวลา | peak MPS | peak ทั้งระบบ | swap |
|---|---|---|---|---|
| โหลด text encoder | 9.7 วิ | — | — | — |
| encode 4 prompt | 9.3 วิ/prompt | 9.77 GB | 15.58 GB | — |
| โหลด transformer GGUF + vae | 11.2 วิ | — | — | — |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 1) | 178 วิ | **13.09 GB** | 16.41 GB | 5.37 → 9.27 GB |
| ภาพ 576×1024, 3 ภาพอ้างอิง (รอบ 2) | 231 วิ | **13.98 GB** | 16.34 GB | → 10.96 GB |

- peak MPS ของ klein อย่างเดียวเกิน ~12 GB ของ D34 ทั้งสองรอบ และเครื่อง swap จริง; ตัวเลขทั้งระบบรวมแอปอื่นที่เปิดอยู่ (swap 5.4 GB ก่อนเริ่ม และ pytest รันช่วงรอบ 2) แต่ MPS เป็นของ klein เอง
- เทียบผลลองเดิม (torch 2.15, 1024×576, 1 ภาพอ้างอิง): 11.2 GB; กรณี 3 ภาพอ้างอิงกับภาพแนวตั้งไม่เคยวัดมาก่อน
- ภาพไทยตรงเข้า klein (ข้อมูลให้ D36): รอบนี้ยังไม่ได้ผล ไปลองต่อพร้อมทางแก้ใน `/warroom toon`
- สคริปต์ลองอยู่นอก repo; ขั้นตอนเหมือน `backend/toon/klein.py` (encode แยก, `device_map`, `no_grad`, `config=` ของ transformer ในเครื่อง)

**Decided:**
- D47 — gguf pin 0.19.0 แทน 0.10.0 ที่อ่าน GGUF ไม่ได้บน numpy 2
- D48 — ค่าเล็กของ Series และ Ref job (ความยาว style/tone, `file_too_large`, `item_id`, ค่าสำรองของคำแปล, `backend/uploads.py`)

**For the next ticket:**
- `backend/uploads.py` คือการรับ body ดิบที่ spoil import และ upload ภาพอ้างอิงใช้ร่วมกัน; Sound import ของ ticket 04 ใช้ตัวนี้
- `gate_rows.klein(project)` เป็นฟังก์ชัน (ต้องใช้ project) ไม่ใช่ค่าคงที่ `gate_rows.KLEIN` ตามที่ spec เขียน

**Checks:** `uv run pytest` 897 passed บน `wip/toon-01`; frontend ไม่ได้แตะ

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: รายการ Series (หน้าแรกของ tab) | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8121-65674)) |
| 2 | 01 | design: ตั้งค่า Series | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8122-66685)) |
| 3 | 01 | design: ตัวละครและฉากหลัง | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8123-68692)) |
| 4 | 01 | design: เลือกภาพอ้างอิง | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8124-70163)) |
| 5 | 02 | design: รายการ EP ใน Series | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8126-71235)) |
| 6 | 02 | design: พล็อต | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8127-72204)) |
| 7 | 02 | design: เส้นเรื่อง (การ์ด) | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8128-76737)) |
| 8 | 04 | design: คลังเสียงพื้น | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8129-80163)) |
| 9 | 04 | design: render และผล | `/warroom toon` พร้อมลิงก์แบบ (ทำจาก `docs/features/toon/ui-prompt.md`) | done ([แบบ](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8130-81152)) |
| 10 | 01 | klein บน torch 2.8.0 กรณีหนักสุด (GGUF Q8_0, 3 ภาพอ้างอิง, 576×1024) peak MPS 13.1–14.0 GB เกิน ~12 GB ของ D34 และ swap; ต้องเลือก: ภาพอ้างอิงเล็กลง, GGUF ที่เล็กกว่า (Q6_K/Q4_K_M), ภาพอ้างอิงสูงสุดน้อยลง, torch รุ่นใหม่ หรือยอมรับ | `/warroom toon` | done (this ticket, D51) |
