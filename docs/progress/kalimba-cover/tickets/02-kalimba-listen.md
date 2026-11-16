# 02: เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา

**What to build:** ผู้ทำคลิปเปิดหน้า reel ของเพลง กด "คาลิมบา" เห็นจำนวนโน้ต การย้ายคีย์ โน้ตที่ตัดและที่ปรับ ตั้งความดังคาลิมบา แล้วกด "ฟัง" ได้ยินทำนองบนคาลิมบา 17 คีย์ที่สังเคราะห์ในแอป; บันทึกแล้วกลับมาเปิดยังเป็นคาลิมบา. "render reel" ของคาลิมบายังกดไม่ได้จนถึง ticket 03.

**Blocked by:** 01: โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI

**Covers:**
- Decisions: D1, D4, D5, D6, D8, D9, D10, D14 (ทำนองด้านบน, ทิ้งเบส, `bent`, เตือนย้ายคีย์, `SegmentedChoice`, `arrange` ไม่ import `drum_cover`), drum-cover D7, D17, D24
- ADR: 0041, 0050, 0055, 0057, 0058, 0059
- Screens: หน้า reel — ส่วนที่เพิ่ม (การ์ดเครื่องดนตรี, การ์ดเสียง, Alert ของโน้ต)
- Seams: 1 (`GET`/`PUT /cover`, `/listen`), 2 (`arrange`, `timeline`, `sound`), 3 (หน้า reel ยกเว้น render)
- User stories: 1, 2, 4, 6
- Legal: 3, 4

**Status:** ready-for-agent

## Acceptance criteria

### การจัดโน้ตและเสียง

- ตัวอย่างทุกข้อใน spec › การจัดโน้ตลงคาลิมบา ให้ผลตามที่เขียน (`transpose`, `dropped`, `bent`, pitch ที่เหลือ)
- `timeline.build`: โน้ตที่ `start_s + 1.0` → `at` 44100; เลขจังหวะเท่า `drum_cover.timeline` ด้วย `numbered_beats` ตัวเดียวกัน
- `sound.note(60, "normal")` → ความถี่หลัก 261.6 ± 1 Hz; `mix` สองครั้ง → bytes เดียวกัน; peak −1 dBFS; ไม่มีโน้ต → wav เงียบยาว `timing.samples`

### API

- `cover.json` เก่าไม่มี `instrument`/`kalimba` → `drums` และ `{on: true, volume: 100}`; ไม่มี `cover.json` กับช่วงที่ไม่มี `hits` แต่มี `notes` → `instrument` `kalimba`
- `GET /cover` มี `notes`, `notes_picked`, `transpose`, `dropped`, `bent`
- `PUT /cover` ไม่มี `instrument`, `instrument` `piano`, `kalimba.volume` 5, `kalimba.on` `false` กับคาลิมบาและ backing ปิด → `400` มี `field`; `drums.on` `false` กับคาลิมบา → `200`
- `/listen` คาลิมบา → wav ยาว `length_s` ± 0.05 ไม่เงียบ; สองครั้ง bytes เดียวกัน; volume 50 → peak ต่ำกว่า 6.0 dB ± 0.1; ไม่มี sample กลองบนดิสก์ → `200`
- `/listen` คาลิมบา `notes` 0 → `409` `no_notes` "ช่วงนี้ไม่มีโน้ตทำนอง…"; `notes_picked` `false` → `409` ข้อความแกะใหม่ (เพลง MIDI: นำเข้าไฟล์เดิม)
- `/listen` กลอง volume 100 → bytes เดียวกับ `mixer.mix` ตรง (D12)

### หน้า reel

- เปิดหน้า reel ที่ `drums` → "กลอง" ถูกเลือก; กด "คาลิมบา" → แถวเสียง "คาลิมบา" และบรรทัด "48 โน้ตทำนองในช่วง · ย้ายคีย์ +2 · ตัด 3 โน้ต · ปรับ 4 โน้ตให้เข้าสเกล" จุด "ยังไม่บันทึก"; "บันทึก" → `PUT` ส่ง `instrument` `kalimba` และ `kalimba` (e2e)
- GET ตอบ `kalimba` กับ `hits` 0 → "คาลิมบา" ถูกเลือก ไม่มี Alert การตีกลองหรือบรรทัดโหมดทำนอง (e2e)
- `notes_picked` `false` หรือ `notes` 0 → Alert ตาม spec ปุ่ม "ฟัง"/"render reel" กดไม่ได้ (e2e)
- "ความดังคาลิมบา" 60 → `PUT` ส่ง `kalimba.volume` 60; "ปิดเสียงคาลิมบา" กับ "คาลิมบาล้วน" → ข้อความห้ามเงียบ ปุ่มกดไม่ได้ (e2e)
- คาลิมบา + backing + `transpose` 2 → คำเตือน "คาลิมบาย้ายคีย์ +2 เสียงจะไม่ตรงกับเพลงต้นฉบับ" (e2e)
- "ฟัง" คาลิมบา → บันทึกก่อนแล้ว `POST /listen` เล่น blob (e2e)
- เลือกคาลิมบา → "render reel" กดไม่ได้ชั่วคราวโดยไม่มีข้อความใหม่ จน ticket 03 เปิด
- "กลองล้วน"/"กลอง + เพลงต้นฉบับ" เดิมใช้ `components/ui/SegmentedChoice` และ test เดิมของหน้า reel ผ่าน
- เจ้าของแกะ Yellow 11.5–30 ใหม่แล้วฟังคาลิมบาจาก "ฟัง": ผลลงใน progress.md › Blocked (D12)
