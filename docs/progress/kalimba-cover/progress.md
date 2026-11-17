# Progress: kalimba-cover

**Now:** merged ([PR #18](https://github.com/mousemouse094526/framecraft/pull/18), `2dff570`)

**Next:**

```
/warroom next
```

## Tickets

| # | Title | Status |
|---|---|---|
| 01 | โน้ตทำนองเข้าเพลง — จากการแกะและจากไฟล์ MIDI | done |
| 02 | เลือกคาลิมบาบนหน้า reel แล้วฟังทำนองที่จัดลงคาลิมบา | done |
| 03 | render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง | done |
| 04 | เสียงคาลิมบาจาก sample จริง VCSL แทนเสียงสังเคราะห์ | done |

## Log

### 04: เสียงคาลิมบาจาก sample จริง VCSL แทนเสียงสังเคราะห์ — done 2026-11-17

**Built:**
- `backend/kalimba_kit`: 14 ไฟล์ VCSL "Kalimba, Tanzania" (CC0) ที่ commit `c1ea7bc` (~9 MB) พร้อม pitch ที่วัดจากเสียงจริงและ sha256; `nearest(pitch)`; Setup โหลดต่อจาก sample กลอง (ลองสามครั้งต่อไฟล์); แถว Status check `kalimba_kit` ต่อจาก `drum_kit`; `paths.kalimba_samples_dir`/`kalimba_kit_marker`
- `kalimba_cover.sound.note(project, pitch, level)`: sample ใกล้สุด → ตัดความเงียบหน้า → ย้าย pitch และ 48 → 44.1 kHz ทีเดียวด้วย spectrum → กรองต่ำกว่า 0.7–0.9 × ความถี่คีย์ (คีย์อื่นที่ดังตาม) และสูงกว่า 4–9 kHz (เสียงซ่า) → fade out → peak ตาม level; `mix(project, timing)` gate แถว `kalimba_kit`
- `render.INSTRUMENTS` คาลิมบา: `sound.mix` ตรง, ฟัง gate `gate_rows.kalimba_kit_row`; `gate_rows.kalimba` เพิ่มแถว sample
- test: `fakes.fake_pluck`/`write_kalimba_kit` ใน `fake_root`; sound test ใหม่ (pitch ต่อคีย์, sample ใกล้สุด, กรองต่ำ/สูง, 503); Setup/Status/API test ของ sample คาลิมบา
- วัดด้วย sample จริง: ทุกคีย์ 17 ตัวตรงเสียง ±2 cent; MIDI Twinkle Twinkle (ช่อง 1, 14 โน้ต) import → cover ตั้งต้นคาลิมบา → render 2.6 วิ → ฟังกลับจาก mp4 ได้ 60 60 67 67 69 69 67 65 65 64 64 62 62 60 ตรงทุกโน้ต (Blocked 5): mp4 อยู่ที่ scratchpad ของ session ไม่ได้ commit
- docs: spec › เสียงคาลิมบา ใหม่ (7 ข้อ), Modules touched, Render job (ฟัง gate `kalimba_kit`), seams, Library assumptions; D5 → superseded by D18; ADR-0061 แทน ADR-0059; ADR-0042 extended by 0061; ADR-0060 changed by 0061; legal ข้อ 3 (CC0, ALLOWED); SKILL.md และ rules/testing.md

**Decided:**
- D18 — sample VCSL แทนเสียงสังเคราะห์ทุกกรณี (เจ้าของ); โหลด 14 จาก 27 ไฟล์ (ตัวที่ใกล้คีย์ใดคีย์หนึ่ง); pitch วัดจากเสียงจริงเพราะชื่อไฟล์ต่ำไปอ็อกเทฟและ mbira คลาด ±60 cent; resample ด้วย `numpy.fft` ไม่เพิ่ม scipy (ADR-0002)

**For the next ticket:**
- ระดับการกรองเสียงซ่า (`sound.BUZZ_FROM/TO` 4–9 kHz) และคีย์ต่ำ (`BELOW_FROM/TO`) ตั้งจากการวัด ไม่ได้ฟัง — เจ้าของฟังตอน review PR; ถ้ายังซ่าหรือทึบ ปรับสองค่านี้ที่เดียว
- review: `kalimba_kit` ลอก check/install/marker ของ `drum_kit` (และ `fonts`) — ชุดที่สาม; ถ้ามีชุด asset ที่สี่ ทำ helper "pinned files" (dir, marker, base_url, files) ใช้ร่วม
- คนที่ติดตั้งแล้วต้องรัน `./setup.sh` อีกครั้งเพื่อโหลด sample คาลิมบา (Status check บอก `missing` จนกว่าจะรัน)

**Checks:** `uv run pytest` 1555 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 622 passed; `npm --prefix frontend run build` ผ่าน; review สามแกน: แก้ทุกข้อ ยกเว้น helper ร่วมของ asset ที่ pin (For the next ticket)

### Feature review — done 2026-11-16

**Built:**
- `arrange.Changes(transpose, dropped, bent)`: one value through `Arranged`, `KalimbaTimeline.changes` and `CoverView` (API stays flat); `arrange.arranged_in(analysis, …)` replaces `cover.arranged_in` and the direct call in `timeline`; `TINES` → `TINE_PITCHES`, `KEYS`/`_key` → `TRANSPOSES`/`_transpose`
- `render._instrument_wav` builds the wav for render and ฟัง alike (was built inline in `_render`)
- `cover.hits_in(analysis, start_s, end_s)` used by `defaults` too
- `drum_cover.captions.riding(...)`: text that rides the picture, shared by the drum lanes' `_sliding` and the kalimba's bar numbers (ASS output unchanged)
- frontend: `NoNotes` union with `NO_NOTES_TEXT`/`NO_NOTES_LINK`, `backingLabels(name)` in `lib/cover` (spec: all new copy in one place)
- tests: `fakes.cover_api()` + `COVER_KEYS` for both cover API files (rules/testing.md); comments on the frames probe and the sync test's stride and half-peak
- docs: spec `reel_wav(audio, fields, instrument_wav, …)`, SKILL.md `instrument_wav`, D16 text; `frames.SLOWEST_PX_PER_S` comment (notes touch); `fill_notes` logs the notes kept; `_note_sprite(level: Level)`; `sound.mix` cache name

**Decided:** (dropped, auto mode took the recommended set)
- `SegmentedChoice` stays in `components/ui/` (D16 per D10)
- per-instrument map for every drums/kalimba switch, `InstrumentReel` as a `Protocol`, `frame_count(length_s)` — wait for a third instrument
- `bar_at(bars, t)`, the sync test's half-peak start, no job-level 20,000-note test, `beat_dots` signature (D14) — kept as they are
- `SongsPage` "MIDI ที่ไม่รับ" test checks the page shows the backend's message; the copy is the backend test's

**For the next ticket:** —

**Checks:** `uv run pytest` 1545 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 622 passed; `npm --prefix frontend run build` ผ่าน

### 03: render reel คาลิมบา — โน้ตตกลงบนคีย์ที่สว่างตรงเสียง — done 2026-11-16

**Built:**
- `kalimba_cover.frames`: คอลัมน์ 17 คีย์ โน้ตสีของเลขตกถึงเส้นเล่น (ต่ำสุด 350 px/วิ), คาลิมบาไม้ คีย์เหล็กมีแถบสีที่ปลาย, คีย์ที่เล่นเติมสีเต็ม ขอบขาว กว้างขึ้น 1.15 (accent 1.25) หดกลับใน 0.15 วิ, จุดอ็อกเทฟ, จุดจังหวะของ reel กลอง; `TINES` ตามตารางใน sketch
- `kalimba_cover.captions`: เลขและตัวอักษรใต้คีย์ 34 event, หัวเรื่อง/บรรทัดรอง/"ห้อง n" จาก `drum_cover.captions`, คำบรรยายบรรทัดเดียวเหนือคอลัมน์, เลขห้องตกตามเส้นห้อง
- `drum_cover`: `bars_of(beats)`, `bar_at(bars, t)`, `beat_dots(...)`, `text_styles`, `text_events`, `bar_counter_events`, `bar_style` แยกออกมาใช้ร่วม — ASS ของ reel กลองได้บรรทัดเดิมทุกบรรทัด (เทียบกับโค้ดก่อนแยก)
- `render`: `INSTRUMENTS` (timeline, เสียง, ASS, ภาพ, gate ต่อเครื่องดนตรี); ลำดับตรวจ 404/`no_analysis` → 400 → `no_notes` → 503 → `busy`; `.json` มี `instrument`, `kalimba` (เก่า → `drums`, `{on: true, volume: 100}`); `gate_rows.kalimba` = Kanit + ffmpeg + pythainlp
- หน้า reel: "render reel" กดได้เมื่อคาลิมบา; ป้ายแถวผล `soundLabel` ("คาลิมบา", "คาลิมบา 60%", "ไม่มีเสียงคาลิมบา")
- เจ้าของ: 3 เฟรมของ reel คาลิมบา Yellow 0–30 วิ (แกะสำเนาใน project ชั่วคราว ได้ 211 โน้ต จัดแล้ว 89 ย้ายคีย์ −4 ตัด 122 ปรับ 11): [07.1 วิ](frames/yellow-07.1s.jpg) · [12.0 วิ](frames/yellow-12.0s.jpg) · [20.0 วิ](frames/yellow-20.0s.jpg)
- เป้า D12 render: reel คาลิมบา 30 วิ render จบใน 5.6 วิบน Apple M1 (≤ 60 วิ ผ่าน); แกะ 0–30 วิโหมดกลอง 2.4 วิ

**Decided:**
- D17 — ลำดับตรวจ render ใช้กับกลองด้วย; `render.INSTRUMENTS`; คำบรรยายคาลิมบาบรรทัดเดียว (`text_events(..., with_caption=False)`); คีย์ที่เล่นจางกลับเป็นเหล็กพร้อมหดใน 0.15 วิ; เลขห้องตกตามเส้น; ป้ายผล render คาลิมบาเสมอ; ภาพเจ้าของจากสำเนา

**For the next ticket:**
- review: `render.InstrumentReel` พิมพ์ field เป็น `Callable[..., Any]` — ถ้ามีเครื่องดนตรีที่สาม ทำ `Protocol` ของ timeline/scene ให้ type ตรวจได้
- review: `beat_dots(frame, bars, beat_times, beats, t)` คง signature ตาม spec D14; `Scene` ทั้งสองถือ `bars` + `beat_times` คู่กัน — รวมเป็นวัตถุเดียวถ้าแตะอีก
- โน้ตคีย์เดียวกันห่าง 0.08 วิที่ 350 px/วิ ชิดกันพอดี 28 px (มุมมนแยกให้เห็น) — ถ้าเจ้าของดูแล้วเหมือนโน้ตเดียว ขึ้นความเร็วต่ำสุดได้ที่ `frames.SLOWEST_PX_PER_S`
- feature review: ข้อ review ของ ticket 02 ที่ยังไม่ทำ (`transpose`/`dropped`/`bent` เป็นวัตถุเดียว, fixture `project`/`client`/`COVER_KEYS` ซ้ำสองไฟล์ test)

**Checks:** `uv run pytest` 1545 passed; `npm --prefix frontend run typecheck` ผ่าน; `npm --prefix frontend test` 622 passed; `npm --prefix frontend run build` ผ่าน

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
| 1 | 01, 02, 03 | design: หน้า reel — ส่วนที่เพิ่ม, หน้าเพลงและรายการเพลง — ส่วนที่เพิ่ม | ไม่รอ Figma: สร้างตาม `ui-prompt.md` กับ design system เดิม (D10); แบบ Figma ภายหลัง → `/warroom kalimba-cover` พร้อมลิงก์ | open (ไม่กันการ merge) |
| 2 | 02 | เจ้าของฟังคาลิมบาของเพลงที่แกะจากเสียง (Yellow 11.5–30 แกะใหม่) ว่ายังจำทำนองได้ไหม (D12) | เจ้าของ: เปิด `#/songs/Ssz69tFTS7Y/cover` เลือก "คาลิมบา" กด "ฟัง" แล้วตอบ จำได้ / ไม่ได้ → `/warroom kalimba-cover` ถ้าไม่ได้ | done (เจ้าของ 2026-11-17: จำได้ แต่เสียงไม่เหมือนคาลิมบา → ข้อ 3) |
| 3 | 02 | เสียงสังเคราะห์พอไหม หรืออยากได้ sample จริง VCSL "Kalimba, Tanzania" (CC0, 27 คีย์ ~23 MB โหลดผ่าน Setup ต้องเลื่อน pitch เสียงออก mbira) (D5) | เจ้าของตอบหลังฟัง → `/warroom kalimba-cover` | done (ticket 04: sample VCSL ทุกกรณี, D18) |
| 4 | 03 | อยากให้รับ MusicXML (`.musicxml`, `.mxl` จาก MuseScore) ด้วยไหม; PDF และภาพไม่ทำ (D3) | เจ้าของตอบ → `/warroom kalimba-cover` (ticket แยก) | open (เจ้าของ 2026-11-17: ยังไม่ทำ เก็บไว้; ไม่กันการ merge) |
| 5 | 03 | เจ้าของ import MIDI ทำนองแล้วรับ reel คาลิมบาว่าเล่นทำนองถูก (D12) | เจ้าของ: import `.mid` ที่ `#/songs` เปิด reel แล้ว render | done (เจ้าของ 2026-11-17 ให้ทดสอบเอง; ticket 04 ตรวจด้วยโค้ดจริง ทุกโน้ตตรง pitch) |
