# Progress: spoil-maker

**Now:** 02 done — หน้า Saved voice (`#/spoil/voices`): ออกแบบเสียงด้วย OmniVoice ฟัง บันทึก เปลี่ยนชื่อ ลบ, ตัวแปลงตัวเลขเป็นคำไทย, แถว `pythainlp`; ต่อไป 03 (ร่างบทและหน้าตรวจแก้)

**Next:**

```
/warroom-build spoil-maker 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 00 | แถบ 3 tab และแก้ Transcript | done |
| 01 | ติดตั้ง Qwen, ช่อง GPU และดูภาพ | done |
| 02 | Saved voice | done |
| 03 | ร่างบทและหน้าตรวจแก้ | ready |
| 04 | เสียงต่อประโยคและ render | ready |

## Log

### 02: Saved voice — done 2026-11-02

**Built:**
- ติดตั้ง: `pythainlp==5.4.0` ใน `pyproject.toml`; แถว Status check `pythainlp` หลัง `mlx_vlm` (14 แถว) เช็คจาก metadata + `find_spec` ผ่าน `Probes.pythainlp`, ทั้ง Mac และ Windows; `checks.check_pinned` ใช้ร่วมกับ `mlx_vlm`
- `backend.spoil_maker.thai`: `spoken` (เลขไทย → จุลภาค → เวลา → % → ทศนิยม → จำนวนเต็ม, `เอ็ด`/`ยี่สิบ`/`สิบ`/ล้านซ้ำ, `007` ทีละหลัก), `letters` (ไม่นับช่องว่างและวรรคตอน), `words` (pythainlp `newmm` ตั้ง `PYTHAINLP_DATA` = `models/pythainlp/` และ `PYTHAINLP_OFFLINE` ก่อน import)
- `backend.spoil_maker.tts`: adapter ของ OmniVoice ใน process ลูก `spawn` — `Design` → พูดประโยคตัวอย่างด้วย `instruct`, สร้าง clone prompt, พูดอีกครั้งที่ speed ที่เลือก, `num_step` 16 → `Designed` (PCM 16 บิต, sample rate, prompt เป็น bytes)
- `backend.spoil_maker.voices` + routes: `POST/GET/DELETE /voice-jobs[/current]`, `GET|HEAD /voice-jobs/preview.wav`, `GET/POST /voices`, `PATCH/DELETE /voices/{id}`, `GET /voices/{id}/sample.wav`; gate `device`, `model_omnivoice`, `pythainlp`; จองช่อง GPU `voice` ("สร้างเสียง"); `invalid_voice`, `no_preview`, `busy`, `gpu_busy`, `not_ready`, `404`; preview ใน `.pending/` (json เขียนท้ายสุด), ยกเลิกหรือล้มเก็บ preview เดิม; start ล้าง `.pending/` และ `*.tmp`; `kind: "sentences"` ตอบ `400` `invalid_request` จนมี Spoil draft
- `backend.files.write_atomic` (ย้ายจาก `spoil.clips`, ผู้ใช้คนที่สาม); `FakeLlm` → `FakeModel` ที่ `FakeTts` ใช้ด้วย
- หน้าเว็บ `#/spoil/voices` (`SavedVoicePage`, `VoiceDesigner`, `VoiceRow`, `NameForm`, `useVoices`) ตาม Figma Saved voice: ไม่มี preview / กำลังสุ่ม / GPU busy (poll งานถอดหรืองานบรรยายฉากจนจบ) / preview พร้อม, แถว default / เปลี่ยนชื่อ / ยืนยันลบ / ลบไม่ได้, รายการว่าง; preview ที่บันทึกไปแล้วเช็คด้วย `HEAD`
- โค้ดใช้ร่วมหน้าเว็บ: `lib/gpu.ts` (+ `GPU_JOB_PATHS`), `lib/job.ts` (+ `isRunning`), `lib/refusal.ts`, `lib/usePollWhile.ts`, `lib/api.ts` `headStatus`, `components/ui/ProgressBar.tsx`
- NOTICE.md: เครดิตโมเดลแนะนำ ไม่บังคับ (D41); README: ส่วน "เสียงบรรยาย" และคำ "บรรยายฉาก" แทน "ดูภาพ" (D58); library notes `omnivoice.md`, `pythainlp.md`; skills `fastapi-api` (module, import, pythainlp, routes รับ body เป็น dict), `vite-react-web` (`lib/`, `#/spoil/voices`)
- เช็คมือบน M2 (Seam 3): Library assumptions ของ omnivoice ผ่านครบก่อนเขียน worker (โหลด 3.8 วินาที, `generate(instruct=…)` 5.6 วินาที, `create_voice_clone_prompt` แล้ว `save` ลง `BytesIO` 10 KB และ `load` ได้, speed 0.8 → 5.96 วินาที / 1.2 → 4.5 วินาที, `num_step` 16); ออกแบบเสียงหญิง young adult จากหน้าเว็บ → preview 4.97 วินาที, `chars_per_s` 15.3, บันทึกแล้ว restart backend → รายการเดิม, `sample.wav` md5 เดิม, `.pt` โหลดกลับเป็น clone prompt ได้, `.pending/` หาย; ตัดคำ pythainlp → ไม่มี `~/pythainlp-data`
- หน้าเว็บเทียบ Figma: 1440 designer 520×390 ที่ (160,177), รายการ 584×212 ที่ (696,177), แถว 60 / เปลี่ยนชื่อ 92 / ยืนยันลบ 139; 375 designer 343×478, แถว 341×97, ปุ่มกลับ 44, ไม่มี scroll แนวนอน

