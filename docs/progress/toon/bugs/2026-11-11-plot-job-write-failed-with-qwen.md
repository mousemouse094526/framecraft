# Debug: Plot job write_failed กับ Qwen จริง

**Status:** fixed

**Summary:**
- **Cause:** Qwen จริงตอบ `acts` เป็นรายการข้อความเสมอ (28/28) แต่ `writer.parse_plot` อ่านเฉพาะ `{"summary"}` จึงตัดทุกคำตอบ
- **Fix:** `writer._summary` อ่าน act ที่เป็นข้อความเป็น summary (D81, `742c644`); Qwen จริงผ่าน 15/20 ครั้ง, ที่เหลือคือจำนวนองก์ผิด
- **Prevention:** regression test ด้วยคำตอบรูปของ Qwen จริง; ticket 16 — log คำตอบที่อ่านไม่ได้, fixture จากคำตอบจริง, ลดจำนวนองก์ผิด

## Symptom

Plot job กับ Qwen จริงบน M1 ล้ม `write_failed` สองครั้งติดกัน (6/6 attempt `plot attempt N is not the JSON asked for`, 129–149 วิ) ของ EP ใหม่ `e_14c37720` ใน Series `s_73ac00e3` (ตัวละครและฉากหลังไม่มีคำบรรยาย); log ไม่เก็บคำตอบของ Qwen จึงไม่รู้ว่าผิดตรงไหน (progress.md › Blocked #35)

ข้อมูลของ EP: ไอเดีย "น็อตอยู่เวรเฝ้าห้องเรียนคืนสุดท้ายก่อนตึกถูกรื้อ แล้วครูเอกที่ตายไปแล้วกลับมาสอนคาบสุดท้าย", 4 องก์ (เปิด, ปม, หักมุม, จบหลอน), ตัวละคร `c_d0cd8188` น็อต, `c_5839e67c` ครูเอก, ฉากหลัง `b_ee2ba62e` ห้องเรียนตอนดึก — คำบรรยายว่างทั้งหมด

## Reproduce

**Command:** `PYTHONPATH=. .venv/bin/python {scratchpad}/plot/repro.py 3 {out}` — โหลด Qwen ตัวจริง (`spoil_maker.llm.load`/`generate` ใน process เดียว ไม่ผ่าน backend), ส่ง `writer.plot_prompt` ของ `e_14c37720` ตรงตัว (`PLOT_MAX_TOKENS`, `TEMPERATURE`), เขียนคำตอบดิบเป็น `reply{n}.txt` แล้วพิมพ์ผล `writer.parse_plot`; ~45 วิต่อครั้ง (script อยู่ใน scratchpad ไม่ commit)

**Rate:** always (3/3 `parsed=NONE`)

**Minimised to:** prompt เดียว, เรียก `parse_plot` กับคำตอบที่เก็บไว้ (`which.py`) — ไม่ต้องรัน Qwen ซ้ำเพื่อดูว่าข้อเช็คไหนตัด

## Scope

- **Docs say:** spec › Plot job ข้อ 3 คำตอบ `"acts": [{"summary": "..."}]`; ข้อ 4 ตรวจ "JSON อ่านได้, `acts` ยาวเท่าองก์ของ EP, ตัวละครไม่เกิน 6, ฉากหลัง 1–6" — โค้ดทำตามนี้; spec ไม่ได้บอกว่า `acts` เป็นรายการข้อความแทน object ต้องทำอย่างไร
- **Last good:** ไม่มี — `plot_prompt` เหมือนเดิมตั้งแต่ ticket 02 (`31c0ec1`); Plot job ไม่เคยผ่านกับ Qwen จริง, test ใช้ fake llm ที่ตอบรูปที่ถูกเสมอ
- **Ruled out:** timeout — คำตอบละ 42–55 วิ ต่ำกว่า `llm.timeouts().write` 600 วิมาก; backend/child/คิว — repro เรียก mlx-vlm ตรงแล้วยังแดง

## Fail path

`writer.parse_plot` (`backend/toon/writer.py`): `summaries = [_cleaned(act.get("summary") if isinstance(act, dict) else None) ...]` — act ที่เป็นข้อความได้ `""` แล้ว `if not all(summaries): return None` → `steps.Qwen.answer` log `plot attempt N is not the JSON asked for` ครบ 3 ครั้ง → `plot.run` `write_failed`. ตัวแปรที่เปิด/ปิด: รูปของ `acts` ในคำตอบ (knob ใน `which.py`: ห่อข้อความเป็น `{"summary": ...}`)

## Hypotheses

| # | Hypothesis | Prediction | Disproof | State |
|---|---|---|---|---|
| H1 | Qwen อ่าน `"acts": [{"summary": "..."}]` ใน prompt เป็นรายการข้อความ แล้วตอบ `"acts": ["...", ...]`; parser ตัด act ที่ไม่ใช่ object | ห่อข้อความเป็น `{"summary"}` แล้ว `parse_plot` ผ่าน | คำตอบที่มี `acts` เป็น object แต่ยังล้ม หรือห่อแล้วยังล้มทุกตัว | confirmed (#2) |
| H2 | Qwen ตอบจำนวนองก์ไม่เท่าองก์ของ EP ("สรุปองก์ละ 1–3 ประโยค" อ่านเป็นหนึ่งประโยคต่อหนึ่งช่อง) | prompt ที่บอกช่องต่อองก์ชัด ได้ `acts` 4 ช่องทุกครั้ง | ทุกคำตอบมี 4 ช่อง | alive, ไม่แก้ในรอบนี้ (7/28 ครั้ง: #1, #3, #4) |
| H3 | อ่าน JSON ไม่ได้ / ตัวอักษร CJK | `json_object` คืน None | `json_object` อ่านได้ทุกคำตอบ | killed by #2 |
| H4 | ตัวละครเกิน 6 หรือฉากหลังเกิน 6/ว่าง | ตัด cast แล้วผ่าน | จำนวนอยู่ในเกณฑ์ | killed by #2 |
| H5 | timeout ของ Qwen | คำตอบเกิน 600 วิ | คำตอบ 42–55 วิ | killed by #1 |

## Ledger

| Run | Changed | Result | Rules in / out |
|---|---|---|---|
| 1 | repro: prompt จริงของ `e_14c37720` กับ Qwen จริง 3 ครั้ง (backend บน 8000 เปิดอยู่) | red 3/3, 42–55 วิ/ครั้ง; ทั้งสามตอบ `"acts": ["...", ...]` | H5 out; H1 in |
| 2 | `which.py` กับ `reply1–3`: ห่อ act ข้อความเป็น `{"summary"}` | JSON อ่านได้ 3/3; ห่อแล้ว reply2, reply3 ผ่าน; reply1 ยังล้ม (`acts` 8 ช่อง) | H1 confirmed; H3, H4 out; H2 in |
| 3 | prompt variant (`variant.py`): ตัวอย่าง JSON เป็น object ต่อองก์ตามชื่อ `[{"summary": "สรุปองก์ เปิด"}, …×4]`, Qwen จริง 5 ครั้ง | red 5/5: ยังตอบ `acts` เป็นข้อความทั้ง 5; ห่อแล้วผ่าน 4/5; reply3 มี 12 ช่อง (4 องก์ × 3 ประโยค แยกช่องละประโยค) | prompt ที่ชัดขึ้นไม่เปลี่ยนรูปของ `acts`: แก้ต้องอยู่ที่ parser; H2 เกิด 2/8 ครั้งรวม #1 |
| 4 | หลังแก้ (`writer._summary`), prompt จริงเดิม, Qwen จริง 20 ครั้ง (การทดลองของ Outsider; รัน `repro.py` ที่ไม่ย่อ) | `acts` เป็นข้อความ 20/20; ผ่าน 15/20 (31–68 วิ, ครั้งหนึ่ง 125 วิ); ล้ม 5/20 ทุกตัวเพราะจำนวนช่อง 6, 12, 55, 3, 25 (ไม่ใช่ทวีคูณของ 4 เสมอ) | H1 fix ยืนยัน; H2 คือสาเหตุที่เหลือ ~25% ต่อครั้ง ≈ 1.6% ต่องาน (3 ครั้ง ถ้าอิสระ) |

## Outsider

จัดอันดับ H1 (`acts` เป็นข้อความ, ห่อแล้วผ่าน 6/8) > H2 (จำนวนองก์ผิด 2/8, น่าจะเป็นผลข้างเคียงของรูปข้อความ: Qwen มอง `acts` เป็นรายการประโยค) > H3–H5 out. ข้อขัด: #3 ขัดส่วน "อ่านตัวอย่างใน prompt ผิด" ของ H1 — ยืนยันได้แค่ว่า parser ตัดข้อความ ไม่ใช่สาเหตุใน prompt; #3 ยังขัดคำทำนายของ H2 (prompt ชัดขึ้นยังได้ 12 ช่อง). การทดลองที่ตัดสิน: prompt จริง ~20 ครั้งกับ parser ที่รับข้อความ นับอัตราผ่านต่อครั้งและการกระจายของจำนวนช่อง. ความเสี่ยงที่ชี้: ~25% ต่อครั้งยังล้มที่จำนวน (3 ครั้ง ~1–2% ของงานยัง `write_failed` ถ้าอิสระกัน); คำตอบ 4 ช่องที่จริงเป็นประโยคไม่ใช่องก์จะผ่านแต่ผิดองก์; รายการปน/ข้อความว่าง/list ซ้อนต้องมีกติกา — รับไว้: ปนได้, ว่างหรือ list ซ้อนได้ `""` แล้วสั่งใหม่ (`_cleaned` ของที่ไม่ใช่ข้อความ); การทดลอง 20 ครั้งรันเป็น #4

## Fix

- **Regression test:** `test_a_plot_answer_whose_acts_are_plain_summaries_is_read_as_one` (`test_toon_eps_api.py`, seam API + fake llm: `acts` 3 ข้อความ (มี CJK) ปนกับ object 1 ตัว) — แดงก่อนแก้ (`plot attempt 3 is not the JSON asked for`), เขียวหลังแก้ด้วยคำขอเดียว
- **Change:** `writer._summary`: act ที่ไม่ใช่ object คือ summary ของมันเอง แล้วผ่าน `_cleaned` เหมือนเดิม (ไม่ใช่ข้อความ → `""` → สั่งใหม่); D81, spec › Plot job ข้อ 4
- **Probes removed:** ไม่มี probe ในโค้ด; `repro.py`, `variant.py`, `which.py` อยู่ใน scratchpad ของ session ไม่ commit

## Postmortem

**Timeline:**
- 2026-11-10 — เริ่ม: `plot_prompt` และ `parse_plot` มาพร้อม ticket 02 (`31c0ec1`), test ด้วย fake llm เท่านั้น
- 2026-11-11 — พบ: Plot job ของ `e_14c37720` ล้ม `write_failed` สองครั้งระหว่างการวัด D74 ของ ticket 15 (Blocked #35)
- 2026-11-11 — หาเจอ: repro กับ Qwen จริงเก็บคำตอบดิบ, `acts` เป็นข้อความ 3/3 (#1–#2)
- 2026-11-11 — แก้: `writer._summary` (D81); Qwen จริงผ่าน 15/20 (#4)

**Root cause:** Plot job ล้มเพราะ parser ตัด act ที่เป็นข้อความ → ทำไมไม่เห็นตอน build: test ทุกตัวใช้ fake llm ที่ตอบรูปเดียวกับตัวอย่างใน prompt ไม่เคยมีคำตอบจากโมเดลจริง → ทำไมไม่เห็นตอนลองจริง: Plot job ไม่เคยถูกรันกับ Qwen จริงก่อน ticket 15 (เช็คมือ #11 ยังไม่ได้ทำ เครื่อง build ไม่มี Qwen) และ log บอกแค่ "not the JSON asked for" ไม่บอกว่าคำตอบเป็นอะไร จึงวินิจฉัยจาก log ไม่ได้

**Prevention:**
- parser รับรูปที่ Qwen จริงตอบ (เอาอันตรายออก) — D81, `test_a_plot_answer_whose_acts_are_plain_summaries_is_read_as_one`
- log เหตุและต้นของคำตอบที่อ่านไม่ได้ เพื่อให้ครั้งหน้าวินิจฉัยจาก log ได้ — ticket 16
- fixture ของ fake llm จากคำตอบจริงของ Qwen (`acts` เป็นข้อความ) — ticket 16
- ลดจำนวนองก์ผิด (H2, 7/28 ครั้ง ≈ 1.6% ต่องาน) — ticket 16 (auto mode เลือกตัวเลือกที่แนะนำ)

**What helped:** เรียก `spoil_maker.llm.load`/`generate` ตรงใน process เดียว ไม่ผ่าน backend ทำให้เห็นคำตอบดิบใน ~45 วิ; เก็บคำตอบเป็นไฟล์แล้วเช็คด้วย `which.py` ทำให้ลอง knob ได้ทันทีโดยไม่รัน Qwen ซ้ำ. ช้า: log เดิมไม่เก็บคำตอบ
