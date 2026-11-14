# Progress: video-gen

**Now:** ready to merge — feature review เสร็จ (`43ed0a9`) CI เขียว; Blocked 1–3 ปิดด้วย D38 (หน้าตาเดิมของแอป, แบบ Figma ทำทีหลังจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md)); เจ้าของยังเช็คเอง: render คลิปจริงเทียบคลิปอ้างอิง, ฟัง sample จริง, ภาพพื้นหลังจริง

**Next:**

```
/pr-open
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้งเสียงกลอง บทเรียน และฟังจังหวะ | done |
| 02 | render คลิปสอนกลอง | done |
| 03 | ภาพพื้นหลังของผู้ใช้ | done |

## Log

### Feature review — 2026-11-14

**Built:** `refactor(video-gen): feature review fixes` (`43ed0a9`), review สามแกนจาก merge-base `e85a1f4`
- ทางเดียวต่อเรื่อง: `renderingOf` (บทเรียนนี้ render อยู่ไหม — เดิมสามแบบใน LessonList/LessonEditor/RendersPage), `lessons.require_short` (`too_long` เดิมสองที่), `lessons.LESSON_FILE`/`BACKGROUND` (render ประกาศซ้ำ), `gate_rows._kanit`, `lessons.lesson_dir` แทน wrapper + `_folder`
- listen เช็คตามลำดับของ render: gate ก่อน แล้วค่อยบทเรียน (เดิม id ผิดรูปได้ 404 ก่อน 503)
- `inputClass` ย้ายไป `components/ui/inputStyles.ts` ใช้ร่วมกับ story-kb (กติกา "Where shared code goes")
- `lib/lesson.test.ts` และ `lib/render.test.ts` ตามกติกา testing ("lib/ helper ที่หลาย hook ใช้มี test ของตัวเอง") — ticket 01 เคยลบ `lesson.test.ts` ว่านอก seam; กติกาของ repo ชนะ
- test แยกไฟล์ตามโมดูล: `test_video_gen_mixer.py`, `test_video_gen_captions.py`; test เท้าเหยียบไฮแฮทตัดเสียงเปิด (AC ticket 01 ที่ขาด); ลบ test `JOB_HOLDERS` (แค่การต่อสาย; test restart ครอบแล้ว)
- ชื่อ: `played` → `timing` (Timeline), `Segment.chapter_index`, `Scene.shown_hits`/`shown_times`, `frames.frame_count` (captions เคยคำนวณซ้ำ), `backgrounds.partial_file` (test ใช้ด้วย); docstring `_tip_before` อธิบาย recursion, `cancel_render` body, `mixing` รวมขั้นบันทึก, ที่อยู่ jpg ของ `_take_upload`
- `legal.md` ข้อ 4 ตาม D23 (`ลองเล่นเอง`)

**Decided:** ไม่แก้ — `render._run` ซ้ำโครง `ModelJobSlot._run_job` (และ `toon/sounds._run`): ยกขึ้น `JobSlot` แตะสาม feature และรูป error ของ job ไม่เหมือนกัน (spec ขอ `error` แบบแบน) — ทิ้งไว้เป็นงาน refactor ข้าม feature ถ้าเจ้าของต้องการ; flag `too_large_status` (spec ขอ 413); ป้าย "(e2e)" ใน Vitest (กติกา testing: e2e = Vitest ผ่าน `App`); `lesson_jobs` เติมตอน import `render` (คอมเมนต์บอกแล้ว); `isRendering` ไม่ใช้ `isUnfinishedIn` (รับ null และเป็น type guard); `size_bytes` ใน `RenderResult` (มากับ `renders.listed` ที่ใช้ร่วม); `NOTICE.md` ไม่มี Big Rusty Drums (CC0 ไม่ต้องให้เครดิต, ADR-0039)

**For the next ticket:**
- เจ้าของ: render Smells Like Teen Spirit intro fill เทียบคลิปอ้างอิง, ฟัง `chik` และทอม (D30), render บทเรียนที่มีภาพจริงดูความอ่านง่าย
- แบบ Figma สามหน้า (Blocked 1–3) แล้วปรับหน้าเว็บตามแบบ

**Checks:** `uv run pytest` 1243 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 497 passed; build ผ่าน. Standards 2 ผิดกติกา (lib ไม่มี test, `inputClass` ซ้ำ) + smell 2 — แก้ทั้งสอง; Spec 0 ผิด + 3 ขาด + 1 เกิน + 1 test + 5 ทำสองแบบ — แก้ทั้งหมดยกเว้น `size_bytes`, `NOTICE.md`; Newcomer สรุปตรง spec › Solution + เดา 13 จุด — แก้ 10, ไม่แก้ 3 (`lesson_jobs`, "(e2e)", อ่านบทเรียนหลายทาง: `get` view / `stored` / `read_under_lock` มี docstring บอกต่างกันแล้ว)

### 03: ภาพพื้นหลังของผู้ใช้ — done 2026-11-13

**Built:**
- `video_gen.backgrounds`: `POST /lessons/{id}/background/check` แล้ว `PUT /lessons/{id}/background?size=` body ดิบ (ADR-0028, `uploads.receive`) → `exif_transpose` ครอป 1080×1920 jpg; `DELETE` กลับเป็นสี; `GET background.jpg`; ทุกทางเช็ค `lesson_busy`
- `lessons.set_background` / `background_file` ใต้ lock เดียว; upload ค้างเป็น `.tmp` ใน `media/drums/.partial/` ที่ start-up ลบ
- หน้าแก้: ส่วน "พื้นหลัง" กรอบ 9:16 (ภาพ หรือ "สีของแอป"), ปุ่มเลือกภาพ/ลบภาพ, ข้อความ D23 ข้างปุ่ม, error `413`/`415` ข้างปุ่ม; ฟอร์มที่ยังไม่บันทึกอยู่ต่อเมื่อได้ภาพ
- `sendFile` รับ `method` (`PUT`)
- แก้ test สุ่มล้ม `test_the_list_puts_the_latest_change_first`: `updated_at` ละเอียดแค่วินาที สองการเขียนในวินาทีเดียวเรียงตาม id สุ่ม → นาฬิกาปลอมใน test (น่าจะเป็น test ที่ล้มสุ่มใน Log ของ 02)

**Decided:** D36 ส่งภาพแบบ ADR-0028 (check ก่อน; auto mode เลือก Recommended), D37 ทางเลือกเล็กของภาพพื้นหลัง; ADR-0028 รายการ route เพิ่ม `PUT /api/drums/lessons/{id}/background`

**For the next ticket:**
- ticket หมดแล้ว: ต่อด้วย feature review (`--review-feature`)
- เจ้าของ: render บทเรียนที่มีภาพจริงหนึ่งครั้งแล้วดูว่าเบลอ/มืดอ่านง่ายไหม; หน้าตาส่วนพื้นหลังรอแบบ Figma (Blocked แถว 2)
- smell ที่ค้าง: `uploads.require_size(too_large_status=)` เป็น flag เพื่อ `413` ของ spec (toon ใช้ `400`); test 413 ฝั่งหน้าเว็บมีแค่จาก `check` (`PUT` ใช้ทางเดียวกัน); test start-up ล้าง `.partial` สร้างชื่อ `.tmp` เอง
- smell จาก 02 ยังค้าง: `render._run` ซ้ำโครง `ModelJobSlot._run_job`

**Checks:** `uv run pytest` 1243 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 486 passed; build ผ่าน. Review สามแกนจาก `254bed3`: Standards 2 ข้อผิดกติกา + smell 8 (แก้: สี hex ในกรอบสีของแอป → token `drum-clip-top/bottom`, state ของภาพเป็น union, `Reply` แทน status 0, `TOO_LARGE` จาก `MAX_BYTES`, `lessons.require_known_idle` แทนการจับ lock ข้าม module, test ใช้ `drums_partial_dir`/`lessons.BACKGROUND`, `fakes.png(color=)`, fixture ที่ไม่ใช้, SKILL อ้าง D6; ไม่แก้: flag `too_large_status` (spec ขอ 413), ข้อความ 20 MB ซ้ำ toon (คนละ feature)), Spec 0 ผิด + 1 ขาด + test 3 (แก้: spec › Seams 3, test เบลอจริงด้วยภาพแดงครึ่งน้ำเงินครึ่ง ค่า 115 ตรงๆ; ไม่แก้: test เปลี่ยนไฟล์บนดิสก์ระหว่าง render (API ตอบ 409 จึงไม่มีทางอื่นถึง AC), ชื่อ `.tmp` ใน test start-up, 413 ของ `PUT` ฝั่งหน้าเว็บ), Newcomer สรุปตรง What to build + เดา 9 จุด (แก้: `took` → `applyBackground`, docstring "beside the lesson", ที่มาของการล้าง `.partial`, `TOO_LARGE_STATUS`, คอมเมนต์ test นาฬิกาปลอม ค่าสีมุม body 1 byte, `noop` ของ `sendFile`, error ที่คงไว้ใน `applyBackground`)

### 02: render คลิปสอนกลอง — done 2026-11-13

**Built:**
- `ffmpeg.h264_args` (spoil trim ใช้ด้วย) และ `ffmpeg.run_piped` ส่งเฟรมทาง stdin เช็คยกเลิกทุกเฟรม
- `video_gen.frames` (`Scene`, `frame_at`): พื้นหลัง ชุดกลองตาม kit-sketch วาดด้วย Pillow ต่อชุดชิ้นที่เน้น เลน playhead; ทุกเฟรมวาดไม้ วงแหวน หัวโน้ต เส้นจังหวะ เท้า วง L/R เป็นชิ้นเล็ก 2 เท่า; `video_gen.lane` ตำแหน่งเลนที่เดียว; `timeline.Hit.note` บอกชนิดโน้ตบนจอ
- `video_gen.captions`: ASS หัวเรื่อง/ป้าย (ย่อ `\fscx` เกิน 860 px) บรรทัดรอง ตัวนับ คำบรรยาย L/R RF/LF เลขจังหวะเลื่อนตามเลน; `.srt` ต่อช่วง
- `video_gen.render`: Render job slot ของตัวเอง `POST/GET /render`, `/render/cancel`, ผล render list/mp4/srt/delete; `lesson_busy` ของลบบทเรียน; start ล้าง `.render/` และ `.partial`; `gate_rows.drums`
- หน้าเว็บ: ปุ่ม render ในหน้าแก้ (บันทึกก่อน แถบ % ยกเลิก ลองอีกครั้ง บอกบทเรียนที่ render อยู่) ป้าย % ในรายการ หน้า `#/drums/{id}/renders` (player 9:16 โหลด mp4/.srt ลบพร้อมยืนยัน)