**Decided:**
- D59 — ทางเลือกเล็ก: `PYTHAINLP_DATA` แทน `PYTHAINLP_DATA_DIR` (spec และ ticket แก้แล้ว), แถว `pythainlp` ไม่ import จริง, นับตัวอักษร, กฎตัวเลขที่ spec ไม่ระบุ, ประโยคล็อก, ไฟล์ผลเป็น bytes, state `voicing`, body ของ `POST /voice-jobs`, `gpu.Kind` `voice`, ลำดับรายการ, หน้าเว็บไม่มีตัวบอกขั้นและค่าตั้งต้น, โค้ดใช้ร่วม, NOTICE.md

**For the next ticket:**
- 03/04: Voice job เป็นงานลูกที่สามที่ท้าย `_run`, `cancel`, `stop_on_shutdown`, `_reply`, `_failed` ซ้ำกับ `Describes` (และ `Transcriptions`) — ย้ายเข้า `backend.jobs` ก่อนเพิ่ม Draft job (review ticket 01 และ 02)
- 03: `voice_in_use` ของ `DELETE /voices/{id}` และ `in_use` ของ `GET /voices` (ตอนนี้ `false` เสมอ); `last_voice_id` ใน settings; ลิงก์ไป `#/spoil/voices` จากหน้าตั้งค่า; `gpu.Kind` เพิ่ม `draft` และ `GPU_JOB_PATHS` ใน `lib/gpu.ts` เพิ่ม path ของ Draft job
- 04: Voice job `sentences` แทนที่ `400` ชั่วคราวใน `voices.VoiceJobs.start` (test `test_sentences_with_ids_that_no_draft_has_are_invalid_request` ต้องเปลี่ยน); test ระดับ API ของประโยคตัวเลขตาม Seam 1 (ตอนนี้ test `thai.spoken` ตรง); `thai.words` ใช้ตัดซับ; seam 3 "5 ประโยคด้วยเสียงเดียวกันฟังเป็นเสียงเดียวกัน" และ "1968, 10:30 อ่านถูก"
- review ที่ไม่ได้แก้: ตัวเลือกเพศ วัย ระดับเสียง และสเกล speed อยู่ทั้ง `voices.py` และ `VoiceDesigner.tsx` (คนละภาษา แยกไม่ได้โดยไม่เพิ่ม API); test ที่อ่าน `{id}.json` และ `.pending/` ตรง (รูปไฟล์ใน spec › Saved voice และ Seams 1 › start)
- ผู้ใช้ควรฟังเสียง `พี่สาวเล่าหนัง` (`media/spoil-maker/voices/v_be1485d1.wav`) ด้วยหูเอง — เช็คมือนี้ยืนยันว่าไฟล์เดิมหลัง restart แต่ไม่ได้ฟัง

**Checks:** `uv run pytest` — 310 passed; `npm --prefix frontend test` — 120 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 01: ติดตั้ง Qwen, ช่อง GPU และดูภาพ — done 2026-11-02

