# 03: เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง

**What to build:** จากห้องที่พบ (เสียงที่แกะแล้ว หรือ MIDI) ผู้ใช้กดห้องแรก เลือกจำนวนห้อง 1–4 แก้ BPM เห็นตาราง Groove แบบอ่านอย่างเดียวที่มีมือ L/R และรายการโน้ตที่ถูกตัด กด "ฟัง" ได้ยินกลองของตารางนั้น แล้วกด "สร้างบทเรียนกลอง" ไปโผล่ที่หน้าแก้บทเรียนใน tab สอนกลองพร้อมแก้ต่อ. หน้าเพลงแสดงบทเรียนที่สร้างจากเพลงนี้.

**Blocked by:** 02: แกะโน้ตกลองจากช่วงที่เลือก

**Covers:**
- Decisions: D11, D12, D13, D15, D19, D20, D21, video-gen D4, video-gen D5, video-gen D20, video-gen D22, video-gen D23
- ADR: 0042, 0044
- Screens: หน้าเพลง (สร้างบทเรียน, บทเรียนจากเพลงนี้)
- Seams: 1 (preview, listen, lessons), 2 (quantize, มือ, ตัด, round trip), 3 (ทางเดินทั้งหมดจนถึง `#/drums/{id}`)
- User stories: 3, 4, 6
- Legal: 5

**Status:** done

## Acceptance criteria

### Score

- ห้องยาว 2.0 วินาที ต้นห้อง 10.0: การตี 10.49 → ช่อง 4; 9.95 → ช่อง 0; 11.94 เมื่อเลือกห้องเดียว → ทิ้ง (ไม่อยู่ใน `dropped`); ชิ้นเดียวกันซ้ำช่อง → เหลือ `level` สูงสุด
- BPM ตั้งต้น = `round(240 / median(ความยาวห้องที่เลือก))` จำกัด 40–240: ห้อง 2.0 วินาที → 120
- เลือกห้องที่ "ไม่ใช่ 4/4" หรือ `bar + bars` เกินจำนวนห้อง → `400` `invalid_request` field `bar` "ห้องนี้ไม่ใช่ 4/4"
- round trip: บทเรียน video-gen (Groove 2 ห้อง BPM 120 มี kick, snare, tom_mid, hihat_closed, crash) → `video_gen.timeline.build` → การตี → quantize ที่ 120 → `groove.notes` เท่ากับของเดิมทุกตัว (ชิ้น ช่อง); เลื่อนสลับ +20/−20 ms ทุกตัว → ยังเท่ากัน
- ตัดต่อช่อง: `hihat_closed` + `snare` + `crash` → เหลือ `snare`, `crash` และ `dropped` = `[{hihat_closed, step}]`; `hihat_open` คู่ `hihat_closed` → เหลือ `hihat_closed`
- มือ: ไฮแฮท 16th ติดกัน 8 ตัว → R L R L …; groove ร็อก (ไฮแฮท 8th + snare ช่อง 4, 12) → ไฮแฮท R ทุกตัว snare L; crash หลังพัก 4 ช่อง → R; snare กับไฮแฮทช่องเดียว → ไฮแฮท R snare L; เท้าไม่มีมือ
- ทุก Groove ที่ Score คืนผ่านกฎ D20 ของ video-gen (`video_gen.lessons` ตรวจไม่ error) สำหรับ activation สุ่มด้วย seed ตายตัว 100 ชุด

### API

- `POST /songs/{id}/preview` `{bar, bars, bpm?}` → `{groove, bpm, dropped: [{piece, step}]}`; ไม่ส่ง `bpm` → ค่าตั้งต้น; ยังไม่มี `analysis` → `409` `no_analysis`
- `POST /songs/{id}/listen` `{bar, bars, bpm}` → `audio/wav` `Cache-Control: no-store` ยาวเท่า `length_s` ของบทเรียนชั่วคราว (นับเข้า 1 ห้อง + ท่อนสอนตั้งต้นสองท่อน + หาง 1.5 วินาที) ไม่มีไฟล์ใหม่ใน `media/`; `drum_kit` ขาด → `503` `not_ready`
- `POST /songs/{id}/lessons` `{bar: 0, bars: 2, bpm}` → `201` `{lesson_id, dropped}` (จำนวน); `GET /api/drums/lessons/{id}` → `title` = ชื่อเพลงตัด 40, `subtitle` = บรรทัดรองตัด 60, `bpm`, Groove 2 ห้องตาม Score, ท่อนสอนสองท่อนตั้งต้น (ป้ายว่าง และ `ลองเล่นเอง`), `caption` ว่าง, `background` `color`
- `GET /songs/{id}` › `lessons` มี id ใหม่; ลบบทเรียนใน `/api/drums` แล้ว → `lessons` ไม่มี id นั้น ไม่ error; `DELETE /songs/{id}` → บทเรียนยังอยู่
- บทเรียนสร้างผ่าน `video_gen.lessons` (ไม่ผ่าน HTTP) ด้วยกฎตรวจเดียวกับ `PUT`; `lesson.json` ไม่มีช่องใหม่

### หน้าเพลง

- กดห้องบนแถบ → ห้องนั้นเป็นห้องแรกและ player เลื่อน; เลือก "จำนวนห้อง" 1–4 (ตัวเลือกที่เกินห้องที่เหลือกดไม่ได้); แก้ BPM → `POST /preview` (debounce 300 ms) → ตาราง `GrooveGrid` แบบอ่านอย่างเดียวมีโน้ตและตัว L/R และรายการ "ตัดโน้ตที่มือตีไม่ได้" (ซ่อนเมื่อว่าง) (e2e)
- กด "ฟัง" → `POST /listen` ปุ่มเป็น "กำลังผสมเสียง…" จนเล่น blob ด้วย `playAudio`; กดใหม่หยุดของเดิม (e2e)
- กด "สร้างบทเรียนกลอง" → `POST /lessons` → hash เป็น `#/drums/{lesson_id}` และหน้าแก้แสดงตารางเดียวกัน (e2e)
- ส่วน "บทเรียนจากเพลงนี้" แสดงลิงก์ `#/drums/{id}` ของทุกบทเรียนที่ยังอยู่; ว่าง → "ยังไม่มี" (e2e)
- เพลง MIDI → เลือกห้องและสร้างได้โดยไม่ต้องแกะ (e2e)
- `GrooveGrid` ของ video-gen ได้โหมดอ่านอย่างเดียว; เมื่อ drum-notes ใช้ด้วย ย้ายไป `components/ui/` ตามกติกา "Where shared code goes"

### ตัดสินโดยเจ้าของ

- จาก `reel.mp4` และจากลิงก์ YouTube ของ Smells Like Teen Spirit เลือกสองห้องแรกของ intro → ตาราง: kick กับ snare ตรงตำแหน่งอย่างน้อยสองห้องแรก และฟังแล้วใช้แก้ต่อได้; บันทึกผลและสิ่งที่ต้องแก้มือใน Log (D19, D20)
