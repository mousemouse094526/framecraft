# 03: render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง

**What to build:** ผู้ทำคลิปกด "render reel" เมื่อเลือกคาลิมบาแล้วได้ mp4 1080×1920 ที่โน้ตสีตกตามคอลัมน์ถึงเส้นเล่น คีย์ที่ถูกเล่นสว่างพร้อมเสียง มีเลขโน้ตใต้คีย์ หัวเรื่องและตัวนับห้องแบบ reel กลอง; แถวผลบอกว่าเป็นคาลิมบา. import MIDI ทำนองแล้วได้ reel คาลิมบาครบทาง.

**Blocked by:** 02: เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา

**Covers:**
- Decisions: D7, D8, D9 (ผล render, gate, `no_notes`), D11, D12, D13, D14 (ไม่มีเลขบนโน้ตที่ตก, ตกต่ำสุด 350 px/วิ, ลำดับ error, helper ที่ใช้ร่วม), drum-cover D8, D12, D15
- ADR: 0040, 0041, 0052, 0053, 0054, 0057, 0058, 0060
- Screens: หน้า reel — ส่วนที่เพิ่ม (ป้ายแถวผล render)
- Seams: 1 (render, เสียงตรงภาพ, ลำดับ error, `.json` เก่า), 2 (`frames`, `captions`), 3 (render และแถวผล)
- User stories: 3, 5
- Legal: 1, 2

**Status:** done

## Acceptance criteria

### ภาพ

- `frames.frame_at` ที่เวลาโน้ต → จุดวัดสีของคีย์นั้นเป็นสีเติมเต็มของเลข (± 12 ต่อช่องสี); 0.2 วิหลัง → สีพัก; `t` เดียวกันสองครั้ง → bytes เดียวกัน
- ตารางคีย์ใน sketch: ไม่ทับกันตอนขยาย 1.25 เท่า อยู่ในกรอบ จุดอ็อกเทฟและเลขอยู่ใต้จุดวัดสีทุกคีย์ สีของเลข 1–7 ต่างกันทุกคู่
- `bpm` 60 กับ C4 สองครั้งห่าง 0.08 วิ → สองโน้ตในคอลัมน์ไม่ทับกัน
- `captions.ass_file`: เลขและตัวอักษรใต้คีย์ 34 event ไม่ขึ้นกับจำนวนโน้ต; หัวเรื่องและ "ห้อง 1" เท่ากับของ reel กลอง
- หลังแยก `numbered_beats`, `bars_of(beats)`, `beat_dots`, `text_events`, `bar_counter_events` → test เดิมของ `drum_cover` timeline/frames/captions ผ่านโดยไม่แก้ assertion

### Render job

- render คาลิมบา poll จน `done` → mp4 1080×1920 30 fps h264 aac ยาว `length_s` ± 0.1; `.json` มี `instrument` `kalimba` และ `kalimba`
- เสียงตรงภาพ: C4 ตัวเดียวที่ `start_s + 1.0` → sample แรกของเสียงใน mp4 กับเฟรมแรกที่คีย์ C4 เติมสีเต็ม ห่าง ≤ 1 เฟรม
- render คาลิมบาเดิมสองครั้ง (backing ปิด) → `audio.wav` เหมือนกันทุก byte
- ลำดับ error: ไม่มี Kanit + `notes` 0 → `409` `no_notes`; ไม่มี Kanit + งานกลองรันอยู่ → `503` มี `rows`; Kanit มี + งานกลองรันอยู่ → `409` `busy`
- `GET …/renders` ของ `.json` เก่า → `instrument` `drums`, `kalimba` `{on: true, volume: 100}`
- reel คาลิมบา 30 วิ render ≤ 60 วิบน Mac วัดมือแล้วบันทึกใน Log (D12)

### หน้า reel

- เลือกคาลิมบา → "render reel" กดได้; กดแล้วแถบ % → `done` → แถวผลใหม่ถูกเลือก มีป้าย "คาลิมบา" (e2e)
- แถวผลคาลิมบา volume 60 → "คาลิมบา 60%"; `kalimba.on` `false` → "ไม่มีเสียงคาลิมบา" (e2e)
- error `no_notes` จาก render → `message` ใน `RefusedAlert` (e2e)

### เจ้าของ

- ดึง 3 เฟรมของ reel คาลิมบา Yellow แนบใน progress.md ให้เจ้าของดู
- เจ้าของ import MIDI ทำนองหนึ่งไฟล์ (เพลงที่หมดลิขสิทธิ์) render แล้วรับว่าเล่นทำนองถูก — ผลลง progress.md › Blocked (D12)