**Decided:** D31 ภาพที่ขยับ, D32 ตัวหนังสือ, D33 copy บทเรียนก่อนตอบ 202, D34 Render job (`title`, cancel 200, `-b:v 8M`), D35 หน้า render ก่อนมีแบบ

**For the next ticket:**
- `render._copy_in` copy `background.jpg` อยู่แล้ว และ `frames._background` เบลอ 24 ทับดำ 55% แล้ว; ticket 03 ทำ route ภาพ + เช็ค `lessons.require_idle` (`lesson_busy`) ใน `PUT`/`DELETE /background`
- `background` = `image` แต่ไม่มีไฟล์ → render ใช้พื้นสี (D34)
- เจ้าของ: render Smells Like Teen Spirit intro fill ในแอปแล้วเทียบคลิปอ้างอิง (AC สุดท้ายของ 02; ยังไม่ได้ทำ) และฟังเสียงจริง (D30) — เครื่องนี้ยังไม่มี sample จริงใน `models/drums/`
- หน้าตาตาม Figma รอ Blocked แถว 3
- ticket 03 test ทาง render ของพื้นภาพ (เบลอ 24 ทับดำ 55%) ที่ `frames._background` มีแล้ว
- smell ที่ค้าง: `render._run` ซ้ำโครง `ModelJobSlot._run_job`; ยก `_run_job` ขึ้น `JobSlot` ได้ใน refactor ภายหลัง
- test ล้มหนึ่งครั้งแบบสุ่มในชุด backend (ผ่านเมื่อรันซ้ำ) — สงสัย test render ที่หยุดกลางเฟรม

