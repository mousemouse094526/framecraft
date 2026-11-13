# Progress: video-gen

**Now:** 01 done; 02 (render) ต่อ

**Next:**

```
/warroom-build video-gen 02
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | ติดตั้งเสียงกลอง บทเรียน และฟังจังหวะ | done |
| 02 | render คลิปสอนกลอง | ready |
| 03 | ภาพพื้นหลังของผู้ใช้ | ready |

## Log

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
