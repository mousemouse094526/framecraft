# Debug: Ref job ค้างบน M1 16 GB

**Status:** blocked: stack ของงานที่ค้างครั้งหน้า (D76 พิมพ์เองเมื่อ request ของ klein เกิน 10 นาที หรือ `kill -USR1`)

**Summary:**
- **Cause:** รอบสองไม่ได้ค้าง: ภาพ 3 กำลังวาดตามปกติตอนถูกกดหยุด (หน้าเว็บนับแค่ภาพที่เสร็จ, CPU ต่ำเพราะ MPS ทำงาน); รอบแรกยังไม่พบเหตุ ล็อกหายและไม่เกิดซ้ำใน 5 ครั้ง
- **Fix:** ไม่มีการแก้เหตุ; ล็อกของ backend มีบรรทัดงานพร้อมเวลา และตัวดึง stack ของ backend กับ klein (D76) — ใน commit ของ ticket 15
- **Prevention:** ครั้งหน้าที่ค้าง ล็อกบอกว่าค้างนานเท่าไรและ stack บอกว่ารออยู่ที่ไหน; ความคืบหน้าระหว่างภาพในหน้าเว็บรอตัดสินใน `/warroom toon`

## Symptom

Blocked #32 (เช็คมือบน M1 16 GB, 2026-11-11): "Ref job ค้าง 2 ครั้ง (ครั้งแรก `drawing 0/3` ไม่มี worker ทำงาน → รีสตาร์ท backend แล้วเดินต่อ; ครั้งที่สองค้างที่ `2/3` worker idle 1% CPU, ภาพใบ 3 ไม่มา)" · "ที่เห็นจริง 8–10 นาที/ภาพ".

## Reproduce

**Command:** `FRAMECRAFT_API=http://127.0.0.1:8001/api .venv/bin/python scripts/measure_toon_memory.py {out} ref s_73ac00e3 characters c_d0cd8188 5` (Ref job จริง 5 ครั้งติดกัน, poll ทุก 3 วิ, จด swap/pressure/footprint ทุก 5 วิ; รอบนี้รันด้วยรุ่น scratchpad ของ script เดียวกัน)

**Rate:** ไม่ค้าง 0 ใน 5 (373–377 วิทุกครั้ง)

**Minimised to:** —

## Scope

- **Docs say:** timeout ต่อภาพ 15 นาที ใช้ทั้งการรอ `Encoded` และแต่ละ `Drawn`; เกิน → `model_failed` และหยุด process ลูก (spec › Image job, D75). log บอกว่างานเริ่มและจบอย่างไรหลังกี่วินาที (spec › Ops)
- **Last good:** ไม่มี: เช็คมือบน M1 ครั้งแรกคือครั้งนี้
- **ล็อกที่มี:** backend รอบสอง (pid 18096, เริ่ม 11:18:16) เขียนลง `~/.hermes/cache/scratch/api.log`; ล็อกของรอบแรกถูกเขียนทับตอนรีสตาร์ท (ไฟล์เดียวกันเริ่มใหม่) จึงไม่มีแล้ว
- **Ruled out:**
  - รอบสอง "ค้างที่ 2/3" — ไม่ได้ค้าง: `api.log` มี tqdm ของ klein ภาพ 1 และ 2 ครบ 4/4 step (26.4 วิ/step, 1:45 ต่อภาพ) และภาพ 3 เดินถึง 2/4 step (0:52) แล้วมี `DELETE /api/toon/jobs/current 202` (กดหยุด); `jobs/current` ตอนนี้ `cancelled` `done 2/3` `cancel_requested true`. CPU 1% ระหว่างวาดคือ MPS ทำงานบน GPU ไม่ใช่ process ว่าง; หน้าเว็บนับแค่ภาพที่เสร็จ (`done`) จึงไม่ขยับราว 2 นาทีต่อภาพ
  - "8–10 นาที/ภาพ" — ล็อกรอบสองไม่ตรง: denoise 1:45 ต่อภาพ ไม่มีการโหลดโมเดลใหม่ระหว่างภาพ (โหลด text encoder 8 วิ และ pipeline ครั้งเดียวก่อนภาพแรก)
