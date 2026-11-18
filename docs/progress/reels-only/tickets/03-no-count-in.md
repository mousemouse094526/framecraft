# 03: reel กลองไม่มีนับเข้า

**What to build:** reel กลองเริ่มที่ห้องแรกของ Groove ตั้งแต่เฟรมแรก: ไม่มีไฮแฮทเบา 4 ครั้ง ไม่มีตัวนับ 1–4 ก่อน Groove ไม่มี cue นับเข้าใน `.srt`; ความยาวที่หน้าแก้ รายการ ฟังจังหวะ และ render สั้นลงหนึ่งห้องตรงกันทุกที่. flam ที่ต้นคลิปเล่นได้ไม่พัง.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D15, D16, video-gen D13, video-gen D21, video-gen D12
- ADR: 0041
- Screens: หน้าแก้ reel กลอง (บรรทัดความยาว), รายการ reel กลอง (ความยาว)
- Seams: 4
- User stories: 6

**Status:** ready-for-agent

## Acceptance criteria

### timeline

- 120 BPM 1 ห้อง 1 รอบ สแนร์ step 0 → hit แรกที่ sample 0 เป็นสแนร์, ไม่มี hit `count`, beats `[1, 2, 3, 4]` ที่ 0, 0.5, 1.0, 1.5 วิ, `length_s` 3.5
- `length_s` = ทุกท่อน + 1.5 วิ; `COUNT_IN_PIECE` และ `"count"` ไม่มีในโค้ด
- flam ที่ step 0 สองรอบ → รอบแรกไม่มีโน้ตนำ ไม่มี hit ที่ sample < 0; รอบสองมีโน้ตนำ 0.03 วิ ก่อน; `POST …/listen` ของ lesson นั้นตอบ 200 (D16)

### ภาพและข้อความ

- `captions.sections` ท่อนเดียวไม่มีป้าย → ส่วนเดียว 0 ถึง `length_s` หัวเรื่องกับบรรทัดรอง; `srt_file` → cue เดียว เริ่ม `00:00:00,000`
- `lane.segments` → segment แรกเริ่ม 0 เป็นท่อนแรก ตามด้วยหาง
- `frames`: สแนร์ step 4 ที่ 120 BPM สีแดงที่ 0.5 วิ ไม่ใช่เฟรมก่อน

### ความยาวสองฝั่ง

- reel ใหม่ (`POST /api/drums/lessons`) `length_s` 11.1; `lengthOf` ของหน้าเว็บได้ค่าเดียวกัน
- test ของ `DrumsPage` ที่บอกความยาวและเพดาน 90 วิ ใช้สูตรใหม่ (97.5 ยังเกิน)

### ของจริง

- render reel ใหม่ผ่าน API ใน project ชั่วคราว → `ffprobe` นับได้ 333 เฟรม ความยาว ~11.1 วิ; `.srt` บรรทัดเวลาแรก `00:00:00,000 --> 00:00:11,100`; ตัวเลขลง progress.md

### ไม่เปลี่ยน

- test ของ `drum_cover` และ `kalimba_cover` ผ่านโดยไม่แก้ ยกเว้น `test_assemble_gives_a_lesson_the_timeline_build_always_gave_it`
- ผล render เก่าไม่แตะ

## Notes

- Testing decisions ใน spec.md บอก test ที่ต้องแก้ตัวเลข ทีละบรรทัด — แก้เป็นค่าของสูตรใหม่ ห้ามแค่หลวม assertion
- docstring/comment ที่พูดถึงนับเข้าใน `timeline` `captions` `lane` `frames` `drum_cover/timeline` `lib/lesson.ts` เขียนใหม่