**Checks:** `uv run pytest` 1226 passed (สองรอบติด; ก่อนนั้นหนึ่งรอบมี 1 test ล้มแล้ว `--lf` ผ่าน ชื่อหาย — ถ้าเจออีกให้ `/kiki-debug`); `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 482 passed; build ผ่าน. Review สามแกนจาก `fcf313a`: Standards 4 ข้อผิดกติกา (แก้: `fixesOf` ย้ายไป `lib/setupFixes`, หน้าผลสองคอลัมน์ที่ `lg:`, folder map ของ `fastapi-api` SKILL, ลำดับ lock ของ `lessons.lock`) + smell 11 (แก้: ท้าย `run`/`run_piped` ใช้ `_failed`, `OFFLINE` ซ้ำ, `RenderProgress`, `read_held` → `read_under_lock`, clean-up ของงานกัน error; ไม่แก้: `_run` ซ้ำแบบ `ModelJobSlot._run_job` (ยก `_run_job` ขึ้น `JobSlot` เป็น refactor ข้าม feature), คู่ (project, lesson_id), ตำแหน่งภาพอยู่ใน `kit`, `lesson_jobs` แบบ toon `ep_jobs`, body `{}` ของ cancel ตาม ADR-0013/spec), Spec 3 ขาด + 2 เกิน + 3 ผิด + 5 test (แก้: ตัว L/R บนหัวไม้เป็น ASS ตาม ADR-0037 (เดิมวาดด้วย Pillow), spec ข้อ 6 ตาม D33, AC `fontsdir` ตาม D34, ตัดบรรทัดไม่ล้น, ลบ test ที่ไม่ได้ผ่านทาง broken write จริงและ test `h264_args` ที่ซ้ำ trim, test busy ของหน้าแก้แยกสองกรณี; ไม่แก้: พื้นภาพเบลอมาก่อน ticket 03 (ใช้ทางเดียวกัน 03 test), ป้ายว่างทุกท่อน = หัวเรื่อง (D32), test ของ captions/ffmpeg นอก seam 2 เพราะ AC ขอเนื้อหา ASS ตรงๆ), Newcomer สรุปตรง What to build + เดา 13 จุด (แก้: `Segment.chapter` + `segment_at`, คอมเมนต์ `lesson_jobs` `CHAIN_DEPTH` `FADE_STEPS` `Drawn.ring` `not_running`, docstring `run_piped` `FakePiped`, ชื่อ test restart, `renderingPercent`; ไม่แก้: เลข D ในคอมเมนต์ (แบบของ repo))

**Measured:** บน Mac M1 คลิป 31.2 วินาที render จบ 6.9 วินาที (เป้า ≤ 60) ด้วย sample ปลอม + Kanit จริง; วาดเฟรมเฉลี่ย 4.6 ms (เป้า ≤ 30 ms → คงขยาย 2 เท่า D18); เสียงตรงภาพ test ผ่าน (ห่าง ≤ 1 เฟรม)

### 01: ติดตั้งเสียงกลอง บทเรียน และฟังจังหวะ — done 2026-11-13

**Built:**
- Setup script โหลด sample กลอง Big Rusty Drums 117 ไฟล์ (13 MB) ลง `models/drums/` ลองสามครั้งต่อไฟล์; Status check มีแถว `drum_kit` ต่อจาก Kanit
- tab "สอนกลอง" (`#/drums`): รายการ สร้าง ทำซ้ำ ลบบทเรียน; หน้าแก้มีตาราง Groove 16 ช่องต่อห้อง 1–4 ห้อง ไม้ R/L ลักษณะตี และกฎ D20, ท่อนสอน 1–6 ท่อน, ความยาวคลิปเทียบเพดาน 90 วินาที, ถามก่อนออก
- "ฟังจังหวะ" ผสมเสียงนับเข้าและทุกท่อนจาก `timeline` ตัวเดียว (ADR-0038) เป็น wav 16-bit 44.1 kHz stereo peak −1 dBFS เหมือนเดิมทุก byte

