# Progress: video-gen

**Now:** 01, 02 done; 03 (ภาพพื้นหลัง) ต่อ

**Next:**

```
/warroom-build video-gen 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้งเสียงกลอง บทเรียน และฟังจังหวะ | done |
| 02 | render คลิปสอนกลอง | done |
| 03 | ภาพพื้นหลังของผู้ใช้ | ready |

## Log

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
| 1 | 01 | design: รายการบทเรียนกลอง — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | open |
| 2 | 01 | design: หน้าแก้บทเรียนกลอง — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | open |
| 3 | 02 | design: ผล render ของบทเรียน — ทำแบบจาก [ui-prompt.md](../../features/video-gen/ui-prompt.md) | `/warroom video-gen` พร้อมลิงก์แบบ | open |