**Built:**
- ติดตั้ง: `QWEN` (Qwen3.5 9B MLX 4bit) ต่อท้าย `MODELS`, `ModelSpec.platforms` — Setup script บน Mac โหลดและเขียน marker, Windows ข้าม; ที่ว่างดิสก์บน Mac 20 GB; `mlx-vlm==0.7.11` marker `darwin`
- Status check: แถว `model_qwen` และ `mlx_vlm` หลัง `device` (13 แถว); Windows → `missing` "ยังไม่รองรับบน Windows"; `mlx_vlm` อ่าน metadata ผ่าน probe `Probes.mlx_vlm` ไม่ import
- ช่อง GPU `backend.gpu.GpuSlot`: งานถอดและงานดูภาพจองก่อนเริ่ม, ชนกัน → `409` `gpu_busy` `running`; คืนช่องทุกทางออก; ลบคลิปที่งานอ่านอยู่ → `409` `clip_busy`; งานโหลดไม่ใช้ช่อง
- Describe job (`backend.spoil_maker`): `POST/GET/DELETE /api/spoil-maker/describes[/current]`, `GET /clips/{id}/shots[/{n}]`; ffmpeg หาจุดตัด (% ของ `cutting`) → `plan_shots` (แบ่งช่วง > 10 วินาที, รวมช่วง < 1 วินาที) → เฟรมกลาง 448 ให้ Qwen + ภาพเล็ก 320 → process ลูก mlx-vlm บรรยายทีละ Shot (timeout 60 วินาที) → สลับ folder `.new-{id}` เมื่อ `done`; ยกเลิกเก็บ Shot เดิม; startup ล้าง `.new-*` และ Shot ของคลิปที่ล้าง; ลบคลิปลบ Shot
- โค้ดใช้ร่วม: `backend.errors.ApiError` (เดิม `SpoilError`), `backend.jobs` (`JobSlot`, `next_message`, `stop_process`); `404` `not_found` สำหรับ path ที่ไม่มี route ทั้งแอป
- หน้าเว็บ: `DescribeControls` ในแถว Temp clip ที่ถอดแล้วตาม Figma Clip row states — ดูภาพ / % / ดูภาพแล้ว / กดไม่ได้พร้อมเหตุผล / ยืนยันดูภาพใหม่ในแถว / error ใต้แถว + ลิงก์ติดตั้ง; `gpu_busy` ของปุ่มถอดขึ้นในกล่องถอด; `ProgressBar` ใช้ร่วมกับ `ProgressCard`
- test เดิน Windows ได้: `fake_root` ตั้ง `checks.this_platform()` = `darwin` และ probe mlx-vlm ปลอม (ADR-0016); กฎใน `fastapi-api/rules/testing.md`
- เช็คมือบน M2 (Seam 3): Library assumptions mlx-vlm ทั้ง 3 ข้อผ่าน (โหลดจาก snapshot 4 วินาที, `enable_thinking=False` ให้ `<think></think>` ว่าง, `generate` มีและไม่มีภาพ → `.text`); หนัง 96 นาที (Night of the Living Dead, 5743 วินาที) → 840 Shot, เฟรม 640 ใช้ ~64 นาที (เกินเป้า) → เปลี่ยนเป็น 448 ใช้ **52.7 นาที** (cutting ~4 นาที, 3.2 วินาที/Shot), สุ่ม 10 Shot ตรงภาพ 9 ทั้งสองรอบ; ยกเลิกระหว่าง `describing` → process ลูกหายใน 0.31 วินาที, ไม่มี `.new-*`
- หน้าเว็บเทียบ Figma ที่ 1440 และ 375 ระหว่างงานจริง (กำลังหาจุดตัดภาพ %, ปุ่มคลิปอื่นกดไม่ได้ "รอให้งานดูภาพเสร็จก่อน"), 375 ไม่มี scroll แนวนอน

**Decided:**
- D56 — ทางเลือกเล็ก: ตำแหน่งแถว Status check, probe mlx-vlm และ `this_platform`, `platforms`, `not_ready` มี `rows`, โค้ดใช้ร่วม, `GpuSlot.clip_untouched`, ลำดับการเช็ค, ไฟล์ของ module, ลำดับต่อ Shot และ timeout, ภาพเล็ก ffmpeg `-q:v 5`, % ของ `cutting`, `404` ทั้งแอป, log, รายละเอียดหน้าเว็บ, `gpu.ADVICE`, `ProgressBar`
- D57 — เฟรมที่ Qwen บรรยายกว้าง 448 ไม่ใช่ 640 (ผู้ใช้เลือก; spec › Describe job ข้อ 5–7 แก้แล้ว)

