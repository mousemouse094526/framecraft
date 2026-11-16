# 01: โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI

**What to build:** ผู้ทำคลิปแกะเพลงแล้วได้โน้ตทำนองพร้อม pitch เก็บไว้ข้างการตีกลอง ทั้งโหมดกลองและโหมดทำนอง และนำเข้าไฟล์ MIDI ที่มีแต่ทำนองได้; หน้าเพลงบอกจำนวนโน้ตทำนอง. reel กลองและการแกะกลองทำงานเหมือนเดิมทุกอย่าง.

**Blocked by:** None (can start immediately)

**Covers:**
- Decisions: D2, D3, D14 (Basic Pitch พังไม่ทำให้แกะกลองพัง, import MIDI เดิมเติม `notes`), drum-notes D6, D9, D10, D14, D19, D22
- ADR: 0049, 0056
- Screens: หน้าเพลงและรายการเพลง — ส่วนที่เพิ่ม
- Seams: 1 (MIDI import, Pick job, `song.json` เก่า), 2 (`score.melody_notes`, `midi.read`), 3 (หน้าเพลงและรายการเพลง)
- User stories: 5, 6
- Legal: 2

**Status:** ready-for-agent

## Acceptance criteria

### ข้อมูลและการแกะ

- `song.json` เก่าที่ `analysis` ไม่มี `notes` → `GET /songs/{id}` ตอบ `analysis.notes` `null`; เขียนกลับแล้วยังอ่านได้
- onset ปลอมคีย์ 39 เฟรม 20–21 กับคีย์ 43 เฟรม 20 → `score.melody_notes` ได้ pitch 60 และ 64 เวลาเดียวกัน ตัวละหนึ่ง; เฟรม 10 ไม่มีโน้ต; `melody_hits` ของ output เดียวกันเท่าเดิม
- Pick job โหมดกลองด้วย `onnx_runner` ปลอม → `analysis` มี `hits` จาก ADTOF และ `notes` จาก Basic Pitch; `percent` นับหน้าต่าง Basic Pitch ด้วย
- Pick job โหมดกลองที่ Basic Pitch ไม่มีหรือโยน error → `done`, `hits` ครบ, `notes` `null`; gate `pick_drums` ไม่ขอแถว Basic Pitch
- Pick job โหมดทำนอง → Basic Pitch รันครั้งเดียว ได้ทั้ง `hits` snare แบบเดิมและ `notes`
- `notes` เกิน 20,000 ตัว → เก็บ 20,000 ตัวแรกตามเวลา งานไม่ fail
- เป้า Pick job 90 วิโหมดกลอง ≤ 60 วิบน Mac วัดมือแล้วบันทึกใน Log (D12)

### ไฟล์ MIDI

- MIDI ช่อง 1 note 60 velocity 40 → Song ที่ `hits` ว่าง `notes` `{pitch: 60, level: ghost}`
- MIDI ช่อง 10 note 38 → `hits` snare `notes` `[]`; ช่อง 10 note 60 → ไม่มีทั้งสอง
- MIDI ไม่มีการตีและไม่มีโน้ต หรือไม่ใช่ 4/4 → `415` "ไฟล์ MIDI ต้องเป็น 4/4 และมีแทร็กกลองหรือโน้ตทำนอง"
- ความยาวเพลง = ตัวสุดท้ายของการตีหรือโน้ต + 1 ห้อง
- `PUT /songs` ไฟล์ MIDI เดิมของเพลงที่ `notes` `null` → ตอบเพลงเดิม `analysis.notes` ครบ `hits` เท่าเดิม; เพลงที่มี `notes` แล้ว → `KnownSong` แบบเดิม

### หน้าเพลงและรายการเพลง

- รายการเพลง → คำใบ้ใต้ "เลือกไฟล์ในเครื่อง" มี "MIDI: ช่อง 10 เป็นกลอง ช่องอื่นเป็นทำนองสำหรับคาลิมบา" และ "ใช้ไฟล์ MIDI ที่ทำเองหรือมีสิทธิ์ใช้" (e2e)
- MIDI ที่ไม่รับ → ข้อความใหม่บนรายการเพลง (e2e)
- หน้าเพลงที่ `analysis.notes` 120 ตัว → ส่วน "Reel cover" มี "· 120 โน้ตทำนอง"; `notes` `null` → บรรทัดเดิม (e2e)
- test เดิมของ drum-notes และ drum-cover ผ่าน; `fakes.written_song` รับ `notes` โดย test เดิมเรียกแบบเดิมได้
