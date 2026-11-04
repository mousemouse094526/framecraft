# Progress: spoil-maker

**Now:** ทุก ticket done (08 เรียบเรียงบท หน้าตาใช้ component เดิมจน Blocked 15 มีแบบ); รอ feature review

**Next:** `/warroom-build spoil-maker --review-feature`

## Tickets

| # | Title | Status |
|---|---|---|
| 00 | แถบ 3 tab และแก้ Transcript | done |
| 01 | ติดตั้ง Qwen, ช่อง GPU และดูภาพ | done |
| 02 | Saved voice | done |
| 03 | ร่างบทและหน้าตรวจแก้ | done |
| 04 | เสียงต่อประโยคและ render | done |
| 05 | ลายน้ำเปิดปิดได้ และงานค้างจาก feature review | done |
| 06 | ตัด EP จากคลิปเดียว | done |
| 07 | ตัวบอกขั้นบอกสถานะจริง | done |
| 08 | เรียบเรียงบท | done |

## Log

### 08: เรียบเรียงบท — done 2026-11-04

**Built:**
- คำสั่งร่างบทบอกว่าทุกประโยคเล่าต่อจากประโยคก่อนเป็นเรื่องเดียว
- Draft job `kind: "draft"`: `writing` → `polishing` → `matching`; ขั้นเรียบเรียง (`script.polish_prompt`, `parse_polish`) ส่งสไตล์ `top_text` ทุกประโยค `[i]` พร้อมบรรทัดที่อ้าง; จับคู่ด้วย `i` (ไม่รู้จัก ซ้ำ fixed ทิ้ง), ต่อประโยค ±50%/ว่าง ใช้ข้อความเดิม, ทั้งบท ไม่ถึงครึ่ง / ±25% ของเป้าหมาย; 2 ครั้ง, timeout terminate แล้วเริ่มใหม่; ไม่ผ่านใช้ข้อความเดิม log ไม่มีข้อความบท; 0.3 / `2 × ตัวอักษรของบท + 1,000` / 5 นาที
- `Sentence.edited`: `PATCH` ข้อความต่างจากที่เก็บ หรือแทรก → `true`; ไฟล์เก่าอ่าน `false`
- `POST /draft-jobs` `{kind: "polish", include_edited?}`: `busy` → `no_draft` → `invalid_request` → `nothing_to_polish` → `not_ready` → `draft_locked` → `gpu_busy`; จองช่อง GPU ด้วย `locks_draft` และคลิปของ draft (`clip_busy`); เขียนเฉพาะ `text` ที่เปลี่ยน (`edited` → `false`); ไม่ผ่าน → `failed` `polish_failed` draft ไม่เปลี่ยน; `done` = ประโยคที่เปลี่ยน, `total` = ที่ขอ; ไม่เกินรวมเดิม +15%
- หน้าตรวจแก้: ปุ่ม "เรียบเรียงใหม่" → `PolishDialog` (ช่องติ๊ก, คำเตือนเขียนทับ, คำเตือนเสียงใหม่, ปุ่มกดไม่ได้เมื่อทุกประโยคแก้เอง); รอ change ที่ยังไม่ตอบ แล้วอ่าน `/draft` ก่อนส่ง; "กำลังเรียบเรียง" กับยกเลิก ช่องแก้กดไม่ได้; จบ "เรียบเรียง {n} ประโยค" / "ไม่มีประโยคที่เปลี่ยน" / ข้อความ `polish_failed`; ป้าย "แก้เอง"
- ตัวบอกขั้น: "กำลังเรียบเรียง" พร้อมจุดหมุน (ทั้ง `polishing` ของ draft และ `polish`), "เรียบเรียงไม่สำเร็จ"; ขั้น 1 ปุ่มร่างแสดง "กำลังเรียบเรียง"
- โค้ดใช้ร่วม: `useDialogKeys` (Esc + focus trap, ShotPicker ใช้ด้วย), `ReviewJobProgress` และ `REVIEW_JOB_TEXT` แทน `PickProgress`
- test: backend +28 (Seam 1 › เรียบเรียง ทุกข้อ + timeout, generation settings, gpu_busy, not_ready, clip_busy); `ScriptReview.test.tsx` +12, `SpoilMakerPage.test.tsx` +3 (Seam 2)
- เช็คใน dev server (draft ปลอมด้วย patch fetch, draft ในเครื่องเป็น `version` 1): 1440 และ 375 ไม่มี scroll แนวนอน ไม่มี console error; กล่องเลือก ติ๊กแล้วเห็นคำเตือน, ป้าย "แก้เอง"
- Review สามแกนแก้แล้ว: `error`/`notice` รวมเป็น `message`, overlay เป็น union เดียว, `PolishProgress` ซ้ำ `PickProgress` → `ReviewJobProgress`, ชื่อ `_ask_to_polish`/`fits`/`sendChange`, `POLISH_GROWTH` และ `grew_little` ย้ายไป `script`, log ใส่ code, test gpu_busy, ชื่อและคำอธิบาย test

**Decided:**
- D79 — ทางเลือกเล็กตอน build เรียบเรียงบท

**For the next ticket:**
- เช็คมือ Seam 3 ยังไม่ทำ: ร่างบท 60 วินาที `drama` จาก EP 30 นาทีบน M2 → รวมเรียบเรียงภายใน 8 นาที, 10 คู่ประโยค ≥ 8 คู่เล่าต่อกัน, ความยาว ±25% (ทำตอน feature review)
- เมื่อ Blocked 15 มีแบบ: ปรับปุ่ม กล่องเลือก ป้าย "แก้เอง" ให้ตรง Figma ที่ 1440 และ 375
- `sm:shadow-[0_16px_48px_0_rgba(0,0,0,0.18)]` และกรอบ modal ซ้ำใน `ShotPicker` กับ `PolishDialog` — ทำเป็น token หรือ component `Modal`
- `style`, `top_text`, `sentences`, `transcript` เดินด้วยกันใน `_ask_to_polish` และ `polish_prompt` — รวมเป็น type ได้ถ้าเพิ่มอีก
- การแยกตาม kind/state ของ Draft job ยังอยู่หลายที่ (`steps.ts`, `SetupSettings`, `REVIEW_JOB_TEXT`) — ถ้าเพิ่ม kind อีกควรรวมเป็น map เดียว
- ยกมาจาก 07: test helper `phased`/`jsonResponse`/`backend` ซ้ำใน 4 ไฟล์ test; `refreshSteps()` ซ้ำใน 4 hook

