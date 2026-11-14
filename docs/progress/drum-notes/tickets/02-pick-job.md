# 02: แกะโน้ตกลองจากช่วงที่เลือก

**What to build:** บนหน้าเพลง ผู้ใช้ตั้งช่วงแกะ 4–90 วินาที เลือกโหมด "กลอง" กด "แกะโน้ต" แล้วเห็นแถบ % จนได้ BPM ที่พบกับห้องที่พบพร้อมจำนวนการตีต่อห้อง; กดห้องแล้ว player เลื่อนไปต้นห้อง. Pick job รัน ADTOF กับ Beat This! บน CPU ใน thread ไม่จองช่อง GPU และเขียน `analysis` ลง `song.json`. โหมด "ทำนอง" ยังกดไม่ได้ (มาใน 04).

**Blocked by:** 01: เอาเพลงเข้า: ลิงก์ ไฟล์เสียง ไฟล์ MIDI และโมเดล

**Covers:**
- Decisions: D5, D6, D7 (gate), D8, D9, D17, D18, D20
- ADR: 0040, 0044
- Screens: หน้าเพลง (ช่วงแกะ, โหมด, แกะโน้ต, ผลที่แกะได้)
- Seams: 1 (range, pick), 2 (stitch, peak picking, จังหวะและห้อง)
- User stories: 2
- Legal: 3 (ใช้โมเดลในเครื่อง ไม่หารายได้)

**Status:** done

## Acceptance criteria

### ช่วงแกะ

- `PUT /songs/{id}/range` `{start_s, end_s, mode}` → Song ที่ `range` เปลี่ยน; ช่วง 2 วินาที, 100 วินาที, `end_s` > `duration_s`, `start_s` < 0 → `400` `invalid_request` มี `field`; MIDI → `409` `not_applicable`
- หน้าเพลง: ช่องเริ่มและจบ ปุ่ม "ใช้เวลาที่เล่นอยู่" ทั้งสองช่อง ความยาวช่วงกับเพดาน 90; ช่วงผิด → ข้อความที่ช่อง (e2e)
- ยังไม่มี `analysis` → ซ่อนส่วนผลและสร้างบทเรียน แสดง "ตั้งช่วงแล้วกด แกะโน้ต" (e2e)

### Pick job

- `POST /songs/{id}/pick` → `202` แล้ว `GET /songs/pick` ผ่าน `preparing` → `picking` (`percent` เพิ่มตาม chunk) → `done`; `song.json` › `analysis` มี `mode` `drums`, `start_s`/`end_s` ของช่วง, `beats`, `downbeats` (⊆ `beats`, ≥ 2), `hits` (`t` บวก `start_s` แล้ว, `piece` ตาม D9, `level` `normal`), `picked_at`
- gate `pick_drums` (`model_adtof`, `model_beat_this`, `onnxruntime`, `ffmpeg`) ขาดแถว → `503` `not_ready` มี `rows`; หน้าเว็บแสดง `fix` (e2e)
- งานรันอยู่ → `409` `busy` มี `song_id`; `DELETE` เพลงที่แกะอยู่ → `409` `song_busy`; MIDI → `409` `not_applicable`; id ไม่มี → `404`
- Pick job ไม่เรียก `gpu.take` และ `GpuSlot` ว่างตลอดงาน (test ยืนยันว่า Transcribe job ปลอมเริ่มพร้อมกันได้)
- `preparing` ใช้ `ffmpeg.run_capture` ถอด `audio.m4a` ช่วง `[start_s, end_s)` เป็น float32 mono 44.1 kHz และ 22.05 kHz ผ่าน stdout; ยกเลิกระหว่างนี้ → ffmpeg ถูก kill งาน `cancelled`; ffmpeg พัง → `failed` `internal` มีบรรทัดท้ายของ stderr
- `onnx_runner` รัน ADTOF ทั้งช่วงครั้งเดียว (`waveform [1, samples]` → `activations [1, frames, 5]`) และ Beat This! ทีละ chunk 1,500 เฟรม (`pad_frames` 6 ที่ต้นและท้ายของทั้งช่วง 0 ที่อื่น; `N = (frames − 1) × 441 + 1024`) คืน array ดิบ; `PickJobs(run_model=…, run_ffmpeg=…)` รับตัวรันทาง constructor
- fake หยุดที่ chunk แรก (`pause_at`) → ยกเลิก → `cancelled` และ `analysis` เดิม (ถ้ามี) ไม่เปลี่ยน; `release` แล้วงานไม่เขียนอะไร
- fake โยนตอนสร้าง session → `failed` `model_broken` มี `rows` และ `fix` คำสั่ง Setup script; fake โยนตอน `run` → `failed` `model_failed` มีบรรทัดแรกใน `message`; หน้าเว็บแสดงทั้งสองแบบ (e2e)
- fake คืน `downbeat` ที่ให้ peak น้อยกว่า 2 → `failed` `no_beats`; หน้าเว็บ "หาจังหวะในช่วงนี้ไม่ได้ ลองช่วงอื่น" (e2e)
- แกะใหม่ด้วยช่วงอื่น → `analysis` ถูกทับทั้งก้อน; restart ระหว่างงาน → งานหาย `analysis` เดิมอยู่
- หน้าเว็บ: กด "แกะโน้ต" → `PUT /range` แล้ว `POST /pick` → แถบ % ปุ่มยกเลิก → `done` → "BPM ที่พบ" และแถบห้อง (e2e); รายการเพลงแสดง "กำลังแกะ {n}%" ระหว่างงาน และ "แกะแล้ว {n} ห้อง" หลังจบ (e2e)

