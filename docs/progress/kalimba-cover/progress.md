# Progress: kalimba-cover

**Now:** 01–02 done; 03 next

**Next:**

```
/warroom-build kalimba-cover 03
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI | done |
| 02 | เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา | done |
| 03 | render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง | ready |

## Log

### 02: เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา — done 2026-11-16

**Built:**
- `backend/kalimba_cover/`: `arrange` (ทิ้งเบส, ย้ายคีย์, `bent`, โน้ตบนสุดของคอร์ด, พับ octave, ตัดโน้ตซ้ำเร็ว; import แค่ `drum_notes.songs`), `timeline` (`KalimbaTimeline` sample + tine, เลขจังหวะจาก `drum_cover.timeline.numbered_beats`), `sound` (สังเคราะห์ 3 partial + เสียงกระทบ seed 0, ออกด้วย `mixer.to_wav` ตัวเดียวกับกลอง)
- `cover.json` มี `instrument` และ `kalimba {on, volume}`; ไฟล์เก่า → `drums` + `{on: true, volume: 100}`; ไม่มี cover กับช่วงไม่มีการตีแต่มีโน้ต → `kalimba`; `GET /cover` มี `notes`, `notes_picked`, `transpose`, `dropped`, `bent`; กฎห้ามเงียบใช้กับเครื่องดนตรีที่เลือก (`CoverFields.instrument_sound()`)
- ฟังย้ายไป `drum_cover.render.listen` + `render.instrument_wav`; `audio.reel_wav` รับ wav ของเครื่องดนตรี; คาลิมบาไม่ต้องมี sample กลอง; `409 no_notes` สามข้อความ
- `POST …/render` ของคาลิมบา → `409 not_ready` จน ticket 03 (review: ก่อนนี้ render reel กลองเงียบได้)
- หน้า reel: การ์ดเครื่องดนตรี (`components/ui/SegmentedChoice`, ใช้กับ "กลองล้วน/กลอง + เพลงต้นฉบับ" ด้วย), แถว "ความดังคาลิมบา", บรรทัดจำนวนโน้ต/ย้ายคีย์/ตัด/ปรับ, Alert โน้ต, คำเตือนย้ายคีย์กับ backing, "render reel" ปิดเมื่อคาลิมบา

**Decided:**
- D16 — ตัวเลขโน้ตเป็นของช่วงที่บันทึก; `listen` อยู่ `render`; `instrument` ผิด → `400`; seed เสียงกระทบ; ลิงก์ใน Alert; render คาลิมบา `409 not_ready`; `SegmentedChoice` อยู่ `components/ui/` ตาม D10

**For the next ticket:**
- ticket 03 แทน `409 not_ready` ใน `CoverRenderJobs.start` ด้วยลำดับตรวจของ spec › Render job และให้ `_render` ใช้ `render.instrument_wav` แทน `mixer.mix` ตรง (ตอนนี้ render กับ listen ผสมเสียงกลองคนละทาง)
- review: การแยก `instrument == "kalimba"` ยังกระจายหลายที่ (`cover.require_notes`, `cover.defaults`, `render.instrument_wav`, `render.listen`, `soundOf` และ ternary ใน `CoverPage`) — ถ้า ticket 03 เพิ่มอีก ให้รวมเป็น map ต่อเครื่องดนตรี (sound model, gate rows, timeline, mixer)
- review: `transpose`/`dropped`/`bent` เดินคู่กันใน `Arranged`, `KalimbaTimeline`, `CoverView`, TS `Cover` — พิจารณาวัตถุนับเดียว
- review: fixture `project`/`client` และรายการ key ของ PUT ซ้ำระหว่าง `test_drum_cover_api.py` กับ `test_kalimba_cover_api.py` (`COVER_KEYS`) — ย้ายเข้า `fakes.py` ถ้าเพิ่ม test ไฟล์ที่สาม
- frontend test "แกะก่อนเก็บโน้ต"/"ช่วงไม่มีโน้ต" assert "render reel" ปิด ซึ่งปิดเสมอเมื่อคาลิมบาใน ticket นี้ — ticket 03 เปิด render แล้ว assertion นี้จึงเริ่มทดสอบ gating จริง
- บรรทัดโน้ตและคำเตือนย้ายคีย์แสดงเฉพาะเมื่อช่วงที่พิมพ์ = ช่วงที่บันทึก (`savedStretch`, D16)

**Checks:** `uv run pytest` 1531 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 619 passed; `npm --prefix frontend run build` ผ่าน

### 01: โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI — done 2026-11-16

**Built:**
- แกะเพลงทุกโหมดได้โน้ตทำนองพร้อม pitch เก็บเป็น `analysis.notes` ข้างการตีกลอง: โหมดกลองรัน Basic Pitch ต่อจาก ADTOF (โมเดลไม่มีหรือพัง → `notes` `null` งานกลองจบตามเดิม), โหมดทำนองรัน Basic Pitch ครั้งเดียวได้ทั้ง snare และโน้ต; `song.json` เก่าอ่านเป็น `null`
- นำเข้าไฟล์ MIDI ทำนองล้วนได้ (ช่องอื่นนอกจาก 10 เป็นโน้ต); ไฟล์ MIDI เดิมของเพลงที่นำเข้าก่อน feature นี้ → `/check` ให้ส่งไฟล์อีกครั้ง แล้วเติม `notes` โดย `hits` เท่าเดิม; ข้อความ `415` ใหม่
- หน้าเพลง ส่วน "Reel cover" บอก "· {m} โน้ตทำนอง"; คำใบ้ใต้ "เลือกไฟล์ในเครื่อง" บอกช่อง MIDI และให้ใช้ไฟล์ที่มีสิทธิ์ใช้
- เป้า D12 Pick job: Yellow (`Ssz69tFTS7Y`) ช่วง 0–90 วิโหมดกลอง ด้วยโมเดลจริงบน Apple M1 จบใน 5.5 วิ (≤ 60 วิ ผ่าน) ได้ 392 การตี 600 โน้ต — วัดด้วย `_pick` ตรงแบบอ่านอย่างเดียว ไม่เขียน `song.json`

**Decided:**
- D15 — MIDI โน้ตเกิน 20,000 → `415`; เติม `notes` ของ MIDI เก่าเฉพาะในช่วง analysis เดิม; Basic Pitch พังในโหมดกลอง → log และหน้าต่างที่เหลือออกจาก `percent`; `/check` ของ MIDI เก่าที่ `notes` `null` ตอบ `{size}`; `midi.DrumTrack` → `MidiSong`

**For the next ticket:**
- `songs.Note(t, pitch, level)` และ `Analysis.notes` (None = แกะก่อน feature) คือสิ่งที่ `kalimba_cover.arrange` รับ; `notes_picked` = `analysis.notes is not None`
- `fakes.written_song(..., notes=[(t, pitch, level)])`; ไม่ส่ง = ไม่มี key `notes` ใน `song.json` แบบไฟล์เก่า; `fakes.drums_and_melody()` สร้าง MIDI กลอง + ทำนอง
- frontend: `Analysis.notes: MelodyNote[] | null` ใน `features/drum-notes/lib/songs.ts`
- การตัด 20,000 โน้ตแรก test ที่ `score.melody_notes` (seam 2) เท่านั้น ไม่มี test ระดับ Pick job; ถ้าเพิ่ม test ใน `test_drum_notes_pick_api.py` ใช้ `FakeOnnxRunner(onset=…)` ทุกคีย์ทุกสองเฟรม

**Checks:** `uv run pytest` 1500 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 612 passed; `npm --prefix frontend run build` ผ่าน

## Blocked

| # | Ticket | What | Needs | Status |
|---|---|---|---|---|
| 1 | 01, 02, 03 | design: หน้า reel — ส่วนที่เพิ่ม, หน้าเพลงและรายการเพลง — ส่วนที่เพิ่ม | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D10); แบบ Figma ภายหลัง → `/warroom kalimba-cover` พร้อมลิงก์ | open |
| 2 | 02 | เจ้าของฟังคาลิมบาของเพลงที่แกะจากเสียง (Yellow 11.5–30 แกะใหม่) ว่ายังจำทำนองได้ไหม (D12) | เจ้าของ: เปิด `#/songs/Ssz69tFTS7Y/cover` เลือก "คาลิมบา" กด "ฟัง" แล้วตอบ จำได้ / ไม่ได้ → `/warroom kalimba-cover` ถ้าไม่ได้ | open |
| 3 | 02 | เสียงสังเคราะห์พอไหม หรืออยากได้ sample จริง VCSL "Kalimba, Tanzania" (CC0, 27 คีย์ ~23 MB โหลดผ่าน Setup ต้องเลื่อน pitch เสียงออก mbira) (D5) | เจ้าของตอบหลังฟัง → `/warroom kalimba-cover` | open |
| 4 | 03 | อยากให้รับ MusicXML (`.musicxml`, `.mxl` จาก MuseScore) ด้วยไหม; PDF และภาพไม่ทำ (D3) | เจ้าของตอบ → `/warroom kalimba-cover` (ticket แยก) | open |
| 5 | 03 | เจ้าของ import MIDI ทำนองแล้วรับ reel คาลิมบาว่าเล่นทำนองถูก (D12) | เจ้าของ: import `.mid` ที่ `#/songs` เปิด reel แล้ว render | open |