**Checks:** `uv run pytest` — 545 passed; `npm --prefix frontend test` — 222 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 07: ตัวบอกขั้นบอกสถานะจริง — done 2026-11-04

**Built:**
- `useStepStatus` (state ร่วมใน `SpoilMakerPage`): อ่าน `/draft`, `/renders`, `/draft-jobs/current`, `/voice-jobs/current` (`sentences` เท่านั้น), `/renders/current`; poll งานที่ยังไม่จบทุก 1 วินาที แม้เปิดขั้นอื่น; งานจบ → อ่าน `/draft` และ `/renders` ใหม่; poll ล้ม → เลิกตามจน refresh
- `StepsRefreshContext`: `useSpoilerSetup`, `useScriptReview`, `useReviewJobs`, `useRenders` เรียก refresh เมื่อเริ่มงาน (รวม `busy`), ยกเลิก, แทรก/ลบประโยค, ลบผล render
- `lib/steps.ts` `stepLines`: ขั้น 1 "{ชื่อคลิป} · EP {n}" / "ยังไม่เลือก"; ขั้น 2 "กำลังร่าง" / "กำลังเลือกภาพ x/y" / "สร้างเสียง x/y" / "{n} ประโยค" / "ยังไม่มีบท" / "ร่างบทไม่สำเร็จ" / "สร้างเสียงไม่สำเร็จ" (งานที่เริ่มล่าสุดเป็นตัวบอก, `pick` คงจำนวนประโยคพร้อมจุดหมุน); ขั้น 3 "render {p}%" / "render…" / "render: สร้างเสียง x/y" / "{n} คลิป" / "ยังไม่มี" / "render ไม่สำเร็จ"
- `SpoilSteps`: ทุกขั้นเป็นลิงก์ที่มีเลข, ที่เปิดอยู่ `aria-current="step"`, ไม่มีเครื่องหมายถูก (`check.svg` ลบ), จุดหมุน `motion-safe:animate-spin`, มือถือซ่อนชื่อและบรรทัดสถานะของขั้นที่ไม่ได้เปิดแต่จุดหมุนอยู่
- test: `SpoilMakerPage.test.tsx` 25 test ตาม Seams 2 › ตัวบอกขั้น (รวม render ตอนเปิดขั้น 1, กด render ในขั้น 2, failed จนเริ่มใหม่, ยกเลิก, Draft job จบอ่าน draft ใหม่, poll ล้มแล้วตามได้อีก, reduced motion, มือถือ); 3 test เดิมที่ตอบ `*/current` เป็นลำดับใช้ `phased`
- เช็คใน dev server กับ backend จริง: 1440 และ 375 ไม่มี scroll แนวนอน ไม่มี console error; render ปลอม (patch fetch ในหน้า) เห็น "render 45%" และจุดหมุนที่ขั้น 3 ทั้งสองขนาด
- Library notes: `react.md` (context เป็น provider, ค่าตั้งต้น), `tailwindcss.md` (`motion-safe:`)
- Review สามแกนแก้แล้ว: poll ล้มค้างถาวร → เลิกตามจน refresh, test ที่ขาด (failed ล้างเมื่อเริ่มใหม่, ยกเลิก, Draft job จบ), test มือถือ query ด้วยข้อความไม่ใช่ selector, `countOf`, `readResults` ใช้ร่วม, `StepLines` tuple, ชื่อ `StepsRefreshContext`/`JobKey`/`changeSentenceCount`, comment `pick` อ้าง spec

**Decided:**
- D78 — ทางเลือกเล็กตอน build ตัวบอกขั้น

**For the next ticket:**
- ticket 08: `reviewLine` ใน `lib/steps.ts` ต้องเพิ่ม `kind: "polish"` และ state `polishing` → "กำลังเรียบเรียง" พร้อมจุดหมุน, `failed` → "เรียบเรียงไม่สำเร็จ" (ตอนนี้ polish ที่ล้มจะขึ้น "ร่างบทไม่สำเร็จ")
- เมื่อ Blocked 14 มีแบบ: ปรับ `SpoilSteps` ให้ตรง Figma ที่ 1440 และ 375 (test มือถือเช็คด้วย class จะต้องตาม)
- test helper: `phased`, `jsonResponse`, `backend` ซ้ำกันใน `RenderResults`, `ScriptReview`, `SpoilerSetup`, `SpoilMakerPage` test — รวมเป็น helper เดียวได้
- `refreshSteps()` ซ้ำใน 4 hook (เริ่ม/ยกเลิก) — ถ้าเพิ่มงานอีก อาจรวมเป็น wrapper ของ `cancelCurrent`/`startJob`
- ไม่ได้เช็คด้วยตา: ตัวบอกขั้นกับงานจริงที่รัน (ไม่มี draft `version` 2 ในเครื่อง)

**Checks:** `uv run pytest` — 517 passed; `npm --prefix frontend test` — 207 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 06: ตัด EP จากคลิปเดียว — done 2026-11-04