**For the next ticket:**
- 03: Draft job ใช้ `backend.spoil_maker.llm` (`Generate` ไม่มีภาพ) และต้องจองช่อง GPU (`gpu.Kind` เพิ่ม `draft`, `RUNNING_NAMES` ทั้ง backend และ `frontend/.../lib/gpu.ts`); `confirm_draft_loss` และ `in_draft` ยังไม่มี; ใส่ check ใน `transcribe.clip_users` (จาก 00)
- review ที่ไม่ได้แก้ (refactor ใหญ่): ท้าย `_run` และ `stop_on_shutdown` ของ `Describes` กับ `Transcriptions` ซ้ำกัน — ย้ายเข้า `backend.jobs` เมื่อ Draft job เป็นงานลูกที่สาม; แถว gate (`ffmpeg`, `Device`) ซ้ำใน `_needed_rows` สามที่; `ending` เป็น `dict` ไม่มี type; `video_id` กับ `clip_id` ใช้ปนใน `describe.py`/`paths.py`; `ClipsPage` เช็ค `.kind` ของ hook ทีละตัวซ้ำ
- `not_ready` ของ spoil มี `rows` และ `404` `not_found` ทั้งแอป — ขยายเกิน ticket (D56); ยืนยันตอน feature review
- หน้าเว็บที่เปิดค้างก่อนงานดูภาพเริ่มจากที่อื่นไม่เห็นงานจนโหลดหน้าใหม่ (poll เฉพาะเมื่อตามงานอยู่, D16) — แบบเดียวกับงานถอด
- มือถือ: tag "ถอดแล้ว" อยู่ใต้ชื่อ แต่ Figma วางท้าย meta (layout ของ ticket 00)

**Checks:** `uv run pytest` — 233 passed; `npm --prefix frontend test` — 100 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 00: แถบ 3 tab และแก้ Transcript — done 2026-11-01

**Built:**
- แถบ tab 3 tab ติดตั้ง (`#/setup`) · คลิป (`#/clips`) · สปอย (`#/spoil`); hash ว่างหรือไม่รู้จัก → ติดตั้ง, `#/spoil/…` → สปอย. `lib/useHashTab.ts` → `lib/useHash.ts` (`useHash`, `tabOf`); nav ของแถบมีชื่อ "แถบ tab"
- tab คลิป: หน้าเดิมของ spoil (`SpoilPage` → `ClipsPage`) ย้ายมาทั้งหน้า; ลิงก์ติดตั้งไม่ครบเป็น "ไปหน้าติดตั้ง"
- tab สปอย (`features/spoil-maker`): `SpoilSteps` ตาม component `Spoil steps` — ขั้นปัจจุบันเด่น ขั้นที่ผ่านมีเครื่องหมายถูก ขั้นอื่นเป็นลิงก์ hash, มือถือแสดงชื่อเฉพาะขั้นปัจจุบัน; ใต้ตัวบอกขั้นยังว่าง (03, 04 ใส่)
- API: `PATCH /api/spoil/clips/{id}/transcript/lines/{n}` → `200` บรรทัดพร้อม `edited: true` เขียนผ่าน `.tmp` ใต้ lock ของงานถอด; `400` `invalid_request`, `404` `not_found`, `409` `transcribing`, `409` `clip_busy` (ผ่าน `transcribe.clip_users`); ข้อความรวมเป็นบรรทัดเดียว; `POST /transcriptions` ของคลิปที่มีบรรทัด `edited` → `409` `has_edits` เว้นแต่ `confirm_edit_loss: true`; `require_json` ครอบ `PATCH`
- หน้าเว็บ: `TranscriptLineItem` ตาม component `Transcript line` (hover "แก้", editing, edited "แก้แล้ว"); Enter บันทึก, Escape ยกเลิก; `409`/`404` แสดงใต้ช่องโดยช่องยังเปิด; ถอดใหม่ได้ `has_edits` → `confirm` แล้วส่งซ้ำ. `GHOST_BUTTON` ใหม่ใน `buttonStyles`; icon pencil และ check จาก Figma
- bug ที่เจอตอนเช็คใน browser: `<video>` กับรายการบรรทัดใช้ key เดียวกัน (React เตือน key ซ้ำ) → แยก key; test "closes the field when another clip is selected" ครอบ
- เช็คมือผ่าน Vite proxy กับ backend จริง: 1440 tab คลิป แก้บรรทัดของ Shorts NASA → บันทึกแล้วขึ้น "แก้แล้ว", ชี้บรรทัดอื่นขึ้น ✎ แก้ ตรง frame "คลิป — แก้ประโยค"; tab สปอย `#/spoil/review` ที่ 1440 และ 375 ตรง frame (375 แสดงชื่อแค่ขั้นปัจจุบัน); 375 tab คลิปไม่มี scroll แนวนอนและจอสัมผัสเห็นปุ่มแก้ตลอด. Transcript ที่แก้ตอนลองคืนจาก backup แล้ว
- README: 3 tab และการแก้บทพูด; skill `vite-react-web` (`useHash.ts`, hash ของขั้น), `fastapi-api` (`PATCH` ต้องเป็น JSON)

