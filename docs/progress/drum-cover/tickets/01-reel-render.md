# 01: reel cover จากเพลงที่แกะ: ตั้งช่วง ข้อความ เสียง ฟัง render

**What to build:** จากหน้าเพลงที่แกะแล้ว ผู้ทำคลิปกด "ทำ reel cover" ไปหน้า reel ตั้งช่วง หัวเรื่อง บรรทัดรอง คำบรรยาย และเสียง (กลองล้วนหรือ + เพลงต้นฉบับ) กด "ฟัง" แล้ว "render reel" ได้ mp4 1080×1920 ที่ไม้ตีและโน้ตตรงการตีที่แกะได้ตามเวลาจริง บนพื้นหลังสีของแอป เก็บผลทุกครั้ง เล่น โหลด ลบได้.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D1, D2, D3, D4, D5, D6, D7, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 (ห้อง, `song_busy`, lock), drum-notes D13, D21, video-gen D14, D21, D29, D33, story-kb D11
- ADR: 0050, 0051, 0052, 0053, 0041, 0010, 0013
- Screens: หน้าเพลง — ส่วนที่เพิ่ม (ส่วน "Reel cover"), หน้า reel (ยกเว้นการ์ดพื้นหลังแบบภาพ)
- Seams: 1 (ยกเว้นข้อ background), 2, 3 (ยกเว้นข้อ Alert หลังแกะและข้อเลือกภาพ)
- User stories: 1, 2, 3, 4, 5
- Legal: 1, 2, 4

**Status:** ready-for-agent

## Acceptance criteria

### Timeline ของ reel
- `analysis` ห้อง 2.0 วินาที cover 10.0–14.0 → `length_s` 5.5, snare ที่ 11.0 อยู่ sample `44100`, จังหวะ 10.0 เลข 1 และ 10.5 เลข 2; cover เริ่ม 9.0 มี beat 9.5 → เลข 4
- ไฮแฮท 16th 8 ตัว → R L R L …; snare + crash + ไฮแฮทช่องเดียว → ไฮแฮท `hand` `null` ยังอยู่ใน `hits`; ชิ้นเดียวห่าง 20 ms → ตัวที่สอง `hand` `null`
- `accent` → `hard`/`accent`, `ghost` → `soft`/`ghost`; โหมดทำนอง → snare ตามที่พบ
- `assemble` ให้ `Timeline` เดียวกับ `build` ของบทเรียนตัวอย่าง video-gen; test เดิมของ video-gen ผ่านโดยไม่แก้
- เฟรมที่เวลาของ snare → จุดกระทบสีแดง เฟรมก่อนหน้าไม่แดง; เวลาเดียวกันสองครั้ง → bytes เดียวกัน

### API
- `GET /cover` ของเพลงที่แกะแล้วไม่มี `cover.json` → `saved` `false`, `start_s` = ต้นห้องแรกที่มีการตี, `has_audio`, `hits`; ยังไม่แกะ → `409` `no_analysis`; analysis ใหม่ที่สั้นกว่า → ค่าดึงเข้าช่วง `adjusted` `true`
- `PUT /cover` ค่าผิด (ช่วง 1 วินาที, เกินช่วงแกะ, `volume` 5, `title` ว่าง, backing กับ MIDI) → `400` มี `field`; ค่าดี → `cover.json`
- `POST /listen` → wav ยาว `length_s` ± 0.05; backing เปิดกับ `audio.m4a` ปลอม → ยาวเท่ากัน ไม่เงียบในช่วงไม่มีการตี และ peak −1 dBFS ไม่ clip; ไม่มี sample → `503` `rows: ["drum_kit"]`
- `POST /render` → poll จน `done` → mp4 1080×1920 30 fps h264 + aac ยาว `length_s` ± 0.1, srt, json มี `start_s`, `end_s`, `picked_at`, `backing`; backing เปิดก็มีภาพและเสียง
- เสียงตรงภาพ: snare ที่ `start_s + 1.0` → เสียงแรกใน mp4 กับเฟรมแรกที่จุดกระทบแดง ห่าง ≤ 1 เฟรม
- render cover เดิมสองครั้ง (backing ปิด) → `audio.wav` เหมือนกันทุก byte
- render ซ้อน → `409` `busy` มี `song_id`; `DELETE /songs/{id}` ระหว่าง render → `409` `song_busy`; ยกเลิกกลางเฟรม → `cancelled` ไม่มี `.partial`; `PUT /cover` ระหว่าง render → `200` และงานใช้ค่าก่อนแก้
- `DELETE /songs/{id}` → `cover.json` และ `renders/` หาย; `DELETE …/renders/{name}` → `204`; ชื่อ `..` → `404`; start ล้าง `media/songs/.render/` และ `.partial`

### หน้าเว็บ
- หน้าเพลงที่มี `analysis` → ส่วน "Reel cover" เหนือ "สร้างบทเรียน" บอก "render แล้ว 2 ครั้ง" กด "ทำ reel cover" → `#/songs/{id}/cover` (e2e)
- เปิดหน้า reel → ฟอร์มจาก `GET /cover`; ยังไม่แกะ → "แกะโน้ตก่อน แล้วกลับมาทำ reel" (e2e)
- แก้หัวเรื่องแล้ว "บันทึก" → `PUT /cover`; "เริ่มที่การตีแรก" → ช่องเริ่ม = `suggested_start_s`; "ฟัง" → บันทึกแล้ว `POST /listen` ปุ่ม "กำลังผสมเสียง…" (e2e)
- เลือก "กลอง + เพลงต้นฉบับ" → ความดังและคำเตือนขึ้น บันทึกส่ง `backing: {on: true, volume: 35}`; `has_audio` `false` → กดไม่ได้ (e2e)
- "render reel" → แถบ % → `done` → ผลใหม่ถูกเลือก; `failed` → ข้อความกับ "ลองอีกครั้ง" (e2e)
- ช่วงไม่มีการตี → Alert ปิด "ฟัง"/"render reel"; `adjusted` → Notice และ "ยังไม่บันทึก"; แถวผลเก่ากว่าผลแกะ → "แกะใหม่แล้ว" (e2e)
- ออกก่อนบันทึก → ถามยืนยัน; ลบผล render พร้อมยืนยัน → `DELETE` (e2e)