**Built:**
- `backend.spoil_maker.episodes`: `GET /clips/{id}/episodes` ตัดตาม `ep_minutes` ที่ขอบ Shot แล้วเขียน `media/temp/episodes/{id}.json` ตอนอ่านแรก; `PUT` `{minutes}` ตัดใหม่ (`custom: false`, จำ `ep_minutes`) หรือ `{minutes, cuts}` ขยับไปเวลาเริ่ม Shot ที่ใกล้สุด (`custom: true`); กฎ ≥ 60 วินาที / EP เดียวสั้นได้, `invalid_episodes`, ไฟล์เสียตัดใหม่; แต่ละ EP มี `thumb_shot`, `lines`, `tokens` (`null` ไม่มี tokenizer), `renders`, `in_draft` เทียบด้วยช่วง ±0.01
- lock: `GpuSlot.clip_files()` ครอบไฟล์การตัดและการสลับ Shot ของ Describe job (ลบไฟล์การตัด); `PUT` ระหว่าง Describe, Transcribe, Draft job ของคลิป → `409` `clip_busy`; ลบคลิปลบไฟล์การตัด; start ลบ `*.tmp` และไฟล์ของคลิปที่ไม่มีหรือไม่ได้บรรยายฉาก; `write_atomic(unique=True)`
- Spoil draft `version` 2 (`clip_id`, `ep`, `GET /draft` มี `clip_title`; `version` 1 = ไม่มี draft); Draft job รับ `{clip_id, ep: {n, start_s, end_s}}` (`invalid_episodes`, `episodes_changed` รวมเช็คซ้ำหลังจอง GPU, `ep_empty`, `transcript_too_long` ต่อ EP); Qwen ได้เฉพาะบรรทัดของ EP เป็น `[{line} {hh:mm:ss}]`, ref นอก EP ถูกตัด, `window` ตัดให้อยู่ใน EP; `PATCH` `shots` นอก EP → `invalid_shot`; `GET /tokens` ลบ
- ผล render `.json` มี `clip_id`, `ep`, `start_s`, `end_s`; `GET /renders` คืน `clip_id`, `ep` (ไฟล์เก่า `null`)
- หน้าเว็บ: ขั้น 1 เลือกคลิปเดียว (`ClipPicker` radio) → `EpisodePicker` (ความยาวต่อ EP 5–60, ยืนยันเมื่อ `custom`, จุดตัด `h:mm:ss` บันทึกเมื่อ blur, "ตัดใหม่ตามความยาว", แถว EP เลข ช่วง ภาพเล็ก token "render แล้ว {k}" ป้าย "อยู่ใน Spoil draft"); `useEpisodes` ส่ง `PUT` ทีละครั้ง, กดร่างรอ `PUT` ค้างแล้วส่งช่วงล่าสุด, `episodes_changed` อ่าน EP ใหม่; EP ไม่มีบรรทัดหรือ `tokens: null` ปุ่มร่างกดไม่ได้พร้อมเหตุผล; มี draft → เลือกคลิปและ EP ของ draft; ตัวเลือก Shot "ดูทั้ง EP" ไม่มีตัวเลือกตอน; การ์ดประโยคและผล render แสดง "EP {n}"
- เช็คใน dev server กับคลิปจริง (14:53): 30 นาที → 1 EP, 5 นาที → 3 EP จุดตัด 4:59 และ 10:02, แก้จุดตัดเป็น 6:00 แล้ว blur → EP 1 0:00–6:00 และปุ่ม "ตัดใหม่ตามความยาว"; 1440 และ 375 ไม่มี scroll แนวนอน ไม่มี console error; ไฟล์การตัดและ `ep_minutes` ที่ลองคืนแล้ว
- Docs: README (ขั้น 1, `media/temp/episodes/`), skill `fastapi-api` (tree: `episodes`, `gpu`)
- Review สามแกนแก้แล้ว: `Ep.matches`/`overlaps` ใช้ร่วม (`Span`, `Episode` สืบจาก `Ep`), `NumberedLine`, `episodes.not_ready`/`invalid`/`is_number`, ชื่อ `clip_files`, ข้อความ `invalid_episodes` ของ Draft job ตาม spec, `ep_minutes` นอกช่วงอ่านเป็น 30, เช็คช่วงซ้ำหลังจอง GPU, ภาพเล็ก EP ไม่ `KeyError`, `tokens: null` แสดงแถวที่ขาดพร้อมลิงก์, comment ของ `READERS`/tmp/`useEpisodes`

**Decided:**
- D77 — ทางเลือกเล็กตอน build ตัด EP

**For the next ticket:**
- เมื่อ Blocked 13 มีแบบ: ปรับหน้าตาขั้น 1 (card เลือก EP) ให้ตรง Figma ที่ 1440 และ 375
- `require_json` ตรวจเฉพาะ POST และ PATCH (ADR-0013) — `PUT /clips/{id}/episodes` ไม่ถูกตรวจ (browser preflight PUT อยู่แล้ว); feature review: เพิ่ม PUT และแก้ข้อความ ADR ถ้าผู้ใช้ตกลง
- `SpoilerSetup.tsx` มี `TOKEN_LIMIT` 32,000 ซ้ำกับ `limit` ของ backend (ใช้แสดงก่อนอ่าน EP เท่านั้น)
- test `clip_busy` ของ `PUT` จอง GPU ด้วย `gpu.slot.take` ตรง (แบบ test `gpu_busy` เดิม) แทนเริ่มงานผ่าน API
- draft `version` 1 ของผู้ใช้ (`media/spoil-maker/draft.json`) อ่านเป็นไม่มี draft แล้ว — ร่างใหม่จาก EP (D70)
- ไม่ได้เช็คด้วยตา: ตัวเลือก Shot และการ์ดประโยคกับ draft จริง (ยังไม่มี draft `version` 2) และ render จริงที่มี "EP {n}"

**Checks:** `uv run pytest` — 517 passed; `npm --prefix frontend test` — 188 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### change request เรียบเรียงบท — 2026-11-04

**Decided:**
- D72–D75: Draft job เรียบเรียงทั้งบทหลังร่างก่อนเลือก Shot, ปุ่ม "เรียบเรียงใหม่" ที่เลือกได้ว่าจะรวมประโยคแก้เองไหม, แก้เฉพาะข้อความ — D74 changed by D75
- D76: ข้อแก้ The Breaker 10 ข้อ (2 BLOCKER: `polish_failed`, จับคู่ด้วย `i`)
- legal: verdict เดิม
- re-cut: ticket 08 (blocked by 06); หน้าตรวจแก้กลับเป็น `pending` (Blocked 15)

### change request ตัด EP จากคลิปเดียว — 2026-11-04