**Decided:**
- D55 — ทางเลือกเล็ก: ชื่อ `ClipsPage`/`SpoilMakerPage`/`useHash.ts`, `#/spoil/…` ไม่รู้จัก = ขั้น 1, ขั้นยังว่าง, `clip_users`, `n` เป็นข้อความ ASCII, ลำดับการเช็ค, `PATCH` ต้องเป็น JSON, บรรทัดเดียวเสมอ, ปุ่มแก้บนจอสัมผัส, error ใต้ช่อง, confirm ด้วย `message` ของ `has_edits`

**For the next ticket:**
- 03: Draft job ต้องใส่ check ของตัวเองใน `backend.spoil.transcribe.clip_users` (คืน `True` เมื่อใช้คลิปนั้น) และเปลี่ยน test `clip_busy` ที่ใช้ check ปลอมเป็น Draft job จริง; เพิ่ม test "คลิปใน Spoil draft ที่ไม่มีงาน → `PATCH` `200`" (Seam 1) ที่ ticket นี้ทำไม่ได้เพราะยังไม่มี Spoil draft
- 01: `POST /transcriptions` รับ `confirm_edit_loss` แล้ว — `confirm_draft_loss` และ `gpu_busy` ต่อท้ายลำดับการเช็คเดียวกัน (gate → `404` → `busy` → `has_edits`)
- 02: `#/spoil/voices` ตอนนี้เปิดขั้น 1; ตัดสินว่าหน้า Saved voice แสดงตัวบอกขั้นหรือไม่
- ADR-0013 ยังเขียนว่า "ทุก POST"; spec ของ spoil-maker ขยายเป็น POST และ PATCH แล้ว (โค้ดทำตาม) — แก้ข้อความ ADR ตอน feature review ถ้าผู้ใช้ตกลง
- review ที่ไม่ได้แก้: `_has_edits` อ่าน Transcript ทั้งไฟล์ในตัว `start` (ไฟล์เล็ก ไม่เป็นปัญหา); บรรทัดที่เริ่มวินาทีเดียวกันได้ชื่อ `aria-label` ซ้ำ; ทดสอบ "มือถือแสดงชื่อเฉพาะขั้นปัจจุบัน" เช็คด้วยมือใน browser ไม่มี test (jsdom ไม่มี layout)

**Checks:** `uv run pytest` — 189 passed; `npm --prefix frontend test` — 88 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: แถว Temp clip ใน tab คลิป | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8032-2275)) |
| 2 | 02 | design: Saved voice | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8034-3220)) |
| 3 | 03 | design: ตั้งค่าคลิปสปอย | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8038-4681)) |
| 4 | 03 | design: หน้าตรวจแก้ (ใช้ต่อใน 04) | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390)) |
| 5 | 03 | design: ตัวเลือก Shot | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8050-16186)) |
| 6 | 04 | design: ผล render | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8055-16850)) |
| 7 | 00 | design: แถบ 3 tab, ตัวบอกขั้นของ tab สปอย และ Transcript ที่แก้ได้ใน tab คลิป (D53, D54) | `/warroom spoil-maker` พร้อมลิงก์แบบ | done (Figma 8071-18633) |