**Decided:**
- D26 — ตาราง sample จาก `.sfz` ไมค์ใกล้: ชั้นแรก กลาง สุดท้าย; snare ไมค์ `top`, kick ไมค์ `kick`
- D27 — ตัวอย่างใน AC แก้เป็น step 2 ที่ 4.5 วินาที (step 4 ที่ 5.0) ตามสูตรของ spec
- D28 — ทางเลือกเล็กของ backend: gate ของ listen แถวเดียว, `field` ทุกค่าผิด, ปัด 16-bit ด้วย numpy, ทำซ้ำ copy ภาพพื้นหลัง
- D29 — ทางเลือกเล็กของหน้าเว็บก่อนมีแบบ Figma
- D30 — Open Question 1: ตาราง Drum kit คงเดิม (`chik` key 44 GM Pedal Hi-Hat; ทอม key 47/45/43, f0 96/93/61 Hz) — ตรวจจากไฟล์ ยังไม่ได้ฟังด้วยหู: เจ้าของฟังตอนใช้ "ฟังจังหวะ" ครั้งแรก

**For the next ticket:**
- เวลาทุกอย่างอ่านจาก `video_gen.timeline.build` (`Hit.at`, `Beat`, `Span` เป็น sample ที่ 44.1 kHz; `Timeline.samples`); เฟรม `n` อยู่ที่ `n / 30` วินาที อย่าคำนวณเวลาโน้ตเอง
- `mixer.mix(project, timeline)` คืน wav bytes ใช้เขียน `audio.wav` ของ render ได้ตรงๆ; `lessons.read`, `lessons.require_id`, `lessons.MAX_LENGTH_S`
- `lessons.delete` ยังไม่เช็ค `lesson_busy` (ไม่มี Render job ใน ticket นี้) — ticket 02 เพิ่ม
- `kit.PIECES` มีแค่เลน สี เท้า; ตำแหน่งบนไดอะแกรมตาม kit-sketch เพิ่มใน ticket 02
- D30 ตรวจจากไฟล์ ยังไม่ได้ฟังด้วยหู: เจ้าของฟัง `chik` และทอมสามใบตอน "ฟังจังหวะ" ครั้งแรก ไม่ตรง → แก้ `drum_kit.SAMPLES` ที่เดียว
- `fakes.fake_sample()` เริ่มด้วยคลิกเต็มแรงที่ sample 0 สำหรับ test เสียงตรงภาพ
- หน้าเว็บ: `DrumsPage` เลือกหน้าจาก hash; ปุ่ม render และหน้า `#/drums/{id}/renders` ยังไม่มี