**Decided:**
- D66–D69: สปอยทำจาก Temp clip เดียว ตัดเป็น EP ตามความยาว 5–60 นาที (ตั้งต้น 30) ที่ขอบ Shot เลื่อนจุดตัดได้; ทำทีละ EP; ตัวบอกขั้นบอกสถานะจริง — D5 superseded, D53 changed
- D70–D71: ทางเลือกเล็กและข้อแก้ The Breaker 12 ข้อ (2 BLOCKER: EP อ้างด้วยช่วง `episodes_changed`, lock ของไฟล์การตัด)
- legal: verdict เดิม (ข้อ 1 รับความเสี่ยงแล้วใน D52)
- re-cut: ticket 06–07; จอตั้งค่าคลิปสปอยและตัวบอกขั้นกลับเป็น `pending` (Blocked 13, 14)

### แบบ Figma สวิตช์และคำเตือนลายน้ำ — 2026-11-03

**Built:** (Figma, ไม่มีโค้ด)
- component `Watermark row` เพิ่ม variant `enabled` (true/false): ใช้ `Switch` ของ design system ในกรอบกด 44 px ระหว่างชื่อกับปุ่มลบ; `enabled=false` ชื่อเป็น `text/subtle`; Switch expose ไว้ตั้ง `disabled` ตอนล็อก
- section Script review เพิ่ม 12 frame (desktop, mobile): `Watermark default`, `Watermark off`, `Overlap warning — layout A`, `Overlap warning — layout C`, `Overlap resolved`, `Watermark locked`; คำเตือนใช้ `Alert` tone warning ใต้ช่อง Hook หรือชื่อตอน
- prototype: สวิตช์ลายน้ำ 1 ใน `Overlap warning — layout A` ↔ `Overlap resolved`
- `ui-prompt.md` ลบ; spec › Design ไม่มีจอ `pending`

**Decided:**
- ใช้ `Switch` ที่มีอยู่ใน design system แทนสร้าง component ใหม่; ไม่มี variant focus (โค้ดใช้ focus ring ของ Tailwind)
- frame `3 tab / สปอย 2 ตรวจแก้บท` เดิมมีลายน้ำ 2 อยู่บนกลางกับ Hook ที่ไม่ว่าง — ไม่แก้ frame นั้น, frame ใหม่ย้ายลายน้ำ 2 ไปล่างซ้าย

**Checks:** ข้อความคำเตือนและ aria-label "แสดงลายน้ำ {n}" ใน Figma ตรงกับ `ScriptReview.tsx` และ `ScriptReview.test.tsx`

### Feature review รอบสอง — 2026-11-03

**Built:** (`refactor(spoil-maker): feature review fixes`, `c1520e3`)
- icon refresh ซ้ำ: `features/spoil-maker/assets/refresh-cw.svg` ลบ, `components/ui/assets/refresh-button.svg` → `refresh-cw.svg` ที่เดียว
- `Describes(find_cuts=...)` (`frames.CutFinder`) แบบ `RenderJobs(run_ffmpeg=...)`: test สลับ holder ไม่ patch `spoil_maker.find_cuts`; กฎ `fastapi-api/rules/testing.md` ยกทั้งสองตัวอย่าง
- `GpuSlot.take(..., locks_draft=True)` แทน `draft=True` (comment ของ Render job ย้ายจาก `Kind` มาที่ `take`); งานทุกงานใช้ `paths.project()` แทน `ProjectPaths(paths.ROOT)`; comment window อ้าง D26, D60
- `VideoSettings` อ่าน `useVideoSettings().watermarks` (ทางเดียว); comment ว่าทำไมสวิตช์ส่งข้อความที่กำลังพิมพ์ไปด้วย; `settings._watermarks` ใช้ `mark_fields`
- test: `fakes.poll_until` แทน `wait_for` ที่ซ้ำ 4 ไฟล์; `threading` import ปกติ; ชื่อและ docstring test render ที่ describe EP2 บอกว่า EP2 อยู่นอก draft
- เช็คด้วยตาบน dev server (draft จริงตั้งเป็น layout A + Hook + ลายน้ำบนกลางชั่วคราว): คำเตือนขึ้นใต้ช่อง Hook, ปิดสวิตช์คำเตือนหาย เปิดกลับมา; draft และ settings คืนตรง backup ทุกไบต์
- `docs/features/spoil-maker/ui-prompt.md`: prompt ออกแบบสวิตช์และคำเตือนลายน้ำของ Script review; spec › Design แถวหน้าตรวจแก้ `pending` ส่วนนั้น

**Decided:**
- ไม่แก้: `_clean_shots` อยู่ใน `app.py` (มี comment เหตุ import วน); คำเตือนความยาวเป็น pill ตาม Figma ต่างจาก `Alert`; `compose.Runner` Protocol; `test_app.py` start-up รวม (เป็น seam ของ `JOB_HOLDERS`); โหลดโมเดลไม่มี timeout (spec กำหนดแค่ timeout ต่อครั้งที่เรียก)

**For the next ticket:**
- เมื่อแบบ Figma กลับมา: เทียบหน้าตรวจแก้ที่ 1440 และ 375 แล้วปรับโค้ดถ้าต่าง (Blocked 12)

**Checks:** `uv run pytest` — 483 passed; `npm --prefix frontend test` — 180 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 05: ลายน้ำเปิดปิดได้ และงานค้างจาก feature review — done 2026-11-03