- **พบระหว่างอ่านล็อก:** ไม่มีบรรทัด `toon job ref … started` / `ended … after N s` เลย: backend ไม่ตั้ง logging (`grep basicConfig|dictConfig` ไม่พบ) uvicorn ตั้งแค่ logger ของตัวเอง จึง INFO ของ `backend.*` ไม่ออก — ขั้นแรกของ D75 ("อ่าน log ว่าค้างนานเท่าไร") ทำไม่ได้ทุกครั้ง และล็อกไม่มีเวลา

## Fail path

ยังไม่มี: ทำให้ค้างซ้ำไม่ได้. timeout ต่อภาพคุมการรอ `Encoded` และทุก `Drawn` อยู่แล้ว (test klein ปลอมเงียบสองตัวใน ticket 15 ผ่านกับโค้ดก่อนแก้)

## Hypotheses

| # | Hypothesis | Prediction | Disproof | State |
|---|---|---|---|---|
| H1 | รอบสองไม่ได้ค้าง แต่ผู้เช็คเห็น `done` ไม่ขยับระหว่างภาพ (~2 นาที) และ CPU ต่ำ จึงกดหยุด | Ref job จริงจบ `done` ภายในราว 6–7 นาที ทุกครั้ง | Ref job จริงที่ไม่มีใครกดหยุดค้างเกิน 15 นาที | confirmed (รอบสอง; run 0–5) |
| H2 | รอบแรก (`drawing 0/3` ไม่มี process ลูก): โหลด text encoder + transformer ช้ามากเพราะ swap ของแอปอื่น (OrbStack, VS Code, Chrome, Claude) ผู้เช็ครีสตาร์ทก่อน 15 นาที | ตอน swap สูง การโหลดนานขึ้นมากแต่จบเอง | Ref job ตอน swap สูงค้างเกิน 15 นาทีโดย timeout ไม่ทำงาน | alive (run 1–5: swap 4–6.8 GB และ pressure critical สองครั้ง แต่โหลดยังราว 25 วิ: อ่อนลง) |
| H3 | backend ค้างก่อน `track` (`klein.start_worker` → `process.start()`) | ค้างอีกครั้ง: ไม่มี process ลูก และ stack ของ backend (SIGUSR1) อยู่ใน `start_worker` | ทุกครั้ง process ลูกเกิดภายในวินาที | alive |
| H4 | process ลูกค้างใน MPS/Metal (deadlock) ระหว่าง `Encode` หรือ `Draw` | stack ของ process ลูก (`DUMP_AFTER`) ค้างที่จุดเดียวกันนานเกิน 10 นาที | ทุกครั้ง step ของ tqdm เดินต่อสม่ำเสมอ | alive |

## Ledger

| Run | Changed | Result | Rules in / out |
|---|---|---|---|
| 0 | อ่าน `api.log` ของรอบสอง | ภาพ 1–2 ครบ, ภาพ 3 ถึง step 2/4 แล้วถูก `DELETE` | H1 in สำหรับรอบสอง; H3, H4 out สำหรับรอบสอง; รอบแรกไม่มีล็อก |
| 1 | Ref job จริงครั้งที่ 1 (backend ใหม่บน port 8001 พร้อม log มีเวลาและตัวดึง stack; backend เดิมยังเปิดอยู่ idle เพราะหยุดมันไม่ได้), swap ก่อนเริ่ม 2.8 GB, แอปอื่นเปิดอยู่ | `done` 377 วิ: Qwen 15 วิ, โหลด + ภาพ 1 136 วิ, ภาพ 2 111 วิ, ภาพ 3 115 วิ; process ลูก CPU 3.8% ระหว่าง denoise | H1 in (CPU ต่ำคือ MPS ทำงาน); swap ขึ้นถึง 5.6 GB ไม่ทำให้ค้าง |
| 2–5 | Ref job จริงครั้งที่ 2–5 ต่อกัน (เว้น 10 วิ) | `done` ทุกครั้ง 374, 377, 374, 374 วิ; ไม่มี stack ถูกพิมพ์ (ไม่มี request ใดเกิน 10 นาที); pressure critical ใน run 3 ตอน decode ภาพแรก | H3, H4 ไม่เกิดใน 5 ครั้ง; H2 อ่อนลง; ทำให้ค้างซ้ำไม่ได้ → D75: ตัวดึง stack แล้ววัดต่อ |

