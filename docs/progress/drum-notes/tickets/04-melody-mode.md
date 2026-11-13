# 04: โหมดทำนอง

**What to build:** บนหน้าเพลง ผู้ใช้เลือกโหมด "ทำนอง" แล้วกด "แกะโน้ต": Pick job รัน Basic Pitch แทน ADTOF หา onset ของโน้ตทำนอง (piano, kalimba) และ Beat This! หาห้องเหมือนเดิม; ตารางตัวอย่างและบทเรียนที่สร้างมี snare ตามจังหวะทำนอง บวก kick จังหวะ 1 และ 3 กับไฮแฮททุก 8th ที่แอปเติม.

**Blocked by:** 03: เลือกห้อง ฟัง แล้วสร้างบทเรียนกลอง

**Covers:**
- Decisions: D14, D7 (gate `pick_melody`), D20 (Open Question 1)
- ADR: 0041
- Screens: หน้าเพลง (โหมด "ทำนอง")
- Seams: 1 (pick โหมด melody), 2 (mapping โหมดทำนอง), 3 (เลือกโหมดแล้วแกะ)
- User stories: 5
- Legal: 6

**Status:** ready-for-agent

## Acceptance criteria

- อ่าน `get_inputs()`/`get_outputs()` ของ `basic_pitch_nmp.onnx` จริงบนเครื่อง → บันทึกชื่อและรูปร่างใน `docs/library-notes/` และปิด Open Question 1 ของ spec (ไม่ตรง 43,844 / 172 × 88 → แก้ `onnx_runner` ให้ตรงไฟล์ และบันทึก D ใหม่)
- `PUT /range` `mode` = `melody` แล้ว `POST /pick` → gate `pick_melody` (`model_basic_pitch`, `model_beat_this`, `onnxruntime`, `ffmpeg`); ขาดแถว → `503` `not_ready` มี `rows`
- `onnx_runner` ป้อน Basic Pitch ทีละหน้าต่าง 43,844 sample ที่ 22.05 kHz ซ้อน 30 เฟรม (ตัด 15 ต่อด้าน, pad ครึ่งหน้าต่างที่ต้น) คืน `onset` ต่อหน้าต่าง; `score` ต่อหน้าต่างและนับ onset = เฟรมที่ `onset` ≥ 0.5 ของโน้ตใด; onset ทุกโน้ตในเฟรมเดียวกันรวมเป็นการตีเดียว
- `analysis` › `mode` = `melody`, `hits` ทุกตัว `piece` `snare` `level` `normal`; `beats`/`downbeats` จาก Beat This! เหมือนโหมดกลอง
- `POST /preview` ของ `analysis` โหมด `melody`: onset 2 ตัวในห้อง → `snare` 2 ตัว + `kick` ช่อง 0 และ 8 + `hihat_closed` ทุกช่องคู่ ของทุกห้องที่เลือก; มือตามกฎ D13 (ไฮแฮท R, snare L เมื่ออยู่ช่องเดียวกับไฮแฮท); ผลผ่าน `video_gen.lessons` ไม่ error
- `POST /lessons` จาก `analysis` โหมด `melody` → บทเรียนที่ Groove มีสามชิ้นนั้น; "ฟัง" ได้ยินทั้งสาม (e2e)
- หน้าเพลง: เลือก "ทำนอง" มีคำอธิบาย "แกะจังหวะของโน้ตทำนอง (piano, kalimba) เป็น snare บน groove พื้นฐาน"; กด "แกะโน้ต" → `PUT /range` ส่ง `mode` `melody` → `done` → ผลระบุโหมด "ทำนอง" และตารางมี kick กับไฮแฮทที่เติม (e2e)
- `GET /songs` แสดงโหมดของ `analysis`; รายการเพลง "แกะแล้ว {n} ห้อง" เหมือนโหมดกลอง
- วัดมือ: เจ้าของแกะเพลง kalimba หรือ piano หนึ่งเพลงจากลิงก์ → ตารางมี snare ตามจังหวะทำนองที่ได้ยิน; บันทึกผลใน Log