**Built:**
- ลายน้ำมี `enabled`: `PATCH /settings` รับ boolean (ไม่ใช่ boolean → `400` `invalid_settings`, ไม่มี = เปิด), `settings.json` เดิมอ่านเป็นเปิด, ที่ปิดยังนับในสูงสุด 6; `captions.ass_file` วาดเฉพาะที่เปิด
- หน้าตรวจแก้: สวิตช์ "แสดงลายน้ำ {n}" ในแถวลายน้ำ (ปิดแล้วชื่อเป็นสี muted) และ `Alert` warning ใต้ช่อง Hook/ชื่อตอน "ลายน้ำ {n} อยู่บนกลาง จะทับ … ในวิดีโอ" ตามข้อความที่กำลังพิมพ์; render ยังกดได้ (`markNumbersOverTopText`, `useVideoSettings().watermarks`)
- Blocked 8: `RenderJobs(run_ffmpeg=...)` (`compose.Runner`); `paused_ffmpeg` สร้าง holder ใหม่ ไม่ patch `compose.run`; test ใหม่ render ที่ทุกประโยคมีเสียงเข้า `rendering` ตรง และ `POST /describes` คลิปอื่น `202`; test ไฟล์ ASS ของ render จริงตอน runner หยุดรอ
- Blocked 9: spec › Describe job เรียงตาม D60; test คลิปใน draft ที่ Qwen ไม่ติดตั้ง → `503` `not_ready`
- Blocked 10: 6 icon ย้ายไป `components/ui/assets/` (`copy`, `trash`, `x`, `circle-alert`, `file-text-24`, `play`), ลบสำเนาใน `spoil/assets/`; `app.JOB_HOLDERS` (`JobEntry(current, clean_on_start)`) ขับทั้งล้างตอน start และ `stop_on_shutdown`; test รวม start-up ลบของค้างของ render, Shot และ voice
- เช็คหน้าตาที่ 1440 และ 375 ใน dev server กับ draft จริง (layout B): สวิตช์เปิด/ปิด, reload แล้วค่าคงอยู่; คำเตือนเช็คผ่าน test เท่านั้น (draft จริงเป็น B) — ลบลายน้ำทดสอบออก settings กลับเหมือนเดิม
- Docs: spec (Describe job, ค่าที่จำไว้, API, Design, Seams 1–2), `vite-react-web` SKILL (`components/ui/assets/`)
- Review สามแกนแก้แล้ว: `JobEntry.current` แทน `JobHolder.holder`, ชื่อพารามิเตอร์ `run_ffmpeg`, ค่าตั้งต้น `enabled` ที่เดียว (model), ชื่อตัวแปร icon ตามไฟล์ใหม่, helper ไม่รู้ layout, hook ส่ง `watermarks`, test ASS ผ่าน render แทน `captions` ตรง

**Decided:**
- D65 — ทางเลือกเล็กตอน build ลายน้ำเปิดปิดและงานค้างจาก review

**For the next ticket:**
- Figma Script review ยังไม่มีสวิตช์และคำเตือนลายน้ำ — วาดเพิ่มใน Figma ถ้าอยากให้แบบตรงโค้ด (D65)
- คำเตือนลายน้ำทับยังไม่เคยเห็นบนจอจริง (draft จริงเป็น layout B): เช็คด้วยตาตอน feature review
- `_clean_shots` อยู่ใน `app.py` เพราะ `spoil.clips` import `shots` (วนกลับไม่ได้) — ย้ายได้ถ้าแยก import นั้นออก

**Checks:** `uv run pytest` — 483 passed; `npm --prefix frontend test` — 180 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### Feature review — 2026-11-03

**Built:** (`refactor(spoil-maker): feature review fixes`, `12becfe`)
- `audio.wav` ของประโยคส่ง `Cache-Control: no-store` (`?v={duration_s}` ซ้ำเมื่อเสียงใหม่ยาวเท่าเดิม)
- `thai.spoken`: `10:30 น.` และ `10.30 น.` → `สิบนาฬิกาสามสิบนาที` (ตัด `น.`)
- พื้นเบลอ layout A ย่อ 270×480 → `gblur` 7.5 → ขยาย: filter 3.07 → 0.46 วินาทีต่อ 10 วินาที, SSIM 0.991
- 404/405/422 ของ framework ตอบ `{code, message}` (422 → `400` `invalid_request`)
- `ModelJobSlot._run_job` รวมท้าย `_run` และ `_failed` ของ 5 งาน; `backend.gate_rows`; `paths.project()`; หน้าเว็บ `RefusalLine`/`refusalLine` แทนสาม type, `SentenceCard` ใช้ `playAudio`
- ชื่อ: `made_from_clip` / `job_reads_clip`, `script.spoken_letters`, `drawn` ใน render; comment ของ `clip_id: None`, `_shots_for`, test `"9-999"`
- Docs: ADR-0013 รวม PATCH; spec (ตัวเลขเป็นคำ, layout A, API, Frontend, ชื่อเก่า `useHashTab` `SpoilError` `SpoilPage.test`); ticket 01 และ D56 ใช้ "บรรยายฉาก"; skills `fastapi-api`, `vite-react-web`

**Decided:**
- D63 — แก้จาก feature review (ข้อ `น.` ผู้ใช้เลือก)

**For the next ticket:**
- ทุกข้อที่ไม่ได้แก้อยู่ใน Blocked 8–11

**Checks:** `uv run pytest` — 474 passed; `npm --prefix frontend test` — 174 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 04: เสียงต่อประโยคและ render — done 2026-11-03