**Checks:** `uv run pytest` 1198 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 471 passed; `npm --prefix frontend run build` ผ่าน. Review สามแกนจาก `8cd9017`: Standards 0 ข้อผิดกติกา + 1 soft + smell 8 (แก้: helper `files.write_marker` ใช้ร่วมกับ Kanit, ลบ `HITS`, `ID_LENGTH`, type ของ `mixer`, `GrooveGrid` คำนวณซ้ำ; บันทึกใน D29: flag ของ `Editing`, `lengthOf` ซ้ำสูตรเพื่อบอกทันที; ไม่แก้: `PieceId` ใน Python, `tabOf` ตามแบบเดิม, แถว `drum_kit` สองที่ตามแบบ Kanit), Spec 0 ผิด + 3 ขาด (แก้: error ของ `field` ที่ไม่มีช่อง, วัดคลิป 89.4 วินาที, AC ฟังจังหวะตาม D29, `fix_kind`, ลบ unit test นอก seam `lib/lesson.test.ts`; ค้าง: ฟังเสียงด้วยหู → For the next ticket), Newcomer สรุปตรง What to build + เดา 12 จุด (แก้: `read` → `stored`, `_read_folder`, คอมเมนต์ step ก่อน pydantic, ป้ายว่าง, `NEW_LABEL`, stereo, ลำดับ round-robin, ที่อยู่ของ `drum_kit`, `save` ของหน้าแก้, `lengthOf`; ไม่แก้: เลข D/ADR ในคอมเมนต์ (แบบของ repo), จำนวนแถว 19→20 ใน test เดิม)

**Measured:** `mixer.mix` คลิป 89.4 วินาที (508 การตี, sample จริงทั้ง 117 ไฟล์) ใช้ 0.08 วินาทีครั้งแรก 0.03 วินาทีครั้งถัดไป บน Mac M1 (เป้า "ฟังจังหวะ" ≤ 5 วินาที)

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01 | design: รายการบทเรียนกลอง — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | done (D38: ใช้หน้าตาเดิมของแอปไปก่อน; prompt ของแบบอยู่ใน ui-prompt.md) |
| 2 | 01 | design: หน้าแก้บทเรียนกลอง — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | done (D38: ใช้หน้าตาเดิมของแอปไปก่อน; prompt ของแบบอยู่ใน ui-prompt.md) |
| 3 | 02 | design: ผล render ของบทเรียน — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | done (D38: ใช้หน้าตาเดิมของแอปไปก่อน; prompt ของแบบอยู่ใน ui-prompt.md) |