### Score ขั้นต้น

- `score.stitch`: logit สังเคราะห์สาม chunk ซ้อน 6 → array เดียวยาวเท่าจำนวนเฟรมของช่วง ค่าตรงต้นฉบับทุกเฟรม; chunk สุดท้ายที่เลื่อนให้จบที่ท้ายช่วงต่อถูก
- peak picking ด้วย threshold 0.22, 0.24, 0.32, 0.22, 0.30 และหน้าต่าง `pre_avg 0.1, post_avg 0.01, pre_max 0.02, post_max 0.01, combine 0.02`: activation สังเคราะห์ (1.0 ที่เฟรมของการตี) → การตีตรงเวลาที่วาง ± 10 ms; สองค่าห่าง 10 ms → รวมเป็นหนึ่ง
- จังหวะ = peak ของ `beat` ในหน้าต่าง 7 เฟรม logit > 0 peak ติดกันรวม; downbeat ย้ายไปจังหวะใกล้สุด: logit สังเคราะห์ (จังหวะทุก 0.5 วินาที downbeat ทุก 2.0) → `beats` และ `downbeats` ตรง ± 10 ms
- ห้องที่พบ = downbeat ติดกัน; ห้องที่มีจังหวะไม่เท่ากับ 4 ตัวถูกทำเครื่องหมาย "ไม่ใช่ 4/4" ใน `GET /songs/{id}` (ช่องของ `analysis` หรือค่าที่คำนวณตอนอ่าน ตามที่ build เลือกและบันทึก) และจางบนแถบ (e2e)
- กดห้องบนแถบ → `audio.currentTime` = ต้นห้อง (e2e)

### วัดมือ

- ช่วง 90 วินาทีของเพลงจริงบน Mac Apple Silicon → `done` ภายใน 60 วินาที (D19); ยกเลิกมีผลภายในหนึ่ง chunk; บันทึกเวลาใน Log
- เจ้าของแกะ intro ของ Smells Like Teen Spirit จาก `reel.mp4` (เอาเข้าเป็นไฟล์) และจากลิงก์ YouTube ของเพลงจริง → ดูการตีต่อห้องเทียบคลิปอ้างอิง บันทึกผลใน Log (ตัดสินเต็มใน 03 เมื่อเห็นตาราง)