**Built:**
- ติดตั้ง Kanit: `backend.fonts` (commit `130fcfb`, sha256 ทั้งสองไฟล์) — setup โหลด `Kanit-Bold.ttf` กับ `OFL.txt` ลง `models/fonts/kanit/` หลังโมเดล, sha256 ไม่ตรงลบไฟล์และล้ม, marker `models/.setup/font_kanit` เขียนท้ายสุด; แถว Status check `font_kanit` "Kanit font" ต่อจาก `pythainlp` (15 แถว)
- Voice job `sentences`: `voices.SentenceVoicer` (ฐานร่วมของ Voice job และ Render job) แปลงตัวเลขก่อนส่ง OmniVoice (`tts.Speak` พร้อม clone prompt และ speed ของ Saved voice, `num_step` 16), เขียน `draft-audio/{id}.wav` และ `audio` ของประโยคทันทีทีละประโยค; จองช่อง GPU `voice` พร้อมคลิปของ draft (`clip_busy`) และล็อก draft (`draft_locked`, `locked: true`); `GET /draft/sentences/{sid}/audio.wav`
- `PATCH /settings`: ลายน้ำสูงสุด 6 อัน (`text` 1–40 ตัวอักษรที่กินที่, `position` 6 จุด, `size` small/medium) และ `original_volume`; ค่าไม่ตรง `400` `invalid_settings`
- Render job (`spoil_maker.render`, `compose`, `captions`, `ffmpeg`): `no_draft` → `missing_shots` → `disk_full` → `not_ready` → `busy` → `gpu_busy`; ประโยคขาดเสียง → `voicing` (จอง GPU `render`) แล้วคืนช่องก่อน `rendering`; ชิ้นต่อ Shot `.render/{i}.mkv` 1080×1920 30 fps ตาม layout A/B/C (A: พื้นเบลอ `gblur` 30 + ภาพ 1080×1350 ที่ y 285; B/C: 1080×608 ที่ y 656/420), Shot เลยท้ายค้างเฟรมสุดท้าย, เสียงต้นฉบับ × `original_volume`; ต่อด้วย concat, ผสมเสียงบรรยาย `amix normalize=0`, วาด ASS ด้วย libass + Kanit, `libx264 crf 20 yuv420p` + `aac 192k 48 kHz` + `faststart`; เขียน `renders/{YYYYMMDD-HHMMSS}.mp4/.srt/.json` ผ่าน `.partial` (json ท้ายสุด); ยกเลิกฆ่า ffmpeg ลบ `.partial` และ `.render/`; start ล้างทั้งสอง
- ASS: hook (A) / ชื่อตอน (C) ตัดบรรทัดที่ขอบคำ `newmm` 18/20 ตัวอักษรที่กินที่, ซับ A ท่อนไม่เกิน 4 คำ 15 ตัวอักษร เวลาแบ่งตามสัดส่วน, ซับ B ไม่เกิน 2 บรรทัด 28 ตัวอักษร, ลายน้ำขาวขอบดำ 3 px ทึบ 80% ที่ 6 มุม, escape `\ { }` และขึ้นบรรทัดใหม่; `.srt` ข้อความตามที่เขียน (ตัวเลขคงเดิม)
- `GET /renders` (ใหม่สุดก่อน, `sources` ชื่อคลิปตามลำดับ EP), `GET /renders/{name}.mp4` (`Range` → `206`), `.srt` (`Content-Disposition`), `DELETE /renders/{name}`; ผล render อยู่แม้ลบคลิป
- โค้ดใช้ร่วม: `backend.clock.srt` (Transcript และ render), `thai.width`/`cut_width` ย้ายจาก `script`, `thai.words` เก็บช่องว่างท้ายคำ, `spoil_maker.ffmpeg` (`frames` ใช้ด้วย); library note `ffmpeg.md`
- หน้าเว็บ ตรวจแก้บท: การ์ดประโยคมี **ฟัง** และ **สร้างเสียงใหม่**; `VideoSettings` (เสียงคลิปต้นฉบับ slider บันทึกเอง, ลายน้ำ เพิ่ม ลบ ข้อความ ตำแหน่ง 6 จุด ขนาด); `ReviewFooter` sticky (สร้างเสียงทั้งหมด / render, "สร้างเสียง x/y", "render %", ยกเลิก, render กดไม่ได้เมื่อมีประโยคไม่มี Shot, รอ AI เลือก Shot); `ReviewBanner` (render ไม่สำเร็จ / งานหยุดกลางทาง พร้อมลองอีกครั้ง, ที่ว่างดิสก์), `not_ready` มีลิงก์ไปหน้าติดตั้ง; render เสร็จเปิด `#/spoil/renders`
- หน้าเว็บ ผล render (ขั้น 3): progress พร้อมยกเลิก, รายการใหม่สุดก่อน (ภาพเล็กจาก mp4, เวลา, ความยาว, "ต้นฉบับ: {ชื่อคลิป}" พร้อม copy, โหลด mp4 / `.srt`, ลบพร้อมยืนยัน), จอ ≥ 1024 เล่นใน panel 324×576 ข้างรายการ, มือถือเล่นใต้แถว; ว่าง "ยังไม่มีผล render"
- README: ขั้น 2–3, ที่เก็บไฟล์ `media/temp/shots/` และ `media/spoil-maker/`, font Kanit; skills `fastapi-api` (tree, rules/setup), `vite-react-web` (`lib/render.ts`, `lg:` ของหน้าสองคอลัมน์)
- หน้าเว็บเทียบ Figma (DOM, pane ถูกซ่อน): 1440 ตรวจแก้ — บท 744, ตั้งค่าวิดีโอ 360, footer 1120×78; ผล render — รายการ 746, panel 358, player 324×576; 375 — การ์ดประโยค 343 ปุ่ม 2 แถว (382 จาก 396), แถว render 341 (เล่นอยู่ 743 จาก 744, ปกติ 182 จาก 176), ไม่มี scroll แนวนอน
- เช็คมือบน M2 (Seam 3), draft จริงของหนัง 96 นาที 20 ประโยค เสียงหญิง young adult `v_be1485d1`:
  - render ผ่านหน้าเว็บทั้งงาน **178 วินาที**: `voicing` 20 ประโยค ~140 วินาที (~7 วินาที/ประโยค) + `rendering` ~38 วินาที; mp4 ยาว 75.47 วินาที เทียบผลรวมเสียง 75.45 (ต่าง 0.02); 1080×1920, aac 48 kHz; 17.6 MB
  - render ซ้ำเมื่อเสียงครบ (Open Question 1, คลิป ~75 วินาที): layout A **79 วินาที** (พื้นเบลอเต็มจอแพง), B ~38 วินาที, C **33 วินาที**
  - ภาพจากทั้ง 3 layout: สระบนล่างและวรรณยุกต์ Kanit ไม่ซ้อนผิด, ภาพตรงตาราง layout (4:3 ใน B/C เติมดำตามสัดส่วน), ลายน้ำ 6 อันอยู่ถูกมุม, ชื่อตอน C เหลืองขอบแดง
  - เสียงประโยค "ปี 1968 เวลา 10:30 น. ผีดิบกว่า 50% บุกเข้ามา" ให้ Whisper ฟัง → "ปี 1968 เวลา 10.30 นาที … ผีดิบกว่า 50% บุกเข้ามา" (ตัวเลขอ่านถูก)
  - draft ของผู้ใช้คืนเป็นเหมือนก่อนเช็ค (layout B, 19 ประโยค) แต่ทุกประโยคมีเสียงแล้ว; ผล render ทดสอบ 3 ไฟล์อยู่ใน `media/spoil-maker/renders/`
  - **ไม่ได้เช็ค:** 5 ประโยคฟังเป็นเสียงเดียวกัน และเสียงต้นฉบับ 20% "ได้ยินแต่ไม่กลบ" — ต้องฟังด้วยหู; เปิด mp4 บน iPhone และอัปโหลด YouTube Shorts แบบ private — ต้องใช้เครื่องและบัญชีของผู้ใช้