## Outsider

ไม่ได้ทำ: ไม่มีการแก้เหตุให้ตรวจก่อน (Phase 4 ทำเมื่อมี stack ของรอบที่ค้าง)

## Fix

- **Regression test:** ไม่มีของเหตุ (ยังไม่พบ). ของที่พบระหว่างทาง: `test_app.py` › `test_the_backend_s_own_info_lines_reach_the_terminal_with_the_time` (ล้มก่อนแก้); `test_toon_klein.py` › stack ของ klein เมื่อ request เกิน `DUMP_AFTER`; กติกา timeout: `test_toon_ref_api.py` › klein ไม่ตอบ `Encode`, `test_toon_images_api.py` › klein ไม่ตอบ `Draw` ใบที่สอง
- **Change:** `app.log_to_terminal` (logger `backend` INFO พร้อมเวลา), `workers.dump_stacks_on_signal` ใน backend และ klein, `workers.dump_stacks_after(klein.DUMP_AFTER)` รอบทุก request ของ klein (D76); `scripts/measure_toon_memory.py`
- **Probes removed:** ไม่ได้ใส่ probe

## Postmortem

**Timeline:**
- 2026-11-11 ราว 11:00 — Ref job รอบแรกค้างที่ `drawing 0/3`, รีสตาร์ท backend
- 2026-11-11 11:18 — Ref job รอบสอง, กดหยุดตอนภาพ 3 (step 2/4)
- 2026-11-11 11:24 — Blocked #32
- 2026-11-11 12:00 — อ่าน `api.log` (ticket 15): รอบสองถูกกดหยุด
- 2026-11-11 12:07–12:39 — Ref job จริง 5 ครั้ง `done` ทุกครั้ง

**Root cause:** (รอบสอง) ผู้เช็คเห็นงานเหมือนค้าง → หน้าเว็บนับแค่ภาพที่เสร็จ ราว 2 นาทีไม่ขยับ และ CPU ของ process ลูกต่ำเพราะงานอยู่บน GPU → ไม่มีอะไรบอกว่างานยังเดิน: ล็อกของ backend ไม่ออกเลย (ไม่มีการตั้ง logging) และไม่มีเวลา → ระบบไม่ให้ทางดูว่างานยังเดินหรือค้าง. (รอบแรก) ยังไม่รู้: ล็อกถูกเขียนทับตอนรีสตาร์ท

**Prevention:**
- ล็อกของ backend ใน `[api]` พร้อมเวลา — ticket 15 (D76)
- stack ของ backend และ klein ตอนค้าง — ticket 15 (D76)
- หน้าเว็บบอก step ของ klein ระหว่างภาพ (ไม่ใช่แค่ภาพที่เสร็จ) — ข้อเสนอ, ตัดสินใน `/warroom toon` (auto mode เลือกตัวเลือกที่แนะนำ: จดไว้ก่อน); อยู่ใน For the next ticket

**What helped:** ล็อกของรอบสองยังอยู่ในไฟล์ (backend รันแบบ background ส่ง stdout ลงไฟล์); ถ้ารันใน terminal ปกติ ล็อกจะหายพร้อม terminal