**Decided:**
- D62 — ทางเลือกเล็ก: `backend.fonts` และ marker, ลำดับการเช็คของ Voice job `sentences` และ Render job, `SentenceVoicer`, ไฟล์กลาง mkv และจุดตัดตามเฟรม 30 fps, `spoil_maker.ffmpeg`, style ของ ASS, ซับ A คำเดียวได้เมื่อคำถัดไปเกิน 15 ตัวอักษร, render เสร็จเปิดผล render, ภาพเล็กจาก mp4, player panel ≥ 1024, ไม่ทำ banner "แอปปิดไประหว่าง…" (งานหายเมื่อ restart)

**For the next ticket:**
- feature review: ลายน้ำ `top_center` (y 60) ทับ hook ของ layout A (y 70) และชิดชื่อตอน C — spec วางทั้งคู่ที่ขอบบน; ผู้ใช้ควรตัดสิน (ย้าย hook ลง หรือเตือนเมื่อเลือกบนกลาง)
- feature review: `น.` หลังเวลา (`10:30 น.`) OmniVoice อ่าน "น" — spec › ตัวเลขเป็นคำ ไม่ได้ระบุ; อาจเพิ่ม `น.` → นาฬิกา/ตัดทิ้ง
- feature review: layout A render ช้ากว่า B/C ~2 เท่า เพราะ `gblur` sigma 30 ที่ 1080×1920 ทุกเฟรม — ย่อ-เบลอ-ขยายจะเร็วขึ้นโดยภาพเหมือนเดิม
- review ที่ไม่ได้แก้: `_run` ของ Voice job กับ Render job (และงานลูกเดิม) รูปเดียวกัน (ending/try/except/finally, `_failed`) — ย้ายเข้า `ModelJobSlot` ได้; `compose.run` ซ้ำการตั้ง Popen + kill กับ `frames.find_cuts`; `JobsState`/`RendersState` เก็บ banner และ refusal แยกฟิลด์แทน union; test ของไฟล์ ASS เรียก `captions.ass_file` ตรง (ไฟล์ ASS ไม่เหลือหลัง render) และ `paused_ffmpeg` แทน `compose.run`
- `?v={duration_s}` ของ audio.wav (spec › Frontend): สองครั้งที่ยาวเท่ากันได้ URL เดียวกัน — browser อาจเล่นเสียงเก่า

**Checks:** `uv run pytest` — 467 passed; `npm --prefix frontend test` — 174 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

### 03: ร่างบทและหน้าตรวจแก้ — done 2026-11-03

**Built:**
- Draft job (`backend.spoil_maker.draft`): `POST/GET/DELETE /api/spoil-maker/draft-jobs[/current]` `kind` `draft` (เช็ค `clip_not_ready` → `invalid_request` → `invalid_target` → `voice_not_found` → `transcript_too_long` → `busy` → `draft_exists` → `not_ready` → `gpu_busy`) และ `pick` (ประโยคเดียว, `no_refs`); `writing` สูงสุด 3 ครั้ง (timeout 10 นาที, ครั้งที่ 2–3 บอกว่าครั้งก่อนพลาดตรงไหน) → `matching` ประโยคละ 2 Shot จากช่วง ±30 วินาทีของ ref แรก (ส่งให้ Qwen ไม่เกิน 40 Shot, timeout 60 วินาที) → เขียน draft ใหม่ ลบเสียงเดิม จำ `last_voice_id`
- `spoil_maker.script` (คำสั่งร่างบทและเลือก Shot, อ่าน JSON, ทำความสะอาด, ref ประโยคละ 3), `draft_file` (Spoil draft `media/spoil-maker/draft.json` เขียนแบบ atomic, `drop_if_uses`, `take_gpu_to_redo`), `settings` (`original_volume` 20, `last_voice_id`), `tokens` (นับ token ด้วย tokenizer ของ Qwen จาก snapshot, `GET /tokens`), `backend.clock`
- แก้ draft: `GET/PATCH /draft`, `POST /draft/sentences` (แทรกใต้), `PATCH/DELETE /draft/sentences/{id}`; สถานะประโยค `no_shot` / `no_audio` / `stale_audio` / `ready`, `estimated_s`, `window`, บรรทัดที่อ้าง; ระหว่างงานแก้ draft → `409` `draft_locked`
- คลิปใน Spoil draft (D49): `in_draft` ในรายการคลิป, ถอดใหม่ / บรรยายฉากใหม่ / ลบคลิป → `409` `in_draft` จนส่ง `confirm_draft_loss` แล้วลบ draft; ลบ Saved voice ที่ draft ใช้ → `409` `voice_in_use`; แก้บรรทัด Transcript ที่ Draft job อ่านอยู่ไม่ได้
- refactor: `jobs.ModelJobSlot` รวมท้ายงานลูก 4 งาน (Transcribe, Describe, Voice, Draft) และ `_reply`; `gpu.slot.draft_lock`; `files.remove_unfinished`
- หน้าเว็บ: หน้าตั้งค่า (`SpoilerSetup`, `ClipPicker` เรียง EP, `SetupSettings` สไตล์ layout ความยาว เสียง token รวม), หน้าตรวจแก้ (`ScriptReview`, `SentenceCard` ข้อความบันทึกเองหลังพิมพ์ 800 ms หรือ blur, แทรก ลบพร้อมยืนยัน AI เลือก Shot ใหม่พร้อมยกเลิก), `ShotPicker` (Shot ในช่วง, ดูทั้งคลิปเลือก EP, tooltip คำบรรยาย, เล่นช่วงนั้น); `DraftWarning` ในแถวคลิปและกล่องถอด; ของใช้ร่วม `components/ui/Alert`, `lib/clips`, `lib/format`, `DESTRUCTIVE_BUTTON`
- หน้าเว็บเทียบ Figma Spoiler setup, Script review, Shot picker, Clip row states ที่ 1440 และ 375
- เช็คมือบน M2 (Seam 3), หนัง 96 นาที (Night of the Living Dead, 840 Shot, prompt 30.9k token):
  - tokenizer จาก snapshot โหลดได้โดยไม่โหลดโมเดล
  - ร่างบท 60 วินาที `drama` ทั้งงานผ่าน API ด้วยค่าสุดท้าย: **7:57** (`writing` ผ่านครั้งแรกใน 5:50, 1021 ตัวอักษร จากเป้า 918 = +11%, 19 ประโยค, Shot ครบ), memory process ลูกสูงสุด ~11 GB (รอบก่อนหน้า)
  - temperature ร่างบท 0.3 ครั้งแรกผ่าน 5 จาก 6 ครั้ง (D61)
  - Shot ตรงเนื้อหา 6 จาก 10 ประโยคที่สุ่ม
  - ยกเลิกระหว่าง `writing` → process ลูกหายใน 0.3 วินาที, `cancelled`, draft เดิมอยู่ครบ
  - แก้ประโยคแล้ว restart backend → draft เหมือนเดิมทุกตัวอักษร
  - **ไม่ได้เช็ค:** 3 EP อนิเมะใต้ 32,000 token — ไม่มีคลิปอนิเมะในเครื่อง; memory ของหนังทั้งเรื่อง (30.9k token) สูงสุด ~11 GB ใต้ 13 GB

**Decided:**
- D60 — ทางเลือกเล็ก: module (`draft_file` / `draft` / `script` / `tokens` / `settings`), lock และ `take(draft=True)`, `ModelJobSlot`, ลำดับการเช็ค, กติกาเลือก Shot ใกล้ ref แรก, แก้ draft, ของใช้ร่วมหน้าเว็บ, หน้าตั้งค่า หน้าตรวจแก้ และคำเตือนใน tab คลิป
- D61 — จากรันจริง: เลือก Shot ส่งให้ Qwen ไม่เกิน 40 Shot (160 Shot = 66.6 วินาที เกิน timeout); บทเก็บ ref ประโยคละ 3 และกฎซ้ำหลัง Transcript (ref เป็นแถว 20–60 id ทำ JSON ถูกตัด); ตัวอักษรต่อประโยคไม่เกิน 1.2 × เฉลี่ย; JSON ขาด `}` ท้ายอ่านได้; temperature ร่างบท 0.7 → 0.3 (spec › ค่าการสร้างข้อความ และข้อ 4–5 แก้แล้ว)

**For the next ticket:**
- 04: `PATCH /settings` และลายน้ำ (D60); Voice job `sentences` แทน `400` ชั่วคราว (จาก 02); ตั้งค่าวิดีโอ ฟัง สร้างเสียง และแถบ render ของหน้าตรวจแก้ (คอลัมน์ขวา); seam 3 ของ 02 ("5 ประโยคเสียงเดียวกัน", "1968, 10:30 อ่านถูก")
- คุณภาพบท: เนื้อเรื่องที่ Qwen เล่ามีส่วนไม่ตรงหนัง (เช่น "ทิ้งแม่ไว้บ้าน") และ Shot ตรง 6/10 เฉียดเกณฑ์ — ประโยคที่อ้างบรรทัดผิดได้ Shot ผิดตาม; ดูอีกครั้งตอน render จริง
- ครั้งที่ 2–3 ที่บอก "ยาวไป" ไม่ได้ทำให้สั้นลงที่ temperature 0.7; ที่ 0.3 ยังไม่ได้วัดผลของข้อความนี้แยก
- ครั้งที่วน (เล่าซ้ำจน `max_tokens`) ยังเกิดได้ราว 1 ใน 6 ที่ 0.3 — นับเป็นไม่ผ่านแล้วสั่งใหม่ เสีย ~7.5 นาที
- 3 EP อนิเมะ: เช็คเมื่อมีคลิป

**Checks:** `uv run pytest` — 400 passed; `npm --prefix frontend test` — 157 passed; `npm --prefix frontend run typecheck` — pass; `npm --prefix frontend run build` — pass

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
| 8 | review | test ของ render ผูกกับ internals: `paused_ffmpeg` patch `compose.run`; test "render ระหว่าง `rendering` → `POST /describes` 202" ผ่าน `voicing` ก่อน ไม่ตรงที่ spec เขียน | `/warroom tickets spoil-maker` | done (ticket 05) |
| 9 | review | ลำดับเช็คของ Describe job: โค้ดเช็ค gate ก่อน `in_draft` (D60) แต่ spec › Describe job ข้อ 1 วาง `in_draft` ก่อน — แก้ spec หรือโค้ดให้ตรงกัน | `/warroom tickets spoil-maker` | done (ticket 05) |
| 10 | review | SVG 6 ไฟล์ซ้ำกันใน `spoil/assets/` และ `spoil-maker/assets/`; งานใหม่ทุกงานต้องแก้สองรายการใน lifespan ของ `app.py` | `/warroom tickets spoil-maker` | done (ticket 05) |
| 11 | review | ลายน้ำ `top_center` ทับ hook ของ layout A (D41 ยอมให้ทับ) — เตือนในหน้าเว็บหรือย้าย hook ลง | `/warroom tickets spoil-maker` | done (ticket 05) |
| 12 | review | design: สวิตช์ลายน้ำและคำเตือนลายน้ำทับใน Figma Script review (D64, D65) | `/warroom spoil-maker` พร้อมลิงก์แบบ | done ([Figma](https://www.figma.com/design/pmdBVIP9xggk1wHCjdlKDZ/framecraft?node-id=8044-7390)) |
| 13 | 06 | design: ตั้งค่าคลิปสปอย — เลือกคลิปเดียว รายการ EP เลื่อนจุดตัด (D66, D67, D69) จาก `ui-prompt.md` | `/warroom spoil-maker` พร้อมลิงก์แบบ | open |
| 14 | 07 | design: ตัวบอกขั้นของ tab สปอย — บรรทัดสถานะและจุดหมุน (D68) จาก `ui-prompt.md` | `/warroom spoil-maker` พร้อมลิงก์แบบ | open |
| 15 | 08 | design: หน้าตรวจแก้ — ปุ่มเรียบเรียงใหม่ กล่องเลือก ป้ายแก้เอง (D72, D74, D75) จาก `ui-prompt.md` | `/warroom spoil-maker` พร้อมลิงก์แบบ | open |
